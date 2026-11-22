# Project worklog

This file records repository milestones and agent handoffs. Do not place personal account identifiers, credentials, or production host details here.

## Baseline

- Project: OCI Always Free A1 capacity monitor and guarded single-instance launcher.
- Runtime: Python + official OCI SDK on Linux.
- Default behavior: read-only.
- Creation requires three independent local/CLI confirmations.
- Network provisioning is out of scope; an existing public subnet and Internet Gateway route are required.
- Local config, OCI credentials, SSH keys, logs, and runtime state must stay outside Git.

## 2026-11-22 — Public multi-user and coding-agent readiness (completed)

- Replaced Dubai-specific example region and AD with blank operator-supplied values.
- Replaced the account-specific SSH key filename and instance display name with generic examples.
- Made A1 OCPU, RAM, boot volume, and OS/version policy configurable within configured caps; kept A1-only, home-region, Free Tier-only, storage, and monthly-budget guards.
- Added finite-number and whole-GB boot-volume validation.
- Added offline --validate-config command.
- Expanded policy tests for alternate valid sizes and invalid values.
- Rewrote README and Linux VPS deployment guide for multi-user setup.
- Added AGENTS.md, CLAUDE.md, GEMINI.md, Copilot instructions, project memory, reusable start prompt, and worklog.
- Strengthened .gitignore for local config, credentials, key files, logs, and state.
- Scanned the current branch files for the known account-specific region/AD, public host IPs, OCID patterns, and repository-owner references; no matches remained in the scanned current tree.
- GitHub Actions passed on Python 3.11 and 3.12: dependency install, py_compile, and unittest discovery all succeeded.
- The reviewed changes were merged into main via PR #1.

## Handoff template

For each future milestone, append:

### YYYY-MM-DD — Short milestone name

- Changes:
- Files:
- Tests run:
- Tests not run:
- Safety review:
- Known risks / limitations:
- Next recommended task:


## 2026-11-22 — Safe operator commands and generic deployment template (completed)

- Added the executable oci-free helper for setup, offline config validation, unit tests, read-only audit, one-shot capacity checks, read-only monitoring, and local systemd status/logs.
- The helper never passes --enable-create; creation remains an explicit advanced workflow outside the helper.
- Replaced the tracked systemd template's original Linux username with CHANGE_ME and documented how to customize the generic installation path.
- Added SECURITY.md, a placeholder-only .env.example, and a Claude Code /work slash command.
- Updated README.md, AGENTS.md, and project memory with the helper commands and validation workflow.
- Added CI checks for shell syntax and executable file mode.
- GitHub Actions passed on Python 3.11 and 3.12, including dependency install, Python compilation, bash -n, executable-bit validation, and unit tests.
- No live OCI API operations or production VPS changes were performed.
- PR #3 was merged into main after the Python 3.11 and 3.12 CI matrix passed.


## 2026-11-22 — Practical AI-agent onboarding documentation

- Replaced the short AI-agent note in README.md with a practical end-to-end guide for opening and using the repository in Codex, Claude Code, Gemini CLI, Google Antigravity, GitHub Copilot, Cursor, and other agentic IDEs.
- Documented which instruction files each tool should use and clarified that auto-loading behavior varies by product/version; agents must be pointed to the files explicitly when needed.
- Added copy/paste prompts for first-time project understanding, feature implementation, review-only sessions, and continuing from the worklog.
- Documented Claude Code's optional /work command, code-only workflows that do not require OCI credentials, local test setup, and the safe development checklist.
- Added a GitHub Actions status badge to README.md.
- Corrected the prior worklog note to record that PR #3 was merged after CI passed.
- Repository description metadata could not be changed through the available GitHub connection actions; a suggested description and topics are provided in the handoff.
- Tests: documentation-only change; CI validation pending on this branch.
- No OCI credentials, live tenancy operations, or production deployments were used.

## 2026-11-22 — CLI V1 foundation (in progress)

- Created isolated branch `feat/cli-v1-foundation` from the reviewed `main` baseline. No changes were made to `main` or any production deployment.
- Added an installable Python project definition and the `oci-platform` console entry point.
- Added a thin CLI layer for local setup, diagnostics, redacted configuration summary, OCI SDK profile listing/selection, VM audit/once/monitor, local status, and logs.
- First-run setup creates a per-user configuration from a packaged generic template only when the target file is absent. It is creation-disabled and performs no OCI API calls.
- Preserved the original `oci_free_watch.py` entry point and added optional argv injection for CLI integration.
- Replaced unconditional POSIX `fcntl` import with platform-specific non-blocking process locking to enable Windows and Linux engine startup.
- Added offline CLI tests for setup preservation, profile redaction/selection, engine argument mapping, read-only defaults, and process-lock behavior.
- Added a GitHub Actions matrix for Windows/Linux and Python 3.11/3.12.
- Updated README, AGENTS.md, and project memory for the new CLI foundation and gradual backward-compatibility approach.
- Tests run locally: none; this environment only provided repository-level GitHub operations. CI is pending and must pass before this milestone is accepted.
- Tests not run: Windows/Linux execution, package build/install, all offline unit tests, and live OCI tests. No live OCI operations were attempted.
- Safety review: no account-specific values or credentials were added; setup does not contact OCI or overwrite an existing config; VM creation still requires the original three independent switches and live preflight.
- Known risks / next checks: validate wheel/editable installation, Windows file-lock behavior, CLI error handling, README command accuracy, and CI matrix results. Do not merge until CI and code review pass.
- Next task: fix any CI or review findings, then prepare a draft PR for operator review. Installer and guided wizard remain a later milestone.
