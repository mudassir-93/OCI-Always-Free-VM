# OCI Always Free A1 Capacity Monitor

A lightweight, configuration-driven Python application that checks Oracle Cloud Infrastructure (OCI) capacity for an A1 Flex VM and can optionally submit one guarded launch request when capacity is reported. It uses the official OCI Python SDK and is designed for Linux hosts such as Ubuntu VPS instances.

**Default behaviour is read-only.** VM creation requires three separate opt-ins and a successful live preflight. This project cannot guarantee that OCI usage will be free or that a capacity report will result in a successful launch.

## What it does

- Authenticates to OCI using a local OCI API signing-key profile.
- Confirms the configured region is the tenancy home region and validates the selected availability domain.
- Inspects an existing VCN, subnet, route table, and Internet Gateway. It does not create or modify network resources.
- Discovers a compatible Canonical Ubuntu 24.04 image for VM.Standard.A1.Flex.
- Checks standard A1 OCPU and memory limits using the OCI Limits API.
- Accounts for existing A1 instances and boot/block volume usage visible to the configured identity.
- Projects worst-case 31-day monthly usage against operator-configured limits.
- Checks the public SSH key and optional manual confirmation of the image's Always Free Eligible label.
- Requests a capacity report and retries with bounded exponential backoff and jitter.
- Optionally submits one A1 launch request after all safeguards pass.
- Records launch-pending/idempotency state to avoid blindly submitting duplicate launch requests.
- Supports optional Telegram notifications through environment variables.

## What it deliberately does not do

- Upgrade an OCI account or change a billing plan.
- Create, edit, or delete VCNs, subnets, gateways, route tables, security lists, NSGs, reserved IPs, or firewall rules.
- Launch non-A1 compute shapes.
- Terminate or modify existing instances.
- Guarantee capacity, Always Free eligibility, or zero charges.
- Store OCI credentials, private keys, Telegram tokens, or user-specific OCIDs in the repository.

## Quick start

Requirements: Linux, Python 3.11 or newer, Git, an OCI tenancy, an OCI API signing-key profile, and an existing VCN with a suitable public subnet and route to an Internet Gateway. Windows users can develop with an IDE, but run the application in WSL2 or a Linux host because the monitor uses Linux process-locking and systemd deployment.

Clone the repository to a directory named oci-free-instance-automation:

    git clone https://github.com/OWNER/REPOSITORY.git
    cd oci-free-instance-automation

Create the virtual environment and local config:

    ./oci-free setup

The setup command creates .venv, installs requirements, copies config.example.json to config.json only if config.json does not already exist, and creates local logs/state directories. It never enables VM creation.

## Configure your own OCI tenancy

### 1. Create an OCI API signing key

Create a dedicated OCI user or use an appropriately scoped identity. Follow Oracle's current documentation to create an API signing key and add its public key to the OCI Console.

Keep the private key on the host running this application. Typical files are:

- ~/.oci/config — local OCI profile; contains identifiers and a private-key path.
- ~/.oci/oci_api_key.pem — private API signing key; never commit or share it.
- ~/.oci/oci_api_key_public.pem — public key uploaded to OCI.

Restrict permissions:

    chmod 700 ~/.oci
    chmod 600 ~/.oci/config ~/.oci/oci_api_key.pem

The OCI profile must include user, tenancy, fingerprint, region, and key_file. The region in the profile must match your configured tenancy home region.

### 2. Configure the application

Edit config.json locally. It is ignored by Git.

At minimum, provide:

- account.home_region — the home region shown in your OCI tenancy.
- target.region — must equal account.home_region.
- target.availability_domain — an availability domain returned by OCI for your tenancy.
- target.vcn_ocid — OCID of your existing VCN.
- target.subnet_ocid — pin the intended subnet when the VCN has multiple subnets.
- target.ssh_public_key_file — path to your SSH public key, not the private key.

The sample target uses 2 OCPU, 4 GB RAM, and a 150 GB boot volume as an example only. You may adjust CPU, memory, and boot volume values within the limits you have independently verified for your tenancy. The application remains restricted to VM.Standard.A1.Flex and Canonical Ubuntu 24.04.

Set the account quota caps to values no greater than the limits shown in your own OCI Console. The sample values are conservative examples, not a claim about every tenancy. Review current Oracle Free Tier terms and your own Billing & Cost Management page. Update monthly usage fields to reflect any A1 usage already incurred during the current billing month.

### 3. Verify image eligibility manually

Run a read-only audit:

    ./oci-free audit

The application discovers a compatible Ubuntu image. The OCI SDK does not expose the Console's Always Free Eligible label as a definitive machine-readable property. Open the exact image in OCI Console, verify its eligibility label, then set target.image_ocid and target.image_console_always_free_confirmed=true in your local config.

### 4. Validate and test

    ./oci-free config-check
    ./oci-free test
    ./oci-free audit

An audit validates configuration and live OCI resources. It does not submit a capacity report or launch request.

## Commands

