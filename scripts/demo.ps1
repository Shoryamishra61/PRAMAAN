param(
    [switch]$SeedOnly,
    [ValidateRange(1024, 65535)][int]$BackendPort = 18000,
    [ValidateRange(1024, 65535)][int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

function Test-LocalPort {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $pending = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(250)) {
            return $false
        }
        $client.EndConnect($pending)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonPath = if (Test-Path -LiteralPath $venvPython) {
    $venvPython
}
else {
    (Get-Command python -ErrorAction Stop).Source
}
$databasePath = Join-Path $repoRoot "var\demo.sqlite3"
$processFile = Join-Path $repoRoot "var\demo-processes.json"
$logDirectory = Join-Path $repoRoot "var\logs"
$viteEntry = Join-Path $repoRoot "frontend\node_modules\vite\bin\vite.js"

if (Test-Path -LiteralPath $processFile) {
    throw "A recorded demo may already be running. Run scripts/stop-demo.ps1 first."
}
if ((Test-LocalPort -Port $BackendPort) -or (Test-LocalPort -Port $FrontendPort)) {
    throw "A requested demo port is already in use: backend=$BackendPort frontend=$FrontendPort."
}
if (-not (Test-Path -LiteralPath $viteEntry)) {
    throw "Frontend dependencies are missing. Run scripts/setup.ps1 first."
}

Push-Location $repoRoot
try {
    & $pythonPath scripts/seed_demo.py --database $databasePath --reset
    if ($SeedOnly) {
        Write-Output "Seeded synthetic PASS, REVIEW, and BLOCK cases at $databasePath"
        exit 0
    }

    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null
    $env:DIG_DATABASE_PATH = $databasePath
    $env:DIG_WEBHOOK_SECRET = "synthetic-demo-only-webhook-secret"
    $env:DIG_INFERENCE_MODE = "offline"
    $env:DIG_BACKEND_URL = "http://127.0.0.1:$BackendPort"

    $backend = Start-Process -FilePath $pythonPath `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "$BackendPort") `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput (Join-Path $logDirectory "backend.stdout.log") `
        -RedirectStandardError (Join-Path $logDirectory "backend.stderr.log") `
        -WindowStyle Hidden `
        -PassThru

    $nodePath = (Get-Command node -ErrorAction Stop).Source
    $frontend = Start-Process -FilePath $nodePath `
        -ArgumentList @($viteEntry, "frontend", "--host", "127.0.0.1", "--port", "$FrontendPort") `
        -WorkingDirectory $repoRoot `
        -RedirectStandardOutput (Join-Path $logDirectory "frontend.stdout.log") `
        -RedirectStandardError (Join-Path $logDirectory "frontend.stderr.log") `
        -WindowStyle Hidden `
        -PassThru

    @{
        schema_version = 1
        processes = @(
            @{ name = "backend"; id = $backend.Id; start_time_ticks = $backend.StartTime.ToUniversalTime().Ticks },
            @{ name = "frontend"; id = $frontend.Id; start_time_ticks = $frontend.StartTime.ToUniversalTime().Ticks }
        )
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $processFile -Encoding utf8

    $backendReady = $false
    $frontendReady = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        if ($backend.HasExited -or $frontend.HasExited) {
            break
        }
        if (-not $backendReady) { $backendReady = Test-LocalPort -Port $BackendPort }
        if (-not $frontendReady) { $frontendReady = Test-LocalPort -Port $FrontendPort }
        if ($backendReady -and $frontendReady) {
            break
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not ($backendReady -and $frontendReady)) {
        foreach ($process in @($backend, $frontend)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
        Remove-Item -LiteralPath $processFile -ErrorAction SilentlyContinue
        throw "Demo services did not become ready. Inspect var/logs."
    }

    Write-Output "Dispute Integrity Gate is ready: http://127.0.0.1:$FrontendPort"
    Write-Output "Synthetic PASS/REVIEW/BLOCK fixtures; offline replay; no Razorpay writes."
    Write-Output "Stop with: powershell -ExecutionPolicy Bypass -File scripts/stop-demo.ps1"
}
finally {
    Pop-Location
}
