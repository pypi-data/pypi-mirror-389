from __future__ import annotations

import argparse
import os
import subprocess  # nosec B404
import sys
from pathlib import Path

from . import __version__
from .config import load_effective_config
from .publisher import Paths, _apply_env_fallback, plan_dry_run, preflight, publish
from .utils import PublishConfig, default_run_id


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("publish-allure")
    p.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    p.add_argument("--config", help="Path to YAML config (optional)")
    p.add_argument("--bucket")
    p.add_argument("--prefix", default=None)
    p.add_argument("--project")
    p.add_argument("--branch", default=os.getenv("GIT_BRANCH", "main"))
    p.add_argument(
        "--run-id",
        default=os.getenv("ALLURE_RUN_ID", default_run_id()),
    )
    # Do NOT pull env into the CLI default here; let the config loader
    # handle env as a lower-precedence source so YAML can override it.
    p.add_argument("--cloudfront", default=None)
    p.add_argument(
        "--results",
        "--results-dir",
        dest="results",
        default=os.getenv("ALLURE_RESULTS_DIR", "allure-results"),
        help="Path to allure-results directory (alias: --results-dir)",
    )
    p.add_argument(
        "--report",
        default=os.getenv("ALLURE_REPORT_DIR", "allure-report"),
        help="Output directory for generated Allure static report",
    )
    p.add_argument("--ttl-days", type=int, default=None)
    p.add_argument("--max-keep-runs", type=int, default=None)
    p.add_argument(
        "--sse",
        default=os.getenv("ALLURE_S3_SSE"),
        help="Server-side encryption algorithm (AES256 or aws:kms)",
    )
    p.add_argument(
        "--sse-kms-key-id",
        default=os.getenv("ALLURE_S3_SSE_KMS_KEY_ID"),
        help="KMS Key ID / ARN when --sse=aws:kms",
    )
    p.add_argument(
        "--s3-endpoint",
        default=os.getenv("ALLURE_S3_ENDPOINT"),
        help=("Custom S3 endpoint URL (e.g. http://localhost:4566)"),
    )
    p.add_argument("--summary-json", default=None)
    p.add_argument(
        "--context-url",
        default=os.getenv("ALLURE_CONTEXT_URL"),
        help="Optional hyperlink giving change context (e.g. Jira ticket)",
    )
    p.add_argument(
        "--meta",
        action="append",
        default=[],
        metavar="KEY=VAL",
        help=(
            "Attach arbitrary metadata (repeatable). Example: --meta "
            "jira=PROJ-123 --meta env=staging. Adds dynamic columns to "
            "runs index & manifest."
        ),
    )
    p.add_argument("--dry-run", action="store_true", help="Plan only")
    p.add_argument(
        "--check",
        action="store_true",
        help="Run preflight checks (AWS, allure, inputs)",
    )
    p.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip automatic preflight before publish (not recommended)",
    )
    p.add_argument(
        "--verbose-summary",
        action="store_true",
        help="Print extended summary (CDN prefixes, manifest path, metadata)",
    )
    p.add_argument(
        "--allow-duplicate-prefix-project",
        action="store_true",
        help=(
            "Bypass guard preventing prefix==project duplication. "
            "Only use if you intentionally want that folder layout."
        ),
    )
    p.add_argument(
        "--upload-workers",
        type=int,
        default=None,
        help="Parallel upload worker threads (auto if unset)",
    )
    p.add_argument(
        "--copy-workers",
        type=int,
        default=None,
        help="Parallel copy worker threads for latest promotion",
    )
    p.add_argument(
        "--archive-run",
        action="store_true",
        help="Also produce a compressed archive of the run (tar.gz)",
    )
    p.add_argument(
        "--archive-format",
        choices=["tar.gz", "zip"],
        default="tar.gz",
        help="Archive format when --archive-run is set",
    )
    p.add_argument(
        "--dashboard-dir",
        default=os.getenv("ALLURE_DASHBOARD_DIR"),
        help=(
            "Path to a local custom dashboard directory to publish under "
            "<prefix>/<project>/<branch>/latest/dashboard/."
        ),
    )
    p.add_argument(
        "--seed-dashboard",
        action="store_true",
        help=(
            "Upload a default dashboard page under latest/dashboard/ and seed "
            "web/static assets. No allure-results required."
        ),
    )
    p.add_argument(
        "--build-dashboard-from-manifest",
        action="store_true",
        help=(
            "After publish, build the full dashboard from the S3 runs "
            "manifest and deploy it under latest/dashboard/. "
            "Uses repo scripts if available; otherwise prints guidance."
        ),
    )
    p.add_argument(
        "--no-auto-seed-dashboard",
        action="store_true",
        help=(
            "Do not automatically seed the packaged dashboard when "
            "latest/dashboard/ is missing. By default the CLI seeds a minimal "
            "dashboard on first publish so styling works out-of-the-box."
        ),
    )
    return p.parse_args()


