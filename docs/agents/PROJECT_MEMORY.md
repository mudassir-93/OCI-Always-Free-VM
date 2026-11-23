# Project memory — OCI Always Free A1 VM Automation

This is durable, repository-level context for any AI coding agent. It describes the project, not an individual user's OCI account.

## Product purpose

A lightweight OCI automation application for monitoring Ampere A1 host capacity and optionally submitting one guarded A1 VM launch request when capacity becomes available. The Python engine and new `oci-platform` CLI target Windows and Linux; the legacy Bash wrapper and systemd deployment remain Linux-only. It uses the official OCI Python SDK.

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
- Windows and Linux runtime for the Python engine and `oci-platform` CLI (Python 3.11+).
- Linux-only systemd service and `oci-free` Bash convenience wrapper.
- The new CLI is a thin layer over the existing engine; preserve direct Python invocation and legacy wrapper behavior during gradual migration.

## Configurability

The public template is account-neutral. Operators provide their own home region, availability domain, VCN/subnet, image, SSH public-key path, display name, A1 OCPU/memory allocation, boot volume size, OS/version, monthly usage budgets, and local policy caps. The code allows A1 resource sizes within configured limits, validates finite numeric values and whole-GB boot volume sizes, and still checks live OCI quotas and existing resource usage. Public IPv4 and an existing public subnet remain required in this release.

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

- oci_free_watch.py — existing engine, policy guards, OCI API calls, audit, capacity monitoring, launch, retries, notifications, and state.
- oci_platform/cli.py — cross-platform command hierarchy, local setup, diagnostics, profile selection, and engine integration.
- oci_platform/tui.py — arrow-key terminal home menu, grouped configuration editor, local validation, and safe review/save workflow.
- oci_platform/templates/config.example.json — packaged, account-neutral first-run configuration.
- pyproject.toml — installable Python project and `oci-platform` console entry point.
- tests/test_cli.py — offline tests for setup, profile handling, command safety, engine argv integration, and process locking.
- oci-free — convenience command wrapper; all exposed monitoring commands remain read-only.
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
python -m pip install -e .
oci-platform --help
oci-platform --version
python -m compileall -q oci_platform oci_free_watch.py
python -m unittest discover -s tests -v
./oci-free config-check
./oci-free test
python -m py_compile oci_free_watch.py
bash -n oci-free
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

## CLI V1 foundation — merged into main (PR #5)

The first implementation milestone is merged into `main` via PR #5. The currently released CLI remains a thin layer over the established engine.

- Product direction: OCI-focused automation platform, CLI-first for V1, with Windows and Linux support.
- Backward compatibility: gradual. Existing `python oci_free_watch.py ...` commands and the Linux `oci-free` wrapper remain supported.
- The `oci-platform` command is a thin interface over the established engine, not a replacement automation engine.
- Initial commands include setup, doctor, config show/validate, OCI profile list/use, VM audit/once/monitor, status, and logs.
- Setup creates a per-user config from a packaged generic template only when missing. It does not connect to OCI, collect credentials, arm VM creation, or overwrite an existing config.
- VM audit and once remain read-only. VM monitor remains read-only unless the operator explicitly supplies the creation CLI switch; the engine's existing two local confirmations and live preflight checks remain mandatory.
- The engine now accepts an argv list for safe in-process CLI integration and uses platform-specific non-blocking process locking instead of importing POSIX `fcntl` unconditionally.
- GitHub Actions tests Windows and Linux on Python 3.11 and 3.12; PR #5's required checks passed before merge.
- The first foundation milestone did not include the later installer, configuration wizard, or interactive terminal home screen; these were delivered in Milestone 2 and the follow-up terminal UX milestone.

## CLI V1 Milestone 2 — installer and guided configuration (merged into main via PR #6)

- Developed on `feat/cli-v1-installer-wizard` and merged after the foundation dependency was merged.
- Added `oci-platform configure`, an interactive local-only wizard for OCI SDK config/profile, Free Tier attestation, home region, existing network identifiers, A1 resources, usage budgets, SSH public-key path, pinned Ubuntu image, retry settings, log/state paths, and log level.
- The wizard rejects a target region different from the tenancy home region and validates requested resources against the operator-entered local policy caps.
- The wizard always forces creation disabled and clears the confirmation phrase, even if an existing config was armed. It backs up an existing config before saving.
- Added `install.ps1` and `install.sh`. They clone the default branch into a new user-owned directory, create an isolated virtual environment, install the CLI, and run local setup. They refuse to overwrite an existing directory and do not require admin/root privileges.
- Installer scripts do not call OCI, create cloud resources, add PATH entries, install systemd services, or arm creation.
- Added offline tests for the wizard's successful configuration path and refusal when the operator does not confirm Free Tier.
- Added CI syntax validation for both installer scripts.
- The Windows and Linux installers are now available from the public default branch.
- No live OCI operations or production deployments were performed.


## Interactive terminal UX milestone (merged into main via PR #7)

- Added Questionary-powered arrow-key menus for an interactive home screen when oci-platform is run without arguments in a real terminal.
- Added grouped field-by-field configuration editing for OCI profile, home region, availability domain, existing VCN/subnet, A1 sizing/storage, policy budgets, usage attestations, SSH public key, pinned Ubuntu image, retry settings, local paths, and logging.
- The target region follows the configured home region automatically. The UI validates the local SDK config/profile, OCI region format, identifier prefixes, SSH public-key file, supported A1/Ubuntu settings, integer resource sizing, and local resource caps before saving.
- Review-before-save, timestamped backups, cancel-without-save, Ctrl+C/EOF handling, and a line-oriented --plain fallback preserve usability in non-interactive sessions.
- The home menu only offers local actions; cloud audit/monitor operations remain explicit subcommands. No live OCI APIs are called by the terminal editor.
- Every successful wizard save reasserts account_type=FREE_TIER, allow_paid_resources=false, mode.creation_enabled=false, and an empty creation confirmation phrase.
- Questionary is pinned as a small pure-Python UI dependency; the OCI SDK and engine remain unchanged.
- PR #7 was squash-merged as 605a01ae92d57920ee116539aa8ed53eae976503. The exact merged main commit passed Python checks 45108762748 (3.11/3.12) and CLI foundation 45108762718 (Windows/Linux × 3.11/3.12). The Windows cp1252 output issue was fixed; tests assert cp1252 compatibility, home-region auto-sync, and credential-safe profile selection. Manual Windows Terminal interaction remains a separate smoke-test requirement.

## Current delivery status and roadmap

The current milestone-by-milestone plan, completion state, CI evidence, workstation validation gaps, and ordered next actions are maintained in [docs/PROJECT_STATUS.md](../PROJECT_STATUS.md). Read that file before continuing implementation or reporting project readiness.

As of 2026-11-23, PRs #5–#8 are merged. Core CLI/installer/configuration/TUI code delivery is complete and the exact PR #8 head passed all six required CI jobs. Real Windows Terminal interaction, fresh Linux workstation installation, user-local configuration, and live OCI tenancy validation remain outstanding. No live VM launch has been performed; the guarded launch remains optional and disabled by default.
