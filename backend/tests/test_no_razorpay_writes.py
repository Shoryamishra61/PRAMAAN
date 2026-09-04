from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.config import Settings
from app.main import create_app
from fastapi.routing import APIRoute

REPO_ROOT = Path(__file__).parents[2]


def test_static_runtime_boundary_has_no_razorpay_write_client_or_endpoint() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_no_razorpay_writes.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "No Razorpay write client" in completed.stdout


def test_http_surface_contains_only_inbound_webhook_and_local_workflow_routes(
    tmp_path: Path,
) -> None:
    app = create_app(Settings(database_path=tmp_path / "boundary.sqlite3"))
    routes = {
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or set())
        if route.path.startswith("/api/v1/")
    }

    assert ("POST", "/api/v1/webhooks/razorpay") in routes
    assert all("razorpay" not in path or path == "/api/v1/webhooks/razorpay" for _, path in routes)
    assert not any(
        term in path.lower()
        for _, path in routes
        for term in ("/accept", "/contest", "/refund", "/payments")
    )
