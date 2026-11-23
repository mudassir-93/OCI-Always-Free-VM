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
- Local tests: not run in this environment because outbound GitHub access was unavailable for cloning the branch.
- CI evidence: the legacy Python checks passed on Python 3.11 and 3.12. The new CLI matrix passed all four Windows/Linux × Python 3.11/3.12 jobs on commit `086eedc295be41f6d46ccba9b5eea610a808c7a3`; the logs show all 24 offline tests passed on Windows and Linux, and wheel template inclusion plus CLI entry-point checks passed on Ubuntu. A final rerun is in progress after a workflow-trigger-only adjustment.
- Tests not run: manual testing on the operator's own fresh Windows/Linux machines and live OCI tests. No live OCI operations were attempted.
- Safety review: no account-specific values or credentials were added; setup does not contact OCI or overwrite an existing config; VM creation still requires the original three independent switches and live preflight.
- Known risks / next checks: perform a human review of CLI UX and configuration migration behavior; verify the final CI rerun. The one-command installer and interactive wizard remain intentionally out of scope. Do not merge until the final checks and operator review are complete.
- Next task: fix any CI or review findings, then prepare a draft PR for operator review. Installer and guided wizard remain a later milestone.

## 2026-11-22 — CLI V1 Milestone 2: installer and guided configuration (in progress)

- Created stacked branch `feat/cli-v1-installer-wizard` from the CLI foundation branch; this milestone depends on PR #5 and does not change `main`.
- Added `oci-platform configure`, a local interactive wizard covering OCI SDK config path/profile, Free Tier confirmation, tenancy home region, target region, existing VCN/subnet, A1 resources, storage, SSH public-key path, pinned Ubuntu image, manual image eligibility, current-month usage review, monthly policy budgets, retry timing, log/state paths, and log level.
- The wizard rejects a target region that differs from the home region, enforces configured resource/storage caps, makes a timestamped backup of existing config, and keeps creation disabled regardless of previous config state.
- Added a Windows PowerShell installer and Linux shell installer. Both clone the repository into a new user-owned install directory, create an isolated venv, install the CLI, and run creation-disabled local setup.
- Installers refuse to overwrite an existing install directory, do not use elevated privileges, do not add PATH entries or install services, and never contact OCI.
- Added offline wizard tests and CI checks for shell and PowerShell syntax.
- CI status: pending for this branch. No local execution in this environment; GitHub Actions will provide Windows/Linux coverage.
- Not tested: running installer on a real fresh Windows or Linux workstation, and any live OCI API interaction.
- Safety review: no credentials or account-specific OCIDs added; no cloud resources or production deployments accessed; no instance launch path enabled by installer/wizard.
- Next: fix CI findings, inspect the final diff, open a draft stacked PR against `feat/cli-v1-foundation`, then manually test installation on the user's separate machine after both PRs are merged.

## 2026-11-22 — Persistent AI session handoff and Milestone 2 CI verification

- Added root-level `AI_HANDOFF.md` as the concise, durable continuation record for future ChatGPT, Claude Code, Codex, Gemini, and other coding-agent sessions.
- Handoff records product objective, non-negotiable safety rules, current branches and PR links/states, dependency ordering, latest checked HEAD, CI evidence, completed milestones, limitations, exact next actions, and session closeout requirements.
- Updated `AGENTS.md` and `docs/agents/START_PROMPT.md` so agents must read and maintain `AI_HANDOFF.md`.
- Re-checked PR #5 and PR #6: both remain OPEN and DRAFT; neither is merged. PR #6 remains stacked on `feat/cli-v1-foundation`.
- Re-checked Milestone 2 HEAD `1f65967a3bd128bd7e55c1314b219a068abd430d`: GitHub Actions `CLI foundation` and `Python checks` both completed successfully.
- The latest checks validate the Windows/Linux × Python 3.11/3.12 matrix, offline test suite, installer syntax parsing, and CLI/package checks as configured by CI.
- No local fresh-workstation installation, live OCI API operation, VM launch, or production deployment test was performed.
- Safety: `main` remains unchanged by this milestone; no PR was merged and no live cloud or production resource was touched.
- Next: perform a focused review of installer failure handling and wizard edge cases on the feature branch; report concrete findings and fixes. Then ask the user to approve PR #5 before merging. Keep PR #6 stacked until #5 is accepted.

