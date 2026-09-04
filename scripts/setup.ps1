$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPath = Join-Path $repoRoot ".venv"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    $candidates = @()
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        $candidates += [PSCustomObject]@{ Executable = $pyLauncher.Source; Arguments = @() }
    }
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        $candidates += [PSCustomObject]@{ Executable = $pythonCommand.Source; Arguments = @() }
    }

    $selected = $null
    foreach ($candidate in $candidates) {
        $probeArguments = @($candidate.Arguments) + @(
            "-c",
            "import sys, venv; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
        )
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "SilentlyContinue"
        & $candidate.Executable @probeArguments 2>$null
        $probeExit = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorAction
        if ($probeExit -eq 0) {
            $selected = $candidate
            break
        }
    }
    if ($null -eq $selected) {
        throw "Python 3.10+ with the standard venv module is required."
    }
    $venvArguments = @($selected.Arguments) + @("-m", "venv", $venvPath)
    & $selected.Executable @venvArguments
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $pythonPath)) {
        throw "The selected Python interpreter could not create .venv."
    }
}

& $pythonPath -m pip install --upgrade pip
& $pythonPath -m pip install -e "${repoRoot}[dev]"
npm --prefix (Join-Path $repoRoot "frontend") ci
& $pythonPath (Join-Path $repoRoot "scripts\train_local_semantic_model.py")

Write-Output "Setup complete. Run: powershell -ExecutionPolicy Bypass -File scripts/demo.ps1"
