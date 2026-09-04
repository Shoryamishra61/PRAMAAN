"""FastAPI entry point for Dispute Integrity Gate."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.ai_lab_api import AiLabArtifactError, AiLabCaseResponse, build_case_ai_lab
from app.ai_research_api import (
    AiResearchArtifactError,
    AiResearchResponse,
    FeclV2Response,
    load_ai_research,
    load_fecl_v2,
)
from app.carve_research_api import (
    CarveResearchError,
    CarveResearchResponse,
    load_carve_research,
)
from app.case_actions import (
    InspectionRequest,
    InspectionResult,
    LocalWorkflowResult,
    OverrideRequest,
    QueuedReprocess,
    WorkflowActionError,
    inspect_source,
    mark_ready,
    override_local_hold,
    queue_reprocess,
)
from app.case_api import CaseDetailResponse, CaseListResponse, get_case, list_cases
from app.config import Settings, get_settings
from app.decision import GateStatus
from app.domain import ProcessingStatus
from app.evaluation_api import (
    EvaluationArtifactError,
    EvaluationDashboardResponse,
    EvaluationNotMeasured,
    load_latest_evaluation,
)
from app.health import HealthResponse, read_health
from app.ingestion import IngestPayloadError, IngestResult, ingest_event
from app.observability import StructuredLogEvent, emit_log
from app.quant_risk_api import (
    QuantRiskError,
    QuantRiskResponse,
    load_quant_risk_research,
)
from app.sandbox_api import (
    SandboxEvaluateRequest,
    SandboxEvaluateResponse,
    evaluate_sandbox_input,
)
from app.security import WebhookSignatureError, verify_webhook_signature

MAX_WEBHOOK_BYTES = 1_000_000


def _error_response(code: str, message: str, correlation_id: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "correlation_id": correlation_id,
            }
        },
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application without performing external network calls."""
    application = FastAPI(
        title="Dispute Integrity Gate",
        version="0.1.0",
        description="Read-only evidence integrity verifier; not a dispute outcome predictor.",
    )
    runtime_settings = settings or get_settings()

    @application.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return read_health(runtime_settings.database_path, runtime_settings.inference_mode)

    @application.post("/api/v1/sandbox/evaluate", response_model=SandboxEvaluateResponse)
    async def sandbox_evaluate(
        request: SandboxEvaluateRequest,
    ) -> SandboxEvaluateResponse | JSONResponse:
        """Evaluate user-supplied synthetic input without persistence or network writes."""
        try:
            return await evaluate_sandbox_input(request)
        except ValueError as error:
            return _error_response("SANDBOX_INPUT_INVALID", str(error), f"corr_{uuid4().hex}", 400)

    @application.post("/api/v1/webhooks/razorpay", response_model=IngestResult, status_code=202)
    async def razorpay_webhook(request: Request) -> IngestResult | JSONResponse:
        started = perf_counter()
        correlation_id = f"corr_{uuid4().hex}"
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_WEBHOOK_BYTES:
                    return _error_response(
                        "INGEST_PAYLOAD_TOO_LARGE",
                        "Webhook payload exceeds the 1 MB limit.",
                        correlation_id,
                        413,
                    )
            except ValueError:
                return _error_response(
                    "INGEST_CONTENT_LENGTH_INVALID",
                    "Webhook Content-Length is invalid.",
                    correlation_id,
                    400,
                )
        raw_body = await request.body()
        if len(raw_body) > MAX_WEBHOOK_BYTES:
            return _error_response(
                "INGEST_PAYLOAD_TOO_LARGE",
                "Webhook payload exceeds the 1 MB limit.",
                correlation_id,
                413,
            )
        signature = request.headers.get("X-Razorpay-Signature")
        event_id = request.headers.get("x-razorpay-event-id")
        if runtime_settings.webhook_secret is None:
            emit_log(
                StructuredLogEvent(
                    module="webhook",
                    action="webhook.configuration_failure",
                    correlation_id=correlation_id,
                    latency_ms=int((perf_counter() - started) * 1000),
                    failure_class="WEBHOOK_SECRET_NOT_CONFIGURED",
                )
            )
            return _error_response(
                "SYSTEM_INTERNAL_ERROR",
                "Webhook authentication is not configured.",
                correlation_id,
                503,
            )
        try:
            verify_webhook_signature(
                raw_body,
                signature,
                runtime_settings.webhook_secret.get_secret_value().encode("utf-8"),
            )
        except WebhookSignatureError as error:
            emit_log(
                StructuredLogEvent(
                    module="webhook",
                    action="webhook.signature_invalid",
                    correlation_id=correlation_id,
                    latency_ms=int((perf_counter() - started) * 1000),
                    failure_class=error.code,
                )
            )
            return _error_response(error.code, str(error), correlation_id, 401)

        if event_id is None or not event_id.strip():
            emit_log(
                StructuredLogEvent(
                    module="webhook",
                    action="webhook.event_id_missing",
                    correlation_id=correlation_id,
                    latency_ms=int((perf_counter() - started) * 1000),
                    failure_class="INGEST_EVENT_ID_MISSING",
                )
            )
            return _error_response(
                "INGEST_EVENT_ID_MISSING",
                "x-razorpay-event-id is required.",
                correlation_id,
                400,
            )

        try:
            result = await run_in_threadpool(
                ingest_event,
                runtime_settings.database_path,
                raw_body,
                event_id,
                correlation_id,
                datetime.now(timezone.utc),
            )
        except IngestPayloadError as error:
            emit_log(
                StructuredLogEvent(
                    module="webhook",
                    action="webhook.payload_invalid",
                    correlation_id=correlation_id,
                    event_id=event_id,
                    latency_ms=int((perf_counter() - started) * 1000),
                    failure_class=error.code,
                )
            )
            return _error_response(error.code, str(error), correlation_id, 400)
        emit_log(
            StructuredLogEvent(
                module="webhook",
                action="webhook.duplicate" if result.duplicate else "webhook.accepted",
                correlation_id=correlation_id,
                event_id=result.event_id,
                case_id=result.case_id,
                latency_ms=int((perf_counter() - started) * 1000),
                status="accepted",
            )
        )
        return result

    @application.get("/api/v1/cases", response_model=CaseListResponse)
    def case_queue(
        gate_status: GateStatus | None = None,
        processing_status: ProcessingStatus | None = None,
        reason_profile: str | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str | None = None,
    ) -> CaseListResponse | JSONResponse:
        try:
            return list_cases(
                runtime_settings.database_path,
                gate_status=gate_status,
                processing_status=processing_status,
                reason_profile=reason_profile,
                limit=limit,
                cursor=cursor,
            )
        except ValueError as error:
            return _error_response("QUEUE_CURSOR_INVALID", str(error), f"corr_{uuid4().hex}", 400)

    @application.get("/api/v1/cases/{case_id}", response_model=CaseDetailResponse)
    def case_detail(case_id: str) -> CaseDetailResponse | JSONResponse:
        detail = get_case(runtime_settings.database_path, case_id)
        if detail is None:
            return _error_response(
                "CASE_NOT_FOUND", "Case was not found.", f"corr_{uuid4().hex}", 404
            )
        return detail

    @application.get("/api/v1/ai-lab/cases/{case_id}", response_model=AiLabCaseResponse)
    def case_ai_lab(case_id: str) -> AiLabCaseResponse | JSONResponse:
        detail = get_case(runtime_settings.database_path, case_id)
        if detail is None:
            return _error_response(
                "CASE_NOT_FOUND", "Case was not found.", f"corr_{uuid4().hex}", 404
            )
        try:
            return build_case_ai_lab(detail)
        except AiLabArtifactError as error:
            return _error_response(
                "AI_LAB_ARTIFACT_UNAVAILABLE",
                str(error),
                f"corr_{uuid4().hex}",
                503,
            )

    @application.get("/api/v1/ai-research", response_model=AiResearchResponse)
    def ai_research() -> AiResearchResponse | JSONResponse:
        try:
            return load_ai_research()
        except AiResearchArtifactError as error:
            return _error_response(
                "AI_RESEARCH_ARTIFACT_UNAVAILABLE",
                str(error),
                f"corr_{uuid4().hex}",
                503,
            )

    @application.get("/api/v1/ai-research/fecl-v2", response_model=FeclV2Response)
    def fecl_v2_research() -> FeclV2Response | JSONResponse:
        try:
            return load_fecl_v2()
        except AiResearchArtifactError as error:
            return _error_response(
                "FECL_V2_ARTIFACT_UNAVAILABLE",
                str(error),
                f"corr_{uuid4().hex}",
                503,
            )

    @application.get("/api/v1/research/carve-v4.5", response_model=CarveResearchResponse)
    def carve_research() -> CarveResearchResponse | JSONResponse:
        try:
            return load_carve_research()
        except CarveResearchError as error:
            return _error_response(
                "CARVE_RESEARCH_ARTIFACT_UNAVAILABLE",
                str(error),
                f"corr_{uuid4().hex}",
                503,
            )

    @application.get("/api/v1/research/quant-risk", response_model=QuantRiskResponse)
    def quant_risk_research() -> QuantRiskResponse | JSONResponse:
        try:
            return load_quant_risk_research(runtime_settings.database_path)
        except QuantRiskError as error:
            return _error_response(
                "QUANT_RISK_ARTIFACT_UNAVAILABLE",
                str(error),
                f"corr_{uuid4().hex}",
                503,
            )

    @application.post("/api/v1/cases/{case_id}/reprocess", response_model=QueuedReprocess)
    def reprocess_case(
        case_id: str,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> QueuedReprocess | JSONResponse:
        try:
            result = queue_reprocess(
                runtime_settings.database_path,
                case_id=case_id,
                operator_id=runtime_settings.demo_operator_id,
                requested_at=datetime.now(timezone.utc),
                idempotency_key=idempotency_key,
            )
        except ValueError as error:
            return _error_response(
                "REPROCESS_REQUEST_INVALID", str(error), f"corr_{uuid4().hex}", 400
            )
        if result is None:
            return _error_response(
                "CASE_NOT_FOUND", "Case was not found.", f"corr_{uuid4().hex}", 404
            )
        return result

    @application.post("/api/v1/cases/{case_id}/inspect", response_model=InspectionResult)
    def inspect_case_source(
        case_id: str, request: InspectionRequest
    ) -> InspectionResult | JSONResponse:
        try:
            return inspect_source(
                runtime_settings.database_path,
                case_id=case_id,
                operator_id=runtime_settings.demo_operator_id,
                request=request,
                inspected_at=datetime.now(timezone.utc),
            )
        except WorkflowActionError as error:
            return _error_response(error.code, str(error), f"corr_{uuid4().hex}", error.status_code)

    @application.post("/api/v1/cases/{case_id}/override", response_model=LocalWorkflowResult)
    def override_case_hold(
        case_id: str, request: OverrideRequest
    ) -> LocalWorkflowResult | JSONResponse:
        try:
            return override_local_hold(
                runtime_settings.database_path,
                case_id=case_id,
                operator_id=runtime_settings.demo_operator_id,
                request=request,
                overridden_at=datetime.now(timezone.utc),
            )
        except WorkflowActionError as error:
            return _error_response(error.code, str(error), f"corr_{uuid4().hex}", error.status_code)

    @application.post("/api/v1/cases/{case_id}/mark-ready", response_model=LocalWorkflowResult)
    def mark_case_ready(case_id: str) -> LocalWorkflowResult | JSONResponse:
        try:
            return mark_ready(
                runtime_settings.database_path,
                case_id=case_id,
                operator_id=runtime_settings.demo_operator_id,
                marked_at=datetime.now(timezone.utc),
            )
        except WorkflowActionError as error:
            return _error_response(error.code, str(error), f"corr_{uuid4().hex}", error.status_code)

    @application.get(
        "/api/v1/evaluation/latest",
        response_model=EvaluationDashboardResponse | EvaluationNotMeasured,
    )
    def latest_evaluation() -> EvaluationDashboardResponse | EvaluationNotMeasured | JSONResponse:
        try:
            return load_latest_evaluation(runtime_settings.results_directory)
        except EvaluationArtifactError as error:
            return _error_response(
                "EVALUATION_ARTIFACT_INVALID", str(error), f"corr_{uuid4().hex}", 500
            )

    return application


app = create_app()
