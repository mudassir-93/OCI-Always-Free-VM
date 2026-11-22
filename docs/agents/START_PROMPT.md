# Universal coding-agent start prompt

Copy this prompt into Codex, Claude Code, Antigravity, Gemini, Cursor, Copilot, or another coding agent after opening this repository:

~~~text
Read AGENTS.md and docs/agents/PROJECT_MEMORY.md first. Read README.md and inspect the repository structure, git status, current branch, and relevant tests before changing anything.

You are helping maintain this public, multi-user OCI Always Free A1 VM automation project and its cross-platform `oci-platform` CLI. First summarize the architecture, safety model, current implementation state, and the task you believe I am asking for. Preserve the existing Python engine and legacy commands during gradual CLI migration. Then make a focused implementation plan and execute it.

Preserve read-only-by-default behavior and all Free Tier, A1-only, home-region, quota, storage, image-confirmation, current-usage, duplicate-launch, pending-state, and idempotency safeguards. Never hard-code or commit real OCI identifiers, credentials, private keys, IPs, or local configuration. Never run commands against a real OCI tenancy or production VPS, enable instance creation, or alter cloud resources unless I explicitly authorize that exact action.

Add or update tests for behavior changes. Run:
- python -m pip install -e .
- python -m compileall -q oci_platform oci_free_watch.py
- python -m unittest discover -s tests -v
- oci-platform --help
- oci-platform --version

Update README.md and docs/agents/PROJECT_MEMORY.md when behavior changes. Update docs/agents/WORKLOG.md with what changed, validation results, risks, and the next handoff. Finish with a concise report of files changed, tests passed/failed/not run, and any manual operator steps.
~~~

## Short follow-up prompt

"Continue from AGENTS.md and docs/agents/PROJECT_MEMORY.md. Inspect the current branch and worklog, then complete the next safe project task. Do not touch live OCI resources or production deployment."
