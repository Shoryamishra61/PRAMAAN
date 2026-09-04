$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

function Invoke-Checked {
    param(
        [Parameter(Mandatory)][scriptblock]$Command,
        [Parameter(Mandatory)][string]$Label
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python -ErrorAction Stop).Source }
Push-Location $repoRoot
try {
    $pythonFiles = @(
        "backend",
        "evaluation",
        "data_pipeline",
        "training",
        "external_validation",
        "scripts/replay_webhook.py",
        "scripts/generate_benchmark.py",
        "scripts/freeze_benchmark.py",
        "scripts/benchmark_cases.py",
        "scripts/generate_offline_demo_cache.py",
        "scripts/check_no_razorpay_writes.py",
        "scripts/seed_demo.py",
        "scripts/spec_lint.py",
        "scripts/package_validate.py",
        "scripts/evaluate_benchmark.py",
        "scripts/freeze_release.py",
        "scripts/failure_demo.py",
        "scripts/verify_live_demo.py",
        "scripts/train_local_semantic_model.py",
        "scripts/run_ai_research_study.py",
        "scripts/audit_ai_holdout_grounding.py",
        "scripts/run_fecl_v2.py",
        "scripts/analyze_fecl_v2.py",
        "scripts/build_fecl_paper_assets.py",
        "scripts/check_stale_claims.py",
        "scripts/demo_smoke_test.py",
        "scripts/load_saturation_benchmark.py"
    )
    Invoke-Checked { & $pythonPath -m ruff format --check @pythonFiles } "Python formatting"
    Invoke-Checked { & $pythonPath -m ruff check @pythonFiles } "Python lint"
    Invoke-Checked { & $pythonPath -m mypy backend/app backend/tests evaluation data_pipeline training external_validation scripts/replay_webhook.py scripts/generate_benchmark.py scripts/freeze_benchmark.py scripts/benchmark_cases.py scripts/generate_offline_demo_cache.py scripts/check_no_razorpay_writes.py scripts/seed_demo.py scripts/spec_lint.py scripts/package_validate.py scripts/evaluate_benchmark.py scripts/freeze_release.py scripts/failure_demo.py scripts/verify_live_demo.py scripts/train_local_semantic_model.py } "Python type check"
    Invoke-Checked { & $pythonPath scripts/spec_lint.py } "Specification lint"
    Invoke-Checked { & $pythonPath scripts/package_validate.py } "Package validation"
    Invoke-Checked { & $pythonPath scripts/check_no_razorpay_writes.py } "Razorpay write-boundary check"
    Invoke-Checked { & $pythonPath scripts/check_stale_claims.py } "Stale-claims check"
    Invoke-Checked { & $pythonPath scripts/demo_smoke_test.py } "Demo smoke test"
    Invoke-Checked { & $pythonPath -m pytest backend/tests } "Backend tests"

    Push-Location frontend
    try {
        Invoke-Checked { npm run format:check } "Frontend formatting"
        Invoke-Checked { npm run lint } "Frontend lint"
        Invoke-Checked { npm run build } "Frontend build"
        Invoke-Checked { npm test } "Frontend tests"
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