def _parse_metadata(pairs: list[str]) -> dict | None:
    if not pairs:
        return None
    meta: dict[str, str] = {}
    for raw in pairs:
        if "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k:
            continue
        safe_k = k.lower().replace("-", "_")
        if safe_k and v:
            meta[safe_k] = v
    return meta or None


def _build_cli_overrides(args: argparse.Namespace) -> dict:
    return {
        "bucket": args.bucket,
        "prefix": args.prefix,
        "project": args.project,
        "branch": args.branch,
        "cloudfront": args.cloudfront,
        "run_id": args.run_id,
        # Region and distribution id come from env/YAML; no
        # dedicated CLI flags needed
        "ttl_days": args.ttl_days,
        "max_keep_runs": args.max_keep_runs,
        "s3_endpoint": args.s3_endpoint,
        "context_url": args.context_url,
        "sse": args.sse,
        "sse_kms_key_id": args.sse_kms_key_id,
        "dashboard_dir": args.dashboard_dir,
    }


def _sanitize_branch(b: str) -> str:
    """Normalize CI-style branch refs like 'refs/heads/main' or 'origin/main'."""
    try:
        return b.replace("refs/heads/", "").replace("origin/", "")
    except Exception:
        return b


def _effective_config(args: argparse.Namespace) -> tuple[dict, PublishConfig]:
    overrides = _build_cli_overrides(args)
    effective = load_effective_config(overrides, args.config)
    cfg_source = effective.get("_config_file")
    if cfg_source:
        print(f"[config] loaded settings from {cfg_source}")
    missing = [k for k in ("bucket", "project") if not effective.get(k)]
    if missing:
        missing_list = ", ".join(missing)
        raise SystemExit(
            f"Missing required config values: {missing_list}. Provide via CLI, env, or YAML."
        )
    cfg = PublishConfig(
        bucket=effective["bucket"],
        prefix=effective.get("prefix") or "reports",
        project=effective["project"],
        branch=_sanitize_branch(effective.get("branch") or args.branch),
        run_id=effective.get("run_id") or args.run_id,
        cloudfront_domain=effective.get("cloudfront"),
        aws_region=effective.get("aws_region"),
        cloudfront_distribution_id=effective.get("cloudfront_distribution_id"),
        ttl_days=effective.get("ttl_days"),
        max_keep_runs=effective.get("max_keep_runs"),
        s3_endpoint=effective.get("s3_endpoint"),
        context_url=effective.get("context_url"),
        sse=effective.get("sse"),
        sse_kms_key_id=effective.get("sse_kms_key_id"),
        metadata=_parse_metadata(args.meta),
        upload_workers=args.upload_workers,
        copy_workers=args.copy_workers,
        archive_run=args.archive_run,
        archive_format=args.archive_format if args.archive_run else None,
        dashboard_dir=effective.get("dashboard_dir"),
    )
    # Guard against accidental duplication like prefix==project producing
    # 'reports/reports/<branch>/...' paths. This is usually unintentional
    # and makes report URLs longer / redundant. Fail fast so users can
    # correct config explicitly (they can still deliberately choose this
    # by changing either value slightly, e.g. prefix='reports',
    # project='team-reports').
    if cfg.prefix == cfg.project and not getattr(args, "allow_duplicate_prefix_project", False):
        parts = [
            "Invalid config: prefix and project are identical (",
            f"'{cfg.project}'). ",
            "This yields duplicated S3 paths (",
            f"{cfg.prefix}/{cfg.project}/<branch>/...). ",
            "Set distinct values (e.g. prefix='reports', project='payments').",
        ]
        raise SystemExit("".join(parts))
    return effective, cfg


