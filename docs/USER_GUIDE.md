# Operator guide

This is the detailed reference for installation, configuration, CLI commands, monitoring, and operational safety. For the short version, start with the [main README](../README.md).

## What it does

- OCI API signing-key authentication using a local OCI SDK profile.
- Home-region and availability-domain validation.
- Inspection of an existing VCN and public subnet, including the default route to an enabled Internet Gateway.
- Compatible image discovery for the configured OS, version, and A1 shape.
- Live standard A1 CPU and memory quota checks.
- Inventory of A1 instances and boot/block volumes across accessible compartments.
- Configurable monthly OCPU-hour and GB-hour budget checks.
- SSH public-key, image-confirmation, usage-review, and duplicate-instance safeguards.
- OCI capacity reports with exponential retry/backoff and jitter.
- Optional Telegram notifications through environment variables.
- Local state and OCI retry-token safeguards to reduce duplicate launch risk.

## Safety scope

This release intentionally supports only VM.Standard.A1.Flex in the tenancy home region, using an existing VCN and public subnet with public IPv4. The target OCPU, memory, boot-volume size, OS/version, region, availability domain, VCN, subnet, image, and SSH public-key path are configured locally by each operator. The sample configuration is a starting example, not a tenancy-specific preset.

The application does not:
- Upgrade an OCI account or change its billing plan.
- Launch non-A1 shapes.
- Create or alter network resources or ingress rules.
- Terminate, resize, or modify existing instances.
- Guarantee Always Free eligibility, zero billing, host capacity, or a successful launch.

The new `oci-platform` CLI and Python engine target Windows and Linux. The legacy Bash helper and systemd service are Linux-only.

The program requires an explicit local Free Tier attestation. OCI APIs used by this application do not provide a definitive billing-plan status. Keep your actual account status and Billing & Cost Management under manual review. The app's safeguards cannot prevent charges caused by account upgrades, unrelated resources, changed policies, or incorrect operator input.

## OCI Always Free reference

Oracle's Free Tier limits and eligibility rules can change. Check the official documentation and your own tenancy's live limits before configuring or enabling any creation workflow. Do not rely on example values as a billing guarantee.

- Oracle Always Free resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Oracle A1 compute: https://docs.oracle.com/en-us/iaas/Content/Compute/References/arm.htm

The example config uses conservative policy caps. The live Limits API check is still required. Include usage from other A1 instances in the current month and all active boot/block volumes in accessible compartments.

## Repository layout

~~~text
.
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── README.md
├── config.example.json
├── oci_free_watch.py
├── oci_platform/
│   ├── cli.py
│   ├── tui.py
│   └── templates/config.example.json
├── install.ps1
├── install.sh
├── pyproject.toml
├── oci-free
├── requirements.txt
├── systemd/oci-free-watch.service
├── tests/
│   ├── test_policy.py
│   ├── test_cli.py
│   ├── test_tui.py
│   ├── test_installers.py
│   ├── test_installers_windows.ps1
│   └── test_install_linux.sh
├── SECURITY.md
├── .env.example
├── .claude/commands/work.md
├── docs/
│   ├── PROJECT_STATUS.md
│   ├── DEPLOY_EC2.md
│   ├── testing/
│   │   └── INSTALLATION_SMOKE_TEST.md
│   └── agents/
│       ├── PROJECT_MEMORY.md
│       ├── START_PROMPT.md
│       └── WORKLOG.md
└── .github/
    ├── copilot-instructions.md
    └── workflows/
        ├── tests.yml
        └── cli-foundation.yml
~~~

## Requirements

- Windows or Linux for the new Python CLI; Ubuntu is recommended for the legacy systemd deployment.
- Python 3.11 or newer.
- Network access to OCI APIs.
- OCI API signing-key authentication.
- An OCI identity with least-privilege read permissions; launch mode requires additional compute/VNIC/volume permissions.
- An existing VCN, public subnet, Internet Gateway route, and SSH public key.
- No Docker, Node.js, Redis, PostgreSQL, or database service.

## Cross-platform CLI — V1 foundation

The default branch includes the cross-platform `oci-platform` CLI, a local configuration editor, and safe first-install scripts for Windows and Linux. The CLI foundation, guided configuration, installer, and interactive terminal UX milestones have all been merged.

See the [project progress report](PROJECT_STATUS.md) for completed milestones, verified CI, remaining workstation validation, and the next steps.

