# ruff: noqa: E501
# flake8: noqa
"""Infrastructure CLI wrapper for AWS setup commands.

Provides console script entry points for AWS infrastructure management
without requiring the full repository clone.

This module intentionally mirrors a few convenience targets from the
repository Makefile so users who install the Python package (wheel)
can perform the same actions without cloning the repo:

- Deploy a prebuilt dashboard directory to S3 under
    ``<prefix>/<project>/<branch>/latest/dashboard/`` with correct
    cache headers.
- Invalidate CloudFront paths for the dashboard and/or runs index.
- Reconstruct a minimal ``.infra_env`` via ``write-env`` (exposed as
    a console script in setup).

All commands prefer values from an explicit YAML config
(``--config``), then fall back to ``.infra_env`` and environment
variables. The S3 bucket and CloudFront distribution must already be
provisioned (use ``allurehost-infra-setup``).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # noqa: S404  # nosec - CLI helper uses subprocess intentionally
import sys
import tempfile
import time
from pathlib import Path

import boto3
import yaml
from botocore.exceptions import ClientError

from .config import discover_yaml_config, load_effective_config
from .utils import PublishConfig, branch_root


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(  # noqa: S603,S607  # nosec - controlled args
            cmd, check=check, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        if e.stdout:
            print(f"stdout: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        raise


def check_aws_cli() -> bool:
    """Check if AWS CLI is available and configured."""
    try:
        run_cmd(["aws", "--version"])
        run_cmd(["aws", "sts", "get-caller-identity"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_aws_region() -> str | None:
    """Get AWS region from environment or AWS config."""
    region = os.getenv("AWS_REGION")
    if region:
        return region

    try:
        result = run_cmd(["aws", "configure", "get", "region"], check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return None


def wait_for_cf_deployed(
    distribution_id: str,
    timeout_sec: int = 900,
    poll_interval_sec: int = 15,
) -> bool:
    """Poll CloudFront distribution status until Deployed or timeout.

    Returns True if Deployed within timeout, else False.
    """
    start = time.monotonic()
    last_status = ""
    while True:
        try:
            result = run_cmd(
                [
                    "aws",
                    "cloudfront",
                    "get-distribution",
                    "--id",
                    distribution_id,
                    "--query",
                    "Distribution.Status",
                    "--output",
                    "text",
                ],
                check=False,
            )
            status = (result.stdout or "").strip()
        except subprocess.CalledProcessError:
            status = ""

        if status and status != last_status:
            print(f"CloudFront status: {status}")
            last_status = status

        if status == "Deployed":
            return True

        if time.monotonic() - start > timeout_sec:
            return False

        time.sleep(poll_interval_sec)


def check_bucket_exists(bucket: str, region: str) -> bool:
    """Check if S3 bucket exists and is accessible."""
    try:
        run_cmd(["aws", "s3api", "head-bucket", "--bucket", bucket, "--region", region])
        return True
    except subprocess.CalledProcessError:
        return False


def create_bucket(bucket: str, region: str) -> bool:
    """Create S3 bucket if it doesn't exist."""
    if check_bucket_exists(bucket, region):
        print(f"Bucket {bucket} already exists in {region}")
        return True

    try:
        print(f"Creating bucket {bucket} in {region}...")
        if region == "us-east-1":
            # us-east-1 doesn't need LocationConstraint
            run_cmd(["aws", "s3api", "create-bucket", "--bucket", bucket, "--region", region])
        else:
            run_cmd(
                [
                    "aws",
                    "s3api",
                    "create-bucket",
                    "--bucket",
                    bucket,
                    "--region",
                    region,
                    "--create-bucket-configuration",
                    f"LocationConstraint={region}",
                ]
            )

        # Enable versioning
        run_cmd(
            [
                "aws",
                "s3api",
                "put-bucket-versioning",
                "--bucket",
                bucket,
                "--versioning-configuration",
                "Status=Enabled",
            ]
        )

        # Block public access
        block_config = (
            "BlockPublicAcls=true,IgnorePublicAcls=true,"
            "BlockPublicPolicy=true,RestrictPublicBuckets=true"
        )
        run_cmd(
            [
                "aws",
                "s3api",
                "put-public-access-block",
                "--bucket",
                bucket,
                "--public-access-block-configuration",
                block_config,
            ]
        )

        print(f"Successfully created bucket {bucket}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create bucket {bucket}: {e}", file=sys.stderr)
        return False


