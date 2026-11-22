# Fresh installation and release smoke test

This checklist is for validating the CLI on a clean Windows or Linux workstation after the installer changes are available from the intended branch. It is deliberately separate from live OCI provisioning.

## Safety boundary

- These checks install local files, create a local virtual environment, and write a local application config only.
- Do not paste or commit OCI credentials, private keys, SSH private keys, full unredacted config files, or real OCIDs into test reports.
- Do not run `oci-platform vm monitor --enable-create`.
- Do not set `mode.creation_enabled=true` or add the launch confirmation phrase during smoke testing.
- `doctor`, `config validate`, and `vm audit` may contact OCI when configured with a real profile. Use a test profile or stop before those commands if you do not explicitly intend a read-only live audit.
- No VM launch, account upgrade, network provisioning, service installation, or production-server change is part of this checklist.

## Preconditions

- A clean user account or disposable workstation profile.
- Git installed and available on PATH.
- Python 3.11 or 3.12 installed.
- Network access to GitHub and Python package indexes.
- A new, unused installation directory. Do not point the installer at an existing project folder.

## Windows — fresh install

Open PowerShell. If the local execution policy blocks the downloaded script, use a process-only policy change:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$env:OCI_PLATFORM_HOME = Join-Path $HOME "oci-platform-smoke-test"
irm https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.ps1 | iex
```

After installation, invoke the installed executable using its printed path:

```powershell
& "$env:OCI_PLATFORM_HOME\.venv\Scripts\oci-platform.exe" --version
& "$env:OCI_PLATFORM_HOME\.venv\Scripts\oci-platform.exe" --help
& "$env:OCI_PLATFORM_HOME\.venv\Scripts\oci-platform.exe" config show
```

Expected:
- Installer completes without administrator privileges.
- The CLI reports its version and help.
- Config summary masks sensitive fields and creation remains disabled.
- Installer does not add PATH entries, install a service, or contact OCI.

### Windows preservation/failure checks

1. Create the target directory yourself and put a sentinel file inside it.
2. Run the installer with `OCI_PLATFORM_HOME` pointing to that directory.
3. Confirm it exits with an error and the sentinel file remains unchanged.
4. For failure-cleanup testing, use a disposable test branch or local copy with a deliberately invalid Git clone URL; confirm only the newly-created incomplete destination is removed. Never test destructive cleanup against a real project directory.

## Linux — fresh install

Run as an ordinary user, not with sudo:

```bash
export OCI_PLATFORM_HOME="$HOME/oci-platform-smoke-test"
curl -fsSL https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.sh | bash
"$OCI_PLATFORM_HOME/.venv/bin/oci-platform" --version
"$OCI_PLATFORM_HOME/.venv/bin/oci-platform" --help
"$OCI_PLATFORM_HOME/.venv/bin/oci-platform" config show
```

Expected:
- Installer completes without sudo/root.
- The CLI reports its version and help.
- Config summary masks sensitive fields and creation remains disabled.
- Installer does not add PATH entries, install a service, or contact OCI.

### Linux preservation/failure checks

1. Create the target directory yourself and put a sentinel file inside it.
2. Run the installer with `OCI_PLATFORM_HOME` pointing to that directory.
3. Confirm it exits with an error and the sentinel file remains unchanged.
4. The automated test suite already exercises partial-clone cleanup and preservation of an existing directory on POSIX. Do not repeat destructive tests against valuable data.

## Local-only configuration checks

Run these without supplying a real OCI profile:

```bash
oci-platform configure
oci-platform config validate
oci-platform config show
```

Use placeholder values only if you are testing the wizard's validation path. The wizard must:
- reject a target region different from the configured home region;
- reject resource/storage values outside configured policy caps;
- reject boot-volume VPUs/GB other than the supported value of 10;
- create a timestamped backup before replacing an existing config;
- force `mode.creation_enabled=false` and clear `mode.creation_confirmation`, even if the previous config had those values armed;
- avoid making OCI API calls while collecting and saving configuration.

## CI and automated test commands

From the repository root:

```bash
python -m pip install -e .
python -m compileall -q oci_platform oci_free_watch.py
python -m unittest discover -s tests -v
oci-platform --help
oci-platform --version
bash -n install.sh
```

On Windows, parse the PowerShell installer without executing it:

```powershell
$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path .\install.ps1),
    [ref]$tokens,
    [ref]$parseErrors
) | Out-Null
if ($parseErrors.Count -gt 0) { throw ($parseErrors | Out-String) }
```

## Evidence to record

Record only:
- OS and version;
- Python version;
- installer branch/commit;
- pass/fail for install, CLI version/help, config redaction, and existing-directory protection;
- sanitized error text if a step fails.

Do not attach `~/.oci/config`, app config, state files, logs, key files, environment dumps, or screenshots containing credentials/OCIDs.

## Known coverage gaps

- GitHub Actions verifies shell/PowerShell syntax and runs the Windows installer safety integration script. Linux integration tests cover clone failure, virtual-environment failure, and existing-directory preservation.
- GitHub Actions now executes the PowerShell installer on Windows with a temporary existing directory and a simulated Git-clone failure. This verifies preservation and cleanup behavior without contacting OCI or cloning the live repository. It is not a successful end-to-end installation from the public default branch.
- A real fresh Linux workstation install has not been performed as part of CI.
- The interactive wizard should receive dedicated regression tests for backup creation, clearing pre-armed creation flags, invalid VPU settings, and write-free rejection paths if those cases are not already covered by the current test suite.
- No live OCI audit or VM launch is required to close the local installer milestone.

## Completion criteria

Do not call the installer milestone release-ready until:
1. the current PR head has green Windows/Linux CI;
2. a fresh Windows installation has been manually completed;
3. a fresh Linux installation has been manually completed;
4. existing-directory protection is verified on both platforms;
5. configuration remains creation-disabled after setup/configure;
6. no secrets or account-specific identifiers are present in committed files or test evidence;
7. the operator has reviewed and approved the PRs before merge.
