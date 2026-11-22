# Security policy

## Sensitive information

Never commit:
- OCI API private keys or full OCI SDK config files.
- Real tenancy, user, compartment, VCN, subnet, image, or other account-specific OCIDs.
- API tokens, passwords, Telegram bot tokens/chat IDs, or secret environment files.
- SSH private/public key files, host IPs, hostnames, or local account paths.
- Local config.json, runtime state, logs, or backups containing account data.

Use config.example.json and .env.example only for placeholders. Keep ~/.oci/, config.json, state/, logs/, and real environment files outside version control.

## If a secret is exposed

1. Treat it as compromised even if the file is deleted or the repository becomes private.
2. Revoke or rotate the affected OCI API key, token, or credential in its provider console.
3. Review OCI audit activity and billing for unexpected actions.
4. Remove the exposed value from the current tracked tree.
5. If it appeared in Git history, coordinate a history rewrite only after considering forks, clones, caches, and collaborators. History cleanup never replaces credential rotation.

## Reporting

Do not publish exploitable details in a public issue. Use the repository maintainer's private security contact if one is configured.