def create_cloudfront_distribution(bucket: str, region: str) -> dict[str, str] | None:
    """Create CloudFront distribution with OAC."""
    try:

        def _find_existing_oac(name: str) -> str | None:
            """Return existing OAC Id by name, if any."""
            try:
                result = run_cmd(
                    [
                        "aws",
                        "cloudfront",
                        "list-origin-access-controls",
                        "--output",
                        "json",
                    ]
                )
            except subprocess.CalledProcessError:
                return None

            payload = json.loads(result.stdout or "{}")
            items = payload.get("OriginAccessControlList", {}).get("Items", [])
            for it in items:
                if it.get("Name") == name:
                    return it.get("Id")
            return None

        desired_oac_name = f"allure-oac-{bucket}"

        # Get or create OAC idempotently
        print("Ensuring CloudFront Origin Access Control exists...")
        oac_id = _find_existing_oac(desired_oac_name)
        if oac_id:
            print(f"Reusing existing OAC '{desired_oac_name}' (Id: {oac_id})")
        else:
            oac_config = {
                "Name": desired_oac_name,
                "Description": f"OAC for Allure hosting bucket {bucket}",
                "OriginAccessControlOriginType": "s3",
                "SigningBehavior": "always",
                "SigningProtocol": "sigv4",
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(oac_config, f)
                oac_file = f.name

            try:
                result = run_cmd(
                    [
                        "aws",
                        "cloudfront",
                        "create-origin-access-control",
                        "--origin-access-control-config",
                        f"file://{oac_file}",
                    ]
                )
                oac_data = json.loads(result.stdout)
                oac_id = oac_data["OriginAccessControl"]["Id"]
                print(f"Created OAC '{desired_oac_name}' (Id: {oac_id})")
            except subprocess.CalledProcessError as e:
                # Fall back to finding it (handles AlreadyExists races)
                oac_id = _find_existing_oac(desired_oac_name)
                if not oac_id:
                    print(
                        f"Failed to create or locate OAC: {e}",
                        file=sys.stderr,
                    )
                    return None
            finally:
                os.unlink(oac_file)

        print("Creating CloudFront distribution...")

        # Create minimal distribution config - CloudFront will fill defaults
        dist_config = {
            # Ensure uniqueness across reruns to avoid CallerReference
            # conflicts
            "CallerReference": f"allure-{bucket}-{region}-{int(time.time())}",
            "DefaultRootObject": "index.html",
            "Comment": f"Allure hosting for {bucket}",
            "Enabled": True,
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": bucket,
                        "DomainName": f"{bucket}.s3.{region}.amazonaws.com",
                        "S3OriginConfig": {"OriginAccessIdentity": ""},
                        "OriginAccessControlId": oac_id,
                    }
                ],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": bucket,
                "ViewerProtocolPolicy": "redirect-to-https",
                "MinTTL": 0,
                "ForwardedValues": {"QueryString": False, "Cookies": {"Forward": "none"}},
                "TrustedSigners": {"Enabled": False, "Quantity": 0},
            },
            "CustomErrorResponses": {
                "Quantity": 2,
                "Items": [
                    {
                        "ErrorCode": 403,
                        "ResponsePagePath": "/index.html",
                        "ResponseCode": "200",
                        "ErrorCachingMinTTL": 300,
                    },
                    {
                        "ErrorCode": 404,
                        "ResponsePagePath": "/index.html",
                        "ResponseCode": "200",
                        "ErrorCachingMinTTL": 300,
                    },
                ],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(dist_config, f)
            dist_file = f.name

        try:
            result = run_cmd(
                [
                    "aws",
                    "cloudfront",
                    "create-distribution",
                    "--distribution-config",
                    f"file://{dist_file}",
                ]
            )
            dist_data = json.loads(result.stdout)
            distribution_id = dist_data["Distribution"]["Id"]
            cf_domain = dist_data["Distribution"]["DomainName"]
        finally:
            os.unlink(dist_file)

        print(f"Created distribution {distribution_id}")
        print(f"CloudFront domain: {cf_domain}")

        return {"distribution_id": distribution_id, "cf_domain": cf_domain, "oac_id": oac_id}

    except subprocess.CalledProcessError as e:
        print(
            f"Failed to create CloudFront distribution: {e}",
            file=sys.stderr,
        )
        return None


def attach_bucket_policy(bucket: str, distribution_id: str) -> bool:
    """Attach bucket policy to allow CloudFront access."""
    try:
        print("Attaching bucket policy...")

        # Get account ID
        result = run_cmd(
            ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"]
        )
        account_id = result.stdout.strip()

        # Create bucket policy
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudFrontServicePrincipal",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudfront.amazonaws.com"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": (
                                f"arn:aws:cloudfront::{account_id}:distribution/{distribution_id}"
                            )
                        }
                    },
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(policy, f)
            policy_file = f.name

        try:
            run_cmd(
                [
                    "aws",
                    "s3api",
                    "put-bucket-policy",
                    "--bucket",
                    bucket,
                    "--policy",
                    f"file://{policy_file}",
                ]
            )
        finally:
            os.unlink(policy_file)

        print("Successfully attached bucket policy")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to attach bucket policy: {e}", file=sys.stderr)
        return False


def write_infra_env(
    bucket: str, region: str, cf_domain: str, distribution_id: str, oac_id: str = ""
) -> None:
    """Write .infra_env file with infrastructure details."""
    env_content = f"""# Generated by allurehost-infra-setup
# Source this file: source .infra_env
export BUCKET={bucket}
export AWS_REGION={region}
export CF_DOMAIN={cf_domain}
export DISTRIBUTION_ID={distribution_id}
"""
    if oac_id:
        env_content += f"export OAC_ID={oac_id}\n"

    with open(".infra_env", "w") as f:
        f.write(env_content)

    print("Wrote .infra_env file")


def load_infra_env() -> dict[str, str]:
    """Load infrastructure environment from .infra_env file."""
    env_vars = {}
    if not os.path.exists(".infra_env"):
        return env_vars

    with open(".infra_env") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                key, value = line[7:].split("=", 1)
                env_vars[key] = value

    return env_vars


def _discover_distribution(
    bucket: str, region: str, cf_domain: str | None
) -> tuple[str, str] | None:
    """Try to discover a CloudFront distribution for the given bucket.

    Returns (distribution_id, cf_domain) or None if not found.
    """
    # If a domain is provided, try to resolve to a distribution id first.
    try:
        result = run_cmd(
            [
                "aws",
                "cloudfront",
                "list-distributions",
                "--output",
                "json",
            ]
        )
        payload = json.loads(result.stdout or "{}")
        items = (payload.get("DistributionList", {}) or {}).get("Items") or []
    except subprocess.CalledProcessError:
        items = []

    # Match by domain if provided
    if cf_domain:
        host = cf_domain
        if host.startswith("http://") or host.startswith("https://"):
            try:
                from urllib.parse import urlparse  # local import

                host = urlparse(cf_domain).netloc
            except Exception:
                host = host.split("://", 1)[-1]
        host = host.strip("/")
        for d in items:
            dname = d.get("DomainName")
            aliases = ((d.get("Aliases") or {}).get("Items")) or []
            if dname == host or host in aliases:
                return d.get("Id"), dname

    # Otherwise, match by S3 origin mapping back to the specific bucket
    expected_origin = f"{bucket}.s3.{region}.amazonaws.com"
    for d in items:
        cfg = d.get("Origins") or {}
        oitems = cfg.get("Items") or []
        for o in oitems:
            if o.get("DomainName") == expected_origin:
                return d.get("Id"), d.get("DomainName")
    return None


def write_env_main() -> int:
    """Write .infra_env from existing resources, without provisioning.

    Usage:
      python -m pytest_allure_host.infra_cli write-env \
        --bucket <BUCKET> [--region <REGION>] [--distribution-id <ID>] \
        [--cf-domain <DOMAIN>]
    """
    parser = argparse.ArgumentParser(description="Write .infra_env from existing CloudFront/S3")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument(
        "--region",
        help="AWS region (default: from AWS_REGION or config)",
    )
    parser.add_argument("--distribution-id", help="CloudFront distribution id")
    parser.add_argument("--cf-domain", help="CloudFront domain name")
    parser.add_argument("--profile", help="AWS profile to use")
    args = parser.parse_args()

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile

    region = args.region or get_aws_region()
    if not region:
        print("Error: AWS region not specified", file=sys.stderr)
        print("Use --region or set AWS_REGION environment variable")
        return 1

    dist_id = args.distribution_id
    cf_domain = args.cf_domain

    if not dist_id or not cf_domain:
        found = _discover_distribution(args.bucket, region, cf_domain)
        if not found:
            print(
                "Error: Could not discover CloudFront distribution for the "
                "bucket/region. Provide --distribution-id and --cf-domain.",
                file=sys.stderr,
            )
            return 1
        dist_id, discovered_domain = found
        cf_domain = cf_domain or discovered_domain

    write_infra_env(args.bucket, region, cf_domain, dist_id)
    return 0


