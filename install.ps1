$ErrorActionPreference = "Stop"

$Repository = "https://github.com/mudassir-93/OCI-Always-Free-VM.git"
$InstallDir = if ($env:OCI_PLATFORM_HOME) {
    $env:OCI_PLATFORM_HOME
} else {
    Join-Path $HOME "oci-automation-platform"
}

Write-Host "OCI Automation Platform installer"
Write-Host "This installs local CLI files only. It does not contact your OCI tenancy or create cloud resources."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required. Install Git for Windows, reopen PowerShell, and run this installer again."
}
$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($PythonCommand) {
    & py -3.11 --version *> $null
    if ($LASTEXITCODE -eq 0) {
        $Python = "py"
        $PythonArgs = @("-3.11")
    } else {
        $Python = "python"
        $PythonArgs = @()
    }
} else {
    $Python = "python"
    $PythonArgs = @()
}
& $Python @PythonArgs --version
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 or newer is required."
}

if (Test-Path $InstallDir) {
    throw "Install directory already exists: $InstallDir. The installer will not overwrite or update existing files. Choose another OCI_PLATFORM_HOME or move the directory after backing it up."
}

$Parent = Split-Path -Parent $InstallDir
New-Item -ItemType Directory -Force -Path $Parent | Out-Null
git clone --depth 1 --branch main $Repository $InstallDir
if ($LASTEXITCODE -ne 0) { throw "Git clone failed." }

Set-Location $InstallDir
& $Python @PythonArgs -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }

$VenvPython = Join-Path $InstallDir ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& $VenvPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "CLI installation failed." }

$Cli = Join-Path $InstallDir ".venv\Scripts\oci-platform.exe"
& $Cli setup
if ($LASTEXITCODE -ne 0) { throw "Initial local configuration setup failed." }

Write-Host ""
Write-Host "Installation complete: $InstallDir"
Write-Host "Next steps:"
Write-Host "  1. Run: $Cli configure"
Write-Host "  2. Run: $Cli doctor"
Write-Host "  3. Run: $Cli vm audit"
Write-Host "VM creation remains disabled. The installer never enables it."
