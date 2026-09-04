# 15 — Database Schema

SQLite logical schema. Exact migration syntax may be implemented with SQLAlchemy or sqlite3; keep field semantics.

## ingest_events
- `razorpay_event_id TEXT PRIMARY KEY`
- `event_name TEXT NOT NULL`
- `account_id TEXT`
- `body_sha256 TEXT NOT NULL`
- `received_at TEXT NOT NULL`
- `event_created_at TEXT`
- `case_id TEXT`
- `correlation_id TEXT NOT NULL`

Do not use Bloom filter; official unique event ID + unique constraint is sufficient.

## dispute_cases
- `id TEXT PRIMARY KEY`
- `razorpay_dispute_id TEXT UNIQUE`
- `payment_id TEXT NOT NULL`
- `amount_minor INTEGER NOT NULL`
- `currency TEXT NOT NULL`
- `raw_reason_code TEXT`
- `reason_description TEXT`
- `reason_profile TEXT NOT NULL`
- `respond_by TEXT`
- `razorpay_status TEXT`
- `razorpay_phase TEXT`
- `processing_status TEXT NOT NULL`
- `workflow_status TEXT NOT NULL`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Do **not** use `payment_id UNIQUE` because one payment can conceptually have lifecycle events/disputes; uniqueness belongs to the dispute/case key.

## payment_snapshots
- `case_id TEXT PRIMARY KEY REFERENCES dispute_cases(id)`
- `payment_id TEXT NOT NULL`
- `captured_amount_minor INTEGER`
- `currency TEXT`
- `captured_at TEXT`
- `snapshot_complete INTEGER NOT NULL`
- `snapshot_json TEXT`

## refund_records
- `id TEXT PRIMARY KEY`
- `case_id TEXT REFERENCES dispute_cases(id)`
- `payment_id TEXT NOT NULL`
- `amount_minor INTEGER NOT NULL`
- `currency TEXT NOT NULL`
- `local_status TEXT NOT NULL`
- `created_at TEXT`
- `processed_at TEXT`
- `reference TEXT`

Index `case_id`, `payment_id`.

## evidence_documents
- `id TEXT PRIMARY KEY`
- `case_id TEXT REFERENCES dispute_cases(id)`
- `source_type TEXT NOT NULL`
- `source_system TEXT`
- `media_type TEXT NOT NULL`
- `canonical_text TEXT NOT NULL`
- `content_sha256 TEXT NOT NULL`
- `captured_at TEXT`
- `ingested_at TEXT NOT NULL`
- `is_complete_source INTEGER`
- `metadata_json TEXT`

## extraction_runs
- `id TEXT PRIMARY KEY`
- `document_id TEXT REFERENCES evidence_documents(id)`
- `extractor_id TEXT NOT NULL`
- `model_id TEXT`
- `prompt_version TEXT NOT NULL`
- `schema_version TEXT NOT NULL`
- `request_hash TEXT NOT NULL`
- `status TEXT NOT NULL`
- `latency_ms INTEGER`
- `created_at TEXT NOT NULL`

## grounded_claims
- `id TEXT PRIMARY KEY`
- `extraction_run_id TEXT`
- `document_id TEXT`
- `claim_type TEXT NOT NULL`
- `subject TEXT`
- `raw_value TEXT`
- `amount_minor INTEGER`
- `currency TEXT`
- `date_text TEXT`
- `normalized_timestamp TEXT`
- `refund_reference TEXT`
- `modality TEXT`
- `source_quote TEXT NOT NULL`
- `span_start INTEGER`
- `span_end INTEGER`
- `grounding_status TEXT NOT NULL`
- `created_at TEXT NOT NULL`

## findings
- `id TEXT PRIMARY KEY`
- `case_id TEXT NOT NULL`
- `rule_code TEXT NOT NULL`
- `severity TEXT NOT NULL`
- `decision_effect TEXT NOT NULL`
- `explanation TEXT NOT NULL`
- `structured_refs_json TEXT`
- `claim_refs_json TEXT`
- `created_at TEXT NOT NULL`

## gate_decisions
- `id TEXT PRIMARY KEY`
- `case_id TEXT NOT NULL`
- `status TEXT NOT NULL`
- `primary_reason_code TEXT`
- `engine_version TEXT NOT NULL`
- `decision_json TEXT NOT NULL`
- `created_at TEXT NOT NULL`

Prefer append-only decision history; query latest by timestamp/sequence.

## jobs
- `id TEXT PRIMARY KEY`
- `case_id TEXT NOT NULL`
- `job_type TEXT NOT NULL`
- `status TEXT NOT NULL`
- `attempt_count INTEGER NOT NULL DEFAULT 0`
- `available_at TEXT NOT NULL`
- `lease_until TEXT`
- `last_error_code TEXT`
- `created_at TEXT NOT NULL`
- `updated_at TEXT NOT NULL`

Indexes on `status, available_at`.

## review_events
- `id TEXT PRIMARY KEY`
- `case_id TEXT NOT NULL`
- `operator_id TEXT NOT NULL`
- `event_type TEXT NOT NULL`
- `reason_code TEXT`
- `note TEXT`
- `details_json TEXT`
- `created_at TEXT NOT NULL`

Event types:
- `SOURCE_INSPECTED`
- `REPAIR_REQUESTED`
- `LOCAL_HOLD_OVERRIDDEN`
- `MARKED_READY`
- `RETURNED_TO_REVIEW`

## audit_chain (SHOULD)
If implemented:
- `seq INTEGER PRIMARY KEY AUTOINCREMENT`
- `review_event_id TEXT`
- `prev_hash TEXT`
- `entry_hash TEXT NOT NULL`
- `canonical_payload TEXT NOT NULL`

No update/delete application API.

## evaluation_runs
- `id TEXT PRIMARY KEY`
- `dataset_id TEXT NOT NULL`
- `dataset_manifest_hash TEXT NOT NULL`
- `system_config_hash TEXT NOT NULL`
- `split TEXT NOT NULL`
- `artifact_path TEXT NOT NULL`
- `artifact_sha256 TEXT NOT NULL`
- `created_at TEXT NOT NULL`

## constraints
- amount fields `CHECK(amount_minor >= 0)` where zero valid;
- currencies normalized uppercase;
- gate status check;
- processing/workflow status check;
- unique extraction cache request hash if desired.

## data privacy
Synthetic demo data only.
Do not store real webhook secrets in database.