def precheck_main() -> int:
    """Infrastructure prerequisites check."""
    parser = argparse.ArgumentParser(description="Check AWS infrastructure prerequisites")
    parser.add_argument("--region", help="AWS region (default: from AWS_REGION or config)")
    parser.add_argument("--profile", help="AWS profile to use")
    args = parser.parse_args()

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile

    print("== AWS CLI prerequisites check ==")

    # Check AWS CLI
    print("Checking AWS CLI is installed...")
    if not check_aws_cli():
        print("❌ AWS CLI not found or not configured", file=sys.stderr)
        print(
            "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        )
        return 1
    print("✅ AWS CLI available and configured")

    # Check region
    region = args.region or get_aws_region()
    if not region:
        print("❌ AWS region not configured", file=sys.stderr)
        print("Set AWS_REGION environment variable or configure default region")
        return 1
    print(f"✅ Region: {region}")

    # Check account
    try:
        result = run_cmd(
            ["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"]
        )
        account_id = result.stdout.strip()
        print(f"✅ Account: {account_id}")
    except subprocess.CalledProcessError:
        print("❌ Cannot access AWS account", file=sys.stderr)
        return 1

    print("\n✅ Prerequisites OK")
    return 0


def setup_main() -> int:  # noqa: C901 - CLI flow orchestration
    """Set up AWS infrastructure (bucket + CloudFront)."""
    parser = argparse.ArgumentParser(description="Set up AWS infrastructure for Allure hosting")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--region", help="AWS region (default: from AWS_REGION or config)")
    parser.add_argument("--profile", help="AWS profile to use")
    parser.add_argument("--yes", action="store_true", help="Proceed without confirmation")
    parser.add_argument(
        "--no-seed-dashboard",
        action="store_true",
        help=(
            "Skip seeding a default dashboard after setup. "
            "By default a minimal dashboard is seeded."
        ),
    )
    parser.add_argument(
        "--seed-project",
        default="myproject",
        help=("Project name to use when seeding the default dashboard (default: myproject)"),
    )
    parser.add_argument(
        "--seed-branch",
        default="main",
        help=("Branch name to use when seeding the default dashboard (default: main)"),
    )
    parser.add_argument(
        "--deploy-timeout-seconds",
        type=int,
        default=900,
        help=("Max seconds to wait for CloudFront to be Deployed (default: 900)"),
    )
    parser.add_argument(
        "--deploy-poll-interval-seconds",
        type=int,
        default=15,
        help=("Seconds between CloudFront status checks (default: 15)"),
    )
    # By default, write a config file alongside .infra_env for clarity.
    # Users can opt out with --no-write-config (kept --write-config args for
    # output/force path control below).
    parser.add_argument(
        "--no-write-config",
        action="store_true",
        help=("Do not write allure-host.yml after setup (default is to write it)."),
    )
    parser.add_argument(
        "--write-config-output",
        default="allure-host.yml",
        help=("Destination YAML path for the generated config (default: allure-host.yml)"),
    )
    parser.add_argument(
        "--write-config-force",
        action="store_true",
        help="Overwrite existing YAML if present",
    )
    args = parser.parse_args()

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile

    region = args.region or get_aws_region()
    if not region:
        print("Error: AWS region not specified", file=sys.stderr)
        print("Use --region or set AWS_REGION environment variable")
        return 1

    # Safety check
    if os.path.exists(".infra_env") and not args.yes:
        print("Warning: .infra_env already exists. This may create a second distribution.")
        print("Use --yes to proceed anyway, or remove .infra_env first.")
        return 1

    # Confirm destructive operation
    if not args.yes:
        print("This will create:")
        print(f"  - S3 bucket: {args.bucket} (in {region})")
        print("  - CloudFront distribution with OAC")
        print("  - Bucket policy restricting access to CloudFront")
        response = input("Proceed? [y/N] ")
        if response.lower() != "y":
            print("Aborted")
            return 1

    print("Setting up infrastructure...")
    print(f"Bucket: {args.bucket}")
    print(f"Region: {region}")

    # Check prerequisites
    if not check_aws_cli():
        print("Error: AWS CLI not configured", file=sys.stderr)
        return 1

    # Create bucket
    if not create_bucket(args.bucket, region):
        return 1

    # Create CloudFront distribution
    cf_info = create_cloudfront_distribution(args.bucket, region)
    if not cf_info:
        return 1

    # Attach bucket policy
    if not attach_bucket_policy(args.bucket, cf_info["distribution_id"]):
        return 1

    # Wait for distribution Deployed with timeout to avoid publish flakiness
    print("Waiting for CloudFront distribution to be deployed...")
    ok = wait_for_cf_deployed(
        cf_info["distribution_id"],
        timeout_sec=args.deploy_timeout_seconds,
        poll_interval_sec=args.deploy_poll_interval_seconds,
    )
    if ok:
        print("Distribution deployed.")
    else:
        print(
            "Warning: Timed out waiting for CloudFront deployment. "
            "It may finish shortly; publishing preflight may fail until then.",
            file=sys.stderr,
        )

    # Seed a minimal dashboard by default to make the Runs page complete
    if not args.no_seed_dashboard:
        try:
            print(
                "Seeding default dashboard "
                f"(project={args.seed_project}, branch={args.seed_branch})..."
            )
            env = dict(os.environ)
            env.update(
                {
                    "BUCKET": args.bucket,
                    "AWS_REGION": region,
                    "DISTRIBUTION_ID": cf_info["distribution_id"],
                    "CF_DOMAIN": cf_info["cf_domain"],
                }
            )
            run_cmd(
                [
                    "publish-allure",
                    "--bucket",
                    args.bucket,
                    "--project",
                    args.seed_project,
                    "--branch",
                    args.seed_branch,
                    "--seed-dashboard",
                ]
            )
            print("Seeded dashboard.")
        except Exception as e:
            print(
                f"Warning: Seeding dashboard failed: {e}",
                file=sys.stderr,
            )

    # Write .infra_env
    write_infra_env(
        args.bucket,
        region,
        cf_info["cf_domain"],
        cf_info["distribution_id"],
        cf_info.get("oac_id", ""),
    )

    # Write allure-host.yml with sensible defaults unless opted out
    if not getattr(args, "no_write_config", False):
        try:
            raw_out = (args.write_config_output or "").strip()
            out_path = Path(raw_out if raw_out else "allure-host.yml")
            if out_path.exists() and out_path.is_dir():
                out_path = out_path / "allure-host.yml"
            elif raw_out.endswith("/"):
                out_path = out_path / "allure-host.yml"
            elif raw_out in {".", ""}:
                out_path = Path("allure-host.yml")
            if out_path.exists() and not args.write_config_force:
                print(
                    f"[setup] Skipping YAML write; {out_path.as_posix()} exists (use --write-config-force to overwrite)",
                )
            else:
                # Normalize CloudFront domain to full https URL
                cf_value = cf_info["cf_domain"].strip()
                if cf_value and not (
                    cf_value.startswith("http://") or cf_value.startswith("https://")
                ):
                    cf_value = f"https://{cf_value}"
                cf_value = cf_value.rstrip("/")

                payload = {
                    "bucket": args.bucket,
                    "aws_region": region,
                    "prefix": "reports",
                    "project": args.seed_project,
                    "branch": args.seed_branch,
                    "cloudfront": cf_value,
                    "cloudfront_distribution_id": cf_info["distribution_id"],
                    "auto_build_dashboard": True,
                }
                out_path.parent.mkdir(parents=True, exist_ok=True)
                header = (
                    "# Generated by allurehost-infra-setup\n"
                    "# Edit as needed; CLI precedence is: CLI > YAML > ENV > defaults\n"
                )
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(header)
                    yaml.safe_dump(payload, f, sort_keys=False)
                print(f"[setup] Wrote config → {out_path.as_posix()}")
        except Exception as e:
            print(f"[setup] Failed to write config YAML (continuing): {e}", file=sys.stderr)

    print("\n✅ Setup complete!")
    print(f"CloudFront URL: https://{cf_info['cf_domain']}")
    print(f"Distribution ID: {cf_info['distribution_id']}")
    print("\nNext steps:")
    print("  1. Source the environment: source .infra_env")
    print(
        f"  2. Publish reports: publish-allure "
        f"--bucket {args.bucket} --project myproject --branch main"
    )
    if not getattr(args, "no_write_config", False):
        print("  3. Config written: allure-host.yml (auto_build_dashboard enabled)")
    else:
        print(
            "  (Tip) A config file was not written. You can create one anytime: allurehost-infra-write-config"
        )

    return 0


def status_main() -> int:
    """Check status of AWS infrastructure."""
    parser = argparse.ArgumentParser(description="Check AWS infrastructure status")
    parser.add_argument("--profile", help="AWS profile to use")
    args = parser.parse_args()

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile

    env_vars = load_infra_env()
    if not env_vars:
        print("Error: .infra_env file not found", file=sys.stderr)
        print("Run: allurehost-infra-setup --bucket <name> --region <region>")
        return 1

    bucket = env_vars.get("BUCKET")
    region = env_vars.get("AWS_REGION")
    distribution_id = env_vars.get("DISTRIBUTION_ID")
    cf_domain = env_vars.get("CF_DOMAIN")

    if not all([bucket, region, distribution_id, cf_domain]):
        print("Error: .infra_env missing required variables", file=sys.stderr)
        return 1

    print("Infrastructure Status:")
    print(f"  Bucket: {bucket}")
    print(f"  Region: {region}")
    print(f"  CloudFront: https://{cf_domain}")
    print(f"  Distribution ID: {distribution_id}")

    # Check bucket
    try:
        run_cmd(["aws", "s3api", "head-bucket", "--bucket", bucket])
        print("  ✅ Bucket accessible")
    except subprocess.CalledProcessError:
        print("  ❌ Bucket not accessible")
        return 1

    # Check distribution status
    try:
        result = run_cmd(
            [
                "aws",
                "cloudfront",
                "get-distribution",
                "--id",
                distribution_id,
                "--query",
                "Distribution.Status",
                "--output",
                "text",
            ]
        )
        status = result.stdout.strip()
        print(f"  ✅ Distribution status: {status}")
    except subprocess.CalledProcessError:
        print("  ❌ Distribution not accessible")
        return 1

    return 0


def validate_main() -> int:
    """Validate AWS infrastructure configuration."""
    parser = argparse.ArgumentParser(description="Validate AWS infrastructure configuration")
    parser.add_argument("--profile", help="AWS profile to use")
    args = parser.parse_args()

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile

    env_vars = load_infra_env()
    if not env_vars:
        print("Error: .infra_env file not found", file=sys.stderr)
        return 1

    bucket = env_vars.get("BUCKET")
    distribution_id = env_vars.get("DISTRIBUTION_ID")

    if not bucket or not distribution_id:
        print("Error: .infra_env missing BUCKET or DISTRIBUTION_ID", file=sys.stderr)
        return 1

    print("Validating infrastructure configuration...")

    # Check bucket policy
    try:
        result = run_cmd(
            [
                "aws",
                "s3api",
                "get-bucket-policy",
                "--bucket",
                bucket,
                "--query",
                "Policy",
                "--output",
                "text",
            ]
        )

        policy = json.loads(result.stdout)

        # Check if policy references the correct distribution
        found_dist = False
        for statement in policy.get("Statement", []):
            condition = statement.get("Condition", {}).get("StringEquals", {})
            source_arn = condition.get("AWS:SourceArn", "")
            if distribution_id in source_arn:
                found_dist = True
                break

        if found_dist:
            print("✅ Bucket policy correctly references distribution")
        else:
            print("❌ Bucket policy does not reference current distribution")
            return 1

    except subprocess.CalledProcessError:
        print("❌ Cannot access bucket policy")
        return 1

    # Check distribution configuration
    try:
        result = run_cmd(
            [
                "aws",
                "cloudfront",
                "get-distribution",
                "--id",
                distribution_id,
                "--query",
                "Distribution.DistributionConfig.Origins.Items[0].DomainName",
                "--output",
                "text",
            ]
        )
        origin_domain = result.stdout.strip()

        if bucket in origin_domain:
            print("✅ Distribution correctly configured for bucket")
        else:
            print("❌ Distribution origin does not match bucket")
            return 1

    except subprocess.CalledProcessError:
        print("❌ Cannot access distribution configuration")
        return 1

    print("✅ Infrastructure validation passed")
    return 0


def cleanup_main() -> int:  # noqa: C901 - CLI flow orchestration
    """Clean up AWS infrastructure."""
    parser = argparse.ArgumentParser(description="Clean up AWS infrastructure")
    parser.add_argument("--profile", help="AWS profile to use")
    parser.add_argument(
        "--destroy-yes", action="store_true", help="Confirm destruction of CloudFront and S3 bucket"
    )
    parser.add_argument(
        "--delete-bucket",
        action="store_true",
        help=("Also empty and delete the S3 bucket. By default the bucket is left intact."),
    )
    args = parser.parse_args()

    if not args.destroy_yes:
        print("Error: This is a destructive operation.", file=sys.stderr)
        print("Use --destroy-yes to confirm deletion of CloudFront distribution and S3 bucket")
        return 1

    if args.profile:
        os.environ["AWS_PROFILE"] = args.profile

    env_vars = load_infra_env()
    if not env_vars:
        print("Error: .infra_env file not found", file=sys.stderr)
        return 1

    bucket = env_vars.get("BUCKET")
    distribution_id = env_vars.get("DISTRIBUTION_ID")

    if not bucket or not distribution_id:
        print("Error: .infra_env missing BUCKET or DISTRIBUTION_ID", file=sys.stderr)
        return 1

    print("Cleaning up infrastructure...")
    print(f"  Distribution: {distribution_id}")
    print(f"  Bucket: {bucket}")
    if not args.delete_bucket:
        print("  (Bucket deletion is skipped by default. Use --delete-bucket to remove it.)")

    try:
        # Disable distribution
        print("Disabling CloudFront distribution...")
        result = run_cmd(["aws", "cloudfront", "get-distribution-config", "--id", distribution_id])

        dist_data = json.loads(result.stdout)
        config = dist_data["DistributionConfig"]
        etag = dist_data["ETag"]

        config["Enabled"] = False

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            config_file = f.name

        try:
            run_cmd(
                [
                    "aws",
                    "cloudfront",
                    "update-distribution",
                    "--id",
                    distribution_id,
                    "--distribution-config",
                    f"file://{config_file}",
                    "--if-match",
                    etag,
                ]
            )
        finally:
            os.unlink(config_file)

        print("Waiting for distribution to be disabled...")
        run_cmd(["aws", "cloudfront", "wait", "distribution-deployed", "--id", distribution_id])

        # Delete distribution
        print("Deleting CloudFront distribution...")
        result = run_cmd(
            [
                "aws",
                "cloudfront",
                "get-distribution",
                "--id",
                distribution_id,
                "--query",
                "ETag",
                "--output",
                "text",
            ]
        )
        etag = result.stdout.strip()

        run_cmd(
            [
                "aws",
                "cloudfront",
                "delete-distribution",
                "--id",
                distribution_id,
                "--if-match",
                etag,
            ]
        )

        # Empty and delete bucket (opt-in)
        if args.delete_bucket:
            print("Emptying S3 bucket (including all object versions)...")

            # Version-aware purge loop using AWS CLI to delete in batches
            def _purge_all_versions(bkt: str) -> None:
                while True:
                    # List up to 1000 versions and delete markers
                    list_proc = run_cmd(
                        [
                            "aws",
                            "s3api",
                            "list-object-versions",
                            "--bucket",
                            bkt,
                            "--output",
                            "json",
                            "--query",
                            (
                                "{Vers: Versions[].{Key:Key,"
                                "VersionId:VersionId},"
                                " Dels: DeleteMarkers[].{Key:Key,"
                                "VersionId:VersionId}}"
                            ),
                        ],
                        check=False,
                    )

                    if list_proc.returncode != 0:
                        # If listing fails (e.g., no versioning),
                        # fall back to rm --recursive
                        run_cmd(
                            ["aws", "s3", "rm", f"s3://{bkt}", "--recursive"],
                            check=False,
                        )
                        break

                    payload = json.loads(list_proc.stdout or "{}")
                    objs = (payload.get("Vers") or []) + (payload.get("Dels") or [])
                    if not objs:
                        # Nothing left to delete
                        break

                    # Build batch delete file
                    delete_spec = {"Objects": objs, "Quiet": True}
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
                        json.dump(delete_spec, tf)
                        del_file = tf.name
                    try:
                        run_cmd(
                            [
                                "aws",
                                "s3api",
                                "delete-objects",
                                "--bucket",
                                bkt,
                                "--delete",
                                f"file://{del_file}",
                            ],
                            check=False,
                        )
                    finally:
                        os.unlink(del_file)

                # Final non-versioned sweep (in case versioning was disabled)
                run_cmd(
                    ["aws", "s3", "rm", f"s3://{bkt}", "--recursive"],
                    check=False,
                )

            _purge_all_versions(bucket)

            print("Deleting S3 bucket...")
            run_cmd(["aws", "s3api", "delete-bucket", "--bucket", bucket])

        # Remove .infra_env
        if os.path.exists(".infra_env"):
            os.unlink(".infra_env")
            print("Removed .infra_env file")

        print("✅ Cleanup complete")
        if not args.delete_bucket:
            print("Note: The S3 bucket was preserved. Re-run with --delete-bucket to remove it.")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Cleanup failed: {e}", file=sys.stderr)
        return 1


# ----------------------- New convenience commands -----------------------


def _resolve_effective_config(
    explicit_config: str | None,
    overrides: dict | None = None,
) -> tuple[dict, PublishConfig]:
    """Load effective config from YAML/.infra_env/env with optional overrides.

    Returns (effective_dict, PublishConfig).
    """
    overrides = overrides or {}
    effective = load_effective_config(overrides, explicit_config)
    # If nothing loaded (no bucket), try discovery of a YAML file
    if not effective.get("bucket"):
        discovered = discover_yaml_config(explicit_config)
        cfg_file = str(discovered.source_file) if discovered.source_file else None
        effective = load_effective_config(overrides, cfg_file)

    # If still missing distribution id or region, try .infra_env
    env_vars = load_infra_env()
    if env_vars:
        effective.setdefault("aws_region", env_vars.get("AWS_REGION"))
        effective.setdefault("cloudfront_distribution_id", env_vars.get("DISTRIBUTION_ID"))
        # Allow cloudfront domain fill-in if YAML omitted it
        cf_dom = env_vars.get("CF_DOMAIN")
        if cf_dom and not effective.get("cloudfront"):
            effective["cloudfront"] = cf_dom

    missing = [k for k in ("bucket", "prefix", "project", "branch") if not effective.get(k)]
    if missing:
        raise SystemExit(
            "Missing config keys: "
            + ", ".join(missing)
            + ". Provide via --config or explicit flags."
        )

    cfg = PublishConfig(
        bucket=str(effective["bucket"]),
        prefix=str(effective.get("prefix") or "reports"),
        project=str(effective["project"]),
        branch=str(effective.get("branch") or "main"),
        run_id=str(effective.get("run_id") or "-"),
        cloudfront_domain=(
            str(effective.get("cloudfront")) if effective.get("cloudfront") else None
        ),
        aws_region=effective.get("aws_region"),
        cloudfront_distribution_id=effective.get("cloudfront_distribution_id"),
        s3_endpoint=effective.get("s3_endpoint"),
    )
    return effective, cfg


def _s3_client(cfg: PublishConfig):
    return (
        boto3.client("s3", endpoint_url=cfg.s3_endpoint) if cfg.s3_endpoint else boto3.client("s3")
    )


def _cf_client():
    return boto3.client("cloudfront")


def _guess_content_type(path: Path) -> str:
    import mimetypes

    ct, _ = mimetypes.guess_type(path.as_posix())
    if ct:
        return ct
    if path.suffix == ".js":
        return "application/javascript"
    if path.suffix == ".css":
        return "text/css"
    return "application/octet-stream"


def _default_dashboard_html(cfg: PublishConfig) -> bytes:
    """Return a minimal default dashboard page that reads Allure JSON and
    links back to runs/latest. Lightweight and self-contained.

    This mirrors the seeding logic used by the publisher so that users who
    only installed the wheel (without a local 'dist' directory) still get a
    functional dashboard under latest/dashboard/.
    """
    title = f"Dashboard: {cfg.project} / {cfg.branch}"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>body{font-family:system-ui;margin:1.25rem;line-height:1.4;}"
        "h1{margin-top:0;font-size:1.35rem;}"
        "nav a{display:inline-block;margin-right:.5rem;padding:2px 6px;border:1px solid #ccc;border-radius:12px;text-decoration:none;color:#555;}"
        "#cards{display:flex;flex-wrap:wrap;gap:.85rem;margin:.6rem 0 1rem;}"
        ".card{flex:0 1 160px;padding:.8rem .9rem;border-radius:12px;border:1px solid #d5d9de;box-shadow:0 1px 2px rgba(0,0,0,.05);}"
        ".label{font-size:10px;font-weight:600;color:#666;text-transform:uppercase;letter-spacing:.5px;}"
        ".val{font-size:22px;font-weight:600;}</style></head><body>"
        f"<h1>{title}</h1>"
        "<nav><a href='../'>latest</a><a href='../../runs/index.html'>runs</a></nav>"
        "<div id='cards'><div class='card'><div class='label'>Passed</div><div class='val' id='p'>-</div></div>"
        "<div class='card'><div class='label'>Failed</div><div class='val' id='f'>-</div></div>"
        "<div class='card'><div class='label'>Broken</div><div class='val' id='b'>-</div></div>"
        "<div class='card'><div class='label'>Total</div><div class='val' id='t'>-</div></div></div>"
        "<script>(async function(){try{const r=await fetch('../widgets/summary.json',{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const j=await r.json();const s=(j&&j.statistic)||{};const p=s.passed||0,f=s.failed||0,b=s.broken||0,t=p+f+b;document.getElementById('p').textContent=p;document.getElementById('f').textContent=f;document.getElementById('b').textContent=b;document.getElementById('t').textContent=t;}catch(e){console.error('dash load',e);}})();</script>"
        "</body></html>"
    ).encode()