| Command | Purpose | Can launch a VM? |
|---|---|---:|
| ./oci-free help | Show command help | No |
| ./oci-free setup | Create venv, install dependencies, create local config if missing | No |
| ./oci-free config-check | Check local JSON structure and required values | No |
| ./oci-free test | Run unit tests | No |
| ./oci-free audit | Run one read-only OCI audit | No |
| ./oci-free once | Run one audit and capacity report | No |
| ./oci-free monitor | Run continuous read-only monitoring | No |
| ./oci-free status | Show systemd service status | No |
| ./oci-free logs | Follow systemd logs | No |

Direct Python usage:

    .venv/bin/python oci_free_watch.py --config config.json --audit
    .venv/bin/python oci_free_watch.py --config config.json --once
    .venv/bin/python oci_free_watch.py --config config.json --monitor

The wrapper's monitor command is read-only. It intentionally does not expose the creation flag.

## Creation mode: high-risk, explicit opt-in

Do not enable creation until you have reviewed the audit, current OCI Free Tier terms, tenancy quotas, image eligibility, storage usage, network, IAM policy, and billing status.

The application enters creation mode only when all three independent switches are present:

1. mode.creation_enabled is true in local config.
2. mode.creation_confirmation is exactly LAUNCH_ONE_ALWAYS_FREE_INSTANCE.
3. The process is started with --enable-create.

The application re-runs its live preflight immediately before submitting one launch request. It uses a retry token and persistent pending state. If the launch outcome is ambiguous, it stops rather than blindly submitting a second request. A successful instance is recorded and the monitor exits instead of launching another.

Creation mode is not enabled by the sample config or any command in the oci-free wrapper. To deliberately run the guarded launch path after manual review:

    .venv/bin/python oci_free_watch.py --config config.json --monitor --enable-create

The supplied systemd unit runs read-only by default and does not pass --enable-create.

**Billing warning:** A1 shape and resource limits, image labels, monthly usage, and account billing status are separate concerns. The OCI APIs used by this project cannot prove that an account remains on Free Tier or guarantee a zero bill. The local FREE_TIER setting is an operator attestation, not an Oracle billing status check. Never treat this tool as a billing guarantee.

## Capacity and retry behaviour

A capacity report is advisory and does not reserve a host. Capacity can disappear between the report and launch request. The application handles explicit capacity-related responses as retryable and uses exponential backoff with jitter. The sample poll interval is 20 minutes and maximum backoff is 180 minutes. Rate limits and Retry-After responses are handled where available.

Authentication failures, invalid configuration, missing permissions, failed guardrails, and non-retryable OCI API errors stop the monitor for manual review.

## IAM permissions

Start with least-privilege read access. The identity needs enough permissions to inspect tenancy and compartments, region subscriptions, availability domains, compute instances and images, VCN/subnet/route-table/Internet Gateway resources, boot/block volumes, and OCI Limits/capacity-report operations.

Launch mode additionally requires permission to create the selected compute instance and associated boot/VNIC resources. Do not grant tenancy administrator privileges merely to make an error disappear. Confirm required policy verbs against Oracle's current IAM documentation.

## Configuration reference

The complete example schema is in config.example.json:

- oci: OCI config file path and profile name.
- account: home region, operator billing attestation, quota caps, storage cap, monthly usage caps, and prior usage.
- target: region, availability domain, existing network OCIDs, VM shape and sizing, OS, boot volume, public IP, SSH public-key path, and manually pinned image.
- mode: creation guard switches, poll/backoff values, and instance wait settings.
- paths: local log and state files.
- logging: log level.

Do not put secrets in config.json. OCI credentials stay in ~/.oci/config and the private key file; Telegram tokens stay in environment variables.

## Project layout

    .
    ├── oci_free_watch.py             # OCI audit, capacity monitor, guarded launcher
    ├── oci-free                      # one-command local operations wrapper
    ├── config.example.json           # safe, generic config template
    ├── config.json                   # local only; ignored by Git
    ├── AGENTS.md                     # canonical instructions for coding agents
    ├── PROJECT_CONTEXT.md            # durable project context and boundaries
    ├── CLAUDE.md                     # Claude Code entry point
    ├── GEMINI.md                     # Gemini / Antigravity entry point
    ├── docs/                         # deployment and agent workflow
    ├── tests/                        # offline unit tests
    └── systemd/                      # read-only service example

## Coding agents

Codex, Claude Code, Gemini-based tools/Antigravity, GitHub Copilot, and other agents should begin with AGENTS.md and PROJECT_CONTEXT.md. Tool-specific entry files point back to the same source of truth so project rules do not drift.

Read docs/AGENT_WORKFLOW.md for the recommended agent workflow, task format, validation commands, and completion report.

## Security and privacy

Never commit config.json, OCI config files, private keys, SSH public keys, tokens, logs, state, personal OCIDs, IP addresses, usernames, local paths, or email addresses. Run a secret scan before every public release. See SECURITY.md for incident response.

## Deployment

See docs/DEPLOY_EC2.md for generic Ubuntu VPS / AWS EC2 deployment. The project is intentionally lightweight and does not require Docker, Node.js, Redis, PostgreSQL, or a database.

## License

No license has been added yet. Until a license is chosen and committed, do not assume the repository grants permission to reuse, modify, or redistribute the code.
