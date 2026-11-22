# GitHub Copilot instructions

Follow the repository-wide rules in ../AGENTS.md and read ../docs/agents/PROJECT_MEMORY.md before architectural or safety-sensitive changes.

Key constraints:
- Keep runtime behavior read-only by default.
- Never hard-code or commit tenancy-specific IDs, credentials, SSH keys, IPs, or local config.
- Keep the A1-only, home-region, quota, storage, image-confirmation, duplicate, pending-launch, and billing-attestation guards fail-closed.
- Do not touch real OCI resources or production deployments from coding tasks without explicit user approval.
- Add/update tests and docs for behavior changes.
- Run python -m py_compile oci_free_watch.py and python -m unittest discover -s tests -v.