# ----------------------- Small internal helpers -----------------------


def _debug_enabled() -> bool:
    return str(os.environ.get("ALLURE_HOST_DEBUG", "")).strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _dprint(*args: object) -> None:
    if _debug_enabled():
        print(*args)


def _upload_index_page(s3, bucket: str, key: str, body: bytes) -> None:
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="text/html; charset=utf-8",
        CacheControl="no-cache",
    )


def _upload_dir_tree(
    s3,
    bucket: str,
    out_dir: Path,
    dest_prefix: str,
    data_ttl: int,
) -> tuple[int, int]:
    """Upload dashboard folder structure (assets/* immutable, data/* short TTL).

    Returns (assets_count, data_count).
    """
    # assets/* → immutable
    assets = out_dir / "assets"
    assets_count = 0
    if assets.exists():
        for p in assets.rglob("*"):
            if p.is_file():
                rel = p.relative_to(out_dir).as_posix()
                s3.upload_file(
                    str(p),
                    bucket,
                    dest_prefix + rel,
                    ExtraArgs={
                        "CacheControl": "public, max-age=31536000, immutable",
                        "ContentType": _guess_content_type(p),
                    },
                )
                assets_count += 1

    # data/* → short TTL
    data = out_dir / "data"
    data_count = 0
    if data.exists():
        for p in data.rglob("*"):
            if p.is_file():
                rel = p.relative_to(out_dir).as_posix()
                s3.upload_file(
                    str(p),
                    bucket,
                    dest_prefix + rel,
                    ExtraArgs={
                        "CacheControl": f"public, max-age={int(data_ttl)}",
                        "ContentType": _guess_content_type(p),
                    },
                )
                data_count += 1

    return assets_count, data_count


