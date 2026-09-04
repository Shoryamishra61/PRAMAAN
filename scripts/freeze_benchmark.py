"""Freeze a generated benchmark version; this operation cannot overwrite a freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.benchmark_integrity import freeze_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--frozen-at", required=True, help="Recorded ISO date/time for the freeze")
    args = parser.parse_args()
    digest = freeze_benchmark(args.dataset, frozen_at=args.frozen_at)
    print(f"Frozen benchmark; holdout manifest SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
