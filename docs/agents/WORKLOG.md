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
- PR #3 contains these changes and awaits merge/review.
