# OCI Always Free A1 VM Automation

A lightweight Python application for monitoring OCI Ampere A1 host capacity and, only after explicit operator approval, requesting one configured A1 VM. It uses the official OCI Python SDK.

**Default behavior is read-only.** The project never creates or modifies VCNs, subnets, gateways, route tables, security lists, NSGs, reserved IPs, or existing compute instances.

## Capabilities

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
- Run directly on Windows. Run it on Linux; Windows can be used for editing and SSH access.

The program requires an explicit local Free Tier attestation. OCI APIs used by this application do not provide a definitive billing-plan status. Keep your actual account status and Billing & Cost Management under manual review. The app's safeguards cannot prevent charges caused by account upgrades, unrelated resources, changed policies, or incorrect operator input.

## OCI Always Free reference

Oracle's current documentation describes the A1 Always Free allowance for Free Tier tenancies as up to 2 OCPUs and 12 GB memory, with 1,500 OCPU-hours and 9,000 GB-hours per month. It also documents 200 GB combined boot-volume and block-volume storage in the home region. These limits and eligibility rules may change. Verify the current terms and your own live tenancy limits before arming creation.

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
├── oci-free
├── requirements.txt
├── systemd/oci-free-watch.service
├── tests/test_policy.py
├── SECURITY.md
├── .env.example
├── .claude/commands/work.md
├── docs/
│   ├── DEPLOY_EC2.md
│   └── agents/
│       ├── PROJECT_MEMORY.md
│       ├── START_PROMPT.md
│       └── WORKLOG.md
└── .github/
    ├── copilot-instructions.md
    └── workflows/tests.yml
~~~

## Requirements

- Linux host; Ubuntu is recommended.
- Python 3.11 or newer.
- Network access to OCI APIs.
- OCI API signing-key authentication.
- An OCI identity with least-privilege read permissions; launch mode requires additional compute/VNIC/volume permissions.
- An existing VCN, public subnet, Internet Gateway route, and SSH public key.
- No Docker, Node.js, Redis, PostgreSQL, or database service.

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

Review systemd/oci-free-watch.service. Its example assumes:
- Application directory: /opt/oci-free-instance-automation
- Linux user/group: ubuntu
- Virtual environment: .venv

Customize the user, group, paths, and writable directories for your host before installing:

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

## CLI reference

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

GitHub Actions runs the checks on pushes and pull requests.

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

## AI coding agents

Read AGENTS.md and docs/agents/PROJECT_MEMORY.md before making changes. Use docs/agents/START_PROMPT.md as a reusable starting prompt. AGENTS.md is the shared project instruction source; CLAUDE.md, GEMINI.md, and .github/copilot-instructions.md provide tool-specific entry points.

## License

No license has been selected. Until a LICENSE file is added, do not assume the repository grants permission to redistribute or reuse the code.
