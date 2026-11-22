## Summary

- [ ] Explain the user-facing change.
- [ ] Explain any OCI policy or launch-guard impact.

## Safety checklist

- [ ] No real OCIDs, IPs, usernames, email addresses, tokens, keys, or local paths were added.
- [ ] Default mode remains read-only.
- [ ] No live OCI API call or resource mutation was performed by tests.
- [ ] Creation guards were not weakened.
- [ ] Billing language does not promise zero cost.

## Validation

- [ ] ./oci-free test
- [ ] .venv/bin/python -m py_compile oci_free_watch.py
- [ ] ./oci-free config-check (when local config is available)
- [ ] Documentation and config example reviewed
