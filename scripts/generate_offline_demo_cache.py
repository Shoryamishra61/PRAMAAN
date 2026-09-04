"""Generate the labeled v1 offline regex-fixture replay cache once."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
from pathlib import Path

from app.evaluation_artifact import compute_config_sha256
from app.extraction import (
    CLAIM_SCHEMA_VERSION,
    PROMPT_VERSION,
    ExtractionRequest,
    default_claim_allowlist,
)
from app.offline_replay import OfflineReplayCache, offline_cache_key
from app.regex_baseline import RegexBaselineExtractor


def replay_config_hash(repo_root: Path, prompt_version: str = PROMPT_VERSION) -> str:
    """Bind replay configuration to deterministic contracts and prompt version."""
    contract_hash = compute_config_sha256(
        repo_root,
        (
            repo_root / "contracts" / "grounded-claim.schema.json",
            repo_root / "contracts" / "refund_not_processed_v1.yaml",
        ),
    )
    return hashlib.sha256(f"{contract_hash}\0{prompt_version}".encode()).hexdigest()


async def generate(repo_root: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite offline cache: {output}")
    config_hash = replay_config_hash(repo_root)
    extractor = RegexBaselineExtractor()
    entries = {}
    for name in ("pass", "review", "block"):
        text = (
            (repo_root / "data" / "demo" / name / "evidence" / "customer_communication.txt")
            .read_text(encoding="utf-8")
            .strip()
        )
        request = ExtractionRequest(
            document_id=f"doc_{name}",
            document_type="text/plain",
            canonical_text=text,
            allowed_claim_types=default_claim_allowlist(),
        )
        result = await extractor.extract(request)
        entries[offline_cache_key(text, config_hash)] = result.model_copy(
            update={"extractor_id": "offline-replay-precomputed-regex-v2"}
        )
    cache = OfflineReplayCache(
        source_mode="precomputed_regex_fixture",
        extractor_config_sha256=config_hash,
        prompt_version=PROMPT_VERSION,
        schema_version=CLAIM_SCHEMA_VERSION,
        entries=entries,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(cache.model_dump_json(indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(generate(args.repo_root.resolve(), args.output))
    print(f"Generated labeled offline replay cache at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
