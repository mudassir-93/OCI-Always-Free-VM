# Coding-agent workflow

This guide standardizes work across Codex, Claude Code, Gemini-based tools/Antigravity, GitHub Copilot, and other repository-aware agents.

## First-run instruction

Give the agent this task:

    Read AGENTS.md and PROJECT_CONTEXT.md first. Inspect the repository and current Git status. Summarize the architecture, safety boundaries, and current state. Do not change files until you have proposed a short implementation plan.

For a specific task, use the task request template in AGENTS.md.

## Recommended work cycle

### Understand

- Read AGENTS.md and PROJECT_CONTEXT.md.
- Inspect README, config.example.json, relevant implementation, and tests.
- Search for hard-coded environment values, secrets, unsafe defaults, and assumptions.
- Check the current branch and uncommitted changes.

### Plan

Produce a short plan with user-visible outcome, files to change, safety impact, tests, docs, and any human approval required.

### Implement

- Work on a feature branch.
- Keep secrets and user config out of tracked files.
- Prefer configuration over hard-coded account-specific assumptions.
- Preserve read-only defaults and the three-part creation guard.
- Do not add services or dependencies without a clear requirement.

### Validate

    ./oci-free test
    .venv/bin/python -m py_compile oci_free_watch.py
    ./oci-free config-check

For OCI API behaviour, use mocks/fakes in tests. Never submit a real capacity or launch request from CI.

### Review

Review the diff for secrets, OCIDs, IPs, usernames, email addresses, personal paths, unexpected resource mutations, billing claims, weakened launch guards, config/docs drift, and missing tests.

### Report

    Summary:
    Files changed:
    Tests run:
    Results:
    Security review:
    Operational impact:
    Human actions still required:
    Known limitations:

## Agent-specific entry points

- Codex: AGENTS.md.
- Claude Code: CLAUDE.md, which points to AGENTS.md and PROJECT_CONTEXT.md.
- Gemini CLI / Antigravity: GEMINI.md, which points to the same source of truth.
- GitHub Copilot: .github/copilot-instructions.md.
- Other agents: start with AGENTS.md.

These entry points avoid duplicated policy text. Keep AGENTS.md canonical.