## 2026-11-22 — Milestone 2 follow-up review

- Added Windows installer path normalization so relative `OCI_PLATFORM_HOME` values are converted to absolute paths before parent-directory creation and cloning.
- Added an offline wizard regression test proving a target region different from the tenancy home region is rejected without writing a config.
- Current code HEAD before this documentation update: `193c1ee35a32fa336d3f2e7e37c7115233a343d8`.
- CI for that code HEAD was queued/running when checked; verify exact-HEAD CLI foundation and Python checks before claiming success.
- No OCI credentials, live API calls, VM launches, production deployment changes, or changes to the `main` working tree remain after the corrective removal of the accidentally placed handoff file.
- Next: inspect exact-HEAD CI results, fix any failures, then continue PR #6 review and fresh-machine test planning.

- Correction note: the handoff file was briefly created on the default branch due an omitted branch argument. It was removed, and `main` was force-restored with an expected-head lease to its exact pre-change commit `3356f03f52cf5c3a7eeb59b3cccdb76a5e967337`. Verified `main` now points to that original commit. The handoff file exists on `feat/cli-v1-installer-wizard` only.

## 2026-11-22 — Installer failure recovery, regression tests, and CI noise reduction

- Reviewed the eight failed historical Actions runs. The common test failure was `StopIteration` in the configure wizard because a sequence-based mocked input did not include the newer image Always Free confirmation prompt. Prompt-aware test callbacks fixed it; later Python checks passed.
- Hardened both installers: they now reserve a previously absent destination and remove only their own incomplete install directory when clone, venv creation, pip installation, or initial local setup fails. Pre-existing install directories are refused and preserved.
- Added `tests/test_installers.py` with Linux integration coverage for cleanup after a partial clone failure and preservation of existing operator data.
- Changed `.github/workflows/tests.yml` to run pushes only on `main`, while validating feature branches through pull-request events. This removes redundant Python-check runs on every feature-branch push.
- Corrected workflow matrix interpolation after an intermediate run exposed a literal backslash in the Python version expression.
- Latest checked branch HEAD: `e6ae13225e646abe9725bd004b4177135483a237`.
- Python checks passed on Python 3.11 and 3.12 at this HEAD. CLI foundation matrix Linux jobs passed; Windows 3.11 and 3.12 were still in progress at last check.
- No PR merged; `main` remains at `3356f03f52cf5c3a7eeb59b3cccdb76a5e967337`. No live OCI calls, VM launch, or production changes.
- Next: verify both Windows matrix jobs, inspect any errors, then finish the installer/configuration code review. Do not merge either PR without explicit approval.


## 2026-11-22 — Wizard/engine policy alignment review

- Reviewed the full installer and wizard changes against the existing engine's live preflight and safety policy.
- Found a mismatch: the wizard accepted 10–120 boot-volume VPUs/GB, but the engine allows exactly 10. Updated the wizard to enforce exactly 10 before saving.
- Added an offline regression test confirming that a requested 20 VPUs/GB is rejected and no config file is written.
- Previous full Windows/Linux × Python 3.11/3.12 CI matrix passed at parent code HEAD `1b4c055cc4a8d08767cba347916b87690eb5971f`; fresh CI for the correction is pending.
- PR #5 and #6 remain open/draft; PR #6 remains stacked on PR #5. No merge performed.
- No live OCI API calls, VM launch, production deployment change, or modification to `main`.
- Next: inspect fresh CI for the new HEAD, continue remaining config/installer edge-case review, and then request operator review before any merge.


## 2026-11-22 — Cross-platform fresh-install release checklist

- Added `docs/testing/INSTALLATION_SMOKE_TEST.md` with explicit clean-machine Windows and Linux install steps, local-only configuration checks, existing-directory preservation checks, evidence rules, completion criteria, and clear OCI safety boundaries.
- Linked the checklist from the README installer section.
- Recorded the current validation gap: CI parses the PowerShell installer but does not execute a full Windows installation; the automated installer integration test currently exercises POSIX cleanup/preservation only.
- The checklist explicitly requires fresh Windows and Linux workstation tests before calling the installer milestone release-ready.
- No installer was executed on the user's machine; no live OCI calls, VM launch, production changes, or merge occurred.
- Next: add wizard regression coverage for backup creation and forcibly clearing previously armed creation settings; then check CI for the new documentation commits and arrange fresh workstation validation after the PRs are merged.


