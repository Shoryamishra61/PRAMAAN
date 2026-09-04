# ADR-004 — Canonical Text/JSON Evidence in v1

**Status:** Accepted

## Context
The core hypothesis is cross-source refund-evidence integrity, not OCR quality. PDF/scanned-document parsing introduces significant security, dependency, and evaluation complexity.

## Decision
The evaluated v1 accepts canonical `text/plain` communication evidence and structured JSON refund/payment records. Demo fixtures may visually resemble exported emails/ledgers, but benchmark truth is based on canonical text/JSON.

PDF/OCR support is deferred until it can be evaluated independently.

## Consequences
- claim grounding is exact and testable;
- upload/parser attack surface is smaller;
- README must disclose this scope explicitly.
