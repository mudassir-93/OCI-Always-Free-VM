# Deploy OCI Always Free VM monitor to your existing AWS EC2 VPS

This deploys the Python OCI monitor to the existing Ubuntu EC2 host. It is **read-only by default**. Audit and monitoring do not launch, terminate, or modify OCI resources. The repository is public, so clone over HTTPS; no GitHub deploy key is required.

## 1. Connect and clone

From Windows PowerShell:

```powershell
ssh ai
```

Then on EC2 as `ubuntu`:

```bash
sudo mkdir -p /opt/oci-free-instance-automation
sudo chown ubuntu:ubuntu /opt/oci-free-instance-automation
git clone https://github.com/mudassir-93/OCI-Always-Free-VM.git /opt/oci-free-instance-automation
cd /opt/oci-free-instance-automation
```

If that directory already exists, do not delete it blindly; inspect and back up local configuration/state first.

## 2. Python environment

```bash
python3 --version
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
cp config.example.json config.json
chmod 600 config.json
mkdir -p logs state
chmod 700 logs state
```

If venv support is missing, install Ubuntu's matching `python3-venv` package. Docker and Node.js are not needed.

## 3. OCI API signing key

Keep the OCI private key only on EC2. Never commit `~/.oci/config`, private keys, Telegram tokens, or local `config.json`.

```bash
mkdir -p ~/.oci
chmod 700 ~/.oci
```

Generate an RSA key pair only if you have not already generated one for this OCI API identity:

```bash
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
chmod 600 ~/.oci/oci_api_key.pem
chmod 644 ~/.oci/oci_api_key_public.pem
```

Upload only the public key in OCI Console → Profile → User Settings → API Keys. Add the real values from Oracle's configuration preview to `~/.oci/config`:

```ini
[DEFAULT]
user=YOUR_USER_OCID
tenancy=YOUR_TENANCY_OCID
fingerprint=YOUR_KEY_FINGERPRINT
region=me-dubai-1
key_file=/home/ubuntu/.oci/oci_api_key.pem
```

Then run `chmod 600 ~/.oci/config`. Never paste the private key into GitHub or chat.

## 4. Configure your existing network and VM settings locally

Edit the ignored local file:

```bash
nano config.json
```

Set `target.vcn_ocid` to the existing `free` VCN OCID and `target.subnet_ocid` to the subnet OCID you already created. Both are intentionally blank in the public example template.

Keep the agreed settings:
- Region: `me-dubai-1`
- AD: `svhq:ME-DUBAI-1-AD-1`
- Shape: `VM.Standard.A1.Flex`
- **2 OCPU, 4 GB RAM**
- **150 GB boot volume**
- Canonical Ubuntu 24.04 ARM64
- Public IPv4 enabled
- Paid resources disabled

Create a separate SSH key for the new Oracle VM if needed:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/oci_free_vm -C oci-free-vm
chmod 600 ~/.ssh/oci_free_vm
chmod 644 ~/.ssh/oci_free_vm.pub
```

Set `ssh_public_key_file` to `/home/ubuntu/.ssh/oci_free_vm.pub`. Keep the private half on EC2.

## 5. Read-only audit

```bash
cd /opt/oci-free-instance-automation
. .venv/bin/activate
python oci_free_watch.py --audit
python oci_free_watch.py --once
```

Start continuous read-only monitoring manually with `python oci_free_watch.py --monitor`. Review the complete audit/log output before installing systemd or considering any creation mode.

## 6. Image and billing safeguards

The audit finds a compatible Ubuntu 24.04 image candidate. The OCI SDK does not expose the Console's **Always Free Eligible** label as a definitive machine-readable property. Verify the exact candidate in OCI Console, then pin its OCID in local `target.image_ocid` and set `target.image_console_always_free_confirmed=true`.

The APIs used here do not conclusively reveal whether the tenancy billing plan has changed. The local Free Tier setting is an operator attestation, not independent proof from Oracle's billing backend. Keep the account on Free Tier and review Billing & Cost Management; do not upgrade. Uncertain image, quota, volume, billing, or network eligibility must block creation.

The app checks A1 policy, home region, CPU/memory limits, active boot/block volume usage, subnet's default route to an enabled Internet Gateway, SSH public key, monthly allowance projection, and existing instances. The storage allowance is combined across boot and block volumes, not granted separately per VM.

## 7. Optional Telegram

Telegram secrets are loaded only from environment variables. Store them outside Git:

```bash
sudo install -m 600 /dev/null /etc/oci-free-watch.env
sudo nano /etc/oci-free-watch.env
```

Add your real values locally:

```ini
TELEGRAM_BOT_TOKEN=REPLACE_LOCALLY
TELEGRAM_CHAT_ID=REPLACE_LOCALLY
```

## 8. systemd, read-only service

The supplied service runs `--monitor` without the `--enable-create` flag:

```bash
sudo cp systemd/oci-free-watch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oci-free-watch
sudo systemctl status oci-free-watch
journalctl -u oci-free-watch -f
```

Stop it with `sudo systemctl disable --now oci-free-watch`. The unit writes only to the project logs/state directories and does not edit SSH, firewall, Tailscale, Docker, or other AWS host configuration.

## 9. Pull code updates later

```bash
cd /opt/oci-free-instance-automation
git pull --ff-only
. .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
python -m py_compile oci_free_watch.py
python -m unittest discover -s tests -v
sudo systemctl restart oci-free-watch
```

## Creation mode remains disabled

Do not enable creation during first deployment. A later launch requires all three app switches: `mode.creation_enabled=true`, exact phrase `LAUNCH_ONE_ALWAYS_FREE_INSTANCE`, and CLI flag `--enable-create`, plus all successful live checks. The provided systemd unit never passes that flag. Capacity reports are advisory and do not reserve hosts.

## EC2 footprint

The existing t3.micro has about 1 GiB RAM and an 8 GB disk. This project uses Python, OCI SDK, rotating logs and a small JSON state file. It needs no Docker, Node.js, Redis, PostgreSQL, or database server. Avoid pip caches and check disk space before upgrades.
