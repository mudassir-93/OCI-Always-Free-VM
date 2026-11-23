# AI session handoff — OCI Always Free A1 VM Automation

> Read this file first when continuing work. GitHub `main`, live pull-request metadata, and the latest CI runs are authoritative. Historical milestones belong in `docs/agents/WORKLOG.md`.

## Mission

Maintain a lightweight, cross-platform Windows/Linux CLI for monitoring OCI Ampere A1 capacity and optionally requesting one guarded A1 VM. Preserve the existing engine, direct Python entry point, and legacy Linux helper. Keep the product CLI-first; do not add a GUI, dashboard, database, Redis, or other unnecessary services.

## Safety boundaries

- Default behavior is read-only.
- VM creation requires all three independent guards: `mode.creation_enabled=true`, the exact phrase `LAUNCH_ONE_ALWAYS_FREE_INSTANCE`, and the explicit CLI flag `--enable-create`.
- `--audit` and `--once` are read-only. Monitoring remains read-only unless all creation guards are deliberately enabled.
- Never create or modify networking, upgrade an OCI account, launch a non-A1 shape, or modify/terminate an existing instance.
- Never run live OCI operations, launch a VM, change billing/IAM, or alter a production deployment without separate explicit authorization for that exact action.
- Never commit credentials, private keys, local config, personal OCIDs, account identifiers, or production host details. Never ask the user to paste secrets.
- Never claim guaranteed Always Free eligibility, zero billing, capacity, or exactly-once launch behavior.
- Preserve backward compatibility and all existing policy, quota, storage, image, duplicate, retry-token, and pending-launch safeguards.

## Current GitHub state — verified 2026-11-23

Repository: https://github.com/mudassir-93/OCI-Always-Free-VM

| Item | Verified state |
|---|---|
| Default branch | `main` |
| Latest main commit inspected for project status | `e60bbc76854b5a712f72a5c63ff6a1e5ee1f884b` |
| PR #8 release merge commit | `948fc148a416556f25900600c21223605e4f3066` (squash merge into `main`) |
| PR #5 | Merged; CLI foundation |
| PR #6 | Merged; installer and guided configuration |
| PR #7 | Merged; interactive terminal home menu and grouped editor |
| PR #8 | Merged; README release status and consolidated AI handoff |
| PR #8 merge commit | `948fc148a416556f25900600c21223605e4f3066` |
| PR #9 | Merged; consolidated project progress tracker and roadmap |
| PR #9 merge commit | `fb46199e16739f30edd5045b7a4282b275cc3bfb` |
| PR #10 | Merged; synchronized handoff and project tracker after PR #9 |
| PR #10 merge commit | `e60bbc76854b5a712f72a5c63ff6a1e5ee1f884b` |
| PR #7 merge commit | `605a01ae92d57920ee116539aa8ed53eae976503` |
| CI on PR #7 merge commit | Python checks run `45108762748` passed on Python 3.11/3.12; CLI foundation run `45108762718` passed on Windows and Ubuntu with Python 3.11/3.12 |
| CI on latest verified main HEAD before PR #8 | Python checks run `45109001375` passed on Python 3.11/3.12; CLI foundation run `45109001365` passed on Windows/Ubuntu × Python 3.11/3.12 |
| CI on PR #8 exact head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca` | Python checks run `45109638479` passed on Python 3.11/3.12; CLI foundation run `45109638472` passed on Windows/Linux × Python 3.11/3.12 |
| CI on PR #9 exact head `4d23c696f22c2b5cb6c50fb7d3ce864eb479139a` | Python checks run `45110780545` passed on Python 3.11/3.12; CLI foundation run `45110780528` passed on Windows/Linux × Python 3.11/3.12 (6/6 jobs total) |
| CI on PR #10 exact head `e6d39d94067a7261d893df5cc5a0b4d19288eb26` | Python checks run `45113875820` passed on Python 3.11/3.12; CLI foundation run `45113875739` passed on Windows/Linux × Python 3.11/3.12 (6/6 jobs total) |
| Fresh Windows PC install and interactive smoke test | Operator reported success on a second PC on 2026-11-23; exact OS/Python versions and test output were not captured |
| Original Windows checkout update | Still pending; do not confuse the second-PC fresh install with updating the original checkout |
| Live OCI / production work | Not performed |

