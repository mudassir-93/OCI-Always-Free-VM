# Project progress and delivery status

**Status checked:** 2026-11-23  
**Repository:** [mudassir-93/OCI-Always-Free-VM](https://github.com/mudassir-93/OCI-Always-Free-VM)  
**Default branch at review:** `main`  
**Latest main commit inspected:** `8c8d3ea18a2dd451c531a3f62d33cc013ce690a9`

## Executive summary

The agreed V1 repository implementation is complete: the existing A1 automation engine is wrapped in a cross-platform CLI, installers and guided configuration are merged, the arrow-key terminal interface is merged, and the project handoff documentation is current.

**The code-delivery phase is complete; end-to-end operator validation is not.** The user's Windows computer is unavailable, so the latest main branch has not yet been pulled into the existing local checkout and the interactive terminal UI has not been manually exercised there. No real OCI tenancy audit, capacity-monitoring run, or VM launch has been performed.

| Workstream | Progress | Evidence / limitation |
|---|---|---|
| Core engine and safety policy | Implemented | Source includes A1-only, home-region, existing-network, quota/storage/usage, image, duplicate and guarded-launch checks; offline policy tests exist. Not live-tested against the user's tenancy. |
| Cross-platform CLI — PR #5 | Complete | CLI commands, local setup/doctor/config/profile/status/logs and engine integration are merged. |
| Installer and configuration — PR #6 | Complete in code | Windows/Linux installers and guided configuration are merged; automated failure/preservation checks exist. A clean public-repository installation has not been manually completed on a fresh workstation. |
| Interactive terminal UX — PR #7 | Complete in code | Arrow-key home menu and grouped configuration editor are merged; offline tests cover validation, backup/disarm, cancellation, region sync and safe profile selection. Real Windows Terminal interaction is pending. |
| Project handoff/documentation — PR #8 | Complete | README release status and AI handoff were consolidated and merged. |
| Automated CI for PR #8 | 6/6 jobs passed | Exact PR head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca`: Python checks 3.11/3.12 and Windows/Linux CLI matrix 3.11/3.12 all passed. |
| Existing Windows checkout update | Pending | Earlier install/starter configuration exists, but the checkout has not been updated to the latest merged main after PR #7/#8. |
| Manual workstation validation | Pending | Windows Terminal smoke test and fresh Linux installation have not been observed. |
| Real OCI tenancy validation | Not started | No live read-only OCI audit or capacity check has been performed. |
| Actual A1 VM launch | Not performed; optional | Creation remains disabled by default. A launch is not required for local CLI validation and must not be attempted without separate explicit approval. |

Do not combine these into one percentage: code delivery is complete, while the separate workstation and live-tenancy acceptance gates remain open.

## Original scope and delivery record

The agreed V1 scope is intentionally narrow:

- Monitor OCI Ampere A1 capacity and optionally request one `VM.Standard.A1.Flex` instance in the tenancy home region.
- Use an existing VCN, public subnet and Internet Gateway route. Do not provision or modify networking.
- Keep account-specific configuration and credentials local; use an account-neutral public template.
- Preserve Free Tier-only policy, configured budget limits, live quota/storage checks, image eligibility confirmation, SSH public-key checks, duplicate protection and retry/idempotency safeguards.
- Support Windows and Linux through the Python CLI; retain the legacy Linux shell wrapper and systemd option.
- Keep all normal actions read-only. VM creation requires three independent local/CLI guards and separate operator authorization.
- Do not add a GUI, dashboard, databases, Redis, Docker, Node.js, or unrelated modules to V1.

### Completed repository milestones

| Milestone | Delivery | State |
|---|---|---|
| Existing engine and policy baseline | A1 capacity workflow, Free Tier policy checks, existing network validation, quota/storage/usage checks, retry/state safeguards | Implemented in source; live tenancy verification pending |
| Cross-platform CLI foundation | [PR #5](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/5) | <badge>MERGED</badge> |
| Installer and guided configuration | [PR #6](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/6) | <badge>MERGED</badge> |
| Interactive terminal menu and editor | [PR #7](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/7) | <badge>MERGED</badge> |
| Release documentation and AI handoff cleanup | [PR #8](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/8) | <badge>MERGED</badge> |

### What the delivered CLI contains

- `oci-platform` interactive home menu with local-only actions.
- `configure` arrow-key editor with grouped fields, current-value defaults, back navigation, validation feedback, review-before-save, timestamped backups and safe cancellation.
- Tenancy home-region to target-region auto-sync.
- OCI SDK profile selection by profile name only; credential values are not displayed.
- `configure --plain` fallback for line-oriented/non-interactive sessions.
- `setup`, `doctor`, redacted config summary, offline config validation, profile list/use, VM audit/once/monitor, local status and logs.
- Creation-disabled setup and configure behavior; a successful configuration save clears any previous launch confirmation and keeps creation disabled.

## Automated verification already passed

The exact PR #8 head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca` passed:

- **Python checks:** run `45109638479`, Python 3.11 and 3.12.
- **CLI foundation:** run `45109638472`, Windows and Ubuntu with Python 3.11 and 3.12 (four matrix jobs).

The Windows jobs include PowerShell installer parsing, Windows installer preservation/failure integration tests, offline tests, packaging and CLI entry-point checks. Ubuntu jobs include compilation, shell syntax, offline tests, packaging and CLI entry-point checks.

These are CI results for the exact PR head before the documentation-only squash merge. Later main-branch edits after that merge were documentation-only; a surfaced post-merge push-workflow result for the latest main commit was not available during this review. Do not describe the latest main commit itself as having a separately verified post-merge run.

## Remaining work — ordered plan

### 1. Update the existing Windows checkout

**State: BLOCKED until the PC is available.**

The known checkout is `$HOME\oci-automation-platform`. The per-user app configuration is separate at `%APPDATA%\oci-platform\config.json`. Preserve it. **Do not rerun the installer** because the installer refuses to overwrite an existing directory.

When the PC is available:
1. Check `git status --porcelain`; stop and inspect any local changes.
2. Confirm the checkout is on `main`.
3. Update using `git pull --ff-only origin main`.
4. Install the updated package into the existing venv with `.venv\Scripts\python.exe -m pip install -e .`.
5. Check `oci-platform --version`, then start `oci-platform` and confirm the home menu appears.

The safe PowerShell block is maintained in [AI_HANDOFF.md](../AI_HANDOFF.md).

### 2. Manually smoke-test the interactive editor

**State: NOT RUN on the user's real Windows Terminal.**

Check arrow keys, j/k, Enter, home-menu navigation, category/field selection, editing, back navigation, cancellation, review, and Ctrl+C. Confirm home-region auto-sync and that profile choices show names only. Verify no unexpected file write occurs on cancellation. Keep VM creation disabled.

### 3. Complete local configuration and local diagnostics

**State: NOT VERIFIED on the user's current machine.**

After the local OCI SDK profile already exists, configure the application with the operator's own region, existing network, SSH public-key path, approved A1 sizing, budgets, pinned image and required attestations. Keep credentials and OCIDs out of Git and chat.

Run:
- `oci-platform doctor` — local Python/SDK/config and offline policy readiness check.
- `oci-platform config validate` — offline application-policy validation.
- `oci-platform config show` — confirm the summary redacts credentials and OCIDs.

The CLI's doctor path calls the engine's local `--validate-config` path; it does not create OCI clients or perform a live cloud audit.

### 4. Run a read-only OCI audit

**State: NOT RUN; requires a separate explicit user go-ahead.**

`oci-platform vm audit` performs live read-only OCI API checks. It should be used only after the user deliberately authorizes that tenancy call and the local profile/config are ready. Review home region, AD, existing VCN/subnet/route, image candidate, quotas, current usage, volumes, IAM visibility and duplicate-instance findings. This step must not modify cloud resources.

### 5. Test one capacity check and read-only monitoring

**State: NOT RUN.**

After a successful audit and explicit approval for live read-only operations:
- `oci-platform vm once` runs one audit/capacity check and never launches.
- `oci-platform vm monitor` repeatedly monitors in read-only mode by default.

Capacity reports do not reserve a host or guarantee a later launch.

### 6. Optional guarded VM creation

**State: NOT STARTED and intentionally disabled.**

This is a separate, optional operational decision — not a missing step in the local CLI build. Do not arm it as part of testing. Any future launch requires:
1. `mode.creation_enabled=true` in the local config.
2. Exact local confirmation phrase `LAUNCH_ONE_ALWAYS_FREE_INSTANCE`.
3. Explicit CLI `--enable-create`.
4. A separate explicit user authorization for the actual launch, following manual review of Free Tier status, billing, image eligibility, current-month usage, quotas, network and IAM.

No launch, account upgrade, network change or existing-instance modification has been performed.

## Known validation limits

- GitHub Actions is not a substitute for a real interactive session in Windows Terminal.
- The Windows installer integration test verifies existing-directory preservation and cleanup after a simulated Git clone failure; it is not a successful fresh installation from the public repository.
- Linux CI covers installation failure cleanup and existing-directory preservation; a fresh Linux workstation installation remains unobserved.
- Unit tests use local fixtures/mocks; they cannot establish the state of the user's live OCI tenancy, billing plan, IAM visibility, image eligibility or available A1 capacity.
- Free Tier status and the Console's “Always Free Eligible” image label remain operator attestations where the SDK cannot reliably verify them.

## Definition of completion

The V1 **code delivery** milestone is complete. Call the initial operator rollout validated only after the existing Windows checkout is updated, the TUI smoke test passes, local diagnostics pass, and the user-approved read-only OCI audit and one-shot capacity check are reviewed. A real VM launch is optional and remains separately guarded.

## Safety and environment closeout

As of this review:
- No local Windows or Linux workstation files were changed.
- No OCI API calls, VM launches, networking changes, billing/IAM changes, EC2 changes or production deployments were performed.
- No credentials, private keys, personal OCIDs or production host details were added to the repository.
