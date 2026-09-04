"""Static release guard for the Track 02 no-provider-write boundary."""

from __future__ import annotations

import ast
import re
from pathlib import Path

FORBIDDEN_NETWORK_IMPORTS = frozenset(
    {"aiohttp", "httpx", "razorpay", "requests", "urllib.request"}
)
FORBIDDEN_RAZORPAY_HOST = re.compile(r"(?:api\.)?razorpay\.com(?:/|\\/)", re.IGNORECASE)
FORBIDDEN_WRITE_PATH = re.compile(
    r"/v1/(?:disputes/[^\s'\"`]+/(?:accept|contest)|payments/[^\s'\"`]+/refund|refunds)",
    re.IGNORECASE,
)
FRONTEND_FETCH = re.compile(r"fetch\(\s*([`'\"])(.*?)\1", re.DOTALL)


def _python_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    return imports


def scan_runtime_tree(repo_root: Path) -> tuple[str, ...]:
    """Return violations from runtime code and production dependency manifests."""
    violations: list[str] = []
    runtime_files = sorted((repo_root / "backend" / "app").glob("*.py"))
    frontend_files = sorted((repo_root / "frontend" / "src").glob("*.ts*"))

    for path in runtime_files:
        relative = path.relative_to(repo_root).as_posix()
        source = path.read_text(encoding="utf-8")
        imports = _python_imports(ast.parse(source, filename=relative))
        forbidden = sorted(
            imported
            for imported in imports
            if any(
                imported == candidate or imported.startswith(f"{candidate}.")
                for candidate in FORBIDDEN_NETWORK_IMPORTS
            )
        )
        for imported in forbidden:
            violations.append(f"{relative}: forbidden runtime network import {imported}")
        if FORBIDDEN_RAZORPAY_HOST.search(source):
            violations.append(f"{relative}: Razorpay API host is forbidden in MVP runtime")
        if FORBIDDEN_WRITE_PATH.search(source):
            violations.append(f"{relative}: Razorpay write endpoint pattern is forbidden")

    for path in frontend_files:
        relative = path.relative_to(repo_root).as_posix()
        source = path.read_text(encoding="utf-8")
        if FORBIDDEN_RAZORPAY_HOST.search(source):
            violations.append(f"{relative}: Razorpay API host is forbidden in browser code")
        if FORBIDDEN_WRITE_PATH.search(source):
            violations.append(f"{relative}: Razorpay write endpoint pattern is forbidden")
        for match in FRONTEND_FETCH.finditer(source):
            target = match.group(2)
            if not target.startswith("/api/v1/"):
                violations.append(f"{relative}: non-local fetch target {target!r}")

    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8").lower()
    project_dependencies = pyproject.split("[project.optional-dependencies]", maxsplit=1)[0]
    if re.search(r"(?m)^\s*[\"']razorpay(?:[<>=~!]|[\"'])", project_dependencies):
        violations.append("pyproject.toml: Razorpay SDK is forbidden in production dependencies")
    return tuple(violations)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    violations = scan_runtime_tree(repo_root)
    if violations:
        for violation in violations:
            print(violation)
        return 1
    print("No Razorpay write client, host, endpoint pattern, or non-local frontend fetch found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
