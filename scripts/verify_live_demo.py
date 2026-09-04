"""Verify the running seeded demo over proxy-free loopback HTTP."""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, cast
from urllib.request import ProxyHandler, build_opener

EXPECTED_ARTIFACT_SHA256 = "15349fd24f2fbceb1c6a38edafee92d5953f22af2e9611efcda17ba20f1992b8"


def _text(url: str) -> str:
    opener = build_opener(ProxyHandler({}))
    last_error: Exception | None = None
    for _ in range(30):
        try:
            with opener.open(url, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"{url} returned HTTP {response.status}.")
                content = cast(bytes, response.read()).decode("utf-8")
                if not content.strip():
                    raise RuntimeError(f"{url} returned an empty body.")
                return content
        except (OSError, RuntimeError, UnicodeError) as error:
            last_error = error
            time.sleep(0.1)
    raise RuntimeError(f"{url} did not become semantically ready.") from last_error


def _object(url: str) -> dict[str, Any]:
    value = json.loads(_text(url))
    if not isinstance(value, dict):
        raise RuntimeError(f"{url} did not return a JSON object.")
    return cast(dict[str, Any], value)


def verify_live_demo(backend_port: int, frontend_port: int) -> dict[str, object]:
    api_root = f"http://127.0.0.1:{backend_port}"
    health = _object(f"{api_root}/api/v1/health")
    if (health.get("app"), health.get("database"), health.get("inference_mode")) != (
        "ok",
        "ready",
        "offline",
    ):
        raise RuntimeError(f"Unexpected health response: {health!r}")

    queue = _object(f"{api_root}/api/v1/cases")
    items = queue.get("items")
    if not isinstance(items, list) or len(items) != 3:
        raise RuntimeError("The seeded queue must contain exactly three cases.")
    if not all(isinstance(item, dict) for item in items):
        raise RuntimeError("The seeded queue returned an invalid case item.")
    statuses = sorted(str(item.get("gate_status")) for item in items)
    if statuses != ["BLOCK", "PASS", "REVIEW"]:
        raise RuntimeError(f"Unexpected seeded gate states: {statuses!r}")
    if any(not str(item.get("raw_reason_code", "")).strip() for item in items):
        raise RuntimeError("A seeded case did not preserve its raw reason code.")

    evaluation = _object(f"{api_root}/api/v1/evaluation/latest")
    dataset = evaluation.get("dataset")
    metrics = evaluation.get("metrics")
    if not isinstance(dataset, dict) or not isinstance(metrics, dict):
        raise RuntimeError("The evaluation projection is incomplete.")
    material = metrics.get("material_conflict")
    operational = metrics.get("operational")
    if not isinstance(material, dict) or not isinstance(operational, dict):
        raise RuntimeError("The evaluation metrics projection is incomplete.")
    expected = {
        "status": "MEASURED",
        "synthetic": True,
        "split": "holdout",
        "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "total_cases": 60,
        "true_positive": 10,
        "false_negative": 10,
        "false_pass": 10,
        "false_block": 0,
    }
    observed = {
        "status": evaluation.get("status"),
        "synthetic": dataset.get("synthetic"),
        "split": dataset.get("split"),
        "artifact_sha256": evaluation.get("artifact_sha256"),
        "total_cases": operational.get("total_cases"),
        "true_positive": material.get("true_positive"),
        "false_negative": material.get("false_negative"),
        "false_pass": operational.get("false_pass_block_cases"),
        "false_block": operational.get("false_block_nonblock_cases"),
    }
    if observed != expected:
        raise RuntimeError(f"Artifact-backed evaluation mismatch: {observed!r}")

    frontend = _text(f"http://127.0.0.1:{frontend_port}")
    if '<div id="root"></div>' not in frontend:
        raise RuntimeError("The frontend root was not served.")

    return {
        "rehearsal": "technical_golden_path",
        "signed_webhook_seeded_cases": len(items),
        "gate_states": statuses,
        "inference_mode": health["inference_mode"],
        "artifact_sha256": evaluation["artifact_sha256"],
        "artifact_case_count": operational["total_cases"],
        "network_write_performed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-port", type=int, default=18000)
    parser.add_argument("--frontend-port", type=int, default=5173)
    args = parser.parse_args()
    print(
        json.dumps(
            verify_live_demo(args.backend_port, args.frontend_port),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
