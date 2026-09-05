"""Run DEV safely or the explicitly confirmed final frozen HOLDOUT evaluation."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, cast

from app.evaluation_artifact import write_evaluation_artifact
from app.evaluator import evaluate_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "holdout"), default="dev")
    parser.add_argument("--confirm-frozen", action="store_true")
    parser.add_argument("--release-freeze", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--created-at")
    parser.add_argument("--code-commit", default="UNAVAILABLE_NOT_RECORDED")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    split = cast(Literal["dev", "holdout"], args.split)
    created_at = (
        datetime.fromisoformat(args.created_at.replace("Z", "+00:00"))
        if args.created_at
        else datetime.now(timezone.utc)
    )
    artifact = asyncio.run(
        evaluate_benchmark(
            Path.cwd(),
            args.dataset,
            split=split,
            run_id=args.run_id,
            created_at=created_at,
            confirm_frozen=args.confirm_frozen,
            release_freeze_path=args.release_freeze,
            code_commit=args.code_commit,
        )
    )
    written = write_evaluation_artifact(args.output, artifact)
    print(f"Wrote {written.path} sha256={written.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
