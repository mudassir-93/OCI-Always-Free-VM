# Deploy to an Ubuntu VPS or AWS EC2 host

This guide deploys the OCI A1 monitor to a small Ubuntu Linux server. It is provider-neutral and does not assume a particular cloud account, IP address, SSH alias, or Linux username.

The project uses Python and the official OCI SDK. Docker, Node.js, Redis, PostgreSQL, and a database server are not required.

## 1. Connect to your Linux host

Use your own SSH command from your local terminal. For example:

~~~powershell
ssh YOUR_SSH_ALIAS
~~~

Never share your SSH private key.

## 2. Clone the repository

Replace OWNER/REPOSITORY with your fork or clone URL:

~~~bash
sudo mkdir -p /opt/oci-free-instance-automation
sudo chown "$USER":"$USER" /opt/oci-free-instance-automation
git clone https://github.com/OWNER/REPOSITORY.git /opt/oci-free-instance-automation
cd /opt/oci-free-instance-automation
~~~

If the directory already exists, do not delete or overwrite it blindly. Inspect and back up local configuration, runtime state, and service overrides first.

## 3. Create the Python environment

Python 3.11 or newer is recommended:

~~~bash
python3 --version
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r requirements.txt
cp config.example.json config.json
chmod 600 config.json
mkdir -p logs state
chmod 700 logs state
~~~

Install the matching python3-venv package if your distribution does not include venv support.

## 4. Configure OCI API signing-key authentication

Keep the OCI private key and SDK config outside the repository:

~~~bash
mkdir -p ~/.oci
chmod 700 ~/.oci
~~~

Generate a key pair only if you do not already have a dedicated OCI API key:

~~~bash
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
chmod 600 ~/.oci/oci_api_key.pem
chmod 644 ~/.oci/oci_api_key_public.pem
~~~

Upload only the public key to OCI Console → Profile → User Settings → API Keys. Create ~/.oci/config using the values from OCI's configuration preview:

~~~ini
[DEFAULT]
user=YOUR_USER_OCID
tenancy=YOUR_TENANCY_OCID
fingerprint=YOUR_KEY_FINGERPRINT
region=YOUR_HOME_REGION
key_file=/absolute/path/to/oci_api_key.pem
~~~

Then run chmod 600 ~/.oci/config. Never commit the OCI config or private key.

## 5. Configure the application

Edit the ignored local config.json. Configure your OCI profile, actual home region, Free Tier attestation, availability domain, existing VCN and public subnet OCIDs, A1 target resources, OS/image settings, SSH public-key path, monthly usage, and storage budgets.

Keep allow_paid_resources=false. This strict workflow rejects non-Free-Tier account settings and non-A1 shapes.

This release requires an existing public subnet, enabled Internet Gateway route, and public IPv4. It does not create or modify network resources or SSH ingress rules.

## 6. Audit and pin the image

~~~bash
. .venv/bin/activate
python oci_free_watch.py --audit
~~~

Review the compatible image candidate in OCI Console. Confirm that the exact image is labelled Always Free Eligible, then set target.image_ocid and target.image_console_always_free_confirmed=true in local config.json.

Review account billing and current-month A1 usage manually. Set account.current_month_usage_reviewed=true only after that review.

Run one capacity check:

~~~bash
python oci_free_watch.py --once
~~~

Both commands are read-only and do not launch an instance.

## 7. IAM permissions

Begin with least-privilege read access for tenancy/compartment discovery, region subscriptions, availability domains, compute instances/images, VCN/subnet/route/Internet Gateway reads, boot/block volume reads, and Limits API access. Capacity reports require the corresponding compute permission. Creation requires additional compute, VNIC, and boot-volume permissions.

Use Oracle's current IAM documentation and grant only the permissions required by enabled operations. Do not grant tenancy administrator access as a shortcut.

## 8. Install systemd (read-only default)

Review systemd/oci-free-watch.service. It uses the generic application path /opt/oci-free-instance-automation and a CHANGE_ME placeholder for the Linux service user and group.

Replace User and Group with your actual Linux account. If your project lives elsewhere, update WorkingDirectory, ExecStart, and ReadWritePaths consistently.

~~~bash
sudo cp systemd/oci-free-watch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oci-free-watch
sudo systemctl status oci-free-watch --no-pager
sudo journalctl -u oci-free-watch -f
~~~

The supplied service runs --monitor without --enable-create, so it is read-only. Stop it with:

~~~bash
sudo systemctl disable --now oci-free-watch
~~~

## 9. Optional unattended creation

Unattended creation is deliberately not enabled by the supplied unit. It requires all three application switches:
1. mode.creation_enabled=true.
2. mode.creation_confirmation=LAUNCH_ONE_ALWAYS_FREE_INSTANCE.
3. CLI argument --enable-create.

Only after reviewing the audit, billing status, current-month usage, image eligibility, IAM permissions, and configuration should an operator use a local systemd drop-in override to add --enable-create. Do not commit an armed service file or account-specific configuration.

The application cannot guarantee zero billing, host availability, or a successful launch. A capacity report does not reserve a host.

## 10. Optional Telegram notifications

Create an external root-readable environment file such as /etc/oci-free-watch.env:

~~~ini
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
~~~

The service loads this file. Never put notification credentials in Git.

## 11. Updating the application

Preserve local configuration, state, and systemd overrides before updating:

~~~bash
cd /opt/oci-free-instance-automation
git status --short
git pull --ff-only
. .venv/bin/activate
python -m pip install --no-cache-dir -r requirements.txt
python -m py_compile oci_free_watch.py
python -m unittest discover -s tests -v
~~~

Review diffs and release notes before restarting a creation-enabled service. Do not automatically restart production creation mode after an unreviewed code update.

## Host footprint

The monitor uses one Python process, rotating local logs, and a small JSON state file. Monitor disk space and memory on your host. The VPS provider may bill separately; this project does not control or verify VPS billing.
