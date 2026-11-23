#!/usr/bin/env bash
set -Eeuo pipefail

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this integration test as an ordinary user, not root." >&2
  exit 2
fi

: "${OCI_PLATFORM_REPOSITORY:?Set OCI_PLATFORM_REPOSITORY to the repository clone URL}"
: "${OCI_PLATFORM_BRANCH:?Set OCI_PLATFORM_BRANCH to the branch to install}"

TEMP_BASE="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
SMOKE_ROOT="$(mktemp -d "${TEMP_BASE%/}/oci-platform-linux-install.XXXXXX")"
cleanup() {
  rm -rf -- "$SMOKE_ROOT"
}
trap cleanup EXIT

export OCI_PLATFORM_HOME="$SMOKE_ROOT/installation"
export XDG_CONFIG_HOME="$SMOKE_ROOT/config"
export XDG_STATE_HOME="$SMOKE_ROOT/state"
unset OCI_PLATFORM_CONFIG || true

echo "Testing Linux installer as $(id -un) (uid $(id -u))"
echo "Source: $OCI_PLATFORM_REPOSITORY ($OCI_PLATFORM_BRANCH)"

# Exercise the actual public installer in a clean, user-owned temporary path.
bash ./install.sh

CLI="$OCI_PLATFORM_HOME/.venv/bin/oci-platform"
CONFIG="$XDG_CONFIG_HOME/oci-platform/config.json"

test -x "$CLI"
"$CLI" --version
"$CLI" --help >/dev/null
"$CLI" config show >"$SMOKE_ROOT/config-summary.txt"
grep -F "Credentials and OCIDs are not displayed." "$SMOKE_ROOT/config-summary.txt" >/dev/null

python3 - "$CONFIG" <<'PY'
import json
import sys
from pathlib import Path

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
mode = config.get("mode", {})
account = config.get("account", {})
assert mode.get("creation_enabled") is False, mode
assert mode.get("creation_confirmation") == "", mode
assert account.get("account_type") == "FREE_TIER", account
assert account.get("allow_paid_resources") is False, account
print("Starter configuration is creation-disabled and Free-Tier-only.")
PY

if [[ -n "${OCI_PLATFORM_EXPECTED_SHA:-}" ]]; then
  actual_sha="$(git -C "$OCI_PLATFORM_HOME" rev-parse HEAD)"
  if [[ "$actual_sha" != "$OCI_PLATFORM_EXPECTED_SHA" ]]; then
    echo "Installed commit mismatch: expected $OCI_PLATFORM_EXPECTED_SHA, got $actual_sha" >&2
    exit 1
  fi
  echo "Installed exact requested commit: $actual_sha"
fi

# A pre-existing directory and its contents must remain untouched.
EXISTING_DIR="$SMOKE_ROOT/existing-install"
mkdir "$EXISTING_DIR"
printf '%s' "preserve-this-data" >"$EXISTING_DIR/sentinel.txt"
if OCI_PLATFORM_HOME="$EXISTING_DIR" bash ./install.sh >"$SMOKE_ROOT/existing-install.log" 2>&1; then
  echo "Installer unexpectedly accepted an existing destination." >&2
  exit 1
fi
test "$(cat "$EXISTING_DIR/sentinel.txt")" = "preserve-this-data"
grep -qi "already exists" "$SMOKE_ROOT/existing-install.log"
echo "Existing destination protection passed."

# A failed clone must remove only the incomplete directory reserved by this run.
FAILED_DIR="$SMOKE_ROOT/failed-install"
MISSING_REPOSITORY="$SMOKE_ROOT/nonexistent-repository.git"
if OCI_PLATFORM_HOME="$FAILED_DIR" OCI_PLATFORM_REPOSITORY="$MISSING_REPOSITORY" bash ./install.sh >"$SMOKE_ROOT/clone-failure.log" 2>&1; then
  echo "Installer unexpectedly accepted a nonexistent repository." >&2
  exit 1
fi
if [[ -e "$FAILED_DIR" ]]; then
  echo "Installer left its incomplete destination behind after clone failure." >&2
  exit 1
fi
grep -qi "removed incomplete installation directory" "$SMOKE_ROOT/clone-failure.log"
echo "Failed-clone cleanup passed."

echo "Linux fresh-install integration checks passed."
