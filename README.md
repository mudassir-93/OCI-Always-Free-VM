# OCI Always Free A1 VM Automation

[![Python checks](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/tests.yml)
[![Windows & Linux CLI](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/cli-foundation.yml/badge.svg?branch=main)](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/cli-foundation.yml)

A small Python CLI for checking Oracle Cloud Infrastructure (OCI) Ampere A1 availability and optionally requesting one VM after explicit approval and safety checks. Works on Windows and Linux.

**Safe by default:** installation and configuration are local-only. Audits and monitoring are read-only unless the separate VM-creation safeguards are deliberately enabled. Capacity and Always Free eligibility are never guaranteed.

## Install

Requirements: Git and Python 3.11 or newer.

**Windows — PowerShell**

```powershell
Invoke-WebRequest "https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.ps1" -OutFile install.ps1
Get-Content .\install.ps1
# Only if PowerShell blocks the script:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
```

**Linux**

```bash
curl -fsSLO https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.sh
less install.sh
bash install.sh
```

The installer creates a private virtual environment and a creation-disabled starter config in `~/oci-automation-platform`. It does not require administrator/root privileges or contact OCI. It will not overwrite an existing installation.

## First run

Open the interactive menu:

- **Windows:** `$HOME\oci-automation-platform\.venv\Scripts\oci-platform.exe`
- **Linux:** `~/oci-automation-platform/.venv/bin/oci-platform`

Choose **Configure / Edit settings**, complete your local settings, then run **Doctor**. The configuration editor does not call OCI.

You can also run the commands directly:

**Windows**

```powershell
$cli = "$HOME\oci-automation-platform\.venv\Scripts\oci-platform.exe"
& $cli configure
& $cli doctor
& $cli config show
```

**Linux**

```bash
CLI="$HOME/oci-automation-platform/.venv/bin/oci-platform"
"$CLI" configure
"$CLI" doctor
"$CLI" config show
```

## Check OCI

After configuring your local OCI SDK profile and existing network details:

- `oci-platform vm audit` — live, read-only tenancy audit.
- `oci-platform vm once` — one read-only audit and capacity check.
- `oci-platform vm monitor` — continuous monitoring; read-only by default.

A capacity report is not a reservation. Check your account plan, current OCI terms, and billing/usage in the OCI Console yourself. The tool cannot guarantee zero charges or Always Free eligibility.

## Guides

- [Detailed operator guide](docs/USER_GUIDE.md) — configuration, commands, monitoring, and legacy options.
- [Installation test checklist](docs/testing/INSTALLATION_SMOKE_TEST.md) — manual checks for Windows and Linux.
- [Security policy](SECURITY.md) — credentials, private keys, and safe operation.
- [Project status and roadmap](docs/PROJECT_STATUS.md) — completed work and remaining validation.
- [Linux VPS / EC2 deployment](docs/DEPLOY_EC2.md) — optional server setup.
- [AI coding-agent guide](docs/agents/README.md) and [repository instructions](AGENTS.md).

---
**Important:** VM creation is optional and remains disabled by default. Never enable it until you have independently checked your OCI billing status, current usage, image eligibility, quotas, and network configuration.
