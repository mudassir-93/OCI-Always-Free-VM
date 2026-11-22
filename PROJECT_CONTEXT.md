# Project context and durable memory

## Product purpose

This repository contains a lightweight OCI A1 capacity monitor. It checks whether a configured A1 Flex VM can be provisioned in the tenancy home region and can optionally submit one launch request after explicit human authorization and live safety checks.

It is a reusable project, not a record of one person's cloud account. No specific tenancy, region, availability domain, VCN, subnet, user identity, public IP, or SSH key is assumed by the source repository.

## Core user workflow

1. Install on a small Linux VPS or server.
2. Configure a local OCI API signing-key profile.
3. Copy config.example.json to config.json and enter tenancy-specific values.
4. Review quotas, billing status, monthly usage, network, SSH key, and image eligibility in OCI Console.
5. Run config checks, tests, and a read-only OCI audit.
6. Optionally run read-only capacity monitoring.
7. Only after explicit human approval, enable all three creation switches and run guarded launch mode.
8. Verify the resulting instance in OCI Console and connect over SSH.

## Current implementation boundaries

- Only VM.Standard.A1.Flex is supported.
- Supported OS image family is Canonical Ubuntu 24.04.
- Region must be the tenancy home region.
- Existing VCN/subnet/network resources are inspected but never created or changed.
- Public IPv4 is currently required by the policy and launch configuration.
- CPU, memory, and boot volume sizes are configurable within operator-entered policy caps and live OCI checks.
- Quota, storage, monthly usage, image confirmation, duplicate detection, and pending launch state are launch guards.
- Creation is disabled by default in the public example configuration.
- The OCI SDK cannot conclusively prove billing plan status or guarantee zero charges.

## Safety and billing model

Account billing plan, shape eligibility, tenancy quota, monthly allowance, boot/block storage usage, image eligibility, and physical host capacity are separate concerns. Passing one does not prove the others. FREE_TIER settings and confirmation booleans are operator attestations, not Oracle billing-backend evidence.

Operators must independently review current Oracle terms, Console labels, quota, usage, and Billing & Cost Management. AWS or other hosting costs are separate.

## Configuration ownership

All account-specific values belong in local config.json, ~/.oci/config, environment files, or local SSH key files. Those files must never be committed. The example template contains placeholders and safe defaults only.

## Agent expectations

Coding agents should read AGENTS.md first, then this file. Use docs/AGENT_WORKFLOW.md for task planning and completion reporting. Never perform live cloud operations or history rewrites without explicit human approval.