def _upload_packaged_dashboard(
    s3,
    bucket: str,
    dest_prefix: str,
    data_ttl: int,
) -> tuple[bool, int, int]:
    """Upload packaged dashboard bundled in the wheel if available.

    Returns (uploaded, assets_count, data_count).
    """
    try:
        from importlib import resources as _res

        base = _res.files("pytest_allure_host").joinpath("_assets", "dashboard")
        idx = base.joinpath("index.html")
        if not idx.is_file():
            return False, 0, 0

        _dprint(f"[deploy-dashboard] Source: packaged wheel → {str(idx)}")
        _upload_index_page(s3, bucket, f"{dest_prefix}index.html", idx.read_bytes())

        # assets → immutable
        assets_count = 0
        try:
            assets = base.joinpath("assets")
            for p in assets.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(base).as_posix()
                    s3.put_object(
                        Bucket=bucket,
                        Key=dest_prefix + rel,
                        Body=p.read_bytes(),
                        ContentType=_guess_content_type(Path(str(p))),
                        CacheControl="public, max-age=31536000, immutable",
                    )
                    assets_count += 1
        except Exception:
            ...

        # data → short TTL
        data_count = 0
        try:
            data = base.joinpath("data")
            for p in data.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(base).as_posix()
                    s3.put_object(
                        Bucket=bucket,
                        Key=dest_prefix + rel,
                        Body=p.read_bytes(),
                        ContentType=_guess_content_type(Path(str(p))),
                        CacheControl=f"public, max-age={int(data_ttl)}",
                    )
                    data_count += 1
        except Exception:
            ...

        return True, assets_count, data_count
    except Exception:
        return False, 0, 0


