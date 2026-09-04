"""Record the exact pre-holdout detector/evaluator/config byte freeze."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from app.release_freeze import create_release_freeze


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--created-at")
    args = parser.parse_args()
    created_at = (
        datetime.fromisoformat(args.created_at.replace("Z", "+00:00"))
        if args.created_at
        else datetime.now(timezone.utc)
    )
    freeze = create_release_freeze(Path.cwd(), args.dataset, args.output, created_at)
    print(
        f"Frozen code_bundle_sha256={freeze.code_bundle_sha256} "
        f"config_sha256={freeze.config_sha256}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