## 2026-11-22 — Installer venv-failure regression coverage

- Added a POSIX installer integration test that simulates virtual-environment creation failing after the destination directory has been reserved and Git clone has succeeded; it asserts the incomplete install directory is removed.
- The first test fixture had an incorrectly escaped shebang/newline and failed in CI. Corrected the fixture and pushed the follow-up commit; this was a test-fixture defect, not an installer defect.
- At HEAD `44040482ddbf711ce843caad3351f27b3863a9c4`, Python checks passed on Python 3.11 and 3.12. The CLI foundation matrix passed both Ubuntu jobs; both Windows jobs were still running at last check.
- Existing wizard tests already verify timestamped backup creation and that a previously armed creation flag/confirmation are forcibly cleared. No duplicate tests were added.
- No fresh workstation installation, live OCI call, VM launch, production change, or PR merge occurred. `main` remains at `3356f03f52cf5c3a7eeb59b3cccdb76a5e967337`.
- Next: verify both Windows jobs, then keep fresh Windows/Linux workstation installation as the remaining manual release gate.


## 2026-11-22 — Final CI recheck for installer milestone branch

- Rechecked the latest installer-wizard branch HEAD `b64a44df77faf37f1a41dbf7db7104e694be975d`: both the CLI foundation workflow and Python checks workflow completed successfully.
- The CLI foundation matrix passed on Ubuntu and Windows with Python 3.11 and 3.12. Python checks passed on Python 3.11 and 3.12.
- Rechecked PR #5 head `5b91248419182a06216f400296a9f2c0546a2be9`: its Python checks and CLI foundation workflow runs are successful.
- PR #5 remains an open draft targeting `main`; PR #6 remains an open draft stacked on `feat/cli-v1-foundation`. Neither has review submissions or inline review threads.
- `main` remains at `3356f03f52cf5c3a7eeb59b3cccdb76a5e967337`. Both PRs remain unmerged pending explicit operator approval.
- Remaining release validation is a fresh real workstation install on Windows and Linux. CI PowerShell syntax parsing is not equivalent to executing the Windows installer end-to-end; Linux integration tests cover clone failure, venv failure, and existing-directory preservation.
- No live OCI audit, VM launch, account/billing change, production server change, or local workstation installation was performed.


## 2026-11-22 — Windows installer safety integration tests

- Added `tests/test_installers_windows.ps1` and wired it into the Windows GitHub Actions matrix.
- The Windows integration test executes the actual PowerShell installer script against temporary directories: it verifies an existing destination and sentinel file remain untouched, then simulates Git clone failure and verifies only the installer-owned incomplete directory is removed.
- First CI attempt correctly exercised both safety scenarios but returned process exit code 1 because the deliberately failing fake Git command left a nonzero native exit code. Added an explicit successful test-process exit after all assertions.
- Corrected code commit `6af29f358c0b8d1c880d76d4da265e8da32b3e68` passed all four CLI matrix jobs (Windows/Linux × Python 3.11/3.12) and both Python-check jobs.
- Updated the installation smoke-test guide to describe the expanded automated coverage and retain successful clean-machine installation as a manual release gate.
- Latest docs commit `bbd803b8f40e10a3d31b50538a31ce947937e4da` has fresh CI queued/running; do not mark that exact HEAD green until both workflows complete.
- No OCI calls, VM launch, production changes, account/billing changes, or PR merges. Main remains untouched.


## 2026-11-22 — PR #5 merged; PR #6 retargeted and de-stacked

