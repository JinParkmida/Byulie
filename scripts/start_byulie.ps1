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

function Assert-Windows11X64 {
    if ($SkipWindowsCheck) {
        Write-Info "Skipping Windows 11 64-bit validation because -SkipWindowsCheck was provided."
        return
    }

    if ($PSVersionTable.PSEdition -eq "Core" -and -not $IsWindows) {
        throw "Byulie's launcher is made for Windows 11 64-bit. Run start-byulie.bat from Windows 11, not this operating system."
    }

    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    $caption = [string]$os.Caption
    $architecture = [string]$os.OSArchitecture
    if ($caption -notlike "*Windows 11*" -or $architecture -notlike "*64*") {
        throw "Byulie is configured for Windows 11 64-bit. Detected '$caption' ($architecture)."
    }

    Write-Info "Validated target OS: $caption ($architecture)."
}

function Get-RepositoryRoot {
    $scriptPath = $PSCommandPath
    if (-not $scriptPath) {
        $scriptPath = $MyInvocation.MyCommand.Path
    }

    return (Resolve-Path (Join-Path (Split-Path -Parent $scriptPath) "..")).Path
}

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$PrefixArguments = @()
    )

    $checkCode = @'
import platform
import sys
major, minor = sys.version_info[:2]
is_supported_version = (major == 3 and minor in (10, 11))
is_64bit = platform.architecture()[0] == "64bit"
print(f"{major}.{minor};{platform.architecture()[0]}")
sys.exit(0 if is_supported_version and is_64bit else 1)
'@

    $output = & $Command @PrefixArguments -c $checkCode 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    return [PSCustomObject]@{
        Command = $Command
        PrefixArguments = $PrefixArguments
        Version = $output
    }
}

function Get-WindowsPython {
    $candidates = @()

    if (Test-CommandExists "py") {
        $candidates += [PSCustomObject]@{ Command = "py"; PrefixArguments = @("-3.11-64") }
        $candidates += [PSCustomObject]@{ Command = "py"; PrefixArguments = @("-3.10-64") }
        $candidates += [PSCustomObject]@{ Command = "py"; PrefixArguments = @("-3-64") }
    }

    if (Test-CommandExists "python") {
        $candidates += [PSCustomObject]@{ Command = "python"; PrefixArguments = @() }
    }

    foreach ($candidate in $candidates) {
        $validated = Test-PythonCandidate -Command $candidate.Command -PrefixArguments $candidate.PrefixArguments
        if ($validated) {
            Write-Info "Using Python $($validated.Version) via '$($candidate.Command) $($candidate.PrefixArguments -join ' ')'."
            return $validated
        }
    }

    throw "Python 3.10 or 3.11 64-bit was not found. Install 64-bit Python for Windows and enable 'Add Python to PATH'."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]$Python,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $command = $Python.Command
    $prefixArguments = @($Python.PrefixArguments)
    & $command @prefixArguments @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $command $($prefixArguments -join ' ') $($Arguments -join ' ')"
    }
}

function Get-VenvPythonPath {
    param([Parameter(Mandatory = $true)][string]$RepoRoot)
    return Join-Path $RepoRoot ".venv\Scripts\python.exe"
}

function Assert-VenvPythonX64 {
    param([Parameter(Mandatory = $true)][string]$VenvPython)

    $checkCode = 'import platform, sys; sys.exit(0 if platform.architecture()[0] == "64bit" else 1)'
    & $VenvPython -c $checkCode
    if ($LASTEXITCODE -ne 0) {
        throw "The virtual environment is not using 64-bit Python. Delete .venv and rerun start-byulie.bat with 64-bit Python installed."
    }
}

function Ensure-VirtualEnvironment {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)]$Python
    )

    $venvPython = Get-VenvPythonPath -RepoRoot $RepoRoot
    if (Test-Path $venvPython) {
        Assert-VenvPythonX64 -VenvPython $venvPython
        Write-Info "Using existing Windows virtual environment at .venv."
        return $venvPython
    }

    Write-Info "Creating Windows virtual environment at .venv."
    Invoke-Python -Python $Python -Arguments @("-m", "venv", ".venv")
    Assert-VenvPythonX64 -VenvPython $venvPython
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
        throw "requirements.txt was not found. This Windows launcher expects dependencies to be listed there."
    }

    Write-Info "Upgrading pip in the Windows virtual environment."
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip."
    }

    Write-Info "Installing Windows Python dependencies from requirements.txt."
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
        Write-Warn "Ollama for Windows is not on PATH. Install Ollama for Windows before chatting with Byulie."
        return
    }

    Write-Info "Checking Ollama for Windows installation."
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

Assert-Windows11X64
$repoRoot = Get-RepositoryRoot
Set-Location $repoRoot

Write-Info "Repository root: $repoRoot"
$python = Get-WindowsPython
$venvPython = Ensure-VirtualEnvironment -RepoRoot $repoRoot -Python $python
Install-Requirements -RepoRoot $repoRoot -VenvPython $venvPython
Test-OllamaModel
Start-Byulie -RepoRoot $repoRoot -VenvPython $venvPython -LaunchMode $Mode
