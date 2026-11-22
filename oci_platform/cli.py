"""Cross-platform CLI entry point for OCI Automation Platform.

The CLI is deliberately a thin layer over the established OCI automation
engine. Cloud operations retain the engine's existing validation and guards.
"""
from __future__ import annotations

import argparse
import configparser
import json
import os
import shutil
import sys
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
    state_path = Path(config.get("paths", {}).get("state_file", "")).expanduser()
    if not str(state_path):
        print("No state file is configured.")
        return 0
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
    log_path = Path(config.get("paths", {}).get("log_file", "")).expanduser()
    if not str(log_path) or not log_path.is_file():
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
