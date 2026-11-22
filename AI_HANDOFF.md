# AI session handoff — OCI Always Free A1 VM Automation

> Read this file first when continuing work. The GitHub repository and current branch/PR state are authoritative; older worklog entries are historical records.

## Objective

Maintain a safe, lightweight, cross-platform Windows/Linux CLI for the OCI Always Free A1 capacity monitor and guarded single-instance launcher. Preserve the existing engine and legacy Linux helper. Do not add a GUI/dashboard or unnecessary services.

## Non-negotiable safety

- Default behavior is read-only. A launch requires all three independent guards: `mode.creation_enabled=true`, exact `LAUNCH_ONE_ALWAYS_FREE_INSTANCE` confirmation, and explicit CLI `--enable-create`.
- `--audit` and `--once` are read-only. Monitor stays read-only unless all creation guards are satisfied.
- Never create/modify networking, upgrade OCI accounts, launch non-A1 shapes, or modify/terminate existing instances.
- Never run live OCI operations, launch a VM, change billing/IAM, or alter production deployments without separate explicit authorization for that exact action.
- Never commit credentials, private keys, local config, personal OCIDs, account IDs, or production host details. Do not ask the user to paste secrets.
- Never guarantee Always Free eligibility, available capacity, or zero billing.
- Preserve backward compatibility and the legacy entry points.

## Current GitHub state — checked 2026-11-22

Repository: https://github.com/mudassir-93/OCI-Always-Free-VM

| Item | Current state |
|---|---|
| `main` | `29b66fbe83655692633b06d1c71157071969c1d6` |
| PR #5 | MERGED into `main`; squash merge commit `29b66fbe83655692633b06d1c71157071969c1d6` |
| PR #6 | OPEN, DRAFT, targeting `main`: https://github.com/mudassir-93/OCI-Always-Free-VM/pull/6 |
| PR #6 branch | `feat/cli-v1-installer-wizard` |
| PR #6 current HEAD | `4b78ee759e7ec95866abdae2a825a4d095492853` |
| PR #6 diff | 15 files, 1,287 additions, 6 deletions; only Milestone 2 installer/wizard and documentation delta |
| PR #6 mergeability | GitHub reports mergeable=true at last check |
| PR #6 CI | Fresh CI for current HEAD was queued at last check; do not merge until every required job completes successfully |
| Live cloud/production | No live OCI API call, VM launch, billing/IAM change, EC2 change, or production deployment was performed |

PR #5 was merged only after the user explicitly approved the order (#5 first, #6 second). PR #6 was retargeted to main after #5 merged. To avoid showing the already-merged foundation changes again in PR #6, main was merged into the feature branch using a normal two-parent merge commit; the branch was advanced with a fast-forward ref update (no force push). The PR diff is now the Milestone 2 delta only.

## Implemented

### Milestone 1 — PR #5, merged

- Installable Python package and `oci-platform` CLI.
- Setup, doctor, redacted config summary/validation, OCI profile list/use, VM audit/once/monitor, status, and logs.
- Thin compatibility layer over the existing engine; direct engine invocation and legacy Linux helper preserved.
- Windows/Linux process locking (`msvcrt` / `fcntl`).
- Offline tests and Windows/Linux × Python 3.11/3.12 CI.
- Existing creation guards retained.

### Milestone 2 — PR #6, pending merge

- `oci-platform configure`: local-only wizard for OCI profile, Free Tier attestation, home region, existing VCN/subnet, A1 resources/storage, SSH public-key path, Ubuntu image, usage/budget policy, retry settings, local paths, and logging.
- Enforces target region == tenancy home region and local policy caps; validates identifier prefixes and SSH public-key format.
- Timestamped backup before updating existing config.
- Wizard always forces creation disabled and clears the confirmation phrase, even if the prior config was armed.
- `install.ps1` and `install.sh`: install into a new user-owned directory, create an isolated virtual environment, install the CLI, and initialize a safe config.
- Installers refuse to overwrite an existing directory, require no admin/root, make no PATH/service changes, and do not contact OCI or create cloud resources.
- Linux and Windows installer failure/preservation integration tests.

## Validation evidence

- PR #5 exact HEAD `5b91248419182a06216f400296a9f2c0546a2be9`: all 10 check runs completed successfully (Windows/Linux × Python 3.11/3.12 plus Python checks).
- PR #6 prior exact HEAD `55ee2ad3145af0b527ce6d9cf9a427d08a24ebeb`: all 6 check runs completed successfully, including executable Windows installer safety tests and Python checks.
- PR #6 now has a new merge commit/base relationship at HEAD `4b78ee759e7ec95866abdae2a825a4d095492853`; fresh CI was queued and must be checked for this exact HEAD.
- Automated CI covers compilation, offline unit tests, CLI help/version, wheel template packaging, Linux shell syntax, PowerShell parsing, Linux installer failure cleanup/preservation, and Windows installer failure cleanup/preservation.
- A successful clean install on the user's actual Windows and Linux workstations has NOT been performed. Keep this as a manual release validation gate; do not claim 100% production validation.
- No live OCI integration, tenancy validation, VM launch, billing change, or production test has been performed.

## Exact next actions

1. Check all workflow runs/check-runs for exact PR #6 HEAD `4b78ee759e7ec95866abdae2a825a4d095492853`; wait for every required Windows/Linux and Python check to finish green.
2. Inspect the final PR #6 diff and verify it remains only the 15-file Milestone 2 delta.
3. Update PR #6 body if needed, mark it ready for review only after CI is green, then merge using the exact expected HEAD SHA. User has already explicitly approved PR #6 after PR #5, so no new approval is needed unless scope changes or a safety issue appears.
4. Verify PR #6 merged and main now contains both milestones.
5. Give the user exact Windows and Linux fresh-install commands. Observe actual workstation outputs before claiming installation success.
6. Keep all local configuration creation-disabled. Do not run OCI audit or launch a VM unless the user separately authorizes it.

## Session closeout

- Update this handoff and append a dated entry to `docs/agents/WORKLOG.md` after meaningful milestones.
- Report passed, failed, and not-run checks separately.
- State explicitly whether main, OCI resources, billing/IAM, EC2, and production were changed.
