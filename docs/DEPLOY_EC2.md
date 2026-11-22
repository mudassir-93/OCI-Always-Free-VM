# Deploy on an Ubuntu VPS or AWS EC2 instance

This guide is provider-neutral. The application runs on a small Linux VM and calls OCI APIs; it does not run an LLM or require Docker.

## 1. Connect to your Linux host

Connect using the SSH command, username, hostname, and key configured for your own server. Do not put private keys in this repository.

## 2. Install the project

Choose a stable directory in your home folder:

    cd "$HOME"
    git clone https://github.com/OWNER/REPOSITORY.git oci-free-instance-automation
    cd oci-free-instance-automation

If the directory already exists, inspect and back up local config and state before updating it. Never delete config.json or state/ as part of a routine update.

Run:

    ./oci-free setup

This creates a Python virtual environment, installs the OCI SDK, copies the generic config template only when config.json is absent, and creates local logs/state directories.

## 3. Configure OCI API authentication

Use a dedicated OCI API identity with least-privilege permissions. Create an API signing key following Oracle's current documentation. Keep the private key and ~/.oci/config on the Linux host only.

The OCI profile needs user, tenancy, fingerprint, region, and key_file values. Restrict the config and private key permissions:

    chmod 700 ~/.oci
    chmod 600 ~/.oci/config ~/.oci/oci_api_key.pem

Never upload the private key or full OCI config to GitHub, an agent, or a chat.

## 4. Configure the application

Edit config.json locally. The file is ignored by Git.

Set account.home_region and target.region to your tenancy home region. Set the availability domain returned by OCI for that region, your existing VCN OCID, and the subnet OCID if you want to pin a specific subnet.

Confirm live quotas in OCI Console and set account.a1_free_max_ocpu and account.a1_free_max_memory_gb no higher than the limits you actually have. Review the combined boot/block volume allowance and current month's usage. Sample config values are examples, not a claim that every tenancy has those quotas.

Create an SSH key pair if required and set target.ssh_public_key_file to the public-key file ending in .pub. Do not point it at the private key.

Run:

    ./oci-free config-check
    ./oci-free test
    ./oci-free audit

The audit must pass before you consider continuous monitoring. Fix IAM permissions or network configuration manually in OCI Console; this application does not modify network resources.

## 5. Verify Ubuntu image eligibility

The application discovers a Canonical Ubuntu 24.04 image compatible with A1. The OCI SDK does not expose the Console's Always Free Eligible label as a definitive machine-readable field. Verify the exact image manually in OCI Console, pin its OCID in target.image_ocid, and set target.image_console_always_free_confirmed=true only after checking it.

## 6. Read-only systemd service

The repository's systemd service template is configured for read-only monitoring. Review its user, working directory, and Python paths before installing. The example assumes the project is in:

    $HOME/oci-free-instance-automation

Copy the template and edit User, Group, WorkingDirectory, ExecStart, and ReadWritePaths for your Linux user and installation path:

    sudo cp systemd/oci-free-watch.service /etc/systemd/system/
    sudo nano /etc/systemd/system/oci-free-watch.service
    sudo systemctl daemon-reload
    sudo systemd-analyze verify /etc/systemd/system/oci-free-watch.service

Only after verifying the effective ExecStart contains --monitor and does not contain --enable-create, enable the service:

    sudo systemctl enable --now oci-free-watch
    sudo systemctl status oci-free-watch --no-pager
    sudo journalctl -u oci-free-watch -f

The service is read-only by default. Never add --enable-create unless you have separately reviewed and explicitly approved an actual launch attempt.

To stop the service:

    sudo systemctl disable --now oci-free-watch

## 7. Optional Telegram notifications

Create an environment file outside the repository, for example /etc/oci-free-watch.env, and restrict it to root:

    sudo install -m 600 /dev/null /etc/oci-free-watch.env
    sudo nano /etc/oci-free-watch.env

Add your own token and chat ID as environment variables. Never commit them.

## 8. Updating safely

Before updating, preserve local config and state:

    cd "$HOME/oci-free-instance-automation"
    cp -a config.json config.json.backup
    cp -a state state.backup 2>/dev/null || true

Review the release notes and Git diff, then pull only the intended branch. Update dependencies and run tests:

    git pull --ff-only
    .venv/bin/python -m pip install --no-cache-dir -r requirements.txt
    ./oci-free test
    .venv/bin/python -m py_compile oci_free_watch.py

Restart systemd only after reviewing the change and confirming the service configuration is still correct:

    sudo systemctl restart oci-free-watch

## Resource footprint

The application uses Python, the OCI SDK, rotating logs, a small JSON state file, and one process lock. It does not require Docker, Node.js, Redis, PostgreSQL, or a database. Monitor disk space and your VPS provider's billing separately.
