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
| Main baseline verified before this handoff sync | `3307f8f44b94c888bdd8f0b76b3746eed19f5dba` |
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
| PR #11 | Merged; recorded operator-reported second-PC Windows fresh install/TUI pass |
| PR #11 merge commit | `6c57040b458cc30c98e3920c5f572f10dc8ab8af` |
| PR #12 | Merged; added clean Linux installer integration CI and source/branch overrides |
| PR #12 merge commit | `7c5e583fe2103f8b39aee82de54dfdde2f35aa6d` |\n| PR #13 | Merged; synchronized validation and handoff records after PR #11/#12 |\n| PR #13 merge commit / main baseline | `3307f8f44b94c888bdd8f0b76b3746eed19f5dba` |
| PR #7 merge commit | `605a01ae92d57920ee116539aa8ed53eae976503` |
| CI on PR #7 merge commit | Python checks run `45108762748` passed on Python 3.11/3.12; CLI foundation run `45108762718` passed on Windows and Ubuntu with Python 3.11/3.12 |
| CI on latest verified main HEAD before PR #8 | Python checks run `45109001375` passed on Python 3.11/3.12; CLI foundation run `45109001365` passed on Windows/Ubuntu × Python 3.11/3.12 |
| CI on PR #8 exact head `dfe10f57ffb6adae34b996ae3d65b1f094b9f8ca` | Python checks run `45109638479` passed on Python 3.11/3.12; CLI foundation run `45109638472` passed on Windows/Linux × Python 3.11/3.12 |
| CI on PR #9 exact head `4d23c696f22c2b5cb6c50fb7d3ce864eb479139a` | Python checks run `45110780545` passed on Python 3.11/3.12; CLI foundation run `45110780528` passed on Windows/Linux × Python 3.11/3.12 (6/6 jobs total) |
| CI on PR #10 exact head `e6d39d94067a7261d893df5cc5a0b4d19288eb26` | Python checks run `45113875820` passed on Python 3.11/3.12; CLI foundation run `45113875739` passed on Windows/Linux × Python 3.11/3.12 (6/6 jobs total) |
| CI on PR #11 exact head `23a2528f93b232a68b7602922ebb724a19d1cc1d` | Python checks run `45116410721` passed on Python 3.11/3.12; CLI foundation run `45116410713` passed on Windows/Linux × Python 3.11/3.12 (6/6 jobs total) |
| CI on PR #12 exact head `8a3f0436b3a6988dcae5d4f620645a5596baa5bd` | Python checks run `45117728501` passed on Python 3.11/3.12; CLI foundation run `45117728426` passed on Windows/Linux × Python 3.11/3.12 (6/6 jobs total). Ubuntu/Python 3.12 additionally passed the full fresh Linux installer integration test. |\n| CI on PR #13 exact head `83e193d07b435a323b9d7771b0e5539af4893022` | Python checks run `45118315425` and CLI foundation run `45118315427` passed (6/6 jobs total). |\n| Push CI on PR #13 merge commit `3307f8f44b94c888bdd8f0b76b3746eed19f5dba` | Python checks run `45118630570` and CLI foundation run `45118630579` both passed (6/6 jobs total). |
| Fresh Windows PC install and interactive smoke test | Operator reported success on a second PC on 2026-11-23; exact OS/Python versions and test output were not captured |
| Fresh Linux installer integration | Passed on hosted Ubuntu/Python 3.12 CI for exact PR #12 head; manual physical Linux workstation test remains pending |
| Original Windows checkout update | Still pending; do not confuse the second-PC fresh install with updating the original checkout |
| Live OCI / production work | Not performed |\n| Open pull requests / issues | None found on 2026-11-23 |

PRs #5–#13 are merged. PR #8–#13 exact heads each passed the required CI before merge. PR #12 added and passed a hosted Ubuntu/Python 3.12 fresh-install integration test from the exact PR branch. PR #13 was documentation-only and merged as `3307f8f44b94c888bdd8f0b76b3746eed19f5dba`; both push-triggered main workflows then passed on that commit (6/6 jobs). No open PRs or issues were found on 2026-11-23.

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

The current plan, milestone-by-milestone completion, CI evidence, workstation validation gaps, and ordered remaining work are maintained in [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md). The operator has reported a successful fresh Windows install and interactive smoke test on a second PC. A fresh Linux install is verified in hosted Ubuntu CI for the exact PR #12 branch; PR #13 and its post-merge main CI are also green. A physical Linux workstation install, original Windows checkout update, real local OCI profile diagnostics, and live-tenancy validation remain open.

At the current review, the operator-reported second-PC Windows interactive smoke test has passed and the hosted Ubuntu fresh-install integration test has passed on PR #12. PR #13's documentation CI and the post-merge main workflows passed. The original Windows checkout has not been confirmed updated; local OCI configuration/doctor checks, a live read-only OCI audit, and a capacity run have not been performed. No VM launch, account/billing change, network provisioning, or production deployment has taken place.

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
