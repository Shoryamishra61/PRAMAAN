"""Replay signed synthetic webhooks and materialize the offline analyst demo."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.case_pipeline import CaseEvaluationInput, CaseEvaluationOutcome, evaluate_case
from app.config import Settings
from app.database import connect_database
from app.domain import to_storage_timestamp
from app.main import create_app
from app.offline_replay import OfflineReplayExtractor
from app.security import compute_webhook_signature
from app.verification import Finding, FindingEffect, RefundRecord
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

DEMO_SECRET = "synthetic-demo-only-webhook-secret"
FIXTURE_NAMES = ("pass", "review", "block")
EVALUATED_AT = datetime(2026, 8, 23, 12, tzinfo=timezone.utc)


class SeededCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture: str
    case_id: str
    gate_status: str
    primary_reason_code: str | None
    signed_webhook_status: int


class DemoSeedSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: str = "offline_replay_precomputed_regex"
    synthetic: bool = True
    database_path: str
    cases: tuple[SeededCase, ...]


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _remove_existing_demo_database(database_path: Path, repo_root: Path) -> None:
    allowed = (repo_root / "var" / "demo.sqlite3").resolve()
    if database_path.resolve() != allowed:
        raise ValueError("--reset is restricted to the repository var/demo.sqlite3 path")
    for suffix in ("", "-shm", "-wal"):
        target = Path(f"{database_path}{suffix}")
        if target.exists():
            target.unlink()


def _finding_refs(finding: Finding) -> tuple[tuple[str, ...], tuple[str, ...]]:
    structured: list[str] = []
    claims: list[str] = []
    for reference in finding.evidence_refs:
        kind, separator, identifier = reference.partition(":")
        if separator and kind == "claim":
            claims.append(identifier)
        elif separator and kind == "refund":
            structured.append(identifier)
        elif kind in {"payment", "case", "document"}:
            structured.append("structured_refund_ledger")
        else:
            structured.append(reference)
    return tuple(dict.fromkeys(structured)), tuple(dict.fromkeys(claims))


def _persist_case_result(
    database_path: Path,
    fixture_name: str,
    case_id: str,
    canonical_text: str,
    payment: dict[str, Any],
    ledger: dict[str, Any],
    outcome: CaseEvaluationOutcome,
) -> None:
    timestamp = to_storage_timestamp(EVALUATED_AT)
    document_id = f"doc_{fixture_name}"
    run_id = f"run_demo_{fixture_name}"
    request_hash = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    extractor_id = "offline-replay-precomputed-regex-v2"
    with connect_database(database_path) as connection:
        connection.execute(
            "INSERT INTO payment_snapshots "
            "(case_id, payment_id, captured_amount_minor, currency, captured_at, "
            "snapshot_complete, snapshot_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                case_id,
                payment["payment_id"],
                payment["captured_amount_minor"],
                payment["currency"],
                payment["captured_at"],
                int(bool(payment["snapshot_complete"])),
                json.dumps(payment, separators=(",", ":"), sort_keys=True),
            ),
        )
        for refund in ledger["records"]:
            connection.execute(
                "INSERT INTO refund_records "
                "(id, case_id, payment_id, amount_minor, currency, local_status, created_at, "
                "processed_at, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    refund["id"],
                    case_id,
                    refund["payment_id"],
                    refund["amount_minor"],
                    refund["currency"],
                    refund["local_status"],
                    refund.get("created_at"),
                    refund.get("processed_at"),
                    refund.get("reference"),
                ),
            )
        connection.execute(
            "INSERT INTO evidence_documents "
            "(id, case_id, source_type, source_system, media_type, canonical_text, "
            "content_sha256, ingested_at, is_complete_source, metadata_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                document_id,
                case_id,
                "customer_communication",
                "synthetic_fixture",
                "text/plain",
                canonical_text,
                hashlib.sha256(canonical_text.encode("utf-8")).hexdigest(),
                timestamp,
                1,
                json.dumps(
                    {"synthetic": True, "fixture": fixture_name},
                    separators=(",", ":"),
                    sort_keys=True,
                ),
            ),
        )
        connection.execute(
            "INSERT INTO extraction_runs "
            "(id, document_id, extractor_id, model_id, prompt_version, schema_version, "
            "request_hash, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                document_id,
                extractor_id,
                None,
                "refund-claims-v1",
                "grounded-claim-v1",
                request_hash,
                outcome.semantic.status.value,
                timestamp,
            ),
        )
        for claim in outcome.semantic.claims:
            connection.execute(
                "INSERT INTO grounded_claims "
                "(id, extraction_run_id, document_id, claim_type, raw_value, amount_minor, "
                "currency, normalized_timestamp, refund_reference, source_quote, span_start, "
                "span_end, grounding_status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    claim.claim_id,
                    run_id,
                    document_id,
                    claim.claim_type.value,
                    claim.raw_value,
                    claim.amount_minor,
                    claim.currency,
                    to_storage_timestamp(claim.normalized_timestamp),
                    claim.refund_reference,
                    claim.source_quote,
                    claim.span_start,
                    claim.span_end,
                    claim.grounding_status.value,
                    timestamp,
                ),
            )
        for index, finding in enumerate(outcome.verification.findings, start=1):
            structured_refs, claim_refs = _finding_refs(finding)
            connection.execute(
                "INSERT INTO findings "
                "(id, case_id, rule_code, severity, decision_effect, explanation, "
                "structured_refs_json, claim_refs_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"finding_demo_{fixture_name}_{index}",
                    case_id,
                    finding.code,
                    "material" if finding.effect is FindingEffect.BLOCK else "non_material",
                    finding.effect.value,
                    finding.summary,
                    json.dumps(structured_refs, separators=(",", ":")),
                    json.dumps(claim_refs, separators=(",", ":")),
                    timestamp,
                ),
            )
        decision = outcome.decision
        connection.execute(
            "INSERT INTO gate_decisions "
            "(id, case_id, status, primary_reason_code, engine_version, decision_json, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                f"decision_demo_{fixture_name}",
                case_id,
                decision.status.value,
                decision.primary_reason_code,
                decision.engine_version,
                decision.model_dump_json(),
                timestamp,
            ),
        )
        connection.execute(
            "UPDATE dispute_cases SET processing_status = 'READY', updated_at = ? WHERE id = ?",
            (timestamp, case_id),
        )
        connection.execute(
            "UPDATE jobs SET status = 'COMPLETED', updated_at = ?, available_at = ?, "
            "lease_until = NULL, last_error_code = NULL WHERE case_id = ?",
            (timestamp, timestamp, case_id),
        )


async def _evaluate_fixture(
    repo_root: Path,
    fixture_name: str,
    case_id: str,
    extractor: OfflineReplayExtractor,
) -> tuple[CaseEvaluationOutcome, str, dict[str, Any], dict[str, Any]]:
    fixture_root = repo_root / "data" / "demo" / fixture_name
    text = (
        (fixture_root / "evidence" / "customer_communication.txt")
        .read_text(encoding="utf-8")
        .strip()
    )
    payment = _read_json(fixture_root / "payment_snapshot.json")
    ledger = _read_json(fixture_root / "refunds.json")
    refunds = tuple(RefundRecord.model_validate(record) for record in ledger["records"])
    outcome = await evaluate_case(
        CaseEvaluationInput(
            case_id=case_id,
            payment_id=payment["payment_id"],
            captured_amount_minor=payment["captured_amount_minor"],
            payment_currency=payment["currency"],
            payment_snapshot_complete=payment["snapshot_complete"],
            refund_ledger_complete=ledger["ledger_complete"],
            document_id=f"doc_{fixture_name}",
            canonical_text=text,
            refunds=refunds,
        ),
        extractor,
        EVALUATED_AT,
    )
    return outcome, text, payment, ledger


def seed_demo(
    repo_root: Path,
    database_path: Path,
    *,
    reset: bool = False,
) -> DemoSeedSummary:
    """Create three synthetic cases through the authenticated inbound API and offline gate."""
    repo_root = repo_root.resolve()
    database_path = database_path.resolve()
    if reset:
        _remove_existing_demo_database(database_path, repo_root)
    elif database_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing demo database: {database_path}")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    extractor = OfflineReplayExtractor(repo_root / "data" / "offline-replay" / "v2.json")
    client = TestClient(
        create_app(Settings(database_path=database_path, webhook_secret=DEMO_SECRET))
    )
    seeded: list[SeededCase] = []
    for fixture_name in FIXTURE_NAMES:
        fixture_root = repo_root / "data" / "demo" / fixture_name
        manifest = _read_json(fixture_root / "manifest.json")
        raw_body = (fixture_root / "razorpay_event.json").read_bytes()
        response = client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": compute_webhook_signature(
                    raw_body, DEMO_SECRET.encode("utf-8")
                ),
                "x-razorpay-event-id": f"evt_{manifest['fixture_id']}",
            },
        )
        if response.status_code != 202:
            raise RuntimeError(f"Signed fixture replay failed for {fixture_name}: {response.text}")
        case_id = cast(str, response.json()["case_id"])
        outcome, text, payment, ledger = asyncio.run(
            _evaluate_fixture(repo_root, fixture_name, case_id, extractor)
        )
        if outcome.decision.status.value != manifest["expected_gate_status"]:
            raise RuntimeError(
                f"{fixture_name} expected {manifest['expected_gate_status']} but produced "
                f"{outcome.decision.status.value}"
            )
        if outcome.decision.primary_reason_code != manifest["expected_primary_reason_code"]:
            raise RuntimeError(f"{fixture_name} primary reason did not match its manifest")
        _persist_case_result(
            database_path,
            fixture_name,
            case_id,
            text,
            payment,
            ledger,
            outcome,
        )
        seeded.append(
            SeededCase(
                fixture=fixture_name,
                case_id=case_id,
                gate_status=outcome.decision.status.value,
                primary_reason_code=outcome.decision.primary_reason_code,
                signed_webhook_status=response.status_code,
            )
        )
    return DemoSeedSummary(database_path=str(database_path), cases=tuple(seeded))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, default=Path("var/demo.sqlite3"))
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    summary = seed_demo(args.repo_root, args.database, reset=args.reset)
    print(summary.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