- User explicitly approved merging PR #5 first and PR #6 second, contingent on latest CI being green.
- Verified all 10 checks on PR #5 exact HEAD `5b91248419182a06216f400296a9f2c0546a2be9` completed successfully. Marked PR #5 ready and squash-merged it; merge commit is `29b66fbe83655692633b06d1c71157071969c1d6`.
- Retargeted PR #6 to `main`. GitHub initially showed a stacked diff containing foundation files and a non-mergeable state because the foundation PR had been squash-merged.
- Merged the new `main` commit into the PR #6 feature branch using a two-parent merge commit with the existing PR #6 tree, then advanced the branch with a fast-forward ref update and expected-head check (no force push).
- Verified PR #6 now has merge base `main`, reports mergeable=true, and its diff is the intended Milestone 2 delta only: 15 files, 1,287 additions, 6 deletions.
- New PR #6 HEAD: `4b78ee759e7ec95866abdae2a825a4d095492853`. Fresh CI checks were queued for this exact commit at the time of this entry; do not merge until all required jobs pass.
- Previous PR #6 code HEAD `55ee2ad3145af0b527ce6d9cf9a427d08a24ebeb` had all six CI checks green, including Windows installer safety integration tests. The new merge commit still requires its own CI.
- No live OCI API calls, VM launch, billing/IAM changes, EC2 changes, or production deployment changes.
- Next: verify exact-HEAD PR #6 CI, inspect final diff, then merge PR #6 using expected HEAD SHA and verify main.


## 2026-11-22 — PR #6 merged; release validation handoff refreshed

- Independently fetched PR #5 and PR #6 from GitHub and confirmed both are closed and merged into `main`.
- PR #5 merge commit: `29b66fbe83655692633b06d1c71157071969c1d6`.
- PR #6 merge commit and current `main` HEAD: `8eebb755b0eb29230e21994eed202a01e9217977`.
- Confirmed PR #6 merged diff: 15 files, 1,224 additions, 6 deletions.
- Refreshed `AI_HANDOFF.md` because its prior state incorrectly described PR #6 as open and `main` as the pre-PR-#6 commit.
- Post-merge main CI is not verified in this session: the available commit-status lookup returned no status entries, while the workflow-run lookup exposed only pull-request-triggered runs. Do not report post-merge CI as green until checked through the Actions run for the exact main SHA.
- The Windows and Linux fresh-workstation installs remain unperformed. Windows prerequisites are Git for Windows and Python 3.11+; installer refuses to overwrite an existing destination.
- No local workstation commands were run. No OCI API calls, VM launch, billing/IAM changes, EC2 changes, or production deployment changes were made.
- Next: verify post-merge Actions for `8eebb755b0eb29230e21994eed202a01e9217977`, then perform the user's Windows fresh install and validate CLI/config safety.


## 2026-11-23 — Interactive terminal UX upgrade (in progress)

- Added a Questionary-powered interactive home menu for launching the CLI without arguments in a real terminal. The menu contains local setup, configuration, doctor, redacted summary, local status/logs, help, and exit; it deliberately does not start cloud operations.
- Added a grouped arrow-key configuration editor with field-by-field selection/editing, current-value defaults, home-region auto-sync, OCI profile selection from local profile names, validation feedback, review-before-save, cancel, and safe Ctrl+C/EOF handling.
- Kept the line-oriented configuration flow available with configure --plain and as the no-TTY fallback for scripted sessions.
- Added local validation for SDK config/profile presence, region format/matching, existing VCN/subnet/image identifier prefixes, SSH public-key file readability, A1-only/Ubuntu 24.04 constraints, integer resource/storage values, and configured policy caps.
- Preserved the existing creation guard: a successful save always forces FREE_TIER, paid resources disabled, creation disabled, and clears the launch confirmation phrase; existing config backup behavior is retained.
- Added questionary==2.1.1 as a dependency and added offline tests for validation, cancellation, backup/disarm behavior, and terminal menu routing.
- Files: oci_platform/tui.py, oci_platform/cli.py, pyproject.toml, requirements.txt, tests/test_tui.py, tests/test_cli.py, README.md, docs/agents/PROJECT_MEMORY.md.
- Tests run: none in this connector-only editing session; GitHub Actions validation is pending.
- Tests not run: Windows/Linux CI, manual Windows terminal interaction, live OCI integration (not authorized and not needed for this task).
- Safety review: no OCI calls, VM launch, billing/IAM changes, local workstation changes, or production deployment. The UI deliberately keeps cloud operations out of the no-argument home menu.
- Known risks / limitations: interactive arrow-key behavior requires a real terminal; configure --plain is retained for piped/line-oriented use. The OCI config file must already exist before the new editor will permit a complete configuration save.
- Next: inspect the final diff, open a PR, and require Windows/Linux Python 3.11/3.12 CI plus manual terminal smoke testing before merge.

### 2026-11-23 — Windows terminal encoding fix and expanded editor tests

