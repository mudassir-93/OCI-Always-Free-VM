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
| Latest verified main HEAD | `948fc148a416556f25900600c21223605e4f3066` (PR #8 squash merge) |
| PR #5 | Merged; CLI foundation |
| PR #6 | Merged; installer and guided configuration |
| PR #7 | Merged; interactive terminal home menu and grouped editor |
| PR #8 | Merged; README release status and consolidated AI handoff |
| PR #8 merge commit | `948fc148a416556f25900600c21223605e4f3066` |
| PR #7 merge commit | `605a01ae92d57920ee116539aa8ed53eae976503` |
| CI on PR #7 merge commit | Python checks run `45108762748` passed on Python 3.11/3.12; CLI foundation run `45108762718` passed on Windows and Ubuntu with Python 3.11/3.12 |
| CI on latest verified main HEAD before PR #8 | Python checks run `45109001375` passed on Python 3.11/3.12; CLI foundation run `45109001365` passed on Windows/Ubuntu × Python 3.11/3.12 |
| CI on PR #8 exact head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca` | Python checks run `45109638479` passed on Python 3.11/3.12; CLI foundation run `45109638472` passed on Windows/Linux × Python 3.11/3.12 |
| Local Windows update and interactive smoke test | Pending; the operator's PC is not currently available |
| Live OCI / production work | Not performed |

PRs #5–#8 are merged. PR #8's exact head passed both required workflows before squash merge. The GitHub status lookup used here does not expose the push-triggered post-merge workflow runs, so do not infer post-merge CI from an empty status response; verify the Actions page if that distinction is required.

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

Automated CI covers compilation, offline unit tests, CLI entry points, packaging, Linux shell syntax, PowerShell parsing, and installer safety integration tests. It does not replace a real interactive session on the operator's Windows Terminal.

Still pending:
1. Update the existing Windows checkout in place.
2. Manually smoke-test arrow-key navigation, field editing, home-region auto-sync, back/cancel, review/save, and Ctrl+C.
3. Run local `oci-platform doctor` after the operator completes local settings.
4. Only consider a read-only live OCI audit after the user has deliberately approved that live cloud operation.

Do not call the project fully workstation-validated until the real Windows interaction is observed. No live tenancy test or VM launch is part of this UI validation.

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
