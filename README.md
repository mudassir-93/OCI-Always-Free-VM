# OCI Always Free A1 capacity monitor

Lightweight Python monitor for the user's OCI Dubai tenancy. It uses the official OCI Python SDK and has **read-only mode by default**.

## Locked target

- Home region: `me-dubai-1`
- Availability domain: `svhq:ME-DUBAI-1-AD-1`
- Shape: `VM.Standard.A1.Flex`
- CPU: **2 OCPU**
- Memory: **4 GB**
- Image: Canonical Ubuntu 24.04 (AArch64-compatible image returned for A1)
- Boot volume: **150 GB** at standard 10 VPU/GB
- Public IPv4: enabled on an existing public subnet
- Existing VCN: the supplied `free` VCN OCID
- No automatic VCN/subnet/gateway/route/security-rule creation or changes

## Important billing boundary

The program only permits the configured A1 shape in the configured tenancy home region, requires the user's explicit Free Tier attestation, checks remaining A1 OCPU/memory through the OCI Limits API, sums existing boot and block volumes across accessible compartments and availability domains, and caps the combined volume target at 200 GB. It also checks the 1,500 OCPU-hour / 9,000 GB-hour monthly allowance against a 31-day month.

**The OCI control-plane APIs do not provide this program with a reliable, definitive switch saying that the billing account is still Free Tier and has not been upgraded.** The `account_type` and `free_tier_only_confirmed` settings are the user's assertion. The program never upgrades the account and never launches shapes other than A1, but the operator must keep the account Free Tier and check Billing & Cost Management. If OCI cannot verify the live limits or storage, creation is blocked.

This project does not create a cost reservation. A capacity report is a point-in-time report and does not reserve a host; capacity can disappear before launch.

## 1. Install on Ubuntu VPS

Copy this directory to the EC2 VPS, then:

```bash
sudo mkdir -p /opt/oci-free-instance-automation
sudo chown -R ubuntu:ubuntu /opt/oci-free-instance-automation
# Copy/extract the project files into that directory first.
cd /opt/oci-free-instance-automation
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp config.example.json config.json
chmod 600 config.json
mkdir -p logs state
```

Python 3.11+ is recommended. The project needs only the OCI SDK beyond the Python standard library.

## 2. OCI API signing-key setup

Use the dedicated OCI API key profile created for this automation. Keep the private key only on the VPS. In `~/.oci/config`, the profile should contain `user`, `tenancy`, `fingerprint`, `region`, and `key_file`.

```bash
mkdir -p ~/.oci
chmod 700 ~/.oci
# Generate once only if you have not already created a key for this OCI user:
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
chmod 600 ~/.oci/oci_api_key.pem
# After creating ~/.oci/config from Oracle's config preview:
chmod 600 ~/.oci/config
```

Upload only `oci_api_key_public.pem` in OCI Console → Profile → User Settings → API Keys. Add Oracle's fingerprint and the OCIDs to `~/.oci/config` using the values from Oracle's configuration preview. Never copy the private key into this project or send it in chat.

## 3. Fill application config

Edit `config.json`:

1. Keep the supplied Dubai region, AD, and VCN OCID. Leave `subnet_ocid` blank only if the VCN has exactly one public subnet; otherwise copy the subnet OCID you just created from OCI Console.
2. Create an SSH key pair on the VPS if you do not already have one, and set `ssh_public_key_file` to the `.pub` file. The private half must remain private.
3. Run `--audit`. It reports the newest compatible Canonical Ubuntu 24.04 image candidate and its OCID.
4. In OCI Console, open that exact image and verify it is labelled **Always Free Eligible**. Then copy its OCID to `target.image_ocid` and set `target.image_console_always_free_confirmed` to `true`.
5. Keep `creation_enabled` false. The image confirmation flag is an operator attestation because the OCI SDK Image model does not expose that Console label as a machine-readable property.