def deploy_dashboard_main() -> int:  # noqa: C901 - CLI flow orchestration
    """Upload a local dashboard directory to S3 under latest/dashboard/.

    Usage (examples):
      allurehost-infra-deploy-dashboard --config allure-host.yml --out dist
      python -m pytest_allure_host.infra_cli deploy-dashboard --out dist
    """
    ap = argparse.ArgumentParser(
        description="Deploy dashboard directory to S3 under latest/dashboard/"
    )
    ap.add_argument("--config", help="YAML config file (optional)")
    ap.add_argument("--out", default="dist", help="Dashboard directory (default: dist)")
    ap.add_argument(
        "--dashboard-prefix",
        default="dashboard",
        help="Prefix under latest/ (default: dashboard)",
    )
    ap.add_argument(
        "--data-ttl",
        type=int,
        default=60,
        help="Seconds to cache data/* objects (default: 60)",
    )
    # Optional overrides so users without YAML can pass coordinates directly
    ap.add_argument("--bucket", help="S3 bucket override (optional)")
    ap.add_argument("--prefix", help="S3 logical prefix root (e.g. reports)")
    ap.add_argument("--project", help="Project name")
    ap.add_argument("--branch", help="Branch name")
    args = ap.parse_args()

    overrides: dict[str, str] = {}
    if args.bucket:
        overrides["bucket"] = args.bucket
    if args.prefix:
        overrides["prefix"] = args.prefix
    if args.project:
        overrides["project"] = args.project
    if args.branch:
        overrides["branch"] = args.branch

    _, cfg = _resolve_effective_config(args.config, overrides)
    out_path = Path(args.out)

    s3 = _s3_client(cfg)
    root = branch_root(cfg.prefix, cfg.project, cfg.branch)
    dest = f"{root}/latest/{args.dashboard_prefix.strip('/')}/"
    _dprint(
        "[deploy-dashboard] Debug:",
        "bucket=",
        cfg.bucket,
        "prefix=",
        cfg.prefix,
        "project=",
        cfg.project,
        "branch=",
        cfg.branch,
        "dest=",
        dest,
    )

    # Case A: --out points to a single HTML file (upload as index.html)
    if out_path.exists() and out_path.is_file():
        _dprint(f"[deploy-dashboard] Source: single file (--out) → {out_path.as_posix()}")
        if out_path.suffix.lower() not in {".html", ".htm"}:
            print(
                f"Unsupported file type for --out: {out_path.suffix}",
                file=sys.stderr,
            )
            return 2
        _upload_index_page(s3, cfg.bucket, f"{dest}index.html", out_path.read_bytes())
        print(f"[deploy-dashboard] Uploaded file → s3://{cfg.bucket}/{dest}index.html")

    # Case B: --out points to a directory containing index.html (plus assets/data)
    elif out_path.exists() and out_path.is_dir():
        idx = out_path / "index.html"
        if not idx.exists():
            print("index.html not found in dashboard directory", file=sys.stderr)
            return 2
        _dprint(f"[deploy-dashboard] Source: directory (--out) → {out_path.as_posix()}")
        _upload_index_page(s3, cfg.bucket, f"{dest}index.html", idx.read_bytes())
        assets_count, data_count = _upload_dir_tree(
            s3, cfg.bucket, out_path, dest, int(args.data_ttl)
        )

        print(f"[deploy-dashboard] Uploaded dir → s3://{cfg.bucket}/{dest}")
        _dprint(f"[deploy-dashboard] Uploaded counts: assets={assets_count}, data={data_count}")

    else:
        # Prefer a packaged dashboard bundled in the wheel, if available
        uploaded_packaged = False
        try:
            uploaded_packaged, assets_count, data_count = _upload_packaged_dashboard(
                s3, cfg.bucket, dest, int(args.data_ttl)
            )
            if uploaded_packaged:
                print(f"[deploy-dashboard] Uploaded packaged dashboard → s3://{cfg.bucket}/{dest}")
                _dprint(
                    f"[deploy-dashboard] Uploaded counts: assets={assets_count}, data={data_count}"
                )
        except Exception:
            uploaded_packaged = False

        if not uploaded_packaged:
            print(
                "[deploy-dashboard] No dashboard path found; uploading a minimal fallback "
                "dashboard bundled in the package."
            )
            _dprint("[deploy-dashboard] Source: minimal fallback (inline HTML)")
            s3.put_object(
                Bucket=cfg.bucket,
                Key=f"{dest}index.html",
                Body=_default_dashboard_html(cfg),
                ContentType="text/html; charset=utf-8",
                CacheControl="no-cache",
            )
            print(f"[deploy-dashboard] Uploaded fallback → s3://{cfg.bucket}/{dest}index.html")

    if cfg.cloudfront_domain:
        url = f"{cfg.cloudfront_domain.rstrip('/')}/{dest}index.html"
        print(f"[deploy-dashboard] URL: {url}")
    else:
        print("[deploy-dashboard] Note: cloudfront domain not configured; skipping URL")
    return 0


