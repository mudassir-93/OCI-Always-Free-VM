$ErrorActionPreference = "Stop"

$Installer = Join-Path $PSScriptRoot "..\install.ps1"
$Installer = [System.IO.Path]::GetFullPath($Installer)
$TestRoot = Join-Path $env:RUNNER_TEMP ("oci-platform-installer-" + [guid]::NewGuid().ToString("N"))
$OriginalInstallHome = $env:OCI_PLATFORM_HOME
$OriginalPath = $env:PATH

New-Item -ItemType Directory -Path $TestRoot | Out-Null

try {
    # Existing destination must be rejected without touching operator data.
    $ExistingDir = Join-Path $TestRoot "existing-install"
    New-Item -ItemType Directory -Path $ExistingDir | Out-Null
    $Sentinel = Join-Path $ExistingDir "operator-data.txt"
    Set-Content -LiteralPath $Sentinel -Value "preserve-this-data" -NoNewline
    $env:OCI_PLATFORM_HOME = $ExistingDir

    $ExistingRejected = $false
    try {
        & $Installer
    }
    catch {
        $ExistingRejected = $_.Exception.Message -match "already exists"
    }

    if (-not $ExistingRejected) {
        throw "Installer did not reject an existing destination directory."
    }
    if ((Get-Content -LiteralPath $Sentinel -Raw) -ne "preserve-this-data") {
        throw "Installer modified the sentinel in an existing destination."
    }

    # A failed git clone after destination reservation must clean up its own
    # incomplete directory without touching pre-existing operator data.
    $FakeBin = Join-Path $TestRoot "fake-bin"
    New-Item -ItemType Directory -Path $FakeBin | Out-Null
    $FakeGit = Join-Path $FakeBin "git.cmd"
    $FakeGitContent = "@echo off" + [Environment]::NewLine + "exit /b 42" + [Environment]::NewLine
    Set-Content -LiteralPath $FakeGit -Value $FakeGitContent -NoNewline

    $FailedInstallDir = Join-Path $TestRoot "failed-install"
    $env:OCI_PLATFORM_HOME = $FailedInstallDir
    $env:PATH = "$FakeBin;$OriginalPath"

    $CloneFailureObserved = $false
    try {
        & $Installer
    }
    catch {
        $CloneFailureObserved = $_.Exception.Message -match "Git clone failed"
    }

    if (-not $CloneFailureObserved) {
        throw "Installer did not surface the simulated Git clone failure."
    }
    if (Test-Path -LiteralPath $FailedInstallDir) {
        throw "Installer left its incomplete destination behind after clone failure."
    }

    Write-Host "Windows installer integration checks passed."
}
finally {
    $env:PATH = $OriginalPath
    if ($null -eq $OriginalInstallHome) {
        Remove-Item Env:OCI_PLATFORM_HOME -ErrorAction SilentlyContinue
    }
    else {
        $env:OCI_PLATFORM_HOME = $OriginalInstallHome
    }
    Remove-Item -LiteralPath $TestRoot -Recurse -Force -ErrorAction SilentlyContinue
}

# The simulated native Git command intentionally returned 42; normalize the
# successful test script's process exit code after all assertions pass.
exit 0
