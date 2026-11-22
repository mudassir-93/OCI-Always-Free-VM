# Project worklog

This file records repository milestones and agent handoffs. Do not place personal account identifiers, credentials, or production host details here.

## Baseline

- Project: OCI Always Free A1 capacity monitor and guarded single-instance launcher.
- Runtime: Python + official OCI SDK on Linux.
- Default behavior: read-only.
- Creation requires three independent local/CLI confirmations.
- Network provisioning is out of scope; an existing public subnet and Internet Gateway route are required.
- Local config, OCI credentials, SSH keys, logs, and runtime state must stay outside Git.

## Current repository-generalization milestone

- Remove tenancy-specific defaults from public configuration and documentation.
- Make A1 OCPU, RAM, boot volume, OS/version, and home-region values operator-configurable within fail-closed policy limits.
- Preserve A1-only and Free Tier-only constraints.
- Add cross-agent instruction and project-memory files.
- Expand policy tests and validate with local unit tests and GitHub Actions.

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
