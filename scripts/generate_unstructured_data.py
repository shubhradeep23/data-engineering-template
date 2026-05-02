"""
Generate semi-structured / unstructured-style JSONL suitable for the sample lake:
nested payload, free-text message, occasional missing fields (realistic messiness).

Usage:
  python scripts/generate_unstructured_data.py --output data/generated/events.jsonl --rows 500

Optional: fetch a public sample instead of synthetic data:
  python scripts/generate_unstructured_data.py --download-sample
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCES = ("api", "mobile", "batch", "partner_feed", "syslog_bridge")

MESSAGES = (
    "heartbeat",
    "order_created",
    "payment_failed",
    "inventory_sync",
    "rate_limit_near",
    "unknown_payload_shape",
)


def random_ts(start: datetime, end: datetime) -> str:
    delta = end - start
    sec = random.randint(0, int(delta.total_seconds()))
    return (start + timedelta(seconds=sec)).replace(tzinfo=timezone.utc).isoformat()


def synthetic_row(i: int) -> dict:
    ts = random_ts(datetime(2025, 1, 1, tzinfo=timezone.utc), datetime.now(timezone.utc))
    row = {
        "event_id": f"evt-{i:08x}",
        "timestamp": ts,
        "source": random.choice(SOURCES),
        "message": random.choice(MESSAGES),
        "payload": {
            "region": random.choice(("us-east-1", "eu-west-1", "ap-south-1", None)),
            "sku": f"SKU-{random.randint(1000, 9999)}",
            "amount": round(random.uniform(0.5, 500.0), 2),
            "tags": random.sample(["trial", "vip", "repeat", "new"], k=random.randint(0, 3)),
        },
        "raw_blob": f"unparsed tail {random.randint(0, 10**6)}",
    }
    if random.random() < 0.08:
        del row["payload"]["region"]
    if random.random() < 0.05:
        row["payload"]["nested"] = {"note": random.choice(("a", "b", None))}
    if random.random() < 0.03:
        row.pop("message", None)
    return row


def write_jsonl(path: Path, rows: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for i in range(rows):
            f.write(json.dumps(synthetic_row(i), default=str) + "\n")


def download_sample(path: Path) -> None:
    """
    NASA meteorite landing JSON (public domain–style open data) as non-tabular JSON array.
    Stored as a single JSON file; Glue can read json if multiLine true — for simplicity
    we convert first N objects to JSONL for this pipeline.
    """
    url = "https://data.nasa.gov/resource/y77d-th95.json?$limit=500"
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    with path.open("w", encoding="utf-8") as f:
        for i, obj in enumerate(data):
            obj.setdefault("_ingest_id", f"nasa-{i:05d}")
            f.write(json.dumps(obj, default=str) + "\n")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("data/generated/events.jsonl"))
    p.add_argument("--rows", type=int, default=500)
    p.add_argument(
        "--download-sample",
        action="store_true",
        help="Pull NASA meteorite sample JSON and convert to JSONL instead of synthetic events.",
    )
    args = p.parse_args()

    try:
        if args.download_sample:
            download_sample(args.output)
            print(f"Wrote sample JSONL to {args.output}")
        else:
            write_jsonl(args.output, args.rows)
            print(f"Wrote {args.rows} synthetic JSONL records to {args.output}")
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
