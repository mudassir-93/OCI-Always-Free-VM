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
