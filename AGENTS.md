# Agent instructions — source of truth

This is the canonical instruction set for every coding agent working in this repository. Read PROJECT_CONTEXT.md before changing code. Read relevant docs before changing deployment or OCI behaviour.

## Mission

Maintain a safe, lightweight, reusable OCI A1 capacity monitor and optionally guarded single-instance launcher. The project must remain understandable to people who have not seen the original author's tenancy or infrastructure.

## Required workflow

1. Inspect the current branch, working tree, project files, and relevant tests before editing.
2. Read PROJECT_CONTEXT.md and relevant documentation.
3. Identify scope, constraints, risks, and acceptance criteria.
4. Prefer small, reviewable changes. Do not refactor unrelated code.
5. Keep user-specific settings in ignored local config or environment files.
6. Add or update tests for every policy or behaviour change.
7. Run the validation commands below.
8. Update README/docs when user-visible behaviour changes.
9. Report changed files, tests, results, risks, and manual steps.

## Non-negotiable safety rules

- Never add real tenancy/user/compartment/VCN/subnet OCIDs, account IDs, public/private IPs, usernames, email addresses, local home paths, SSH keys, API keys, passwords, tokens, or billing screenshots to tracked files.
- Never read, print, upload, or commit config.json, ~/.oci/config, private keys, state files, logs, or secret environment files unless a task explicitly requires safe local inspection. Redact all values in reports.
- Never make live OCI API calls from unit tests or CI.
- Never enable creation, submit a launch request, upgrade an account, create paid resources, terminate resources, or modify live network/security resources unless the human explicitly authorizes that exact operation.
- Default mode must remain read-only. Sample config must keep creation disabled and the confirmation phrase empty.
- Do not remove or weaken a safety guard merely to make a test pass. Explain proposed guard changes and add tests.
- Treat capacity reports as advisory, not reservations. Never promise zero cost or guaranteed Free Tier eligibility.
- Do not rewrite Git history or force-push without explicit human approval.
- Do not run destructive cleanup on a user's VPS or cloud account.

## Architecture

- oci_free_watch.py: OCI auth, validation, audit, capacity reporting, retry, state, notifications, guarded launch.
- config.example.json: public, non-secret schema template.
- config.json: per-user local config; must remain ignored.
- oci-free: operational command wrapper.
- tests/: offline unit tests; no OCI credentials required.
- systemd/: read-only service example.
- AGENTS.md and PROJECT_CONTEXT.md: source of truth for agent work.

## Development constraints

- Keep runtime dependencies minimal. Do not add Docker, databases, Redis, Node.js, or unrelated services without a clear requirement.
- Runtime is Linux-first. Windows developers should use WSL2 for execution/tests if platform-specific modules are required.
- Keep Python typed and readable. Avoid broad exception swallowing and blind retries.
- Maintain atomic state writes, idempotency, and pending-launch safeguards.
- Make configuration errors actionable without leaking sensitive values.
- Keep user-facing documentation in clear English.

## Validation

Run:

    ./oci-free test
    .venv/bin/python -m py_compile oci_free_watch.py
    ./oci-free config-check

For changes to OCI logic, add mock-based tests. Never use --enable-create in automated validation.

## Definition of done

- Acceptance criteria are met and relevant tests pass.
- No secrets or user-specific infrastructure values were added.
- Default execution remains read-only.
- Documentation and example config match the code.
- No live cloud resource was created, changed, or deleted.
- Final report lists files changed, commands run, outcomes, and unresolved risks.

## Task request template

    Goal:
    User problem:
    Scope:
    Out of scope:
    Constraints:
    Acceptance criteria:
    Files likely involved:
    Validation:
    Approval required for:

If details are missing, inspect the repository first and ask only for a decision that blocks safe progress.
