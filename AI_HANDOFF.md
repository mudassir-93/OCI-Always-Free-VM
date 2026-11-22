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
| Milestone 2 HEAD | `12016469da75e03ea2ec2d9b8e6a263b4f15a933` (latest review fix + regression test) |
| PR #6 base | `feat/cli-v1-foundation` (stacked on PR #5) |
| CI at latest checked code HEAD | Python checks and CLI foundation matrix completed SUCCESS on Windows/Linux × Python 3.11/3.12 at parent HEAD `1b4c055cc4a8d08767cba347916b87690eb5971f`; new VPU guard fix is awaiting fresh CI |
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

At the previous verified Milestone 2 HEAD (`1f65967a3bd128bd7e55c1314b219a068abd430d`):

- GitHub Actions `CLI foundation`: completed successfully (Windows/Linux × Python 3.11/3.12).
- GitHub Actions `Python checks`: completed successfully.
- Prior CI logs include offline tests, compile checks, Linux shell syntax, Windows PowerShell parser validation, wheel packaging, and CLI help/version checks.
- Follow-up review added Windows install-path normalization for relative `OCI_PLATFORM_HOME` values and an offline test proving a target region different from the tenancy home region is rejected without writing config.
- The earlier wizard-test `StopIteration` failures were caused by a prompt mock that did not answer a newly added image-eligibility question. Prompt-aware callbacks fixed that issue; subsequent Python checks passed.
- Installer failure handling now reserves a new install directory atomically and removes only that directory if clone, venv, pip, or initial setup fails. Existing install directories are preserved.
- Added Linux installer integration tests for partial-clone cleanup and preservation of pre-existing install data.
- Python checks at HEAD `e6ae13225e646abe9725bd004b4177135483a237` passed on Python 3.11 and 3.12. CLI foundation matrix: Linux jobs passed; Windows jobs were still in progress at last check.
- Python workflow now runs feature-branch checks on pull requests rather than on both push and pull_request events, reducing duplicate notifications.
- The temporary accidental default-branch handoff commit was removed and `main` was force-restored with a lease to its exact pre-change commit `3356f03f52cf5c3a7eeb59b3cccdb76a5e967337`; the default branch now matches its original head again.
- No real fresh-machine installation has been performed yet.
- No live OCI integration test has been performed or authorized.
- Do not describe installer as production-validated until a fresh Windows and Linux workstation test has passed.

## Known limitations / items to review

- Installers currently clone `main`; until PR #5 and #6 are merged, users must not expect the installers to fetch these in-progress changes from the default branch.
- Installers are first-install scripts, not update/uninstall/rollback managers.
- The wizard does not authenticate to OCI or verify the account/image/region live; its confirmations are operator attestations. The engine's live preflight remains authoritative.
- No GUI/dashboard, multi-cloud support, auto-update, rollback, service manager, or interactive monitoring TUI is in scope yet.
- Wizard boot-volume performance now rejects anything except the engine's exact 10-VPU/GB policy; regression test added. Fresh CI is pending.
- Review remaining wizard validation and installer failure cleanup before calling this release-ready.
- Do not assume OCI billing or Always Free eligibility from local configuration values.

## Exact next actions

1. Re-read `AGENTS.md`, `docs/agents/PROJECT_MEMORY.md`, this file, and the latest PR #5/#6 status.
2. Re-check fresh CI for HEAD `12016469da75e03ea2ec2d9b8e6a263b4f15a933`. Review PowerShell cleanup behavior and remaining PR #6 edge cases. Do not merge.
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


## Review correction — boot-volume policy alignment (2026-11-22)

- Code review found that the wizard accepted boot-volume performance values from 10 through 120 VPUs/GB, while the existing engine's safety guard permits exactly 10 VPUs/GB.
- Updated the wizard to reject every value except 10 before saving configuration.
- Added an offline regression test proving a value of 20 is rejected and no new config file is written.
- New feature-branch HEAD: `12016469da75e03ea2ec2d9b8e6a263b4f15a933`.
- Previous full CI matrix at parent HEAD `1b4c055cc4a8d08767cba347916b87690eb5971f` passed Windows/Linux × Python 3.11/3.12. Fresh CI for this review fix is pending.
- PR #5 and PR #6 remain open and draft. PR #6 remains stacked on PR #5.
- `main`, production deployments, and live OCI resources were not modified or accessed.
- Next: verify fresh CI, continue safety review, then request operator review; do not merge without explicit approval.


## Latest continuation update — fresh-install validation plan (2026-11-22)

- Added `docs/testing/INSTALLATION_SMOKE_TEST.md` covering fresh Windows/Linux installation, existing-directory protection, local-only configuration checks, sanitized test evidence, and release completion criteria.
- Linked the smoke-test guide from README.
- Confirmed the current gap: Windows installer has PowerShell parser validation but no end-to-end automated Windows execution test; the integration cleanup/preservation test is POSIX-only.
- No fresh workstation install has been performed. Do not call the installer release-ready until both Windows and Linux manual fresh-install checks pass.
- Next coding task: add focused wizard tests for timestamped backup behavior and for clearing pre-existing `creation_enabled` / `creation_confirmation` values; run exact-HEAD CI and keep PRs unmerged pending operator approval.
