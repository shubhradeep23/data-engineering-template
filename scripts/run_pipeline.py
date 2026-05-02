"""
Upload generated JSONL to raw/, start Glue jobs, optionally start crawlers.
Requires AWS credentials and Terraform-deployed resources.

Example:
  python scripts/run_pipeline.py --bucket YOUR_BUCKET --region us-east-1 \\
    --generate --glue-jobs --glue-raw-job NAME --glue-curated-job NAME \\
    --crawler CRAWLER1 --crawler CRAWLER2
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    print("Install boto3: pip install -r scripts/requirements.txt", file=sys.stderr)
    raise


def run_generate(repo_root: Path, download_sample: bool) -> Path:
    gen = repo_root / "scripts" / "generate_unstructured_data.py"
    out = repo_root / "data" / "generated" / "events.jsonl"
    cmd = [sys.executable, str(gen), "--output", str(out)]
    if download_sample:
        cmd.append("--download-sample")
    subprocess.check_call(cmd, cwd=str(repo_root))
    return out


def start_glue_job(glue, name: str) -> str:
    resp = glue.start_job_run(JobName=name)
    return resp["JobRunId"]


def wait_job(glue, name: str, run_id: str, poll_s: int = 15) -> None:
    terminal = {"SUCCEEDED", "FAILED", "STOPPED", "TIMEOUT"}
    while True:
        resp = glue.get_job_run(JobName=name, RunId=run_id, PredecessorsIncluded=False)
        state = resp["JobRun"]["JobRunState"]
        if state in terminal:
            if state != "SUCCEEDED":
                raise RuntimeError(f"Glue job {name} run {run_id} ended with {state}")
            return
        time.sleep(poll_s)


def start_crawler(glue, name: str) -> None:
    glue.start_crawler(Name=name)


def main() -> int:
    p = argparse.ArgumentParser(description="Upload raw data and orchestrate Glue.")
    p.add_argument("--bucket", required=True, help="Data lake bucket (terraform output data_lake_bucket)")
    p.add_argument("--region", default="us-east-1")
    p.add_argument("--profile", default=None)
    p.add_argument("--prefix-raw", default="raw")
    p.add_argument("--key", default="events/events.jsonl", help="S3 key under raw/ prefix")
    p.add_argument("--generate", action="store_true", help="Run generate_unstructured_data.py first")
    p.add_argument("--download-sample", action="store_true", help="Use NASA JSON sample instead of synthetic")
    p.add_argument("--local-file", type=Path, default=None, help="Upload this file instead of default")
    p.add_argument("--glue-raw-job", default=None, help="Glue job name for raw to staging")
    p.add_argument("--glue-curated-job", default=None, help="Glue job name for staging to curated")
    p.add_argument("--glue-jobs", action="store_true", help="Start both Glue jobs and wait")
    p.add_argument(
        "--crawler",
        action="append",
        default=[],
        metavar="NAME",
        help="Glue crawler to start (repeat for multiple)",
    )
    args = p.parse_args()

    session_kw: dict = {"region_name": args.region}
    if args.profile:
        session_kw["profile_name"] = args.profile

    session = boto3.Session(**session_kw)
    s3 = session.client("s3")
    glue = session.client("glue")

    repo_root = Path(__file__).resolve().parents[1]

    if args.generate or args.download_sample:
        local_path = run_generate(repo_root, download_sample=args.download_sample)
    elif args.local_file:
        local_path = args.local_file.expanduser().resolve()
    else:
        default_gen = repo_root / "data" / "generated" / "events.jsonl"
        if not default_gen.is_file():
            print("No local file. Use --generate, --download-sample, or --local-file.", file=sys.stderr)
            return 1
        local_path = default_gen

    key = f"{args.prefix_raw}/{args.key}".lstrip("/")
    try:
        s3.upload_file(str(local_path), args.bucket, key)
        print(f"Uploaded s3://{args.bucket}/{key}")
    except (BotoCoreError, ClientError) as e:
        print(f"S3 upload failed: {e}", file=sys.stderr)
        return 1

    if args.glue_jobs:
        if not args.glue_raw_job or not args.glue_curated_job:
            print("With --glue-jobs, set --glue-raw-job and --glue-curated-job.", file=sys.stderr)
            return 1
        try:
            r1 = start_glue_job(glue, args.glue_raw_job)
            print(f"Started {args.glue_raw_job} run {r1}")
            wait_job(glue, args.glue_raw_job, r1)
            r2 = start_glue_job(glue, args.glue_curated_job)
            print(f"Started {args.glue_curated_job} run {r2}")
            wait_job(glue, args.glue_curated_job, r2)
        except (BotoCoreError, ClientError, RuntimeError) as e:
            print(f"Glue run failed: {e}", file=sys.stderr)
            return 1
    else:
        print("Skip Glue jobs (pass --glue-jobs to run).")

    for c in args.crawler:
        try:
            start_crawler(glue, c)
            print(f"Started crawler {c}")
        except (BotoCoreError, ClientError) as e:
            print(f"Crawler {c} failed: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