def invalidate_main() -> int:
    """Invalidate CloudFront paths for dashboard and/or runs pages.

    Examples:
      allurehost-infra-invalidate --config allure-host.yml --paths dashboard
      allurehost-infra-invalidate --paths runs
    """
    ap = argparse.ArgumentParser(description="CloudFront invalidation helper")
    ap.add_argument("--config", help="YAML config file (optional)")
    ap.add_argument(
        "--paths",
        choices=["dashboard", "runs", "all"],
        default="dashboard",
        help="Which paths to invalidate (default: dashboard)",
    )
    args = ap.parse_args()

    effective, cfg = _resolve_effective_config(args.config)
    dist_id = cfg.cloudfront_distribution_id
    if not dist_id:
        print(
            "CloudFront distribution id not found in config or .infra_env",
            file=sys.stderr,
        )
        return 2

    root = f"/{cfg.prefix}/{cfg.project}/{cfg.branch}"
    dashboard_base = f"{root}/latest/dashboard"
    runs_index = f"{root}/runs/index.html"

    if args.paths == "dashboard":
        paths = [
            f"{dashboard_base}/index.html",
            f"{dashboard_base}/data/*",
            f"{dashboard_base}/assets/*",
        ]
    elif args.paths == "runs":
        paths = [runs_index]
    else:  # all
        paths = [
            f"{dashboard_base}/index.html",
            f"{dashboard_base}/data/*",
            f"{dashboard_base}/assets/*",
            runs_index,
        ]

    cf = _cf_client()
    ref = f"ah-{int(time.time())}"

    def _do_invalidate(did: str) -> str:
        resp_inner = cf.create_invalidation(
            DistributionId=str(did),
            InvalidationBatch={
                "CallerReference": ref,
                "Paths": {"Quantity": len(paths), "Items": paths},
            },
        )
        return (resp_inner.get("Invalidation") or {}).get("Id")

    try:
        inval_id = _do_invalidate(str(dist_id))
        print(f"[invalidate] Submitted invalidation {inval_id} for: \n - " + "\n - ".join(paths))
        return 0
    except ClientError as e:
        code = (e.response.get("Error") or {}).get("Code")
        if code != "NoSuchDistribution":
            raise

        # Try to discover the current distribution (YAML may be stale)
        print(
            "[invalidate] Distribution not found. Attempting discovery from cloudfront/bucket...",
            file=sys.stderr,
        )
        discovered = _discover_distribution(
            cfg.bucket,
            cfg.aws_region
            or (effective.get("aws_region") if isinstance(effective, dict) else None),
            cfg.cloudfront_domain,
        )
        if not discovered:
            print(
                "[invalidate] Could not discover distribution. Update your YAML with the new distribution id (try: allurehost-infra-write-config)",
                file=sys.stderr,
            )
            return 2
        new_id, _new_domain = discovered
        try:
            inval_id = _do_invalidate(str(new_id))
            print(
                f"[invalidate] Submitted invalidation {inval_id} (recovered via discovery) for: \n - "
                + "\n - ".join(paths)
            )
            print(
                f"[hint] Consider syncing config: allurehost-infra-write-config --force (will update cloudfront_distribution_id to {new_id})"
            )
            return 0
        except ClientError:
            raise


