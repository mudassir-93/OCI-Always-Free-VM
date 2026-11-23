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
| `main` code merge | PR #7 merge commit `605a01ae92d57920ee116539aa8ed53eae976503` (a documentation-only handoff update may advance the branch) |
| PR #5 | MERGED into `main`; merge commit `29b66fbe83655692633b06d1c71157071969c1d6` |
| PR #6 | MERGED into `main`; merge commit `8eebb755b0eb29230e21994eed202a01e9217977` |
| PR #7 | MERGED into `main`; https://github.com/mudassir-93/OCI-Always-Free-VM/pull/7 |
| PR #6 branch | `feat/cli-v1-installer-wizard` |
| PR #6 merged diff | 15 files, 1,224 additions, 6 deletions |
| PR #7 post-merge main CI | PASS on merge commit `605a01ae92d57920ee116539aa8ed53eae976503`: Python checks run 45108762748 and CLI foundation run 45108762718; all Windows/Linux Python 3.11/3.12 jobs succeeded. |
| Fresh Windows/Linux workstation install | NOT YET PERFORMED |
| Live cloud/production | No live OCI API call, VM launch, billing/IAM change, EC2 change, or production deployment was performed |

The user explicitly approved the order: PR #5 then PR #6, followed by the interactive CLI UX implementation. PR #5, PR #6, and PR #7 are all closed and merged into `main`. PR #7 merge commit: `605a01ae92d57920ee116539aa8ed53eae976503`. Both required post-merge workflows passed on this exact code merge commit.


## Interactive terminal UX — PR #7 (merged into main)

- Branch: feat/interactive-cli-ux.
- Added a Questionary arrow-key home menu for no-argument interactive terminal use; menu actions are local-only and do not initiate OCI operations.
- Added grouped, field-by-field configure editor with current values, selectable OCI SDK profile names, home-region auto-sync, validation feedback, review-before-save, backup, cancel, and safe Ctrl+C/EOF handling.
- Retained line-oriented setup as oci-platform configure --plain and as the non-TTY fallback.
- Added validation for local OCI SDK file/profile, region shape/match, AD, VCN/subnet/image OCID prefixes, SSH public-key file, A1-only shape, supported OS and boot volume performance, whole-number resource sizing, usage and policy limits.
- Successful configure saves always force FREE_TIER, paid resources disabled, VM creation disabled, and clear the launch phrase.
- Adds pinned dependency questionary==2.1.1 and offline tests for editor validation, backup, cancellation, home-menu routing, and EOF behavior.
- CI evidence: implementation/test commit 1ba41480d4314a789775f12826b8994489830ef1 passed Python checks run 45108231189 and CLI foundation run 45108231166. Both Python checks (3.11/3.12) passed; the full CLI matrix passed on Windows and Ubuntu with Python 3.11/3.12, including installer safety integration, offline tests, wheel packaging, and CLI entrypoint checks. An earlier Windows cp1252 encoding failure was fixed and covered by tests. A documentation-only update may trigger newer workflows; check the live PR head and both workflows before merging.
- No local workstation update has been applied yet. User's existing starter config remains at %APPDATA%\oci-platform\config.json, and VM creation was observed disabled.
- No OCI API calls, VM launches, billing/IAM/network changes, production deployments, or main-branch changes were made for PR #7.
## Implemented

### Milestone 1 — PR #5, merged

- Installable Python package and `oci-platform` CLI.
- Setup, doctor, redacted config summary/validation, OCI profile list/use, VM audit/once/monitor, status, and logs.
- Thin compatibility layer over the existing engine; direct engine invocation and legacy Linux helper preserved.
- Windows/Linux process locking (`msvcrt` / `fcntl`).
- Offline tests and Windows/Linux × Python 3.11/3.12 CI.
- Existing creation guards retained.

### Milestone 2 — PR #6, merged

- `oci-platform configure`: local-only wizard for OCI profile, Free Tier attestation, home region, existing VCN/subnet, A1 resources/storage, SSH public-key path, Ubuntu image, usage/budget policy, retry settings, local paths, and logging.
- Enforces target region == tenancy home region and local policy caps; validates identifier prefixes and SSH public-key format.
- Timestamped backup before updating existing config.
- Wizard always forces creation disabled and clears the confirmation phrase, even if the prior config was armed.
- `install.ps1` and `install.sh`: install into a new user-owned directory, create an isolated virtual environment, install the CLI, and initialize a safe config.
- Installers refuse to overwrite an existing directory, require no admin/root, make no PATH/service changes, and do not contact OCI or create cloud resources.
- Linux and Windows installer failure/preservation integration tests.

## Validation evidence

- PR #5 exact HEAD `5b91248419182a06216f400296a9f2c0546a2be9`: all 10 pre-merge checks completed successfully (Windows/Linux × Python 3.11/3.12 plus Python checks).
- PR #6 exact pre-merge HEAD `4b78ee759e7ec95866abdae2a825a4d095492853`: previous session reported all six required checks green before merge.
- PR #6 merged as `8eebb755b0eb29230e21994eed202a01e9217977`; this is confirmed as current `main` HEAD.
- Post-merge CI for the current `main` commit is not verified here. The GitHub commit-status lookup returned an empty status list; the available workflow-run lookup filters to pull-request-triggered runs and therefore did not expose the push-triggered main run. Do not infer success or failure from the empty response.
- Automated CI in the repository covers compilation, offline unit tests, CLI help/version, wheel template packaging, Linux shell syntax, PowerShell parsing, Linux installer failure cleanup/preservation, and Windows installer failure cleanup/preservation.
- A successful clean install on the user's actual Windows and Linux workstations has NOT been performed. Keep this as a manual release validation gate; do not claim production readiness.
- No live OCI integration, tenancy validation, VM launch, billing change, or production test has been performed.

## Exact next actions

1. Update the existing Windows clone in place. Do not rerun install.ps1 because the installer intentionally refuses an existing directory.
2. In PowerShell, first check for local source edits:

   ```powershell
   Set-Location "$HOME\oci-automation-platform"
   git status --short
   ```

   If this prints any files, stop and review them before pulling. If it prints nothing, continue:

   ```powershell
   git pull --ff-only origin main
   .\.venv\Scripts\python.exe -m pip install -e .
   & .\.venv\Scripts\oci-platform.exe --version
   & .\.venv\Scripts\oci-platform.exe
   ```

3. The last command opens the new arrow-key home menu. Select Configure / edit settings to start the local editor. Your existing app configuration remains at %APPDATA%\oci-platform\config.json; do not delete or recreate it.
4. The OCI SDK config file must exist locally before the editor can validate a complete configuration. Enter the path to that file in the UI; do not paste credentials or private keys into chat.
5. Manually smoke-test arrow keys, selecting/editing a single field, home-region auto-sync, back/cancel, review/save, and Ctrl+C. Keep VM creation disabled. Do not run a live OCI audit or launch during the UI smoke test.

## Session closeout

- Update this handoff and append a dated entry to docs/agents/WORKLOG.md after meaningful milestones.
- Report passed, failed, and not-run checks separately.
- State explicitly whether main, OCI resources, billing/IAM, EC2, and production were changed.
