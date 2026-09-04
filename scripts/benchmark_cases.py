"""List benchmark runtime case paths with DEV-safe defaults."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal, cast

from app.benchmark_integrity import load_benchmark_case_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument("--confirm-frozen", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    split = cast(Literal["dev", "holdout"], args.split)
    cases = load_benchmark_case_paths(
        args.dataset,
        split=split,
        confirm_frozen=args.confirm_frozen,
    )
    print("\n".join(path.name for path in cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