def write_config_main() -> int:
    """Generate an allure-host.yml from .infra_env (with optional overrides).

    This helps keep your YAML aligned after recreating infrastructure.

    Examples:
      allurehost-infra-write-config --project demo --branch main
      allurehost-infra-write-config --output allure-host.yaml --force \
        --prefix reports --project payments --branch main
    """
    ap = argparse.ArgumentParser(description="Write allure-host.yml from .infra_env")
    ap.add_argument(
        "--output",
        default="allure-host.yml",
        help="Destination YAML path (default: allure-host.yml)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it exists",
    )
    ap.add_argument("--prefix", default="reports", help="S3 logical prefix (default: reports)")
    ap.add_argument("--project", default="myproject", help="Project name (default: myproject)")
    ap.add_argument("--branch", default="main", help="Branch name (default: main)")
    # Optional direct overrides in case .infra_env is absent
    ap.add_argument("--bucket", help="S3 bucket (overrides .infra_env)")
    ap.add_argument("--region", help="AWS region (overrides .infra_env)")
    ap.add_argument("--cloudfront", help="CloudFront domain (overrides .infra_env)")
    ap.add_argument(
        "--distribution-id",
        help="CloudFront distribution id (overrides .infra_env)",
    )
    args = ap.parse_args()

    env = load_infra_env()

    bucket = args.bucket or env.get("BUCKET")
    region = args.region or env.get("AWS_REGION") or get_aws_region()
    cf_domain = args.cloudfront or env.get("CF_DOMAIN")
    dist_id = args.distribution_id or env.get("DISTRIBUTION_ID")

    # Validate required core fields
    missing = [
        name
        for name, val in (
            ("bucket", bucket),
            ("region", region),
            ("cloudfront_domain", cf_domain),
            ("distribution_id", dist_id),
        )
        if not val
    ]
    if missing:
        print(
            "Error: Missing values: "
            + ", ".join(missing)
            + ". Provide overrides or ensure .infra_env exists.",
            file=sys.stderr,
        )
        return 2

    # If we have a distribution id, prefer resolving the active domain from AWS to avoid
    # YAML drift when the distribution was recreated (stale CF_DOMAIN in .infra_env).
    resolved_domain = None
    try:
        if dist_id:
            _cf = boto3.client("cloudfront")
            resp = _cf.get_distribution(Id=str(dist_id))
            resolved_domain = (resp.get("Distribution") or {}).get("DomainName")
    except Exception:
        resolved_domain = None

    # Choose domain: prefer resolved from AWS, else provided cf_domain
    chosen_domain = (resolved_domain or cf_domain or "").strip()

    # Normalize cloudfront value to full https URL
    cf_value = chosen_domain
    if cf_value and not (cf_value.startswith("http://") or cf_value.startswith("https://")):
        cf_value = f"https://{cf_value}"
    cf_value = cf_value.rstrip("/")

    # Resolve output path; tolerate directory or empty '.' by defaulting to a filename
    raw_out = (args.output or "").strip()
    out_path = Path(raw_out if raw_out else "allure-host.yaml")
    # If explicitly a directory (existing) or a trailing slash was provided, write inside it
    if out_path.exists() and out_path.is_dir():
        out_path = out_path / "allure-host.yaml"
    elif raw_out.endswith("/"):
        out_path = out_path / "allure-host.yaml"
    elif raw_out in {".", ""}:
        out_path = Path("allure-host.yaml")
    if out_path.exists() and not args.force:
        print(
            f"Error: {out_path.as_posix()} already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 3

    # Compose YAML structure consistent with loader expectations
    payload = {
        "bucket": bucket,
        "aws_region": region,
        "prefix": args.prefix,
        "project": args.project,
        "branch": args.branch,
        "cloudfront": cf_value,
        "cloudfront_distribution_id": dist_id,
        # Enable one-step UX: after publish, build and deploy dashboard from manifest.
        # Users can disable via YAML (auto_build_dashboard: false) or env
        # (ALLURE_AUTO_BUILD_DASHBOARD=0/false).
        "auto_build_dashboard": True,
    }

    # Create folders and write YAML
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Prepend a small header comment for clarity
    header = (
        "# Generated by allurehost-infra-write-config from .infra_env\n"
        "# Edit as needed; CLI precedence is: CLI > YAML > ENV > defaults\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(payload, f, sort_keys=False)

    print(f"Wrote config → {out_path.as_posix()}")
    print("Values:")
    for k in ("bucket", "aws_region", "prefix", "project", "branch"):
        print(f"  {k}: {payload[k]}")
    print(f"  cloudfront: {cf_value}")
    print(f"  cloudfront_distribution_id: {dist_id}")
    if resolved_domain and cf_domain and resolved_domain != cf_domain:
        print(
            "[write-config] Note: CloudFront domain was updated based on distribution lookup "
            f"({cf_domain} → {resolved_domain})"
        )
    return 0


if __name__ == "__main__":
    # Allow direct execution for testing after all functions are defined
    if len(sys.argv) > 1:
        command = sys.argv[1]
        sys.argv = sys.argv[1:]  # Remove the command from argv
        if command == "precheck":
            sys.exit(precheck_main())
        elif command == "setup":
            sys.exit(setup_main())
        elif command == "status":
            sys.exit(status_main())
        elif command == "validate":
            sys.exit(validate_main())
        elif command == "cleanup":
            sys.exit(cleanup_main())
        elif command == "write-env":
            sys.exit(write_env_main())
        elif command == "write-config":
            sys.exit(write_config_main())
        elif command == "invalidate":
            sys.exit(invalidate_main())
        elif command == "deploy-dashboard":
            sys.exit(deploy_dashboard_main())
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            "Usage: python -m pytest_allure_host.infra_cli <command>",
            file=sys.stderr,
        )
        sys.exit(1)
