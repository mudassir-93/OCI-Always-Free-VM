# OCI Always Free A1 VM Automation

[![Python checks](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/tests.yml)
[![Cross-platform CLI](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/cli-foundation.yml/badge.svg?branch=main)](https://github.com/mudassir-93/OCI-Always-Free-VM/actions/workflows/cli-foundation.yml)


A lightweight OCI automation application for monitoring Oracle Cloud Infrastructure Ampere A1 capacity and, only after explicit operator approval, requesting one configured Always Free A1 VM. The project is adding a cross-platform `oci-platform` CLI for setup, profile/configuration management, diagnostics, and day-to-day automation control. It uses the official OCI Python SDK.

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

The new `oci-platform` CLI and Python engine target Windows and Linux. The legacy Bash helper and systemd service are Linux-only.

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
├── oci_platform/
│   ├── cli.py
│   └── templates/config.example.json
├── pyproject.toml
├── oci-free
├── requirements.txt
├── systemd/oci-free-watch.service
├── tests/
│   ├── test_policy.py
│   └── test_cli.py
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

The repository now includes the first version of `oci-platform`. This is the CLI foundation, not yet the one-command GitHub installer. The installer and guided configuration wizard are planned for a later milestone.

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

Start with local setup and diagnostics:

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

## Using this repository with AI coding agents

This repository is prepared for agent-assisted development. You do not need to understand the entire Python codebase before asking an agent to explain it or work on a focused task. The instruction files give the agent the project purpose, architecture, safety rules, development workflow, and current project memory.

**Recommended approach: clone the repository and open its root folder in your coding agent.** Do not just paste individual Python files into a chat: the agent needs the surrounding tests, configuration template, documentation, and instruction files.

### 1. Open the repository in your agent

~~~bash
git clone https://github.com/mudassir-93/OCI-Always-Free-VM.git
cd OCI-Always-Free-VM
~~~

Then open this folder in the tool you want to use. Examples:

| Agent / tool | How to start | Instruction file |
|---|---|---|
| OpenAI Codex (CLI or IDE) | Open the repository root, start Codex, then give it the task | `AGENTS.md` |
| Claude Code | Run `claude` from the repository root | `CLAUDE.md`, then `AGENTS.md` |
| Gemini CLI | Run `gemini` from the repository root | `GEMINI.md`, then `AGENTS.md` |
| Google Antigravity | Open the repository folder and start an agent session | Point the agent to `GEMINI.md`, `AGENTS.md`, and project memory if it does not load them automatically |
| VS Code GitHub Copilot | Open the repository folder, open Copilot Chat, and use Agent mode | `.github/copilot-instructions.md` and `AGENTS.md` |
| Cursor or another agentic IDE | Open the repository root and start its agent | Give it `AGENTS.md` and the project memory file |

Agent instruction-file support can vary by product, version, and IDE configuration. If the agent does not automatically load its instruction file, explicitly ask it to read the files listed above. Do not assume that every tool automatically reads every file.

### 2. Give the agent the project context

The agent should read these files in this order:

1. `AGENTS.md` — mandatory project rules, safety boundaries, coding standards, and workflow.
2. `docs/agents/PROJECT_MEMORY.md` — durable architecture, decisions, and project context.
3. `README.md` — operator-facing setup and behavior.
4. `docs/agents/WORKLOG.md` — completed milestones, known limitations, and handoff notes.
5. Relevant source code and tests for the task.

The reusable prompt is in [docs/agents/START_PROMPT.md](docs/agents/START_PROMPT.md). Copy it into any agent when you want a full project briefing. It tells the agent to inspect the repository first, explain its understanding, plan the work, preserve the safety model, test changes, update documentation, and report the result.

### 3. Start a task — copy one of these prompts

**First session: understand the project (no code changes)**

~~~text
Read AGENTS.md, docs/agents/PROJECT_MEMORY.md, README.md, and docs/agents/WORKLOG.md.
Do not edit files yet. Explain in simple language:
1. What this project does and who it is for.
2. How the Python application, config, OCI SDK, state, and systemd service fit together.
3. What each CLI command does.
4. How the three-part creation safety guard works.
5. Which parts are implemented, tested, and still limited.
6. How I should request the next change safely.
Do not connect to OCI or run live cloud commands.
~~~

**Implement a feature or fix**

~~~text
Read the repository instructions and project memory first. Inspect git status, current branch, source code, and related tests. Explain the issue and propose a short plan before editing. Implement only this task: [DESCRIBE THE CHANGE]. Add or update offline tests, run the required checks, review the diff for secrets and safety regressions, update the worklog and relevant documentation, and report exactly what changed and what remains. Do not run live OCI operations or touch a production server.
~~~

**Ask for a code review only**

~~~text
Read AGENTS.md and docs/agents/PROJECT_MEMORY.md. Review the current branch for bugs, security problems, unsafe defaults, missing tests, and documentation mismatches. Do not modify files. Prioritize findings by severity and include file paths and line numbers. Do not run live OCI operations.
~~~

**Continue work from a previous agent session**

~~~text
Read AGENTS.md, docs/agents/PROJECT_MEMORY.md, and the latest entries in docs/agents/WORKLOG.md. Inspect git status and the current branch. Summarize the last completed milestone, current state, and next safe task. Do not repeat completed work or touch live OCI resources.
~~~

### 4. Tool-specific shortcuts

- **Claude Code:** from the repository root run `claude`. The repository includes a custom `/work` command in `.claude/commands/work.md`. In Claude Code, enter `/work`, then describe the task in your next message. If the command is not listed, ask Claude Code to read `AGENTS.md` and `docs/agents/START_PROMPT.md` directly.
- **Codex:** open the repository root in Codex. It should use `AGENTS.md` as repository guidance; if it has not loaded the file, explicitly ask it to read it before acting.
- **Gemini CLI:** run `gemini` from the root. If your environment does not automatically import `GEMINI.md`, ask it to open that file and the shared instructions.
- **Antigravity:** open this folder as the workspace. At the beginning of the agent conversation, paste the reusable start prompt or explicitly name the instruction and memory files.
- **GitHub Copilot:** open the folder in VS Code, start Copilot Chat in Agent mode, and ask it to read the repository instructions before making changes.

### 5. Do you need to install the application to work on the code?

Not always.

- For explanation, planning, documentation, and code review, the agent can inspect the repository without OCI credentials or a running VM.
- For Python tests, install the project dependencies. The simplest local setup is:

~~~bash
./oci-free setup
./oci-free test
~~~

- `./oci-free setup` creates a local virtual environment and creates `config.json` from the generic example only if it does not already exist. It preserves an existing config file.
- Do not add your real `config.json`, OCI SDK profile, private keys, or tokens to Git.
- You do not need to run `./oci-free audit` or connect to an OCI tenancy for ordinary development tasks.

### 6. Safe development workflow

For each task, ask the agent to:

1. Inspect the current branch and `git status`; preserve any unrelated local changes.
2. Explain the proposed change and identify cloud, billing, security, or data-loss risks.
3. Make a focused change on a separate Git branch.
4. Add or update offline tests.
5. Run:

~~~bash
python -m py_compile oci_free_watch.py
bash -n oci-free
python -m unittest discover -s tests -v
~~~

6. Review the final diff for credentials, personal identifiers, account-specific OCIDs, unsafe defaults, and weakened guardrails.
7. Update the README, project memory, and worklog when relevant.
8. Report changed files, commands and test results, limitations, and any manual operator action.

**Important:** Agent-ready does not mean permission to operate your cloud account. Agents must not run live OCI audits, enable a creation-capable service, submit an instance launch, change IAM/network/billing settings, or modify a production VPS unless you explicitly authorize that exact operation. The three-part creation guard must never be weakened or bypassed.

### Agent instruction files at a glance

| File | Purpose |
|---|---|
| `AGENTS.md` | Shared rules for Codex and other coding agents |
| `CLAUDE.md` | Claude Code entry point |
| `GEMINI.md` | Gemini-family entry point |
| `.github/copilot-instructions.md` | GitHub Copilot repository instructions |
| `docs/agents/PROJECT_MEMORY.md` | Durable technical memory; not personal account data |
| `docs/agents/START_PROMPT.md` | Copy/paste universal agent briefing |
| `docs/agents/WORKLOG.md` | Milestones, test evidence, and agent handoffs |
| `.claude/commands/work.md` | Optional Claude Code `/work` shortcut |

## License

No license has been selected. Until a LICENSE file is added, do not assume the repository grants permission to redistribute or reuse the code.
