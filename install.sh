#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY="https://github.com/mudassir-93/OCI-Always-Free-VM.git"
INSTALL_DIR="${OCI_PLATFORM_HOME:-$HOME/oci-automation-platform}"

echo "OCI Automation Platform installer"
echo "This installs local CLI files only. It does not contact your OCI tenancy or create cloud resources."

command -v git >/dev/null 2>&1 || { echo "Git is required." >&2; exit 2; }
PYTHON=""
for candidate in python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    version="$("$candidate" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
    major="${version%%.*}"
    minor="${version#*.}"
    if (( major == 3 && minor >= 11 )); then
      PYTHON="$candidate"
      break
    fi
  fi
done
[[ -n "$PYTHON" ]] || { echo "Python 3.11 or newer is required." >&2; exit 2; }

if [[ -e "$INSTALL_DIR" ]]; then
  echo "Install directory already exists: $INSTALL_DIR" >&2
  echo "The installer will not overwrite or update existing files. Set OCI_PLATFORM_HOME to a new directory." >&2
  exit 2
fi

mkdir -p "$(dirname "$INSTALL_DIR")"
git clone --depth 1 --branch main "$REPOSITORY" "$INSTALL_DIR"
cd "$INSTALL_DIR"
"$PYTHON" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/oci-platform setup

echo
echo "Installation complete: $INSTALL_DIR"
echo "Next steps:"
echo "  1. $INSTALL_DIR/.venv/bin/oci-platform configure"
echo "  2. $INSTALL_DIR/.venv/bin/oci-platform doctor"
echo "  3. $INSTALL_DIR/.venv/bin/oci-platform vm audit"
echo "VM creation remains disabled. The installer never enables it."