Example SSH key (only if you need a separate key):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/oci_free_vm -C oci-free-vm
chmod 600 ~/.ssh/oci_free_vm
chmod 644 ~/.ssh/oci_free_vm.pub
```

## 4. Read-only checks

Run one read-only audit:

```bash
. .venv/bin/activate
python oci_free_watch.py --audit
```

Run one audit plus one capacity check:

```bash
python oci_free_watch.py --once
```

Continuous read-only monitoring:

```bash
python oci_free_watch.py --monitor
```

`--audit` and `--once` do not launch an instance, even if the configuration is later changed. Review the logs and fix any missing read permissions or network configuration before moving on.

## 5. IAM permissions

Start with read-only access for the automation user/group. It needs permission to inspect tenancy/compartments, read compute instances and images, read VCN/subnet/route-table/Internet Gateway resources, read boot/block volumes, read region subscriptions, and query resource availability/limits. OCI's exact policy verbs can vary by operation; use Oracle's Core Services and Limits policy references and grant only what is needed.

For capacity reports, ensure the identity is authorized for the capacity-report operation. Do not grant broad tenancy administrator privileges merely to make the script pass. The launch phase needs additional create/attach permissions and should be added only after the read-only audit is clean.

## 6. Creation guard (do not enable during first tests)

Creation is disabled unless **all** conditions below are true:

- `mode.creation_enabled` is set to `true` in `config.json`.
- `mode.creation_confirmation` is set to exactly `LAUNCH_ONE_ALWAYS_FREE_INSTANCE`.
- The process is started with `--enable-create`.
- The home-region, A1 shape/CPU/RAM, live quota, total storage, subnet route, SSH key, monthly allowance and duplicate checks all pass.
- The exact Ubuntu image OCID is pinned in `target.image_ocid`, and you manually confirm its Console **Always Free Eligible** label by setting `target.image_console_always_free_confirmed=true`.

Only then can the script submit exactly one A1 launch request. It writes a pending/idempotency record before calling LaunchInstance, adopts an existing matching instance rather than creating a duplicate, and never terminates or modifies existing resources.

To arm manually after reviewing a successful audit:

```bash
# Edit config.json: creation_enabled=true and the exact confirmation phrase.
python oci_free_watch.py --monitor --enable-create
```

The supplied systemd unit deliberately does **not** pass `--enable-create`. Do not change it unless you intentionally want unattended launch attempts after completing the review.

## 7. Optional Telegram notifications

Set these environment variables in `/etc/oci-free-watch.env` (not in source code or Git):

```bash
sudo install -m 600 /dev/null /etc/oci-free-watch.env
sudo nano /etc/oci-free-watch.env
```

Add the following lines, save, then restart the service after it is installed:

```ini
TELEGRAM_BOT_TOKEN=REPLACE_LOCALLY
TELEGRAM_CHAT_ID=your_chat_id
```

The systemd unit loads this file. Keep it root-readable only. Notifications are optional; the monitor continues if Telegram is unavailable.

## 8. systemd (read-only by default)

After reviewing the unit paths and confirming the Linux account is `ubuntu`:

```bash
sudo cp systemd/oci-free-watch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oci-free-watch
sudo systemctl status oci-free-watch
journalctl -u oci-free-watch -f
```

The unit writes only to this project directory's `logs/` and `state/` directories and does not edit SSH, firewall, Tailscale, Docker, or other AWS system configuration.

## Retry policy

Default capacity poll is 20 minutes. Backoff is exponential and capped at 180 minutes, with ±15% jitter. HTTP 429 and 5xx are treated as transient; a `Retry-After` header is observed where present. Authentication, authorization, invalid configuration, quota, and other non-transient 4xx errors stop the process for manual intervention. There is no tight retry loop.

## Limitations / operator checks

- Capacity reports are advisory; they do not reserve capacity.
- The program cannot verify a billing plan upgrade status through the OCI APIs used here; keep the tenancy on Free Tier and review Billing & Cost Management. The `account_type` and confirmation flags are operator attestations, not proof from Oracle's billing backend.
- Monthly A1 usage may include prior usage from earlier instances in the same billing month. `other_monthly_a1_ocpu_hours` and `other_monthly_a1_memory_gb_hours` must reflect any such usage; keep them at zero only if that is accurate.
- OCI Limits API must expose the A1 CPU and memory remaining values to the automation identity for creation to be enabled. If not, the script intentionally blocks launch.
- The SDK can enumerate Ubuntu 24.04 images compatible with A1, but it does not expose the Console's Always Free Eligible label. Pin the image OCID only after verifying that label in Console; the script blocks launch without this manual confirmation.
- Public SSH reachability also requires a suitable ingress rule on the subnet security list or an NSG. The app does not create or change those rules; restrict SSH to your IP or use Tailscale.

## Deploy to the existing AWS EC2 VPS

See [`docs/DEPLOY_EC2.md`](docs/DEPLOY_EC2.md). The repository contains no OCI credentials or private keys. `config.json`, logs, and runtime state stay on EC2 and are excluded by `.gitignore`.
