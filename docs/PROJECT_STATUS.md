# Project progress and delivery status

**Status checked:** 2026-11-23  
**Repository:** [mudassir-93/OCI-Always-Free-VM](https://github.com/mudassir-93/OCI-Always-Free-VM)  
**Default branch at review:** `main`  
**Main baseline inspected before this documentation sync:** `3307f8f44b94c888bdd8f0b76b3746eed19f5dba`  
**GitHub queue:** No open pull requests or issues were found on 2026-11-23.

## Executive summary

The agreed V1 repository implementation is complete: the existing A1 automation engine is wrapped in a cross-platform CLI, installers and guided configuration are merged, the arrow-key terminal interface is merged, and the project handoff documentation is current.

**The code-delivery phase is complete; end-to-end operator validation is still in progress.** On 2026-11-23, the operator reported that a fresh Windows installation and CLI/interactive terminal smoke test worked on a second PC. PR #12 also added a successful end-to-end fresh Linux install to the Ubuntu CI matrix, including creation-disabled config, exact-commit verification, existing-directory preservation, and failed-clone cleanup. A separate manual Linux workstation install has not been reported. The original Windows checkout update, real local OCI profile diagnostics, and all live OCI validation remain outstanding. PR #13 then synchronized the validation record, and the squash-merge commit passed both push-triggered main workflows (6/6 jobs). No VM launch has been performed.

| Workstream | Progress | Evidence / limitation |
|---|---|---|
| Core engine and safety policy | Implemented | Source includes A1-only, home-region, existing-network, quota/storage/usage, image, duplicate and guarded-launch checks; offline policy tests exist. Not live-tested against the user's tenancy. |
| Cross-platform CLI — PR #5 | Complete | CLI commands, local setup/doctor/config/profile/status/logs and engine integration are merged. |
| Installer and configuration — PR #6 | Complete in code | Windows/Linux installers and guided configuration are merged; automated failure/preservation checks exist. A clean public-repository installation has not been manually completed on a fresh workstation. |
| Interactive terminal UX — PR #7 | Complete in code | Arrow-key home menu and grouped configuration editor are merged; offline tests cover validation, backup/disarm, cancellation, region sync and safe profile selection. Real Windows Terminal interaction is pending. |
| Project handoff/documentation — PR #8 | Complete | README release status and AI handoff were consolidated and merged. |
| Automated CI for PR #8 | 6/6 jobs passed | Exact PR head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca`: Python checks 3.11/3.12 and Windows/Linux CLI matrix 3.11/3.12 all passed. |
| Progress tracker and roadmap — PR #9 | Merged | Added the consolidated status report, handoff links, and clarified offline versus live validation boundaries. |
| Handoff synchronization — PR #10 | Merged | Synchronized the status tracker and AI handoff to PR #9, recorded its CI evidence, and corrected the README test-file tree. |
| Automated CI for PR #10 | 6/6 jobs passed | Exact PR head `e6d39d94067a7261d893df5cc5a0b4d19288eb26`: Python checks run `45113875820` and CLI foundation run `45113875739`; Windows/Linux × Python 3.11/3.12 all passed before squash merge. |
| Windows fresh-PC validation record — PR #11 | Merged | Recorded the operator-reported successful fresh Windows installation and CLI/TUI smoke test on a second PC. |
| Automated CI for PR #11 | 6/6 jobs passed | Exact PR head `23a2528f93b232a68b7602922ebb724a19d1cc1d`: Python checks run `45116410721` and CLI foundation run `45116410713`; Windows/Linux × Python 3.11/3.12 all passed before squash merge. |
| Linux clean-install integration — PR #12 | Passed in CI | Ubuntu/Python 3.12 installed the exact PR commit in a fresh temporary directory as a non-root user; CLI, redacted config, disabled creation, existing-directory preservation, and failed-clone cleanup all passed. |
| Automated CI for PR #12 | 6/6 jobs passed | Exact PR head `8a3f0436b3a6988dcae5d4f620645a5596baa5bd`: Python checks run `45117728501` and CLI foundation run `45117728426`; Windows/Linux × Python 3.11/3.12 all passed before squash merge. |\n| PR #13 documentation synchronization CI | 6/6 jobs passed | Exact PR head `83e193d07b435a323b9d7771b0e5539af4893022`: Python checks run `45118315425` and CLI foundation run `45118315427`; Windows/Linux × Python 3.11/3.12 all passed before merge. |\n| Latest main push CI after PR #13 | 6/6 jobs passed | Merge commit `3307f8f44b94c888bdd8f0b76b3746eed19f5dba`: Python checks run `45118630570` and CLI foundation run `45118630579`; both push-triggered workflows completed successfully. |
| Automated CI for PR #9 | 6/6 jobs passed | Exact PR head `4d23c696f22c2b5cb6c50fb7d3ce864eb479139a`: Python checks run `45110780545` (3.11/3.12) and CLI foundation run `45110780528` (Windows/Linux × 3.11/3.12) all passed before squash merge. |
| Fresh Windows PC installation and CLI/TUI smoke test | Passed — operator-reported | On 2026-11-23, the operator confirmed the fresh download/install and the described version/help/config-summary, home-menu, and configuration-editor checks worked on a second PC. Exact OS/Python versions and captured output were not supplied; this is not an independently observed test run. |
| Existing Windows checkout update | Pending | This second-PC fresh install does not confirm that the original `$HOME\oci-automation-platform` checkout has been updated in place. |
| Manual workstation validation | Partially complete | Fresh Windows install/TUI test is operator-reported passed. Separate Linux workstation install and original Windows checkout update remain pending. Existing-directory preservation is now covered by both Windows and Linux CI integration tests. |
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
| Cross-platform CLI foundation | [PR #5](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/5) | **MERGED** |
| Installer and guided configuration | [PR #6](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/6) | **MERGED** |
| Interactive terminal menu and editor | [PR #7](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/7) | **MERGED** |
| Release documentation and AI handoff cleanup | [PR #8](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/8) | **MERGED** |
| Consolidated progress tracker and roadmap | [PR #9](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/9) | **MERGED** |
| Handoff and release-state synchronization | [PR #10](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/10) | **MERGED** |
| Operator-reported Windows validation record | [PR #11](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/11) | **MERGED** |
| Fresh Linux installer integration and source branch override | [PR #12](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/12) | **MERGED** |\n| Handoff and validation record synchronization | [PR #13](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/13) | **MERGED** |\n| Handoff and validation record synchronization | [PR #13](https://github.com/mudassir-93/OCI-Always-Free-VM/pull/13) | **MERGED** |

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

The exact PR #9 head `4d23c696f22c2b5cb6c50fb7d3ce864eb479139a` also passed all six jobs before squash merge:

- **Python checks:** run `45110780545`, Python 3.11 and 3.12.
- **CLI foundation:** run `45110780528`, Ubuntu and Windows with Python 3.11 and 3.12 (four matrix jobs).

PR #9 was squash-merged as main commit `fb46199e16739f30edd5045b7a4282b275cc3bfb`.

The exact PR #10 head `e6d39d94067a7261d893df5cc5a0b4d19288eb26` passed all six jobs before squash merge:

- **Python checks:** run `45113875820`, Python 3.11 and 3.12.
- **CLI foundation:** run `45113875739`, Ubuntu and Windows with Python 3.11 and 3.12 (four matrix jobs).

PR #10 was squash-merged as main commit `e60bbc76854b5a712f72a5c63ff6a1e5ee1f884b`.

The exact PR #11 head `23a2528f93b232a68b7602922ebb724a19d1cc1d` passed all six jobs before squash merge:

- **Python checks:** run `45116410721`, Python 3.11 and 3.12.
- **CLI foundation:** run `45116410713`, Ubuntu and Windows with Python 3.11 and 3.12 (four matrix jobs).

PR #11 was squash-merged as main commit `6c57040b458cc30c98e3920c5f572f10dc8ab8af`.

The exact PR #12 head `8a3f0436b3a6988dcae5d4f620645a5596baa5bd` passed all six jobs before squash merge:

- **Python checks:** run `45117728501`, Python 3.11 and 3.12.
- **CLI foundation:** run `45117728426`, Ubuntu and Windows with Python 3.11 and 3.12 (four matrix jobs). The Ubuntu/Python 3.12 job ran the new fresh Linux installer integration step successfully, including exact-commit, starter-config, CLI, sentinel preservation, and failed-clone cleanup assertions.

PR #12 was squash-merged as main commit `7c5e583fe2103f8b39aee82de54dfdde2f35aa6d`. The available commit-run lookup did not expose a separate post-merge push-triggered run for that merge commit; do not claim one was verified.

The Windows jobs include PowerShell installer parsing, Windows installer preservation/failure integration tests, offline tests, packaging and CLI entry-point checks. Ubuntu jobs include compilation, shell syntax, offline tests, packaging and CLI entry-point checks; the Ubuntu/Python 3.12 job also runs a real fresh installation of the exact PR branch as a non-root user.

The PR #13 exact head `83e193d07b435a323b9d7771b0e5539af4893022` passed all six required jobs before merge. It was squash-merged as `3307f8f44b94c888bdd8f0b76b3746eed19f5dba`. The subsequent push-triggered workflows for that exact main commit also passed: Python checks run `45118630570` and CLI foundation run `45118630579`, covering Python 3.11/3.12 and Windows/Linux × Python 3.11/3.12 (6/6 jobs total). These checks validate repository code and installation workflows; they do not validate the user's OCI tenancy, billing state, or VM capacity.

## Remaining work — ordered plan

### 1. Update the existing Windows checkout

**State: PENDING for the original checkout.** A separate fresh install on another PC has now been reported working; that does not update the original checkout.

The known checkout is `$HOME\oci-automation-platform`. The per-user app configuration is separate at `%APPDATA%\oci-platform\config.json`. Preserve it. **Do not rerun the installer** because the installer refuses to overwrite an existing directory.

When the PC is available:
1. Check `git status --porcelain`; stop and inspect any local changes.
2. Confirm the checkout is on `main`.
3. Update using `git pull --ff-only origin main`.
4. Install the updated package into the existing venv with `.venv\Scripts\python.exe -m pip install -e .`.
5. Check `oci-platform --version`, then start `oci-platform` and confirm the home menu appears.

The safe PowerShell block is maintained in [AI_HANDOFF.md](../AI_HANDOFF.md).

### 2. Manually smoke-test the interactive editor

**State: PASSED — operator-reported on a second Windows PC (2026-11-23).**

The operator confirmed the fresh install and the test sequence's CLI version/help, redacted config summary, interactive home menu, and configuration editor navigation all worked. The operator was instructed to cancel without saving and keep VM creation disabled. Exact OS/Python versions, commit SHA installed, and command output were not captured, so this is recorded as operator-reported rather than independently reproduced. A separate existing-directory sentinel test and line-oriented `--plain` fallback have not been confirmed.

### 3. Complete local configuration and local diagnostics

**State: NOT VERIFIED.** The fresh-PC smoke test used a temporary test config and did not establish readiness of the operator's real OCI SDK profile or tenancy configuration.

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

- GitHub Actions is not a substitute for a real interactive session in Windows Terminal. A second-PC Windows fresh install and interactive smoke test were reported passed by the operator on 2026-11-23; no screenshots/logs or OS/Python version details were collected.
- The Windows installer integration test verifies existing-directory preservation and cleanup after a simulated Git clone failure; it is not a successful fresh installation from the public repository.
- Linux CI now performs a real fresh install from the exact PR branch using the public installer, then validates CLI startup, safe starter config, exact commit, existing-directory protection, and failed-clone cleanup. This is a hosted Ubuntu CI run, not a manual install on a separate physical Linux workstation.
- Unit tests use local fixtures/mocks; they cannot establish the state of the user's live OCI tenancy, billing plan, IAM visibility, image eligibility or available A1 capacity.
- Free Tier status and the Console's “Always Free Eligible” image label remain operator attestations where the SDK cannot reliably verify them.

## Definition of completion

The V1 **code delivery** milestone is complete. Call the initial operator rollout validated only after the original Windows checkout is updated, local diagnostics pass, and the user-approved read-only OCI audit and one-shot capacity check are reviewed. The second-PC Windows TUI test is operator-reported passed, and the Linux installer now has end-to-end hosted CI coverage; a separate physical Linux workstation test remains an additional manual acceptance step when Linux is an intended operator platform. A real VM launch is optional and remains separately guarded.

## Safety and environment closeout

As of this review:
- No local Windows or Linux workstation files were changed.
- No OCI API calls, VM launches, networking changes, billing/IAM changes, EC2 changes or production deployments were performed.
- No credentials, private keys, personal OCIDs or production host details were added to the repository.
- The second-PC Windows smoke-test result is based on the operator's confirmation; no test files, logs, credentials, or machine-specific details were uploaded.
