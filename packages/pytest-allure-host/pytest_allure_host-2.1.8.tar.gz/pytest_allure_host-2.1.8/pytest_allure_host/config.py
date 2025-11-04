"""Configuration loading utilities (YAML + env) for Allure hosting publisher.

Precedence (highest first):
1. Explicit CLI / pytest flag values
2. YAML file values (provided via --config or auto-discovered; overrides ENV)
3. Environment variables (ALLURE_BUCKET, ALLURE_PREFIX, ...; provide bootstrap/defaults)
4. Built-in defaults

Auto-discovery order if --config not supplied:
- ./allure-host.yml
- ./allure-host.yaml
- ./.allure-host.yml
- ./.allure-host.yaml

YAML schema (example):

    bucket: my-reports-bucket
    prefix: reports
    project: payments
    branch: main
    ttl_days: 30
    max_keep_runs: 20
    cloudfront: https://reports.example.com
    retention:
      default_ttl_days: 30           # alias of ttl_days
      max_keep_runs: 20              # duplicate path accepted

Unknown keys are ignored (forward compatible).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILENAMES = [
    # YAML (legacy / original)
    "allure-host.yml",
    "allure-host.yaml",
    ".allure-host.yml",
    ".allure-host.yaml",
    # TOML (new preferred simple format)
    "allurehost.toml",
    ".allurehost.toml",
    # Additional generic app config names people often use:
    "application.yml",
    "application.yaml",
]

ENV_MAP = {
    "bucket": "ALLURE_BUCKET",
    "prefix": "ALLURE_PREFIX",
    "project": "ALLURE_PROJECT",
    "branch": "ALLURE_BRANCH",
    "cloudfront": "ALLURE_CLOUDFRONT",
    # Optional explicit region and distribution id for stricter preflight
    "aws_region": "ALLURE_AWS_REGION",
    "cloudfront_distribution_id": "ALLURE_CLOUDFRONT_DISTRIBUTION_ID",
    "run_id": "ALLURE_RUN_ID",
    "ttl_days": "ALLURE_TTL_DAYS",
    "max_keep_runs": "ALLURE_MAX_KEEP_RUNS",
    "s3_endpoint": "ALLURE_S3_ENDPOINT",
    "context_url": "ALLURE_CONTEXT_URL",
    # optional local custom dashboard directory
    "dashboard_dir": "ALLURE_DASHBOARD_DIR",
    # optionally auto-build dashboard from manifest after publish
    "auto_build_dashboard": "ALLURE_AUTO_BUILD_DASHBOARD",
}


def _normalize_cloudfront_domain(val: str | None) -> str | None:
    if not val:
        return None
    v = str(val).strip().rstrip("/")
    if not v:
        return None
    if v.startswith("http://") or v.startswith("https://"):
        return v
    return f"https://{v}"


@dataclass
class LoadedConfig:
    source_file: Path | None
    data: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f) or {}
        if not isinstance(content, dict):
            return {}
        return content
    except FileNotFoundError:
        return {}
    except Exception:
        # best effort - ignore malformed file
        return {}


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        import sys

        if sys.version_info >= (3, 11):  # stdlib tomllib
            import tomllib  # type: ignore
        else:  # fallback to optional dependency
            import tomli as tomllib  # type: ignore
    except Exception:  # pragma: no cover - toml not available
        return {}
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # pragma: no cover - malformed
        return {}


def discover_yaml_config(explicit: str | None = None) -> LoadedConfig:
    if explicit:
        p = Path(explicit)
        if p.suffix.lower() == ".toml":
            return LoadedConfig(
                source_file=p if p.exists() else None,
                data=_read_toml(p),
            )
        return LoadedConfig(
            source_file=p if p.exists() else None,
            data=_read_yaml(p),
        )
    for name in CONFIG_FILENAMES:
        p = Path(name)
        if p.exists():
            if p.suffix.lower() == ".toml":
                return LoadedConfig(source_file=p, data=_read_toml(p))
            return LoadedConfig(source_file=p, data=_read_yaml(p))
    return LoadedConfig(source_file=None, data={})


def merge_config(  # noqa: C901 - complex but intentional merge precedence
    yaml_cfg: dict[str, Any],
    env: dict[str, str],
    cli_overrides: dict[str, Any],
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    # Support nested structure under `allure_host:`
    base_yaml = (
        yaml_cfg.get("allure_host")
        if (isinstance(yaml_cfg, dict) and isinstance(yaml_cfg.get("allure_host"), dict))
        else yaml_cfg
    )

    # 1) Start with ENVIRONMENT (bootstrap/defaults)
    for key, env_var in ENV_MAP.items():
        if env_var in env and env[env_var]:
            merged[key] = env[env_var]

    # 2) Overlay YAML (YAML should win over ENV when present)
    if isinstance(base_yaml, dict):
        merged.update(base_yaml)

    # retention nested block normalization (YAML-driven)
    retention = base_yaml.get("retention") if isinstance(base_yaml, dict) else None
    if isinstance(retention, dict):
        # YAML aliases take precedence even if ENV provided values
        if retention.get("default_ttl_days") is not None:
            merged["ttl_days"] = retention.get("default_ttl_days")
        if retention.get("max_keep_runs") is not None:
            merged["max_keep_runs"] = retention.get("max_keep_runs")

    # YAML key aliases (override ENV when YAML provides alias values)
    if isinstance(base_yaml, dict):
        if base_yaml.get("region") is not None:
            merged["aws_region"] = base_yaml.get("region")
        dist_id = base_yaml.get("distribution_id")
        if dist_id is not None:
            merged["cloudfront_distribution_id"] = dist_id
        # Accept cf_domain/cloudfront_domain → canonical 'cloudfront'
        alt_cf = base_yaml.get("cloudfront_domain") or base_yaml.get("cf_domain")
        if alt_cf:
            merged["cloudfront"] = alt_cf

    # 3) explicit CLI overrides (ignore None only) – highest precedence
    for k, v in cli_overrides.items():
        if v is not None:
            merged[k] = v

    # type adjust
    for int_field in ("ttl_days", "max_keep_runs"):
        if int_field in merged and merged[int_field] not in (None, ""):
            try:
                merged[int_field] = int(merged[int_field])
            except ValueError:
                merged[int_field] = None

    return merged


def load_effective_config(  # noqa: C901 - orchestrates discovery/env handling
    cli_args: dict[str, Any], explicit_config: str | None = None
) -> dict[str, Any]:
    loaded = discover_yaml_config(explicit_config)
    # If a YAML config file is present, ignore ambient environment variables
    # for required keys to avoid accidental leakage from the developer/CI env.
    # This ensures missing required fields remain None when YAML is partial.
    if loaded.source_file is not None:
        # Allow env for non-required/optional fields only when YAML exists.
        REQUIRED_KEYS = {"bucket", "aws_region", "cloudfront_distribution_id"}
        filtered_env: dict[str, str] = {}
        for key, env_var in ENV_MAP.items():
            if key in REQUIRED_KEYS:
                continue
            val = os.environ.get(env_var)
            if val is not None:
                filtered_env[env_var] = val
        env_for_merge = filtered_env
    else:
        env_for_merge = dict(os.environ)
    data = merge_config(loaded.data, env_for_merge, cli_args)

    # Attach source path (if any)
    data["_config_file"] = str(loaded.source_file) if loaded.source_file else None

    # Additional generic env fallbacks (e.g. when only `.infra_env` is sourced)
    # Apply only when no YAML config file is present.
    if loaded.source_file is None:
        if not data.get("bucket"):
            env_bucket = os.getenv("ALLURE_BUCKET") or os.getenv("BUCKET")
            if env_bucket:
                data["bucket"] = env_bucket

        if not data.get("project"):
            env_project = os.getenv("ALLURE_PROJECT") or os.getenv("PROJECT")
            if env_project:
                data["project"] = env_project

        if not data.get("branch"):
            env_branch = os.getenv("ALLURE_BRANCH") or os.getenv("BRANCH")
            if env_branch:
                data["branch"] = env_branch

        if not data.get("prefix"):
            env_prefix = os.getenv("ALLURE_PREFIX") or os.getenv("PREFIX")
            if env_prefix:
                data["prefix"] = env_prefix

    # --- Environment fallbacks for common variables (.infra_env etc.) ---
    # Region: prefer explicit ALLURE_AWS_REGION (handled in merge_config),
    # then fall back to standard AWS envs if still missing.
    if loaded.source_file is None:
        if not data.get("aws_region"):
            data["aws_region"] = (
                os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or data.get("aws_region")
            )

    # CloudFront values from env
    # CloudFront domain may be provided via env even when YAML exists,
    # but only fill when missing in the merged data (do not override YAML/CLI).
    if not data.get("cloudfront"):
        cf_env = (
            os.getenv("ALLURE_CLOUDFRONT")
            or os.getenv("CF_DOMAIN")
            or os.getenv("CLOUDFRONT_DOMAIN")
        )
        if cf_env:
            data["cloudfront"] = cf_env
    # Prefer explicit domain env for cloudfront_domain (preserve scheme)
    cf_dom_env = os.getenv("CF_DOMAIN") or os.getenv("CLOUDFRONT_DOMAIN")
    if cf_dom_env and not data.get("cloudfront_domain"):
        data["cloudfront_domain"] = cf_dom_env

    # Distribution id: allow explicit env or .infra_env's DISTRIBUTION_ID
    if loaded.source_file is None:
        if not data.get("cloudfront_distribution_id"):
            dist_env = (
                os.getenv("ALLURE_CLOUDFRONT_DISTRIBUTION_ID")
                or os.getenv("DISTRIBUTION_ID")
                or os.getenv("CF_DISTRIBUTION_ID")
            )
            if dist_env:
                data["cloudfront_distribution_id"] = dist_env

    # --- Keep cloudfront and cloudfront_domain in sync (normalized)
    dom_src = data.get("cloudfront_domain") or data.get("cloudfront")
    norm_dom = _normalize_cloudfront_domain(dom_src)
    if norm_dom:
        data["cloudfront_domain"] = norm_dom
        # Also mirror to 'cloudfront' for URL assembly elsewhere
        data["cloudfront"] = norm_dom

    # If only cloudfront_domain is present, mirror to cloudfront as well
    if data.get("cloudfront_domain") and not data.get("cloudfront"):
        data["cloudfront"] = data["cloudfront_domain"]

    # Optional INFO logging of config sources when ALLURE_HOST_DEBUG=1
    try:
        debug_on = str(os.getenv("ALLURE_HOST_DEBUG", "")).strip().lower() in {"1", "true", "yes"}
        if debug_on:
            logger = logging.getLogger("pytest_allure_host.config")
            # Build a human-friendly source map for key fields
            src_map: dict[str, str] = {}
            # Helper closures

            def _yaml_val(keys: list[str]) -> Any:
                y = loaded.data
                if isinstance(y, dict) and isinstance(y.get("allure_host"), dict):
                    y = y.get("allure_host") or {}
                # direct keys
                for k in keys:
                    if isinstance(y, dict) and y.get(k) is not None:
                        return y.get(k)
                # retention aliases
                if "ttl_days" in keys and isinstance(y, dict):
                    ret = y.get("retention") or {}
                    if isinstance(ret, dict) and ret.get("default_ttl_days") is not None:
                        return ret.get("default_ttl_days")
                if "max_keep_runs" in keys and isinstance(y, dict):
                    ret2 = y.get("retention") or {}
                    if isinstance(ret2, dict) and ret2.get("max_keep_runs") is not None:
                        return ret2.get("max_keep_runs")
                return None

            def _env_val(vars_: list[str]) -> Any:
                for v in vars_:
                    if os.getenv(v):
                        return os.getenv(v)
                return None

            fields = {
                "bucket": (["bucket"], ["ALLURE_BUCKET", "BUCKET"]),
                "prefix": (["prefix"], ["ALLURE_PREFIX", "PREFIX"]),
                "project": (["project"], ["ALLURE_PROJECT", "PROJECT"]),
                "branch": (["branch"], ["ALLURE_BRANCH", "BRANCH"]),
                "aws_region": (
                    ["aws_region", "region"],
                    ["ALLURE_AWS_REGION", "AWS_REGION", "AWS_DEFAULT_REGION"],
                ),
                "cloudfront_distribution_id": (
                    ["cloudfront_distribution_id", "distribution_id"],
                    [
                        "ALLURE_CLOUDFRONT_DISTRIBUTION_ID",
                        "DISTRIBUTION_ID",
                        "CF_DISTRIBUTION_ID",
                    ],
                ),
                "cloudfront_domain": (
                    ["cloudfront", "cloudfront_domain", "cf_domain"],
                    ["ALLURE_CLOUDFRONT", "CF_DOMAIN", "CLOUDFRONT_DOMAIN"],
                ),
                "ttl_days": (["ttl_days"], ["ALLURE_TTL_DAYS"]),
                "max_keep_runs": (["max_keep_runs"], ["ALLURE_MAX_KEEP_RUNS"]),
                "s3_endpoint": (["s3_endpoint"], ["ALLURE_S3_ENDPOINT"]),
                "context_url": (["context_url"], ["ALLURE_CONTEXT_URL"]),
            }
            # Determine source per key
            for k, (yaml_keys, env_vars) in fields.items():
                if cli_args.get(k) is not None:
                    src_map[k] = "cli"
                    continue
                yv = _yaml_val(yaml_keys)
                if yv is not None:
                    src_map[k] = "yaml"
                    continue
                ev = _env_val(env_vars)
                if ev is not None:
                    src_map[k] = "env"
                else:
                    src_map[k] = "default"

            # Pretty print a compact summary (similar to example)
            lines = ["Loaded config:"]
            show_keys = [
                "bucket",
                "aws_region",
                "cloudfront_distribution_id",
                "cloudfront_domain",
                "project",
                "branch",
            ]
            for sk in show_keys:
                if sk in data:
                    val = data.get(sk)
                    src = src_map.get(sk, "?")
                    lines.append(f"  {sk} = {val}  ({src})")
            logger.info("\n".join(lines))
    except Exception as e:
        # Never fail config loading due to logging
        try:
            logging.getLogger("pytest_allure_host.config").debug(
                "config source logging suppressed: %s", e
            )
        except Exception:
            # ignore secondary logging issues
            ...

    return data


# --- Backward-compat alias -------------------------------------------------


def load_config(
    cli_args: dict[str, Any] | None = None,
    explicit_config: str | None = None,
) -> dict[str, Any]:
    """Backward-compatible alias for older callers/imports.
    Mirrors previous API where `load_config` returned the effective dict.
    """
    return load_effective_config(cli_args or {}, explicit_config)
