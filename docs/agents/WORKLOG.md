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