- The first Windows Python 3.11/3.12 CI run exposed a cp1252 UnicodeEncodeError in the new terminal header because the box-drawing character was not encodable on the default Windows runner console.
- Replaced unsupported box-drawing and arrow/prompt glyphs with ASCII-safe alternatives; retained punctuation supported by cp1252.
- Strengthened TUI tests to explicitly encode captured save/cancel output as cp1252, preventing this regression.
- Added interaction tests proving that changing the tenancy home region updates the target region automatically and that profile selection exposes profile names only, not credentials or private-key paths.
- Previous-head Linux 3.11/3.12 jobs and Python checks passed; previous-head Windows jobs failed only on the encoding issue described above.
- New CI is running on the latest PR head; do not merge until all Python checks and Windows/Linux 3.11/3.12 jobs are green.
- No OCI API calls, VM launches, billing/IAM changes, local workstation changes, or production deployments were performed.

### 2026-11-23 — PR #7 cross-platform CI passed; review-ready

- The latest implementation and test commit 1ba41480d4314a789775f12826b8994489830ef1 passed both GitHub Actions workflows: Python checks run 45108231189 and CLI foundation run 45108231166.
- Python checks passed on Python 3.11 and 3.12.
- CLI foundation matrix passed on Windows and Ubuntu, each with Python 3.11 and 3.12. This includes editable dependency installation, compileall, PowerShell installer syntax, Windows installer safety integration tests, offline unit tests, wheel template packaging, and CLI entrypoint checks.
- The Windows cp1252 output regression is fixed; TUI tests assert that save/cancel output can be encoded by cp1252. Region auto-sync and credential-safe profile selection have dedicated tests.
- PR #7 remains open and unmerged pending the user's explicit merge approval. The arrow-key UX still requires a manual smoke test in the user's actual Windows Terminal/PowerShell session after the PR is merged.
- The handoff/worklog update is documentation-only and is being committed separately; GitHub may run the workflows again for that newer PR head, so verify the latest head checks before any merge.
- No local workstation was changed. No OCI API calls, VM launches, billing/IAM/network changes, or production deployments were performed.

### 2026-11-23 — PR #7 merged; main CI passed

- User approved proceeding with the CLI UX upgrade; PR #7 was squash-merged after the exact PR head passed both GitHub Actions workflows.
- PR #7 merge commit: 605a01ae92d57920ee116539aa8ed53eae976503.
- Main-branch post-merge workflows also passed on the exact merge commit: Python checks run 45108762748 (Python 3.11/3.12) and CLI foundation run 45108762718 (Windows/Ubuntu × Python 3.11/3.12).
- The CLI provides the arrow-key home menu, grouped configuration editor, field selection/editing, home-region auto-sync, OCI profile-name selection, local validation, review-before-save, timestamped backups, and clean cancel behavior.
- The Windows cp1252 terminal encoding regression was fixed and covered by tests. All four Windows/Linux × Python 3.11/3.12 CI jobs passed after the fix.
- The user's existing Windows installation has not yet been updated. The known checkout is %USERPROFILE%\oci-automation-platform, with the application config stored separately under %APPDATA%\oci-platform\config.json. Preserve that config; update the existing checkout in place, not by rerunning the installer.
- Manual Windows Terminal interaction remains pending: test the home menu, field editing, region auto-sync, back/cancel, review/save, and Ctrl+C. Keep creation disabled.
- No OCI API calls, VM launches, billing/IAM/network changes, local workstation modifications, or production deployments were performed.

## 2026-11-23 — Workstation-independent release documentation review

