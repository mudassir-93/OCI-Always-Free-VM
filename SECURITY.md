# Security policy

## Sensitive data

Never commit or share OCI API private keys or full OCI config files; tenancy/user/compartment/VCN/subnet OCIDs from a real account; tokens, passwords, Telegram bot tokens, chat IDs, or secret environment files; SSH private or public key files; local state, logs, IP addresses, hostnames, or personal filesystem paths.

Use config.example.json and .env.example for placeholders only. Keep config.json, ~/.oci/, state/, logs/, and real environment files local.

## If a secret is exposed

1. Treat it as compromised even if the repository is later made private or the commit is deleted.
2. Revoke/rotate the affected OCI API key or token in the provider console.
3. Review OCI audit logs and billing for unexpected activity.
4. Remove the value from current tracked files.
5. If it appeared in Git history, plan a coordinated history rewrite only after considering forks, clones, caches, and collaborators. Rewriting history does not replace credential rotation.

## Reporting

Do not publish exploitable details in a public issue. Contact the repository maintainer privately through the repository's configured security contact.