Install the current checkout in an isolated virtual environment:

~~~bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e .
~~~

Start the interactive terminal home screen by running:

~~~bash
oci-platform
~~~

Use the arrow keys and Enter to choose local actions such as Configure / Edit settings, diagnostics, configuration summary, status, logs, and starter setup. The home screen does not run OCI cloud operations; VM audit and monitoring remain explicit commands.

The guided configuration editor is also available directly:

~~~bash
oci-platform configure
~~~

Use the arrow keys to choose a settings group, select the individual field to edit, review the configuration, and then save. The target region automatically follows the tenancy home region. The editor validates paths, profile names, region format, OCID prefixes, SSH public-key files, whole-number compute/storage values, and local policy limits before saving. Press Ctrl+C to cancel safely without writing the pending edits.

For scripts or terminals without interactive arrow-key support, use the line-oriented fallback:

~~~powershell
oci-platform configure --plain
~~~

Start with version and local diagnostics:

~~~bash
oci-platform --version
oci-platform setup
oci-platform doctor
oci-platform config show
oci-platform config validate
~~~

`setup` creates a per-user config from the generic template only when no config exists. It does not contact OCI, create credentials, arm VM creation, or overwrite an existing config. The initial template is intentionally incomplete: configure your own OCI values before validation can pass.

Manage OCI SDK profile names without displaying credentials:

~~~bash
oci-platform profile list
oci-platform profile use DEFAULT
~~~

Run the existing automation through the new command hierarchy:

~~~bash
oci-platform vm audit
oci-platform vm once
oci-platform vm monitor
oci-platform status
oci-platform logs --lines 100
~~~

The `--config` global option must appear before the command, for example `oci-platform --config /path/to/config.json vm audit`.

VM audit and one-shot checks are read-only. Monitoring is read-only unless the operator deliberately supplies `vm monitor --enable-create`; even then, the existing engine still requires both local creation settings and all live safety checks. The CLI does not bypass or replace those protections.

Configuration defaults are stored under the user's application configuration directory; state and logs are stored under the user's application state directory. The CLI never prints credentials or OCIDs in its configuration summary. Existing direct Python commands and the Linux `oci-free` wrapper remain available during the gradual transition.

## One-command first installation

The installer scripts download the repository into a new user-owned directory, create an isolated Python virtual environment, install the CLI, and create a creation-disabled starter config. They do not use sudo/administrator elevation, contact OCI, change cloud resources, or arm VM creation.

**Windows PowerShell** (download the script first, then inspect/run it):

~~~powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.ps1" -OutFile install.ps1
Get-Content .\install.ps1
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install.ps1
~~~

**Linux**:

~~~bash
curl -fsSLO https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.sh
less install.sh
bash install.sh
~~~

Requirements: Git and Python 3.11 or newer. The default install directory is ~/oci-automation-platform (Windows: your home directory). To select a different new directory, set OCI_PLATFORM_HOME before running the installer. The installer refuses to overwrite an existing directory; it is not an updater and does not silently pull changes over local work. For a trusted fork or a deliberate branch test, optionally set OCI_PLATFORM_REPOSITORY to its Git clone URL and OCI_PLATFORM_BRANCH to the branch name; both installers default to this project's public repository and `main` when these variables are unset.

For a safe manual validation sequence on clean Windows and Linux machines, including existing-directory protection and known test-coverage limits, see [the installation smoke-test checklist](testing/INSTALLATION_SMOKE_TEST.md).

After installation, use the installed CLI:

~~~bash
# Linux
~/oci-automation-platform/.venv/bin/oci-platform configure
~/oci-automation-platform/.venv/bin/oci-platform doctor
~/oci-automation-platform/.venv/bin/oci-platform vm audit
~~~

~~~powershell
# Windows PowerShell
& "$HOME\oci-automation-platform\.venv\Scripts\oci-platform.exe" configure
& "$HOME\oci-automation-platform\.venv\Scripts\oci-platform.exe" doctor
& "$HOME\oci-automation-platform\.venv\Scripts\oci-platform.exe" vm audit
~~~

The installer deliberately does not add the application to the system PATH or install a background service. This keeps installation reversible and avoids changing machine-wide settings.

## Guided configuration wizard

Run oci-platform configure after installation. In a normal terminal, this opens the arrow-key editor rather than a long sequence of one-shot questions. Select a category, choose a field, edit its current value, and return to the category menu. The final review lists missing or invalid items before it permits saving.