- Reviewed the merged CLI/installer/interactive UX documentation while the operator's Windows PC was unavailable.
- Corrected a stale README sentence that still described the merged CLI, wizard, and installers as pending milestones.
- Replaced the duplicated and contradictory `AI_HANDOFF.md` with a current continuation record: verified main HEAD, merged PRs #5–#8, exact CI run IDs, safety boundaries, remaining manual Windows Terminal validation, and the safe update procedure for the existing checkout.
- Submitted as PR #8: https://github.com/mudassir-93/OCI-Always-Free-VM/pull/8; squash-merged as `948fc148a416556f25900600c21223605e4f3066`. This was a documentation-only change; no application code or dependencies changed.
- Exact PR head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca` passed Python checks run `45109638479` (Python 3.11/3.12) and CLI foundation run `45109638472` (Windows/Linux × Python 3.11/3.12). Windows 3.12 completed successfully, including PowerShell parsing and Windows installer safety integration tests.
- Manual Windows Terminal interaction remains NOT RUN because the operator's PC is unavailable.
- PR #8 merge commit: `948fc148a416556f25900600c21223605e4f3066`. Post-merge push-triggered CI status was not exposed by the available commit-workflow lookup; do not claim it was verified.
- No local workstation changes, OCI API calls, VM launches, billing/IAM changes, EC2 changes, or production deployments were performed.

## 2026-11-23 — Consolidated project progress and remaining roadmap

- Added `docs/PROJECT_STATUS.md` as the current project progress and delivery tracker. It records original V1 scope, completed milestones, exact CI evidence, workstation and tenancy validation gaps, the safe next-step order, and the optional guarded launch boundary.
- Confirmed PRs #5–#8 are merged. The core CLI, installer/configuration editor, and interactive terminal UX code milestones are complete in the repository.
- Reconfirmed PR #8 exact-head CI: Python checks run `45109638479` passed on Python 3.11/3.12; CLI foundation run `45109638472` passed on Windows/Linux × Python 3.11/3.12.
- Explicitly separated source-code completion and automated CI from manual Windows Terminal testing, fresh Linux installation, local configuration/doctor validation, and live OCI audit/capacity testing; those operational checks remain outstanding.
- Updated README.md, AI_HANDOFF.md, and PROJECT_MEMORY.md to link to the status tracker. Corrected the installation smoke checklist because existing tests already cover backup/disarm behavior and unsupported VPU write-free rejection.
- Documentation-only change. No source code, dependencies, user workstation, OCI resources, billing/IAM, EC2 or production deployment changed. No live OCI calls or VM launch were performed.
- Next: complete manual Windows checkout update and terminal smoke tests when the PC is available; then finish local-only validation, and request separate approval before any live OCI read-only audit.


## 2026-11-23 — PR #9 merged; progress tracker synchronized

- Merged PR #9 `docs: add project progress and remaining roadmap` into `main` after reviewing its six-file documentation-only diff and confirming all six required CI jobs passed on exact head `4d23c696f22c2b5cb6c50fb7d3ce864eb479139a`.
- PR #9 CI: Python checks run `45110780545` passed on Python 3.11/3.12; CLI foundation run `45110780528` passed on Windows/Linux × Python 3.11/3.12.
- Merge commit: `fb46199e16739f30edd5045b7a4282b275cc3bfb`.
- Parallel static review tracks found no open issues or PRs, confirmed the three launch guards and read-only audit/once restrictions in source, and found no TODO/FIXME/XXX or `shell=True` search hits. This was a scoped static review, not a formal security audit.
- The PR #9 merge commit did not expose a separate post-merge push workflow through the available commit-status/run lookup; only the exact PR-head CI is claimed as verified.
- No source code, dependencies, workstation files, OCI resources, billing/IAM, EC2, or production deployment changed. No live OCI calls or VM launch were performed.
- Next work remains operator-side: update the existing Windows checkout when the PC is available, complete manual terminal/local validation, and request separate approval before a live read-only OCI audit.


## 2026-11-23 — Operator-reported fresh Windows PC smoke test passed

- The operator reported that they downloaded/installed the project on a second PC and confirmed that everything in the supplied fresh-Windows test sequence worked.
- Recorded as an operator-reported manual pass for fresh install, `oci-platform --version`, `--help`, redacted `config show`, interactive home menu, and configuration-editor navigation/cancel path as described in the preceding test instructions.
- Exact Windows build, Python version, installed commit SHA, command transcripts, and screenshot evidence were not supplied. Do not describe this result as independently reproduced by CI or by this agent.
- This result does not establish that the original Windows checkout was updated, that the separate existing-directory/sentinel preservation test passed, that fresh Linux installation passed, or that the real OCI SDK profile/tenancy was validated.
- Fresh Linux workstation install, original Windows checkout update, local OCI configuration/doctor validation, and explicitly approved read-only live OCI audit/capacity checks remain pending. Actual VM creation remains optional and disabled.
- No repository application code, dependencies, workstation files, OCI resources, billing/IAM, EC2, or production deployments were changed as part of this test report. No live OCI calls or VM launch were performed.


## 2026-11-23 — PR #11 merged; operator Windows test recorded

- PR #11 records the operator-reported successful fresh Windows install and interactive CLI/TUI smoke test on a second PC.
- Exact PR head: `23a2528f93b232a68b7602922ebb724a19d1cc1d`; PR #11 squash merge commit: `6c57040b458cc30c98e3920c5f572f10dc8ab8af`.
- CI passed all six jobs before merge: Python checks run `45116410721` (3.11/3.12) and CLI foundation run `45116410713` (Windows/Linux × 3.11/3.12).
- The user-reported Windows pass remains labelled as operator-reported because exact OS/Python version, installed SHA and captured transcript were not supplied.

## 2026-11-23 — PR #12 merged; real Linux fresh-installer CI added

- Updated both installers to accept optional `OCI_PLATFORM_REPOSITORY` and `OCI_PLATFORM_BRANCH` environment variables. Defaults remain this repository's public clone URL and `main`; no behavior changes when the variables are unset.
- Added `tests/test_install_linux.sh` and an Ubuntu/Python 3.12 CI step that clones the exact PR source branch as a non-root user into a unique temporary directory and runs the public Linux installer end-to-end.
- The new integration test verifies CLI executable/version/help, redacted starter config summary, Free Tier-only and creation-disabled config, exact installed commit, existing-destination sentinel preservation, and cleanup after a deliberately failed clone.
- Exact PR head `8a3f0436b3a6988dcae5d4f620645a5596baa5bd`; PR #12 squash merge commit: `7c5e583fe2103f8b39aee82de54dfdde2f35aa6d`.
- CI passed all six jobs: Python checks run `45117728501` (3.11/3.12) and CLI foundation run `45117728426` (Windows/Linux × Python 3.11/3.12). The new Ubuntu/Python 3.12 fresh-install integration step passed and confirmed it installed the exact PR head.
- A separate attempt to run the installer in an isolated Debian 13 container could not resolve `raw.githubusercontent.com` because the container environment had no DNS access; no local manual Linux pass is claimed. The hosted GitHub Actions Ubuntu integration test completed successfully.
- No OCI credentials/profile were configured, no live OCI API calls or VM launches were performed, and no workstation, billing/IAM, EC2 or production resources were changed.
- Remaining: update the original Windows checkout when available; validate the real local OCI profile and diagnostics; request separate explicit approval before any live read-only OCI audit/capacity run. Manual Linux workstation install remains an optional additional operator acceptance check; automated hosted Linux installer coverage is now present.


## 2026-11-23 — PR #13 and latest main CI verified; handoff synchronized

- Rechecked the repository default branch and confirmed PR #13 merge commit / main baseline `3307f8f44b94c888bdd8f0b76b3746eed19f5dba`.
- Confirmed PR #13 exact-head workflows passed: Python checks run `45118315425` and CLI foundation run `45118315427` (6/6 jobs across Python 3.11/3.12 and Windows/Linux).
- Confirmed both push-triggered workflows on the PR #13 merge commit passed: Python checks run `45118630570` and CLI foundation run `45118630579` (6/6 jobs).
- Re-synchronized `docs/PROJECT_STATUS.md`, `AI_HANDOFF.md`, and `docs/agents/PROJECT_MEMORY.md` with PR #13 and current main CI evidence; checked for open PRs and issues (none found).
- Reviewed the installer scripts, CI workflows, CLI setup/configuration flow, static Free Tier policy checks, and existing policy tests. No new actionable defect was identified in the inspected paths; this was a focused review, not a full security audit or live tenancy test.
- Tests run: repository main push CI passed 6/6 jobs; PR #13 exact-head CI passed 6/6 jobs.
- Tests not run: local Windows checkout update, manual physical Linux workstation install, real local OCI profile diagnostics, live read-only OCI audit/capacity check, and VM launch.
- Safety: only a documentation branch was updated. No local workstation files, OCI resources, OCI credentials, billing/IAM, EC2, or production deployment were changed. VM creation remains disabled; no OCI API calls were made.
- Next: when the Windows PC is available, fast-forward the existing clean `main` checkout using the safe in-place procedure in `AI_HANDOFF.md`; then complete local-only `doctor` and config validation. Any live read-only OCI audit requires separate explicit approval.
