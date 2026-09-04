"""Generate the deterministic synthetic benchmark at an explicit new path."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.benchmark_generator import generate_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    generate_benchmark(args.output)
    print(f"Generated synthetic benchmark at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
