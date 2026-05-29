# Stop Byulie API and web app processes.
$Root = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $Root ".byulie"

function Stop-Port($port) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping $($proc.ProcessName) on port $port (PID $($proc.Id))"
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "  Stopping Byulie..." -ForegroundColor Cyan

if (Test-Path $PidDir) {
    foreach ($name in @("api.pid", "web.pid")) {
        $pidFile = Join-Path $PidDir $name
        if (Test-Path $pidFile) {
            $procId = Get-Content $pidFile -ErrorAction SilentlyContinue
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
        }
    }
}

Stop-Port 8000
Stop-Port 5173

Write-Host "  Done." -ForegroundColor Green
Write-Host ""
