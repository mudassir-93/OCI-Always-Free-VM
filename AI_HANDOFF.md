# AI session handoff — OCI Always Free A1 VM Automation

> **Read this file at the start of every AI coding session.** It is the concise, current continuation point. For durable rules and architecture, also read `AGENTS.md` and `docs/agents/PROJECT_MEMORY.md`. The repository and GitHub branches are the source of truth; do not rely on a previous chat transcript.

## Current objective

Build a safe, lightweight, cross-platform Windows/Linux CLI for the existing OCI Always Free A1 capacity monitor and guarded single-instance launcher. Keep OCI as the first supported cloud. Preserve the original engine and Linux helper during gradual CLI migration. Do not add a GUI/dashboard yet.

## Non-negotiable safety

- Default behavior is read-only. A launch requires all existing independent guards: local `mode.creation_enabled=true`, exact `LAUNCH_ONE_ALWAYS_FREE_INSTANCE` confirmation, and explicit CLI `--enable-create`.
- Never upgrade an OCI account, create/modify networking, launch a non-A1 shape, or modify/terminate existing resources.
- Never run live OCI operations, change production deployments, or enable a creation service during coding work unless the user explicitly authorizes that exact action.
- Never commit credentials, private keys, local config, personal OCIDs, account IDs, or production host details. Do not ask the user to paste secrets.
- Never claim guaranteed Always Free eligibility, capacity, or zero cost.
- Do not merge PRs, retarget PRs, or deploy without the user's explicit approval.
- Preserve backward compatibility; add migration paths rather than removing legacy entry points.

## Current GitHub state (checked 2026-11-22)

Repository: [mudassir-93/OCI-Always-Free-VM](https://github.com/mudassir-93/OCI-Always-Free-VM)

| Item | Current state |
|---|---|
| Default branch | `main` — untouched by the current CLI work |
| Milestone 1 branch | `feat/cli-v1-foundation` |
| Milestone 1 PR | [#5 — cross-platform CLI foundation](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/5), OPEN, DRAFT, not merged |
| Milestone 2 branch | `feat/cli-v1-installer-wizard` |
| Milestone 2 PR | [#6 — installer and guided configuration](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/6), OPEN, DRAFT, not merged |
| Milestone 2 HEAD | `1f65967a3bd128bd7e55c1314b219a068abd430d` at last check |
| PR #6 base | `feat/cli-v1-foundation` (stacked on PR #5) |
| CI at Milestone 2 HEAD | CLI foundation matrix and Python checks both COMPLETED / SUCCESS |
| Live cloud work | None; no OCI API calls, VM launch, or production deployment changes |

PR #6 depends on PR #5. Keep the dependency explicit. Do not merge #6 into `main` before #5 is accepted. After the user approves merging #5, re-check PR #6's base and retarget it to `main` only with approval. Then rerun all CI before requesting approval to merge #6.

## Implemented

### Milestone 1 — CLI foundation (PR #5; not merged)

- Installable Python package and `oci-platform` console command.
- Setup, doctor, redacted config display/validation, OCI profile list/use, VM audit/once/monitor, status, and logs.
- Thin CLI integration over the existing engine; direct engine invocation and legacy helper preserved.
- Windows/Linux process locking (`msvcrt` / `fcntl`).
- Offline tests and Windows/Linux × Python 3.11/3.12 CI.
- Existing launch guards retained.

### Milestone 2 — installer and guided configuration (PR #6; not merged)

- `oci-platform configure`: local-only wizard for OCI profile, Free Tier attestation, home region, existing network IDs, A1 resources/storage, SSH public-key path, pinned Ubuntu image, usage/budget policy, retry settings, paths, and log level.
- Wizard requires target region == tenancy home region, checks operator-entered policy caps, validates VCN/subnet/image identifier prefixes and reads the SSH public key file.
- Existing config gets a timestamped backup before save.
- Wizard always forces VM creation disabled and clears the launch confirmation phrase, even if previous config was armed.
- `install.ps1` and `install.sh`: clone default branch into a new user-owned directory, create isolated venv, install CLI, and create a safe starter config.
- Installers refuse existing install directories; no admin/root requirement, PATH modification, background service, OCI API call, or cloud resource operation.
- README and agent docs updated. Offline wizard tests and installer syntax CI added.

## Validation evidence

At the latest checked Milestone 2 HEAD (`1f65967a3bd128bd7e55c1314b219a068abd430d`):

- GitHub Actions `CLI foundation`: completed successfully (Windows/Linux × Python 3.11/3.12).
- GitHub Actions `Python checks`: completed successfully.
- Prior CI logs include offline tests, compile checks, Linux shell syntax, Windows PowerShell parser validation, wheel packaging, and CLI help/version checks.
- No real fresh-machine installation has been performed yet.
- No live OCI integration test has been performed or authorized.
- Do not describe installer as production-validated until a fresh Windows and Linux workstation test has passed.

## Known limitations / items to review

- Installers currently clone `main`; until PR #5 and #6 are merged, users must not expect the installers to fetch these in-progress changes from the default branch.
- Installers are first-install scripts, not update/uninstall/rollback managers.
- The wizard does not authenticate to OCI or verify the account/image/region live; its confirmations are operator attestations. The engine's live preflight remains authoritative.
- No GUI/dashboard, multi-cloud support, auto-update, rollback, service manager, or interactive monitoring TUI is in scope yet.
- Review wizard validation and installer failure cleanup before calling this release-ready.
- Do not assume OCI billing or Always Free eligibility from local configuration values.

## Exact next actions

1. Re-read `AGENTS.md`, `docs/agents/PROJECT_MEMORY.md`, this file, and the latest PR #5/#6 status.
2. Review the full PR #6 diff for safety, platform compatibility, config validation, installer failure handling, and test coverage. Do not merge.
3. Add tests/fixes for any concrete findings on `feat/cli-v1-installer-wizard`; update this file and `docs/agents/WORKLOG.md` after meaningful changes.
4. Ask the user to review/approve PR #5 before merging it. Do not merge autonomously.
5. After #5 is approved and merged, with approval retarget #6 to `main`, rerun CI, and ask for #6 approval.
6. After both PRs are merged, guide the user through fresh-machine installation tests on Windows and Linux. Keep setup creation-disabled and use only offline validation until the user separately authorizes live OCI access.
7. Next product milestone after stable installation: configuration migration/import and safe profile/config backup/restore. Discuss scope before implementation.

## Session closeout requirements

Before ending a work session:
- Update this file with current branch, HEAD SHA, PR state, CI state, completed work, blockers, and exact next actions.
- Append a dated entry to `docs/agents/WORKLOG.md`.
- Keep `docs/agents/PROJECT_MEMORY.md` aligned with durable architecture changes.
- Commit/push work on the approved feature branch only.
- Report tests passed, failed, and not run separately.
- State explicitly whether `main`, live OCI, and production were untouched.
