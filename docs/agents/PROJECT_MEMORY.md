# Project memory — OCI Always Free A1 VM Automation

This is durable, repository-level context for any AI coding agent. It describes the project, not an individual user's OCI account.

## Product purpose

A lightweight Python application that helps an operator monitor OCI Ampere A1 host capacity and optionally submit one guarded A1 VM launch request when capacity becomes available. It is designed for Linux VPS/EC2 hosting and uses the official OCI Python SDK.

The intended audience includes technically capable operators and people who use AI coding agents to configure and maintain the project. Documentation should be clear, explicit, and safe for first-time OCI users.

## Current scope

- Only VM.Standard.A1.Flex compute.
- Only the tenancy home region.
- Existing VCN and public subnet; no network provisioning.
- Existing Internet Gateway route.
- Public IPv4 currently required.
- Operator-selected OCPU, RAM, boot volume, OS/version, image, region/AD, and local network/key paths.
- One target instance only.
- Optional Telegram notifications via environment variables.
- Linux runtime; Windows may be used as the developer workstation but is not a supported direct runtime.

## Runtime flow

1. Read local JSON config.
2. Validate strict Free Tier policy and required fields.
3. Load the local OCI SDK profile and verify region consistency and private-key permissions.
4. Acquire a process lock so two monitors do not run simultaneously.
5. Create OCI Identity, Compute, Virtual Network, Block Storage, and Limits clients.
6. Verify the tenancy home region and availability domain.
7. Inspect the configured VCN/public subnet and Internet Gateway route.
8. Discover a compatible image for configured OS/version and A1 shape.
9. Inventory accessible compartments, active A1 instances, and boot/block volumes.
10. Verify configured monthly budgets, live A1 CPU/memory limits, SSH public key, current-month usage attestation, and manual image eligibility attestation.
11. Report read-only audit status.
12. In monitor mode, request a capacity report.
13. If all three creation switches are armed and capacity is reported, run preflight again and submit one launch request with an OCI retry token and a persisted pending state.
14. Wait for RUNNING, collect VNIC IP information, persist the result, and notify if configured.

## Safety model

The three independent creation switches are:
- local config mode.creation_enabled=true;
- local config mode.creation_confirmation exactly LAUNCH_ONE_ALWAYS_FREE_INSTANCE;
- process argument --enable-create.

--audit and --once are strictly read-only and reject --enable-create. The supplied systemd unit omits --enable-create. Do not change that default.

The app refuses non-Free-Tier account attestations, paid-resource permission, non-A1 shape, target region different from home region, over-budget resource settings, missing live quota, missing or unconfirmed image OCID, missing SSH public key, unreviewed current-month usage, network misconfiguration, and duplicate/ambiguous launch state.

Important limitations:
- account_type and free_tier_only_confirmed are operator assertions; OCI API calls used here cannot authoritatively prove billing plan status.
- The Console's Always Free Eligible image label is manually confirmed; OCI SDK image metadata is not a trusted substitute.
- Capacity reports are advisory and do not reserve a host.
- The app does not guarantee zero billing or exactly-once behavior for every ambiguous network failure.
- IAM permissions and accessible compartments affect the completeness of inventory checks.

## Important files

- oci_free_watch.py — CLI, policy guards, OCI API calls, audit, capacity monitoring, launch, retries, notifications, state.
- config.example.json — generic example configuration; never put real OCIDs or credentials here.
- tests/test_policy.py — offline policy tests.
- systemd/oci-free-watch.service — Linux service that is read-only by default.
- README.md — operator setup, configuration, security, and command reference.
- docs/DEPLOY_EC2.md — generic Linux VPS deployment.
- AGENTS.md — shared coding-agent contract.
- CLAUDE.md / GEMINI.md / .github/copilot-instructions.md — tool entry points.

## Local-only files and secrets

Never commit:
- config.json or other real account configuration.
- ~/.oci/config or OCI private keys.
- SSH private keys or public-key identity files.
- Telegram bot tokens/chat details.
- logs, state files, lock files, environment files, or provider-specific host data.

Use config.example.json and placeholder documentation only. If a credential was ever committed, removing it from the latest tree is not enough: revoke/rotate it and follow a reviewed history-cleanup process.

## Development commands

~~~bash
python -m py_compile oci_free_watch.py
python -m unittest discover -s tests -v
python oci_free_watch.py --audit --config config.json
~~~

Offline unit tests should not require OCI credentials or access a live tenancy. Use mocks for OCI SDK behavior.

## User/operator handoff rules

An agent may inspect and edit repository code when asked. It must not silently:
- run a real audit against the user's tenancy;
- enable a creation-capable service;
- restart a production creation-enabled service;
- edit cloud resources, IAM policies, security rules, or billing settings;
- overwrite local config/state or systemd overrides.

Ask before any of these actions. Keep the live server and local account configuration separate from public repository changes.