def _write_json(path: str, payload: dict) -> None:
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _print_publish_summary(
    cfg: PublishConfig,
    out: dict,
    verbose: bool = False,
) -> None:
    print("Publish complete")
    if out.get("run_url"):
        print(f"Run URL: {out['run_url']}")
    if out.get("latest_url"):
        print(f"Latest URL: {out['latest_url']}")
    if out.get("dashboard_url"):
        print(f"Dashboard URL: {out['dashboard_url']}")
    # Main aggregated runs index (HTML) at branch root if CDN configured
    if cfg.cloudfront_domain:
        branch_root = f"{cfg.prefix}/{cfg.project}/{cfg.branch}"
        cdn_root = cfg.cloudfront_domain.rstrip("/")
        runs_index_url = f"{cdn_root}/{branch_root}/runs/index.html"
        print(f"Runs Index URL: {runs_index_url}")
    run_prefix = out.get("run_prefix") or cfg.s3_run_prefix
    latest_prefix = out.get("latest_prefix") or cfg.s3_latest_prefix
    print(f"S3 run prefix: s3://{cfg.bucket}/{run_prefix}")
    print(f"S3 latest prefix: s3://{cfg.bucket}/{latest_prefix}")
    print(
        "Report files: "
        f"{out.get('report_files', '?')}  Size: "
        f"{out.get('report_size_bytes', '?')} bytes"
    )
    if verbose and cfg.cloudfront_domain:
        # Duplicate earlier lines but clarify this is the CDN-root mapping
        print("CDN run prefix (index root):", cfg.url_run())
        print("CDN latest prefix (index root):", cfg.url_latest())
    if verbose:
        # Manifest stored at branch root under runs/index.json
        branch_root = f"{cfg.prefix}/{cfg.project}/{cfg.branch}"
        manifest_key = f"{branch_root}/runs/index.json"
        print("Manifest object:", f"s3://{cfg.bucket}/{manifest_key}")
        if cfg.metadata:
            print("Metadata keys:", ", ".join(sorted(cfg.metadata.keys())))
        if cfg.sse:
            print("Encryption:", cfg.sse, cfg.sse_kms_key_id or "")