- The main terminal home screen opens when running oci-platform with no arguments.
- Menus support arrow keys, j/k, and Enter. Ctrl+C exits the current interactive flow without saving pending edits.
- The target region follows the tenancy home region automatically; it cannot be set to a different region.
- OCI SDK profile names are selected from the local SDK config file; credential values are never displayed.
- Region syntax, VCN/subnet/image identifier prefixes, SSH public-key file, integer resource sizes, configured A1/storage caps, and supported Ubuntu/A1 settings are checked before saving.
- The editor is local-only; it does not call OCI APIs.
- It keeps allow_paid_resources=false and account_type=FREE_TIER.
- It creates a timestamped backup before updating an existing config.
- It never asks for or stores your OCI private API key or SSH private key.
- Every successful save forces mode.creation_enabled=false and clears the creation confirmation phrase. The editor cannot arm a launch.
- oci-platform configure --plain remains available for non-interactive or line-oriented terminals.

After configuration, run oci-platform doctor, review the output, and then use oci-platform vm audit only when you deliberately want a read-only live OCI call. Review the live tenancy and billing status yourself; a successful local wizard is not a guarantee of Always Free eligibility or zero charges.

## Quick start

### 1. Clone and install

Replace the repository placeholder with your fork or clone URL:

~~~bash
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY
./oci-free setup
~~~

### 2. Configure OCI API authentication

Create an OCI API signing key and upload only the public key to OCI Console. Keep the private key outside the repository. The SDK config normally lives at ~/.oci/config:

~~~ini
[DEFAULT]
user=YOUR_USER_OCID
tenancy=YOUR_TENANCY_OCID
fingerprint=YOUR_KEY_FINGERPRINT
region=YOUR_HOME_REGION
key_file=/absolute/path/to/oci_api_key.pem
~~~

Protect the directory, config, and private key:

~~~bash
chmod 700 ~/.oci
chmod 600 ~/.oci/config
chmod 600 /absolute/path/to/oci_api_key.pem
~~~

Never commit or paste private keys, OCI config, OCIDs, Telegram tokens, or local config.json.

### 3. Configure the local application file

Edit config.json. The example is intentionally account-neutral.

| Field | Operator action |
|---|---|
| oci.config_file / profile | Set the local OCI SDK config path and profile |
| account.account_type | Keep FREE_TIER for this strict workflow |
| account.free_tier_only_confirmed | Set true only after confirming your account is still Free Tier |
| account.home_region | Enter your tenancy's actual home region |
| account.a1_free_max_ocpu / a1_free_max_memory_gb | Set local policy caps; the live Limits API is checked separately |
| account.combined_free_volume_gb | Enter your verified combined boot + block storage allowance |
| account.monthly_a1_ocpu_hours / monthly_a1_memory_gb_hours | Enter the monthly budgets you have verified |
| account.other_monthly_a1_*_hours | Include usage already consumed by other A1 instances this month |
| account.current_month_usage_reviewed | Set true only after reviewing current-month usage |
| target.region | Must equal the tenancy home region |
| target.availability_domain | Choose an AD in that region |
| target.vcn_ocid / subnet_ocid | Enter existing network resource OCIDs |
| target.display_name | Choose a unique instance name |
| target.ocpus / memory_gb | Choose a configuration within your policy and live quota |
| target.boot_volume_size_gb | At least 50 GB and within remaining combined storage |
| target.operating_system / operating_system_version | Select the desired compatible image filter |
| target.ssh_public_key_file | Absolute path to your SSH public key, never the private key |
| target.image_ocid | Pin the exact image after reviewing the audit candidate |
| target.image_console_always_free_confirmed | Set true only after checking the exact image's Always Free Eligible label in OCI Console |

This release requires an existing public subnet and public IPv4. It does not create a VCN, subnet, gateway, route, or SSH ingress rule. Configure ingress securely yourself.

### 4. Audit and test capacity

~~~bash
python oci_free_watch.py --audit
python oci_free_watch.py --once
python oci_free_watch.py --monitor
~~~

- --audit performs a read-only audit and does not submit a capacity report or launch request.
- --once performs one audit and capacity check, but never launches.
- --monitor continuously monitors in read-only mode unless separately armed.

The audit discovers a compatible image candidate. Pin its exact OCID locally, then manually confirm that exact image is labelled Always Free Eligible in OCI Console. The OCI SDK does not expose this Console label as a reliable machine-readable property.

