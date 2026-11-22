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
| `main` | `8eebb755b0eb29230e21994eed202a01e9217977` |
| PR #5 | MERGED into `main`; merge commit `29b66fbe83655692633b06d1c71157071969c1d6` |
| PR #6 | MERGED into `main`; merge commit `8eebb755b0eb29230e21994eed202a01e9217977` |
| PR #6 branch | `feat/cli-v1-installer-wizard` |
| PR #6 merged diff | 15 files, 1,224 additions, 6 deletions |
| Main CI after PR #6 merge | NOT VERIFIED in this handoff. The available commit-status query returned no status entries, and the workflow-run connector only exposes pull-request-triggered runs. Check the GitHub Actions UI/API before claiming post-merge CI is green. |
| Fresh Windows/Linux workstation install | NOT YET PERFORMED |
| Live cloud/production | No live OCI API call, VM launch, billing/IAM change, EC2 change, or production deployment was performed |

The user explicitly approved the order: PR #5 first, then PR #6, with fresh CI green before each merge. PR #5 and PR #6 are now both confirmed closed and merged into `main`. PR #6 was retargeted and de-stacked before merge; its final merge commit is the current `main` HEAD.


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

1. Verify GitHub Actions for current `main` commit `8eebb755b0eb29230e21994eed202a01e9217977`; inspect both the CLI foundation matrix and Python checks workflow. Report each job separately.
2. Run the fresh Windows installer on the user's workstation using the commands below; observe actual output before claiming success.
3. If Windows installation succeeds, run `oci-platform --version`, `oci-platform doctor`, and inspect the generated configuration summary. Keep creation disabled.
4. Keep fresh Linux workstation installation as a separate manual validation gate if the user has a Linux machine available.
5. Do not run OCI audit or launch a VM unless the user separately authorizes the live cloud action.

Windows first-install command (PowerShell):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$env:OCI_PLATFORM_HOME = Join-Path $HOME "oci-platform"
irm https://raw.githubusercontent.com/mudassir-93/OCI-Always-Free-VM/main/install.ps1 | iex
```

Prerequisites: Git for Windows and Python 3.11 or newer. The chosen install directory must not already exist. If it does, stop and choose a different `OCI_PLATFORM_HOME`; do not delete or overwrite existing files.

## Session closeout

- Update this handoff and append a dated entry to `docs/agents/WORKLOG.md` after meaningful milestones.
- Report passed, failed, and not-run checks separately.
- State explicitly whether main, OCI resources, billing/IAM, EC2, and production were changed.
