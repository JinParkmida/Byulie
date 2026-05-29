[CmdletBinding()]
param(
    [ValidateSet("voice", "web")]
    [string]$Mode = "voice",

    [switch]$SkipInstall,
    [switch]$SkipOllamaCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "[Byulie] $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "[Byulie] WARNING: $Message" -ForegroundColor Yellow
}

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-RepositoryRoot {
    $scriptPath = $PSCommandPath
    if (-not $scriptPath) {
        $scriptPath = $MyInvocation.MyCommand.Path
    }

    return (Resolve-Path (Join-Path (Split-Path -Parent $scriptPath) "..")).Path
}

function Get-PythonCommand {
    if (Test-CommandExists "py") {
        return "py"
    }

    if (Test-CommandExists "python") {
        return "python"
    }

    throw "Python was not found. Install Python 3.10 or 3.11 and enable 'Add Python to PATH'."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)][string]$PythonCommand,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    if ($PythonCommand -eq "py") {
        & py -3 @Arguments
    } else {
        & $PythonCommand @Arguments
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $PythonCommand $($Arguments -join ' ')"
    }
}

function Get-VenvPythonPath {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)
    return Join-Path $RepoRoot ".venv\Scripts\python.exe"
}

function Ensure-VirtualEnvironment {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$PythonCommand
    )

    $venvPython = Get-VenvPythonPath -RepoRoot $RepoRoot
    if (Test-Path $venvPython) {
        Write-Info "Using existing virtual environment at .venv."
        return $venvPython
    }

    Write-Info "Creating virtual environment at .venv."
    Invoke-Python -PythonCommand $PythonCommand -Arguments @("-m", "venv", ".venv")
    return $venvPython
}

function Install-Requirements {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$VenvPython
    )

    if ($SkipInstall) {
        Write-Info "Skipping dependency installation because -SkipInstall was provided."
        return
    }

    $requirements = Join-Path $RepoRoot "requirements.txt"
    if (-not (Test-Path $requirements)) {
        Write-Warn "requirements.txt was not found; skipping dependency installation."
        return
    }

    Write-Info "Upgrading pip."
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip."
    }

    Write-Info "Installing Python dependencies from requirements.txt."
    & $VenvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install requirements.txt."
    }
}

function Test-OllamaModel {
    if ($SkipOllamaCheck) {
        Write-Info "Skipping Ollama check because -SkipOllamaCheck was provided."
        return
    }

    if (-not (Test-CommandExists "ollama")) {
        Write-Warn "Ollama is not on PATH. Install Ollama for Windows before chatting with Byulie."
        return
    }

    Write-Info "Checking Ollama installation."
    & ollama --version
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Ollama did not respond to --version. Start Ollama manually if Byulie cannot connect."
    }
}

function Start-Byulie {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][string]$VenvPython,
        [Parameter(Mandatory = $true)][string]$LaunchMode
    )

    if ($LaunchMode -eq "web") {
        Write-Info "Launching Byulie web UI at http://127.0.0.1:7860."
        & $VenvPython (Join-Path $RepoRoot "client\app.py")
    } else {
        Write-Info "Launching Byulie voice chat."
        & $VenvPython (Join-Path $RepoRoot "server\main_chat.py")
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Byulie exited with code $LASTEXITCODE."
    }
}

$repoRoot = Get-RepositoryRoot
Set-Location $repoRoot

Write-Info "Repository root: $repoRoot"
$pythonCommand = Get-PythonCommand
$venvPython = Ensure-VirtualEnvironment -RepoRoot $repoRoot -PythonCommand $pythonCommand
Install-Requirements -RepoRoot $repoRoot -VenvPython $venvPython
Test-OllamaModel
Start-Byulie -RepoRoot $repoRoot -VenvPython $venvPython -LaunchMode $Mode
