# Byulie one-click launcher — starts API + web app and opens your browser.
param(
    [switch]$SetupOnly,
    [switch]$SkipBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $Root ".byulie"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"
$WebDir = Join-Path $Root "client\web"
$ApiUrl = "http://127.0.0.1:8000/api/health"
$AppUrl = "http://127.0.0.1:5173"

Set-Location $Root
New-Item -ItemType Directory -Force -Path $PidDir | Out-Null

function Write-Step($text) {
    Write-Host ""
    Write-Host "  $text" -ForegroundColor Cyan
}

function Write-Ok($text) {
    Write-Host "  [ok] $text" -ForegroundColor Green
}

function Write-Warn($text) {
    Write-Host "  [!] $text" -ForegroundColor Yellow
}

function Write-Fail($text) {
    Write-Host "  [x] $text" -ForegroundColor Red
}

function Test-CommandAvailable($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Wait-ForUrl($url, $label, $seconds = 60) {
    for ($i = 0; $i -lt $seconds; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Ok "$label is ready"
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    Write-Warn "$label did not respond in time ($url)"
    return $false
}

function Stop-Port($port) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

Clear-Host
Write-Host ""
Write-Host "  Byulie — local launcher" -ForegroundColor Magenta
Write-Host "  =======================" -ForegroundColor DarkGray
Write-Host ""

if (-not (Test-CommandAvailable "python")) {
    Write-Fail "Python not found. Install Python 3.10+ and enable Add to PATH."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-CommandAvailable "node") -or -not (Test-CommandAvailable "npm")) {
    Write-Fail "Node.js not found. Install Node 20+ for the web app."
    Read-Host "Press Enter to exit"
    exit 1
}

# --- First-time / missing deps ---
if (-not (Test-Path $Python)) {
    Write-Step "Creating Python virtual environment (first run)..."
    python -m venv (Join-Path $Root ".venv")
}

if (-not (Test-Path $Pip)) {
    Write-Fail "Virtual environment setup failed."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Step "Checking Python packages..."
$depsMarker = Join-Path $Root ".venv\.deps_ok"
& $Pip install -q --upgrade pip 2>$null
if (-not (Test-Path $depsMarker)) {
    Write-Warn "First-time Python setup (may take a few minutes)..."
    & $Pip install -r (Join-Path $Root "requirements-byulie.txt")
    New-Item -ItemType File -Path $depsMarker -Force | Out-Null
} else {
    & $Pip install -q -r (Join-Path $Root "requirements-byulie.txt")
}
Write-Ok "Python dependencies ready"

Write-Step "Checking web dependencies..."
Set-Location $WebDir
if (-not (Test-Path "node_modules")) {
    Write-Warn "Installing npm packages (first run may take a minute)..."
    npm install --silent
}
Write-Ok "Web dependencies ready"
Set-Location $Root

if ($SetupOnly) {
    Write-Ok "Setup complete. Run Start-Byulie.bat to launch."
    Read-Host "Press Enter to exit"
    exit 0
}

# --- Stop anything already on our ports ---
Write-Step "Preparing ports..."
Stop-Port 8000
Stop-Port 5173
Start-Sleep -Seconds 1

# --- Start API ---
Write-Step "Starting Byulie API (port 8000)..."
$apiLog = Join-Path $PidDir "api.log"
$apiArgs = @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
    "Set-Location '$Root'; & '$Python' -m uvicorn server.api.main:app --reload --host 127.0.0.1 --port 8000 2>&1 | Tee-Object -FilePath '$apiLog'"
)
$apiProc = Start-Process powershell -ArgumentList $apiArgs -WindowStyle Minimized -PassThru
$apiProc.Id | Out-File (Join-Path $PidDir "api.pid") -Encoding ascii

# --- Start Vite ---
Write-Step "Starting Byulie web app (port 5173)..."
$webLog = Join-Path $PidDir "web.log"
$webArgs = @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
    "Set-Location '$WebDir'; npm run dev 2>&1 | Tee-Object -FilePath '$webLog'"
)
$webProc = Start-Process powershell -ArgumentList $webArgs -WindowStyle Minimized -PassThru
$webProc.Id | Out-File (Join-Path $PidDir "web.pid") -Encoding ascii

# --- Wait & open browser ---
Write-Step "Waiting for services..."
Wait-ForUrl $ApiUrl "API" | Out-Null
$webReady = Wait-ForUrl $AppUrl "Web app"

if (-not $SkipBrowser) {
    if ($webReady) {
        Start-Process $AppUrl
        Write-Ok "Opened $AppUrl in your browser"
    } else {
        $indexPath = Join-Path $Root "index.html"
        if (Test-Path $indexPath) {
            Start-Process $indexPath
            Write-Warn "Web app still starting — landing page opened. It will redirect when ready."
        }
    }
}

Write-Host ""
Write-Host "  Byulie is running." -ForegroundColor Green
Write-Host "  App:    $AppUrl" -ForegroundColor DarkGray
Write-Host "  API:    http://127.0.0.1:8000" -ForegroundColor DarkGray
Write-Host "  Logs:   .byulie\api.log · .byulie\web.log" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Keep Ollama and GPT-SoVITS running separately." -ForegroundColor DarkGray
Write-Host "  To stop Byulie: close this window and run Stop-Byulie.bat" -ForegroundColor DarkGray
Write-Host "  (or press Enter below)" -ForegroundColor DarkGray
Write-Host ""

Read-Host "Press Enter to stop Byulie"

Write-Step "Stopping Byulie..."
foreach ($name in @("api.pid", "web.pid")) {
    $pidFile = Join-Path $PidDir $name
    if (Test-Path $pidFile) {
        $procId = Get-Content $pidFile -ErrorAction SilentlyContinue
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}
Stop-Port 8000
Stop-Port 5173
Write-Ok "Stopped"
