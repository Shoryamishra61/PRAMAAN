$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$processFile = Join-Path $repoRoot "var\demo-processes.json"
if (-not (Test-Path -LiteralPath $processFile)) {
    Write-Output "No recorded demo processes are running."
    exit 0
}

$state = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
if ($state -is [System.Array]) {
    $records = $state
}
elseif ($state.PSObject.Properties.Name -contains "processes") {
    $records = $state.processes
}
else {
    throw "Demo process record has an unsupported schema."
}
foreach ($record in $records) {
    $process = Get-Process -Id $record.id -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        continue
    }
    if ($process.StartTime.ToUniversalTime().Ticks -ne $record.start_time_ticks) {
        throw "PID $($record.id) was reused; refusing to stop an unrelated process."
    }
    Stop-Process -Id $record.id -Force
    Write-Output "Stopped $($record.name) process $($record.id)."
}
Remove-Item -LiteralPath $processFile