def main() -> int:  # noqa: C901 (reduced but keep guard just in case)
    args = parse_args()
    if args.version:
        print(__version__)
        return 0
    effective, cfg = _effective_config(args)
    cfg = _apply_env_fallback(cfg)
    # Shortcut: seed default dashboard/static assets (no allure-results needed)
    if getattr(args, "seed_dashboard", False):
        try:
            from .publisher import seed_dashboard  # lazy import to avoid cycle

            out = seed_dashboard(cfg)
            print(out)
            print("Dashboard seeded")
            if out.get("dashboard_url"):
                print("Dashboard URL:", out["dashboard_url"])  # noqa: T201
            return 0
        except SystemExit:
            raise
        except Exception as e:  # pragma: no cover - non-critical helper
            print("Failed to seed dashboard:", e)
            return 2
    # Construct explicit Paths honoring custom results/report dirs
    paths = Paths(results=Path(args.results), report=Path(args.report))

    def _checks_pass(chk: dict) -> bool:
        # Prefer explicit gate if provided by preflight()
        if isinstance(chk.get("preflight_ok"), bool):
            return bool(chk["preflight_ok"])  # explicit gate from preflight

        # Use the same critical keys preflight() validates
        gate_keys = [
            "allure_cli",
            "allure_results",
            "s3_bucket",
            "config_bucket_present",
            "config_aws_region_present",
            "config_cloudfront_distribution_id_present",
            "s3_public_access_block",
            "s3_bucket_not_public",
            "cloudfront_found",
            "cloudfront_deployed",
            "cloudfront_oac",
        ]
        present = [k for k in gate_keys if k in chk]
        if present:
            return all(bool(chk[k]) for k in present)

        # No recognized signals → be conservative
        return False

    if args.check:
        checks = preflight(cfg, paths=paths)
        print(checks)
        # Concise success line for humans
        if _checks_pass(checks):
            bucket = cfg.bucket
            region = getattr(cfg, "aws_region", None) or checks.get("bucket_region") or "?"
            dist = (
                getattr(cfg, "cloudfront_distribution_id", None)
                or checks.get("cloudfront_distribution_id")
                or "?"
            )
            print(
                "[preflight] OK — bucket=",
                bucket,
                ", region=",
                region,
                ", distribution=",
                dist,
                sep="",
            )
            return 0
        else:
            return 2
    if args.dry_run:
        plan = plan_dry_run(cfg, paths=paths)
        print(plan)
        if args.summary_json:
            _write_json(args.summary_json, plan)
        return 0
    # Automatic preflight prior to publish unless explicitly skipped
    if not args.skip_preflight:
        checks = preflight(cfg, paths=paths)
        if not _checks_pass(checks):
            print("Preflight failed; refusing to publish. Details:")
            print(checks)
            # Help pinpoint failing gates using the critical set
            try:
                gate_keys = [
                    "allure_cli",
                    "allure_results",
                    "s3_bucket",
                    "config_bucket_present",
                    "config_aws_region_present",
                    "config_cloudfront_distribution_id_present",
                    "s3_public_access_block",
                    "s3_bucket_not_public",
                    "cloudfront_found",
                    "cloudfront_deployed",
                    "cloudfront_oac",
                ]
                failed = [k for k in gate_keys if checks.get(k) is False]
                if failed:
                    print("Failing gates:", ", ".join(sorted(failed)))
            except Exception:
                # do not block on diagnostics
                print("[preflight] gate diagnostics suppressed")
            return 2
        # Concise success line for humans
        bucket = cfg.bucket
        region = getattr(cfg, "aws_region", None) or checks.get("bucket_region") or "?"
        dist = (
            getattr(cfg, "cloudfront_distribution_id", None)
            or checks.get("cloudfront_distribution_id")
            or "?"
        )
        print(
            "[preflight] OK — bucket=",
            bucket,
            ", region=",
            region,
            ", distribution=",
            dist,
            sep="",
        )
        # (duplicate concise line removed)
    # Auto-seed default dashboard on first publish so styling works
    # out-of-the-box (can be disabled via --no-auto-seed-dashboard or env)
    # (can be disabled via --no-auto-seed-dashboard or env)
    # Track dashboard presence before publish to tailor later messages
    dash_exists_pre: bool | None = None
    try:
        disable_auto_seed = bool(
            getattr(args, "no_auto_seed_dashboard", False)
            or os.getenv("ALLURE_NO_AUTO_SEED_DASHBOARD") in {"1", "true", "True", "yes", "YES"}
            or os.getenv("ALLURE_AUTO_SEED_DASHBOARD") in {"0", "false", "False", "no", "NO"}
        )
        if not disable_auto_seed:
            # Compute the expected S3 key for dashboard index
            branch_root = f"{cfg.prefix}/{cfg.project}/{cfg.branch}"
            dash_key = f"{branch_root}/latest/dashboard/index.html"
            # Use region from config; if preflight was skipped, this
            # still works because S3 is global and boto can resolve.
            region_hint = getattr(cfg, "aws_region", None)
            try:
                import boto3  # lazy import

                s3 = boto3.client("s3", region_name=region_hint)
                exists = True
                try:
                    s3.head_object(Bucket=cfg.bucket, Key=dash_key)
                    print(
                        "[dash] latest/dashboard/index.html present — "
                        "skipping auto-seed (will preserve during publish)"
                    )
                    dash_exists_pre = True
                except Exception:
                    exists = False  # 404/access → treat as missing
                if not exists:
                    print("[dash] Auto-seeding default dashboard (first publish)...")
                    from .publisher import seed_dashboard  # lazy import

                    try:
                        _ = seed_dashboard(cfg)
                        print("[dash] Seeded dashboard under latest/dashboard/ (packaged assets)")
                        dash_exists_pre = False
                    except Exception as e:  # pragma: no cover
                        print("[dash] Auto-seed failed (continuing):", e)
            except Exception as _auto_err:
                # boto3 missing or head failed; do not block publish
                print("[dash] Auto-seed skipped:", _auto_err)
    except Exception as _outer_auto_err:
        # Never block main publish path on auto-seed guardrails
        print("[dash] Auto-seed guard failed:", _outer_auto_err)

    out = publish(cfg, paths=paths)
    print(out)  # raw dict for backward compatibility
    _print_publish_summary(cfg, out, verbose=args.verbose_summary)
    if args.summary_json:
        _write_json(args.summary_json, out)
    # Optional: build and deploy the full dashboard using repo scripts.
    # Enabled when --build-dashboard-from-manifest is passed OR when
    # config/env sets auto_build_dashboard=true.
    should_build = bool(getattr(args, "build_dashboard_from_manifest", False))
    if not should_build:
        abd = effective.get("auto_build_dashboard")
        if isinstance(abd, bool) and abd:
            should_build = True
    if not should_build:
        env_abd = str(os.getenv("ALLURE_AUTO_BUILD_DASHBOARD", "")).strip().lower()
        if env_abd in {"1", "true", "yes"}:
            should_build = True
    if should_build:
        # Final stage: dashboard data/enrichment
        print("[publish] [7/7] Dashboard data — preparing…")
        # Scripts live in dev/scripts/, template in dashboard/.
        # Only run if present in this checkout.
        build_script = Path("dev/scripts/build_dashboard_from_manifest.py")
        deploy_script = Path("dev/scripts/deploy_dashboard.py")
        template_html = Path("dashboard/template.html")
        dist_dir = Path("dist")
        if not build_script.exists() or not deploy_script.exists() or not template_html.exists():
            # Inline fallback: seed packaged dashboard and write enriched data
            try:
                from .publisher import seed_dashboard, write_dashboard_data_enriched_from_manifest
            except Exception:
                seed_dashboard = None  # type: ignore
                write_dashboard_data_enriched_from_manifest = None  # type: ignore
            print(
                "[dash] Helper scripts not found — attempting inline enrichment from manifest (wheel-safe)."
            )
            try:
                if seed_dashboard:
                    _ = seed_dashboard(cfg)
                ok = bool(
                    write_dashboard_data_enriched_from_manifest
                    and write_dashboard_data_enriched_from_manifest(cfg)
                )  # type: ignore
                if ok:
                    print("[dash] Inline enrichment: OK — wrote latest/dashboard/data/*")
                    print(
                        "[dash] Tip: invalidate CDN paths to refresh: allurehost-infra-invalidate --paths dashboard\n"
                        f"[dash] Paths to invalidate: /{cfg.prefix}/{cfg.project}/{cfg.branch}/latest/dashboard/data/*, "
                        f"/{cfg.prefix}/{cfg.project}/{cfg.branch}/latest/dashboard/index.html"
                    )
                else:
                    # Provide a more specific note based on what we know
                    if write_dashboard_data_enriched_from_manifest is None:
                        reason = "dashboard module not available in this install"
                    else:
                        reason = "runs manifest/widgets not available for enrichment"
                    preserve_msg = (
                        "preserved existing dashboard"
                        if dash_exists_pre is True
                        else "seeded default dashboard"
                    )
                    print(
                        f"[dash] Inline enrichment unavailable ({reason}); {preserve_msg}. "
                        "Top failing tests or suite breakdown may be empty until widgets are present or helper scripts are used."
                    )
            except Exception as e:
                print("[dash] Inline build failed:", e)
            return 0
        # Build dashboard dist/ from manifest
        try:
            cmd_build = [
                sys.executable,
                str(build_script),
                "--out",
                str(dist_dir),
                "--template",
                str(template_html),
            ]
            # Pass through explicit config file if provided
            if args.config:
                cmd_build += ["--config", args.config]
            print("[dash] Build scripts present — building dashboard from manifest…")
            # Security note (S603/B603): fixed args + validated paths;
            # uses sys.executable; no shell interpolation.
            # Ensure local repo modules (e.g., 'dashboard') are
            # importable by script
            env = dict(os.environ)
            existing_pp = env.get("PYTHONPATH", "")
            # Build PYTHONPATH portably without shadowing 'paths'
            pp_segments = [os.getcwd()]
            # Also include the directory of the provided config file
            try:
                if args.config:
                    pp_segments.append(str(Path(args.config).resolve().parent))
            except Exception:
                ...
            # Build PYTHONPATH value (use os.pathsep for portability)
            joined = os.pathsep.join(pp_segments)
            env["PYTHONPATH"] = f"{joined}{os.pathsep}{existing_pp}" if existing_pp else joined
            # Optional debug of PYTHONPATH to help diagnose import issues
            try:
                if os.environ.get("ALLURE_HOST_DEBUG"):
                    print("[dash] PYTHONPATH=", env.get("PYTHONPATH", ""))
            except Exception:
                ...
            subprocess.run(cmd_build, check=True, env=env)  # noqa: S603  # nosec B603
        except subprocess.CalledProcessError as e:  # pragma: no cover
            print("[dash] Build failed (skipping deploy):", e)
            return 2
        # Deploy dashboard to latest/dashboard/
        try:
            cmd_deploy = [
                sys.executable,
                str(deploy_script),
                "--out",
                str(dist_dir),
                "--prefix",
                "dashboard",
            ]
            if args.config:
                cmd_deploy += ["--config", args.config]
            print("[dash] Deploying dashboard to latest/dashboard/…")
            # Security: fixed args + validated paths.
            # Uses sys.executable; no shell.
            subprocess.run(cmd_deploy, check=True, env=env)  # noqa: S603  # nosec B603
            # Optional note about CDN invalidation
            msg = (
                "[dash] Deployed. If you changed template/assets, consider invalidating dashboard paths.\n"
                f"[dash] Paths to invalidate: /{cfg.prefix}/{cfg.project}/{cfg.branch}/latest/dashboard/*"
            )
            print(msg)
        except subprocess.CalledProcessError as e:  # pragma: no cover
            print("[dash] Deploy failed:", e)
            return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
