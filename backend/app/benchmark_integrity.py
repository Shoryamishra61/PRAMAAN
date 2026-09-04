"""One-way benchmark freeze and holdout byte-integrity verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Literal, cast

MANIFEST_SCHEMA_VERSION = "1.0"
HOLDOUT_MANIFEST_NAME = "holdout-manifest.json"
MANIFEST_DIGEST_NAME = "manifest.sha256"


class BenchmarkIntegrityError(ValueError):
    """Raised when the frozen benchmark does not match its committed manifest."""


class HoldoutAccessError(PermissionError):
    """Raised when a caller attempts to load holdout without explicit confirmation."""


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _read_json_object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BenchmarkIntegrityError(f"Expected JSON object: {path}")
    return cast(dict[str, object], value)


def _holdout_files(dataset_root: Path) -> list[Path]:
    holdout_root = dataset_root / "holdout"
    if not holdout_root.is_dir():
        raise BenchmarkIntegrityError(f"Missing holdout directory: {holdout_root}")
    files = sorted(path for path in holdout_root.rglob("*") if path.is_file())
    if not files:
        raise BenchmarkIntegrityError("Holdout directory contains no files.")
    return files


def _build_holdout_manifest(dataset_root: Path, dataset: dict[str, object]) -> dict[str, object]:
    cases: list[dict[str, object]] = []
    holdout_root = dataset_root / "holdout"
    case_directories = sorted(path for path in holdout_root.iterdir() if path.is_dir())
    for case_root in case_directories:
        files: list[dict[str, object]] = []
        for path in sorted(item for item in case_root.rglob("*") if item.is_file()):
            content = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(dataset_root).as_posix(),
                    "bytes": len(content),
                    "sha256": _sha256_bytes(content),
                }
            )
        if not files:
            raise BenchmarkIntegrityError(f"Empty holdout case directory: {case_root}")
        cases.append({"case_id": case_root.name, "files": files})
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "dataset_id": dataset.get("dataset_id"),
        "generator_version": dataset.get("generator_version"),
        "seed": dataset.get("seed"),
        "split": "holdout",
        "case_count": len(cases),
        "cases": cases,
    }


def freeze_benchmark(dataset_root: Path, *, frozen_at: str) -> str:
    """Freeze a new dataset version once and return its holdout manifest SHA-256."""
    dataset_path = dataset_root / "dataset.json"
    dataset = _read_json_object(dataset_path)
    if dataset.get("frozen") is True:
        raise BenchmarkIntegrityError(
            "Dataset is already frozen; create a new version to change it."
        )
    for name in (HOLDOUT_MANIFEST_NAME, MANIFEST_DIGEST_NAME):
        if (dataset_root / name).exists():
            raise BenchmarkIntegrityError(f"Refusing to overwrite existing freeze artifact: {name}")

    manifest = _build_holdout_manifest(dataset_root, dataset)
    counts = dataset.get("counts")
    expected_count = counts.get("holdout") if isinstance(counts, dict) else None
    if manifest["case_count"] != expected_count:
        message = (
            f"Holdout case count mismatch: expected {expected_count}, "
            f"found {manifest['case_count']}"
        )
        raise BenchmarkIntegrityError(message)

    manifest_bytes = _canonical_json(manifest)
    digest = _sha256_bytes(manifest_bytes)
    (dataset_root / HOLDOUT_MANIFEST_NAME).write_bytes(manifest_bytes)
    (dataset_root / MANIFEST_DIGEST_NAME).write_text(
        f"{digest}  {HOLDOUT_MANIFEST_NAME}\n", encoding="ascii"
    )
    dataset.update(
        {
            "frozen": True,
            "frozen_at": frozen_at,
            "holdout_manifest": HOLDOUT_MANIFEST_NAME,
            "holdout_manifest_sha256": digest,
        }
    )
    dataset_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verify_holdout_manifest(dataset_root)
    return digest


def _manifest_file_records(manifest: dict[str, object]) -> dict[str, tuple[int, str]]:
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        raise BenchmarkIntegrityError("Holdout manifest cases must be a list.")
    records: dict[str, tuple[int, str]] = {}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("files"), list):
            raise BenchmarkIntegrityError("Malformed holdout manifest case record.")
        for record in case["files"]:
            if not isinstance(record, dict):
                raise BenchmarkIntegrityError("Malformed holdout manifest file record.")
            relative = record.get("path")
            size = record.get("bytes")
            digest = record.get("sha256")
            if (
                not isinstance(relative, str)
                or not isinstance(size, int)
                or not isinstance(digest, str)
            ):
                raise BenchmarkIntegrityError("Malformed holdout manifest file fields.")
            pure = PurePosixPath(relative)
            if (
                pure.is_absolute()
                or ".." in pure.parts
                or not pure.parts
                or pure.parts[0] != "holdout"
            ):
                raise BenchmarkIntegrityError(f"Unsafe holdout manifest path: {relative}")
            if relative in records:
                raise BenchmarkIntegrityError(f"Duplicate holdout manifest path: {relative}")
            records[relative] = (size, digest)
    return records


def verify_holdout_manifest(dataset_root: Path) -> str:
    """Verify root digest, complete file set, sizes, and per-file hashes."""
    dataset = _read_json_object(dataset_root / "dataset.json")
    if dataset.get("frozen") is not True:
        raise BenchmarkIntegrityError("Dataset is not frozen.")
    manifest_path = dataset_root / HOLDOUT_MANIFEST_NAME
    manifest_bytes = manifest_path.read_bytes()
    actual_manifest_digest = _sha256_bytes(manifest_bytes)
    expected_manifest_digest = dataset.get("holdout_manifest_sha256")
    digest_record = (dataset_root / MANIFEST_DIGEST_NAME).read_text(encoding="ascii")
    expected_digest_record = f"{actual_manifest_digest}  {HOLDOUT_MANIFEST_NAME}\n"
    if (
        actual_manifest_digest != expected_manifest_digest
        or digest_record != expected_digest_record
    ):
        raise BenchmarkIntegrityError("Holdout manifest SHA-256 mismatch.")

    manifest = _read_json_object(manifest_path)
    if (
        manifest.get("dataset_id") != dataset.get("dataset_id")
        or manifest.get("split") != "holdout"
    ):
        raise BenchmarkIntegrityError("Holdout manifest dataset identity mismatch.")
    records = _manifest_file_records(manifest)
    actual_paths = {
        path.relative_to(dataset_root).as_posix() for path in _holdout_files(dataset_root)
    }
    if actual_paths != set(records):
        raise BenchmarkIntegrityError("Holdout file set differs from frozen manifest.")
    for relative, (expected_size, expected_digest) in records.items():
        content = (dataset_root / Path(relative)).read_bytes()
        if len(content) != expected_size or _sha256_bytes(content) != expected_digest:
            raise BenchmarkIntegrityError(f"Holdout file hash mismatch: {relative}")
    return actual_manifest_digest


def load_benchmark_case_paths(
    dataset_root: Path,
    *,
    split: Literal["dev", "holdout"] = "dev",
    confirm_frozen: bool = False,
) -> list[Path]:
    """Return case paths without reading generator metadata or ground truth."""
    if split == "holdout":
        if not confirm_frozen:
            raise HoldoutAccessError("HOLDOUT requires explicit --confirm-frozen.")
        verify_holdout_manifest(dataset_root)
    split_root = dataset_root / split
    if not split_root.is_dir():
        raise FileNotFoundError(split_root)
    return sorted(path for path in split_root.iterdir() if path.is_dir())
