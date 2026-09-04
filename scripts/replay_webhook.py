"""Replay one exact Razorpay-compatible fixture with an environment-provided secret."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx
from app.security import compute_webhook_signature


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--event-id", required=True)
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:18000/api/v1/webhooks/razorpay",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    secret = os.environ.get("DIG_WEBHOOK_SECRET")
    if not secret:
        print("DIG_WEBHOOK_SECRET is required.", file=sys.stderr)
        return 2

    raw_body = args.fixture.read_bytes()
    signature = compute_webhook_signature(raw_body, secret.encode("utf-8"))
    response = httpx.post(
        args.url,
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": args.event_id,
        },
        timeout=5.0,
    )
    print(json.dumps(response.json(), indent=2, sort_keys=True))
    return 0 if 200 <= response.status_code < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())
