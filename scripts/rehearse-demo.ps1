$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonPath = if (Test-Path -LiteralPath $venvPython) {
    $venvPython
}
else {
    (Get-Command python -ErrorAction Stop).Source
}
$demoStarted = $false
$backendPort = 18001
$frontendPort = 15173

Push-Location $repoRoot
try {
    & $pythonPath scripts/failure_demo.py
    if ($LASTEXITCODE -ne 0) {
        throw "The intentional failure-recovery demonstration failed."
    }

    & (Join-Path $PSScriptRoot "demo.ps1") -BackendPort $backendPort -FrontendPort $frontendPort
    $demoStarted = $true

    & $pythonPath scripts/verify_live_demo.py --backend-port $backendPort --frontend-port $frontendPort
    if ($LASTEXITCODE -ne 0) {
        throw "The live demo verification failed."
    }
}
finally {
    if ($demoStarted) {
        & (Join-Path $PSScriptRoot "stop-demo.ps1")
    }
    Pop-Location
}