### 5. Creation mode — explicit and optional

Do not arm creation until you have reviewed account status, billing, current-month usage, image eligibility, IAM permissions, storage, network, and a successful audit.

All three independent switches are required:
1. mode.creation_enabled = true in local config.json.
2. mode.creation_confirmation = LAUNCH_ONE_ALWAYS_FREE_INSTANCE.
3. Start the process with --enable-create.

Example foreground command after deliberate local arming:

~~~bash
python oci_free_watch.py --monitor --enable-create
~~~

The supplied systemd unit is read-only and intentionally omits --enable-create. For unattended launch, use a local systemd drop-in override; do not commit an armed unit or account-specific configuration.

Before launch, the program re-runs preflight, writes a pending/idempotency record, uses an OCI retry token, and refuses duplicate or ambiguous launches. These safeguards reduce risk but cannot guarantee exactly-once behavior across every network/API failure. Ambiguous outcomes stop for manual reconciliation.

### 6. systemd

Review systemd/oci-free-watch.service. It uses the generic application path /opt/oci-free-instance-automation and the explicit CHANGE_ME placeholder for the Linux service user and group.

Customize the service user/group and, if you use another install path, all matching paths and writable directories before installing:

~~~bash
sudo cp systemd/oci-free-watch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oci-free-watch
sudo systemctl status oci-free-watch --no-pager
sudo journalctl -u oci-free-watch -f
~~~

Stop the service with sudo systemctl disable --now oci-free-watch. Do not add --enable-create unless unattended creation is explicitly intended and approved.

### 7. Optional Telegram notifications

Store secrets outside the repository in a root-readable environment file such as /etc/oci-free-watch.env:

~~~ini
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
~~~

The systemd unit loads this file. Never place notification credentials in source code or Git.

## Legacy engine CLI reference

The original Python entry point remains supported for backward compatibility. The new `oci-platform` commands are documented above.


| Command | Effect |
|---|---|
| python oci_free_watch.py --validate-config | Validate local configuration and policy offline; no OCI API call |
| python oci_free_watch.py --audit | One read-only OCI audit |
| python oci_free_watch.py --once | One audit and capacity check; never launches |
| python oci_free_watch.py --monitor | Continuous read-only monitoring |
| python oci_free_watch.py --monitor --enable-create | Creation-capable monitoring only when both local config confirmations are also set |
| python oci_free_watch.py --config /path/to/config.json --audit | Use an alternate local configuration file |

## Convenience command wrapper

The executable oci-free wrapper provides short commands for routine operations. It never passes --enable-create:

~~~bash
./oci-free setup
./oci-free config-check
./oci-free test
./oci-free audit
./oci-free once
./oci-free monitor
./oci-free status
./oci-free logs
~~~

- setup creates the virtual environment, installs dependencies, and creates config.json only if it does not already exist.
- config-check runs the application's offline --validate-config check.
- audit and once are read-only OCI operations.
- monitor is explicitly read-only because the wrapper never supplies --enable-create.
- status and logs inspect the local systemd service.

Use the Python CLI directly only for advanced workflows. The creation-capable --enable-create flag is deliberately not exposed by this helper.

## Retry policy

Default polling is 20 minutes. Exponential backoff is capped at 180 minutes with ±15% jitter. Throttling and transient server errors are retried; Retry-After is observed when available. Authentication, authorization, invalid configuration, quota, and other non-transient errors stop for manual intervention.

A capacity report is advisory and does not reserve a host. Capacity can disappear before launch.

## Tests

Run without OCI credentials:

~~~bash
python -m py_compile oci_free_watch.py
python -m unittest discover -s tests -v
~~~

GitHub Actions runs the legacy checks and the new CLI foundation matrix on Windows and Linux with Python 3.11 and 3.12. Tests use local fixtures and do not require OCI credentials or contact a live tenancy.

## Security checklist

- Keep config.json local with restrictive permissions.
- Keep OCI SDK config and private keys outside Git.
- Use least-privilege OCI IAM policies.
- Never commit SSH private keys or public-key identity files.
- Keep Telegram secrets in an external environment file.
- Manually verify the image's Always Free Eligible label.
- Manually review account billing and current-month usage.
- Keep creation disabled until explicitly approved.
- Do not publish logs or runtime state.

## License

No license has been selected. Until a LICENSE file is added, do not assume the repository grants permission to redistribute or reuse the code.