PRs #5–#10 are merged. PR #8, PR #9, and PR #10 exact heads passed both required workflows before their squash merges. PR #10 exact head was `e6d39d94067a7261d893df5cc5a0b4d19288eb26`; merge commit `e60bbc76854b5a712f72a5c63ff6a1e5ee1f884b`. The available commit lookup did not expose a separate post-merge push-triggered run for PR #10's merge commit, so do not describe post-merge CI as verified.

## Implemented product

### CLI foundation — PR #5

- Installable Python package and `oci-platform` command.
- Local setup, diagnostics, redacted configuration summary/validation, OCI profile list/use, VM audit/once/monitor, local status, and logs.
- Thin CLI adapter over the established `oci_free_watch.py` engine.
- Cross-platform process locking and Windows/Linux × Python 3.11/3.12 CI.

### Installer and guided configuration — PR #6

- Local-only `oci-platform configure` wizard.
- Windows PowerShell and Linux shell installers that use a new user-owned directory, refuse to overwrite existing installations, and do not require elevation.
- Install/setup do not call OCI, create cloud resources, install services, or enable VM creation.
- Existing configuration is backed up before wizard saves.

### Interactive terminal UX — PR #7

- Running `oci-platform` in an interactive terminal opens an arrow-key home menu with local-only actions.
- Grouped field-by-field configuration editor with current values, back navigation, local validation, review-before-save, timestamped backup, cancel, and Ctrl+C/EOF handling.
- Target region follows the tenancy home region.
- OCI profile selection displays profile names only, never credential values.
- `oci-platform configure --plain` and the non-TTY fallback retain line-oriented operation.
- Every successful editor save forces Free Tier settings, disables paid resources, sets `mode.creation_enabled=false`, and clears the launch phrase.
- Questionary is pinned at `2.1.1`.

## Validation limits and remaining work

The current plan, milestone-by-milestone completion, CI evidence, workstation validation gaps, and ordered remaining work are maintained in [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md). The code-delivery milestones are complete. The operator has now reported a successful fresh Windows install and interactive smoke test on a second PC; fresh Linux installation, the original Windows checkout update, real local OCI profile diagnostics, and live-tenancy validation remain open.

At the last review, the existing Windows checkout had not been updated to the latest main branch, interactive Windows Terminal testing had not been performed, local OCI application configuration had not been completed/verified, and no live OCI audit or capacity run had been performed. No VM launch, account/billing change, network provisioning, or production deployment has taken place.

Do not describe the project as end-to-end or production validated until the workstation and user-approved OCI validation steps in the project status report are completed.

## Exact next actions when the Windows PC is available

The known checkout is `$HOME\oci-automation-platform` and the app config is stored separately under `%APPDATA%\oci-platform\config.json`. Preserve the existing config. Do not rerun the installer.

In PowerShell:

```powershell
Set-Location "$HOME\oci-automation-platform"

# Stop if local source changes exist.
$status = @(git status --porcelain)
if ($status.Count -gt 0) {
    $status
    throw "Local changes found. Review them before updating."
}

$branch = git branch --show-current
if ($branch -ne "main") {
    throw "Expected main branch, found: $branch"
}

git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw "Git update failed." }

& .\.venv\Scripts\python.exe -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw "Application update failed." }

& .\.venv\Scripts\oci-platform.exe --version
& .\.venv\Scripts\oci-platform.exe
```

Use the home menu's **Configure / Edit settings** action. Keep VM creation disabled. Do not run a live OCI audit or launch during the UI smoke test. Never paste OCI credentials, private keys, or the full local config into chat.

## Session closeout

After each meaningful milestone:
- Update this handoff and append a dated entry to `docs/agents/WORKLOG.md`.
- Report passed, failed, and not-run checks separately.
- State explicitly whether local workstation files, `main`, OCI resources, billing/IAM, EC2, or production were changed.
