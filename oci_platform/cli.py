"""Cross-platform CLI entry point for OCI Automation Platform.

The CLI is deliberately a thin layer over the established OCI automation
engine. Cloud operations retain the engine's existing validation and guards.
"""
from __future__ import annotations

import argparse
import configparser
import json
import math
import os
import shutil
import sys
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from . import __version__


def default_config_path() -> Path:
    """Return the per-user configuration path without requiring extra packages."""
    override = os.environ.get("OCI_PLATFORM_CONFIG")
    if override:
        return Path(override).expanduser()

    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "oci-platform" / "config.json"


def default_state_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", Path.home())))
    else:
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "oci-platform"


def read_config(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(
            f"Configuration not found: {path}. Run 'oci-platform setup' first."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("Configuration must contain a top-level JSON object.")
    return value


def write_config(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if os.name == "posix":
        temporary.chmod(0o600)
    os.replace(temporary, path)


def initialize_config(path: Path) -> bool:
    """Create a safe template once; never overwrite an existing operator config."""
    if path.exists():
        return False

    template = files("oci_platform").joinpath("templates", "config.example.json")
    config = json.loads(template.read_text(encoding="utf-8"))
    state_dir = default_state_dir()
    config["paths"]["log_file"] = str(state_dir / "logs" / "oci-free-watch.log")
    config["paths"]["state_file"] = str(state_dir / "state" / "state.json")
    write_config(path, config)
    state_dir.joinpath("logs").mkdir(parents=True, exist_ok=True)
    state_dir.joinpath("state").mkdir(parents=True, exist_ok=True)
    return True


def _ask(prompt: str, default: str = "", *, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip()
        if not value:
            value = default
        if value or not required:
            return value
        print("This value is required.")


def _ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} ({hint}): ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def _ask_number(prompt: str, default: str, *, integer: bool = False, minimum: float = 0) -> int | float:
    while True:
        raw = _ask(prompt, default, required=True)
        try:
            value = float(raw)
            if not math.isfinite(value) or value < minimum:
                raise ValueError
            if integer:
                if not value.is_integer():
                    raise ValueError
                return int(value)
            return value
        except ValueError:
            qualifier = f"whole number >= {minimum:g}" if integer else f"number >= {minimum:g}"
            print(f"Enter a {qualifier}.")


def _configure_interactively(config_path: Path) -> int:
    """Collect local settings only. Never contacts OCI or arms instance creation."""
    config = read_config(config_path) if config_path.exists() else json.loads(
        files("oci_platform").joinpath("templates", "config.example.json").read_text(encoding="utf-8")
    )
    if not config_path.exists():
        state_dir = default_state_dir()
        config.setdefault("paths", {})["log_file"] = str(state_dir / "logs" / "oci-free-watch.log")
        config["paths"]["state_file"] = str(state_dir / "state" / "state.json")

    print("\nOCI Automation Platform — guided local configuration")
    print("This wizard only edits your local config. It does not call OCI or create cloud resources.")
    print("The account must remain Free Tier; paid resources are disabled by policy.\n")

    if not _ask_yes_no("Do you confirm this tenancy is on OCI Free Tier (not upgraded to Paid)?"):
        print("Stopped without changing configuration. Check your OCI account plan first.")
        return 2

    oci = config.setdefault("oci", {})
    account = config.setdefault("account", {})
    target = config.setdefault("target", {})
    mode = config.setdefault("mode", {})

    oci["config_file"] = str(Path(_ask(
        "OCI SDK config file",
        str(Path(oci.get("config_file", "~/.oci/config")).expanduser()),
        required=True,
    )).expanduser())
    oci["profile"] = _ask("OCI profile name", str(oci.get("profile", "DEFAULT")), required=True)

    home_region = _ask("Tenancy home region (e.g. us-phoenix-1)", str(account.get("home_region", "")), required=True)
    target_region = _ask("Target region (must equal home region)", str(target.get("region") or home_region), required=True)
    if target_region != home_region:
        print("Stopped: Always Free A1 target region must match the tenancy home region.")
        return 2

    account["account_type"] = "FREE_TIER"
    account["free_tier_only_confirmed"] = True
    account["allow_paid_resources"] = False
    account["home_region"] = home_region
    account["a1_free_max_ocpu"] = _ask_number(
        "Verified A1 OCPU policy cap", str(account.get("a1_free_max_ocpu", 2)), minimum=0.000001
    )
    account["a1_free_max_memory_gb"] = _ask_number(
        "Verified A1 memory policy cap in GB", str(account.get("a1_free_max_memory_gb", 12)), minimum=0.000001
    )
    account["combined_free_volume_gb"] = _ask_number(
        "Verified combined boot + block volume allowance in GB",
        str(account.get("combined_free_volume_gb", 200)), integer=True, minimum=1,
    )
    account["monthly_a1_ocpu_hours"] = _ask_number(
        "Monthly A1 OCPU-hour budget", str(account.get("monthly_a1_ocpu_hours", 1500))
    )
    account["monthly_a1_memory_gb_hours"] = _ask_number(
        "Monthly A1 GB-hour budget", str(account.get("monthly_a1_memory_gb_hours", 9000))
    )
    account["other_monthly_a1_ocpu_hours"] = _ask_number(
        "A1 OCPU-hours already consumed this month", str(account.get("other_monthly_a1_ocpu_hours", 0))
    )
    account["other_monthly_a1_memory_gb_hours"] = _ask_number(
        "A1 GB-hours already consumed this month", str(account.get("other_monthly_a1_memory_gb_hours", 0))
    )
    account["current_month_usage_reviewed"] = _ask_yes_no(
        "Have you reviewed current-month A1 compute and storage usage in OCI Cost Analysis?",
        account.get("current_month_usage_reviewed") is True,
    )

    target["region"] = target_region
    target["availability_domain"] = _ask(
        "Availability Domain name", str(target.get("availability_domain", "")), required=True
    )
    target["vcn_ocid"] = _ask("Existing VCN OCID", str(target.get("vcn_ocid", "")), required=True)
    if not target["vcn_ocid"].startswith("ocid1.vcn."):
        print("The VCN value must be an OCI VCN OCID; no changes were saved.")
        return 2
    target["subnet_ocid"] = _ask("Existing public subnet OCID (optional)", str(target.get("subnet_ocid", "")))
    if target["subnet_ocid"] and not target["subnet_ocid"].startswith("ocid1.subnet."):
        print("The subnet value must be an OCI subnet OCID; no changes were saved.")
        return 2
    target["display_name"] = _ask("Instance display name", str(target.get("display_name", "oci-a1-free-instance")), required=True)

    for key, prompt, default in (
        ("ocpus", "Requested OCPU (within your verified free allowance)", str(target.get("ocpus", 2))),
        ("memory_gb", "Requested RAM in GB (within your verified free allowance)", str(target.get("memory_gb", 4))),
        ("boot_volume_size_gb", "Boot volume size in GB (within your verified storage allowance)", str(target.get("boot_volume_size_gb", 150))),
    ):
        while True:
            raw = _ask(prompt, default, required=True)
            try:
                number = float(raw)
                if not number.is_integer() or number <= 0:
                    raise ValueError
                target[key] = int(number)
                break
            except ValueError:
                print("Enter a positive whole number.")

    if target["ocpus"] > float(account.get("a1_free_max_ocpu", 2)):
        print("Requested OCPU exceeds the configured Free Tier allowance; no changes were saved.")
        return 2
    if target["memory_gb"] > float(account.get("a1_free_max_memory_gb", 12)):
        print("Requested RAM exceeds the configured Free Tier allowance; no changes were saved.")
        return 2
    if target["boot_volume_size_gb"] < 50:
        print("OCI boot volume must be at least 50 GB; no changes were saved.")
        return 2
    if target["boot_volume_size_gb"] > int(account.get("combined_free_volume_gb", 200)):
        print("Boot volume exceeds the configured combined storage allowance; no changes were saved.")
        return 2

    target["shape"] = "VM.Standard.A1.Flex"
    target["operating_system"] = "Canonical Ubuntu"
    target["operating_system_version"] = "24.04"
    target["boot_volume_vpus_per_gb"] = _ask_number(
        "Boot volume performance in VPUs per GB", str(target.get("boot_volume_vpus_per_gb", 10)),
        integer=True, minimum=10,
    )
    if target["boot_volume_vpus_per_gb"] > 120:
        print("Boot volume performance must not exceed 120 VPUs per GB; no changes were saved.")
        return 2
    target["assign_public_ip"] = _ask_yes_no("Assign a public IPv4 address?", target.get("assign_public_ip") is True)
    ssh_public_key_path = Path(_ask(
        "Path to your SSH PUBLIC key file (never a private key)",
        str(Path(target.get("ssh_public_key_file", "~/.ssh/id_ed25519.pub")).expanduser()),
        required=True,
    )).expanduser()
    try:
        ssh_public_key = ssh_public_key_path.read_text(encoding="utf-8").strip()
    except OSError:
        print(f"SSH public key file is not readable: {ssh_public_key_path}; no changes were saved.")
        return 2
    if not ssh_public_key.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-")):
        print("The selected file does not look like an OpenSSH public key; no changes were saved.")
        return 2
    target["ssh_public_key_file"] = str(ssh_public_key_path)
    target["image_ocid"] = _ask("Pinned Ubuntu 24.04 ARM64 image OCID", str(target.get("image_ocid", "")), required=True)
    if not target["image_ocid"].startswith("ocid1.image."):
        print("The image value must be an OCI image OCID; no changes were saved.")
        return 2
    target["image_console_always_free_confirmed"] = _ask_yes_no(
        "Have you personally verified this exact image is marked 'Always Free Eligible' in OCI Console?",
        target.get("image_console_always_free_confirmed") is True,
    )

    mode["capacity_poll_minutes"] = _ask_number(
        "Capacity polling interval in minutes", str(mode.get("capacity_poll_minutes", 20)),
        integer=True, minimum=1,
    )
    mode["max_backoff_minutes"] = _ask_number(
        "Maximum retry backoff in minutes", str(mode.get("max_backoff_minutes", 180)),
        integer=True, minimum=1,
    )
    mode["max_attempts"] = _ask_number(
        "Maximum monitoring attempts (0 means unlimited)", str(mode.get("max_attempts", 0)),
        integer=True, minimum=0,
    )
    mode["instance_wait_timeout_minutes"] = _ask_number(
        "Instance readiness timeout in minutes", str(mode.get("instance_wait_timeout_minutes", 40)),
        integer=True, minimum=1,
    )
    mode["instance_poll_seconds"] = _ask_number(
        "Instance readiness poll interval in seconds", str(mode.get("instance_poll_seconds", 20)),
        integer=True, minimum=1,
    )

    paths = config.setdefault("paths", {})
    log_value = _ask("Log file path", str(paths.get("log_file", "")))
    state_value = _ask("State file path", str(paths.get("state_file", "")))
    paths["log_file"] = str(Path(log_value).expanduser()) if log_value else ""
    paths["state_file"] = str(Path(state_value).expanduser()) if state_value else ""
    logging = config.setdefault("logging", {})
    log_level = _ask("Log level (DEBUG/INFO/WARNING/ERROR)", str(logging.get("level", "INFO"))).upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        print("Invalid log level; no changes were saved.")
        return 2
    logging["level"] = log_level

    # This wizard must never arm a real cloud launch.
    mode["creation_enabled"] = False
    mode["creation_confirmation"] = ""

    print("\nConfiguration review")
    print(f"  OCI profile: {oci['profile']}")
    print(f"  Region / AD: {target['region']} / {target['availability_domain']}")
    print(f"  Shape: {target['shape']} — {target['ocpus']} OCPU / {target['memory_gb']} GB RAM")
    print(f"  Boot volume: {target['boot_volume_size_gb']} GB")
    print(f"  Current-month usage reviewed: {account['current_month_usage_reviewed']}")
    print(f"  Image Always Free label confirmed: {target['image_console_always_free_confirmed']}")
    print("  VM creation: DISABLED")
    if not _ask_yes_no("Save these settings?", False):
        print("Cancelled. Existing configuration was not changed.")
        return 1

    backup_path = None
    if config_path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = config_path.with_name(f"{config_path.name}.{stamp}.bak")
        shutil.copy2(config_path, backup_path)
        if os.name == "posix":
            backup_path.chmod(0o600)
    write_config(config_path, config)
    for configured_path in (paths.get("log_file"), paths.get("state_file")):
        if configured_path:
            Path(configured_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
    print(f"Saved configuration: {config_path}")
    if backup_path:
        print(f"Previous configuration backup: {backup_path}")
    print("Creation remains disabled. Run 'oci-platform doctor' and 'oci-platform vm audit' next.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oci-platform",
        description="Manage guarded Oracle Cloud Infrastructure automation.",
        epilog="Cloud operations are read-only unless the existing launch safeguards are explicitly satisfied.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config_path(),
        help="Application config path (default: per-user oci-platform config directory)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("setup", help="Create initial user configuration without contacting OCI")
    commands.add_parser("configure", help="Interactively configure OCI and target settings (local only)")
    commands.add_parser("doctor", help="Check local runtime, SDK and configuration readiness")

    config_cmd = commands.add_parser("config", help="Inspect and validate application configuration")
    config_sub = config_cmd.add_subparsers(dest="config_command", required=True)
    config_sub.add_parser("show", help="Show a redacted configuration summary")
    config_sub.add_parser("validate", help="Run the engine's offline policy/config validation")

    profile_cmd = commands.add_parser("profile", help="Manage named profiles in the local OCI SDK config")
    profile_sub = profile_cmd.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("list", help="List profile names without displaying credentials")
    use_profile = profile_sub.add_parser("use", help="Select an existing OCI SDK profile")
    use_profile.add_argument("name", help="Profile section name in the OCI SDK config")

    vm_cmd = commands.add_parser("vm", help="Run OCI VM acquisition operations")
    vm_sub = vm_cmd.add_subparsers(dest="vm_command", required=True)
    vm_sub.add_parser("audit", help="Run a read-only OCI audit")
    vm_sub.add_parser("once", help="Run one read-only capacity check")
    monitor = vm_sub.add_parser("monitor", help="Continuously monitor OCI capacity (read-only by default)")
    monitor.add_argument(
        "--enable-create",
        action="store_true",
        help="Explicitly pass the engine's creation CLI switch; local config confirmation is still required",
    )

    commands.add_parser("status", help="Show local automation state")
    logs = commands.add_parser("logs", help="Display recent local application log lines")
    logs.add_argument("--lines", type=int, default=50, help="Number of trailing lines to display (default: 50)")
    return parser


def _engine_main(arguments: list[str]) -> int:
    try:
        import oci_free_watch as engine
        return int(engine.main(arguments))
    except Exception as exc:
        # GuardError is intentionally imported lazily with the engine so that
        # setup/help remain usable even if the OCI SDK is unavailable.
        from oci_free_watch import GuardError
        if isinstance(exc, GuardError):
            print(f"SAFETY/CONFIGURATION STOP: {exc}", file=sys.stderr)
            return 3
        raise


def _profile_config_path(config: dict[str, Any]) -> Path:
    return Path(config.get("oci", {}).get("config_file", "~/.oci/config")).expanduser()


def _profile_names(path: Path) -> list[str]:
    if not path.is_file():
        raise ValueError(f"OCI SDK config not found: {path}. Configure the OCI CLI/SDK first.")
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    names = list(parser.sections())
    if parser.defaults():
        names.insert(0, "DEFAULT")
    return names


def _run_doctor(config_path: Path) -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python >= 3.11", sys.version_info >= (3, 11), sys.version.split()[0]))
    try:
        import oci  # noqa: F401
        checks.append(("OCI Python SDK", True, "installed"))
    except ImportError:
        checks.append(("OCI Python SDK", False, "not installed; reinstall the application dependencies"))

    if config_path.is_file():
        try:
            config = read_config(config_path)
            checks.append(("Application config", True, str(config_path)))
            try:
                import oci_free_watch as engine
                # This is strictly local validation; no OCI clients are created.
                result = engine.main(["--config", str(config_path), "--validate-config"])
                checks.append(("Offline policy validation", result == 0, "passed" if result == 0 else "failed"))
            except Exception as exc:
                checks.append(("Offline policy validation", False, str(exc)))
        except Exception as exc:
            checks.append(("Application config", False, str(exc)))
    else:
        checks.append(("Application config", False, f"not found: {config_path}; run setup"))

    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    return 0 if all(item[1] for item in checks) else 1


def _show_config(config_path: Path, config: dict[str, Any]) -> None:
    account = config.get("account", {})
    target = config.get("target", {})
    mode = config.get("mode", {})
    print(f"Config file: {config_path}")
    print(f"OCI profile: {config.get('oci', {}).get('profile', 'DEFAULT')}")
    print(f"Home region: {account.get('home_region') or '(not configured)'}")
    print(f"Target region: {target.get('region') or '(not configured)'}")
    print(f"Availability domain: {target.get('availability_domain') or '(not configured)'}")
    print(f"Shape: {target.get('shape', 'VM.Standard.A1.Flex')}")
    print(f"Resources: {target.get('ocpus', '?')} OCPU / {target.get('memory_gb', '?')} GB RAM")
    print(f"Boot volume: {target.get('boot_volume_size_gb', '?')} GB")
    print(f"Creation enabled in config: {mode.get('creation_enabled') is True}")
    print("Credentials and OCIDs are not displayed.")


def _show_status(config_path: Path) -> int:
    config = read_config(config_path)
    state_value = config.get("paths", {}).get("state_file")
    if not state_value:
        print("No state file is configured.")
        return 0
    state_path = Path(state_value).expanduser()
    if not state_path.is_file():
        print(f"No automation state found yet: {state_path}")
        return 0
    state = read_config(state_path)
    print(f"State file: {state_path}")
    print(f"Last event: {state.get('last_event', '(not recorded)')}")
    print(f"Launch pending: {'yes' if state.get('launch_pending') else 'no'}")
    print(f"Instance recorded: {'yes' if state.get('created_instance_ocid') else 'no'}")
    return 0


def _show_logs(config_path: Path, line_count: int) -> int:
    if line_count < 1 or line_count > 10000:
        raise ValueError("--lines must be between 1 and 10000.")
    config = read_config(config_path)
    log_value = config.get("paths", {}).get("log_file")
    if not log_value:
        print("No log file is configured.")
        return 0
    log_path = Path(log_value).expanduser()
    if not log_path.is_file():
        print(f"No log file found: {log_path}")
        return 0
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print("\n".join(lines[-line_count:]))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = args.config.expanduser()

    try:
        if args.command == "setup":
            created = initialize_config(config_path)
            if created:
                print(f"Created configuration: {config_path}")
                print("The template is intentionally incomplete and creation-disabled.")
                print("Edit the configuration, then run: oci-platform doctor")
            else:
                print(f"Existing configuration preserved: {config_path}")
            return 0

        if args.command == "configure":
            return _configure_interactively(config_path)

        if args.command == "doctor":
            return _run_doctor(config_path)

        if args.command == "config":
            config = read_config(config_path)
            if args.config_command == "show":
                _show_config(config_path, config)
                return 0
            return _engine_main(["--config", str(config_path), "--validate-config"])

        if args.command == "profile":
            config = read_config(config_path)
            oci_path = _profile_config_path(config)
            if args.profile_command == "list":
                names = _profile_names(oci_path)
                for name in names:
                    selected = name == config.get("oci", {}).get("profile", "DEFAULT")
                    print(f"{'*' if selected else ' '} {name}")
                return 0
            names = _profile_names(oci_path)
            if args.name not in names:
                raise ValueError(f"OCI profile '{args.name}' was not found in {oci_path}.")
            config.setdefault("oci", {})["profile"] = args.name
            write_config(config_path, config)
            print(f"Selected OCI profile: {args.name}")
            return 0

        if args.command == "vm":
            engine_args = ["--config", str(config_path)]
            if args.vm_command == "audit":
                engine_args.append("--audit")
            elif args.vm_command == "once":
                engine_args.append("--once")
            else:
                engine_args.append("--monitor")
                if args.enable_create:
                    print("WARNING: passing the explicit creation switch; the engine's local creation guards still apply.")
                    engine_args.append("--enable-create")
            return _engine_main(engine_args)

        if args.command == "status":
            return _show_status(config_path)

        if args.command == "logs":
            return _show_logs(config_path, args.lines)

        parser.error("Unsupported command.")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
