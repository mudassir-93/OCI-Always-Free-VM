# Repository instructions for AI coding agents

This file is the shared source of truth for coding agents working in this repository. Read it before editing code, tests, configuration, deployment files, or documentation. Then read docs/agents/PROJECT_MEMORY.md for the architecture and durable project context.

## Mission

Maintain a reusable, public, multi-user OCI Always Free A1 capacity monitor and explicitly guarded single-instance launcher. The project must remain lightweight, understandable, secure, and usable by operators with different OCI tenancies and regions.

## Non-negotiable safety rules

1. Default behavior must remain read-only. Never enable instance creation by default.
2. A launch requires all three independent switches: local mode.creation_enabled=true, the exact confirmation phrase LAUNCH_ONE_ALWAYS_FREE_INSTANCE, and the CLI flag --enable-create.
3. Never change an OCI billing plan, upgrade an account, or launch a non-A1 shape.
4. Never create, modify, or delete VCNs, subnets, gateways, route tables, security lists, NSGs, reserved IPs, or existing compute resources.
5. Never terminate, resize, or modify existing instances.
6. Never hard-code or commit a user's OCIDs, tenancy/user IDs, fingerprints, image IDs, subnet IDs, SSH details, IP addresses, tokens, private keys, or local config.
7. Never ask the user to paste credentials, private keys, OCI config files, Telegram tokens, or full unredacted config files.
8. Never run commands against a real OCI tenancy or production VPS from an agent coding session unless the user explicitly requests that operation. Prefer mocks and offline tests.
9. Do not arm, start, restart, or deploy a creation-enabled systemd service without explicit user approval.
10. Do not weaken billing, quota, storage, image-confirmation, home-region, duplicate, pending-launch, or idempotency guards to make a test pass.
11. If a task requires a destructive or cost-sensitive cloud action, explain the impact and ask before proceeding.
12. Do not claim zero cost, guaranteed Always Free eligibility, guaranteed capacity, or guaranteed exactly-once launch.

## Product and architecture boundaries

- Runtime: Windows and Linux, Python 3.11+, official OCI Python SDK. The legacy Bash helper and systemd unit remain Linux-only.
- Supported compute shape: VM.Standard.A1.Flex only.
- Target region must equal the tenancy home region.
- Use an existing public subnet and existing Internet Gateway route; public IPv4 is currently required.
- User-specific values belong only in per-user application configuration and the local OCI SDK profile; never commit them.
- The new `oci-platform` CLI is a thin compatibility layer over `oci_free_watch.py`; preserve the existing engine and direct Python commands during gradual migration.
- Keep `oci-platform setup` and `configure` local-only: they must not contact OCI, create credentials, or arm creation. Setup must never overwrite an existing config; configure must create a timestamped backup before updating one.
- The configure wizard must always force `mode.creation_enabled=false` and clear the launch confirmation phrase, regardless of previous config contents.
- Installer scripts must install into a new user-owned directory, refuse to overwrite existing directories, avoid administrator/root privileges, and never start a background service or enable VM creation.
- The CLI must not display credentials or OCIDs in ordinary configuration summaries.
- Preserve cross-platform process locking; do not reintroduce unconditional POSIX-only imports.
- config.example.json must contain placeholders or generic defaults only.
- Keep the systemd unit read-only by default.
- Keep dependencies minimal. Do not add Docker, Node.js, databases, Redis, queues, or frameworks without a clear requirement and approval.
- Keep state and logs local and excluded from Git.

## Multi-user configuration rules

- Region, availability domain, VCN, subnet, image, display name, SSH public-key path, OCPU, memory, boot volume, OS/version, and monthly usage budgets must be operator-configurable.
- Validate all configurable values fail-closed against configured policy caps and live OCI limits.
- Never restore one tenancy's identifiers or region as a public default.
- Any new config field must be documented in config.example.json and README.md.
- Keep manual image Always Free Eligible confirmation because the OCI SDK does not expose that Console label as a trusted boolean.
- Keep explicit current-month usage review; account and billing status are operator attestations, not facts independently verified by this application.

## Required development workflow

1. Inspect git status, current branch, and relevant source/tests/docs before editing.
2. State the intended change and identify any safety-sensitive behavior.
3. Make the smallest coherent change; do not rewrite unrelated modules.
4. Add or update unit tests for policy and safety changes.
5. Run:
   - python oci_free_watch.py --validate-config --config config.json (when a complete local config is available)
   - python -m pip install -e .
   - python -m compileall -q oci_platform oci_free_watch.py
   - python -m unittest discover -s tests -v
   - oci-platform --help
   - oci-platform --version
   - bash -n oci-free (when changing the command wrapper)
   - bash -n install.sh (when changing the Linux installer)
   - Parse install.ps1 with PowerShell's parser (when changing the Windows installer)
   - ./oci-free test (when the local virtual environment is installed)
6. Review the diff for hard-coded identifiers, secrets, unsafe defaults, and contradictions.
7. Update README.md and docs/agents/PROJECT_MEMORY.md when behavior or architecture changes.
8. Update docs/agents/WORKLOG.md with completed work, tests, open risks, and handoff state.
9. Report exactly what changed, tests run, tests not run, and any operator action still required.

## Coding standards

- Use Python standard-library features where practical.
- Preserve type hints and clear function boundaries.
- Raise GuardError for non-retryable configuration or safety failures.
- Never log secrets or private key material.
- Avoid broad exception handling that converts safety failures into retries.
- Keep retry/backoff bounded and respectful of Retry-After.
- Preserve atomic state writes, cross-platform process locking, and OCI retry-token behavior.
- Avoid hidden side effects in audit/once commands.
- Use descriptive, operator-readable log messages without account-specific identifiers in source defaults.

## Documentation and agent memory

- Keep AGENTS.md concise and operational.
- Put durable architecture and decisions in docs/agents/PROJECT_MEMORY.md.
- Record milestones and handoffs in docs/agents/WORKLOG.md.
- Use docs/agents/START_PROMPT.md as the generic prompt users can give any coding agent.
- CLAUDE.md and GEMINI.md should remain thin wrappers around the shared instructions.
- Do not store personal user preferences, account identifiers, secrets, or deployment-specific values in committed agent memory.

## Done means

A task is not complete merely because files were edited. Relevant tests must pass, documentation must match behavior, the default must remain safe, and the final report must distinguish verified facts from assumptions.
