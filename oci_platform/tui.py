"""Friendly, menu-driven terminal UI for OCI Platform.

All setup/configuration actions in this module are local-only. Cloud operations
remain explicit subcommands handled by the existing CLI/engine.
"""
from __future__ import annotations

import configparser
import json
import math
import re
import shutil
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable

import questionary


class UserCancelled(Exception):
    """Raised when an operator cancels an interactive prompt."""


_STYLE = questionary.Style([
    ("qmark", "fg:#00afff bold"),
    ("question", "bold"),
    ("answer", "fg:#00af5f bold"),
    ("pointer", "fg:#00afff bold"),
    ("highlighted", "fg:#00afff bold"),
    ("selected", "fg:#00af5f"),
    ("instruction", "fg:#808080"),
    ("text", ""),
    ("disabled", "fg:#808080 italic"),
])

_REGION_RE = re.compile(r"^[a-z]{2,3}-[a-z0-9]+(?:-[a-z0-9]+)*-\d+$")
_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def _select(message: str, choices: list[str], *, default: str | None = None) -> str:
    value = questionary.select(
        message,
        choices=choices,
        default=default,
        use_arrow_keys=True,
        use_jk_keys=True,
        qmark="◆",
        instruction="(↑/↓ move · Enter select · Ctrl+C cancel)",
        style=_STYLE,
    ).ask()
    if value is None:
        raise UserCancelled
    return str(value)


def _text(message: str, current: Any = "", *, hint: str = "") -> str:
    value = questionary.text(
        message,
        default="" if current is None else str(current),
        instruction=hint or "Press Enter to keep the current value",
        qmark="✎",
        style=_STYLE,
    ).ask()
    if value is None:
        raise UserCancelled
    return str(value).strip()


def _confirm(message: str, default: bool = False) -> bool:
    value = questionary.confirm(message, default=default, qmark="◆", style=_STYLE).ask()
    if value is None:
        raise UserCancelled
    return bool(value)


def _notice(message: str) -> None:
    print(f"\n{message}\n")


def _path_value(value: str) -> str:
    return str(Path(value).expanduser()) if value else ""


def _valid_ssh_public_key(path_value: str) -> bool:
    if not path_value:
        return False
    try:
        contents = Path(path_value).expanduser().read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return contents.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-"))


def _profile_names(config_path: str) -> list[str]:
    path = Path(config_path).expanduser()
    if not path.is_file():
        return []
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error):
        return []
    names = list(parser.sections())
    if parser.defaults():
        names.insert(0, "DEFAULT")
    return names


def _edit_text(
    label: str,
    current: Any,
    *,
    required: bool = True,
    validator: Callable[[str], str | None] | None = None,
    hint: str = "",
) -> str:
    while True:
        value = _text(label, current, hint=hint)
        if not value and not required:
            return ""
        if not value and required:
            _notice("This value is required. Nothing has been changed.")
            continue
        error = validator(value) if validator else None
        if error:
            _notice(error)
            continue
        return value


def _edit_number(
    label: str,
    current: Any,
    *,
    integer: bool = False,
    minimum: float = 0,
) -> int | float:
    while True:
        raw = _text(label, current, hint=f"Enter a {'whole number' if integer else 'number'} ≥ {minimum:g}")
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
            _notice(f"Enter a valid {'whole number' if integer else 'number'} greater than or equal to {minimum:g}.")


def _field_choice(label: str, value: Any, *, secret: bool = False) -> str:
    shown = "Configured" if secret and value else ("Not set" if secret else (str(value) if value not in (None, "") else "Not set"))
    return f"{label}  —  {shown}"


def _edit_identity(config: dict[str, Any]) -> None:
    while True:
        oci = config.setdefault("oci", {})
        account = config.setdefault("account", {})
        target = config.setdefault("target", {})
        entries = [
            ("OCI SDK config file", "oci_file"),
            ("OCI SDK profile", "profile"),
            ("Tenancy home region", "region"),
            ("Availability domain", "ad"),
            ("Existing VCN OCID", "vcn"),
            ("Existing public subnet OCID (optional)", "subnet"),
            ("Back to configuration menu", "back"),
        ]
        labels = {
            "oci_file": _field_choice("OCI SDK config file", oci.get("config_file", "~/.oci/config")),
            "profile": _field_choice("OCI profile", oci.get("profile", "DEFAULT")),
            "region": _field_choice("Home / target region", account.get("home_region", "")),
            "ad": _field_choice("Availability domain", target.get("availability_domain", "")),
            "vcn": _field_choice("Existing VCN OCID", target.get("vcn_ocid", ""), secret=True),
            "subnet": _field_choice("Existing public subnet OCID", target.get("subnet_ocid", ""), secret=True),
            "back": "← Back to configuration menu",
        }
        selected = _select(
            "Account, region and existing network — select a field to edit",
            [labels[key] for _, key in entries],
        )
        selected_key = next(key for _, key in entries if labels[key] == selected)
        if selected_key == "back":
            return
        if selected_key == "oci_file":
            value = _edit_text(
                "Path to your existing OCI SDK config file",
                oci.get("config_file", "~/.oci/config"),
                validator=lambda item: None if Path(item).expanduser().is_file() else
                    "File not found. Create your OCI SDK profile first, or enter the correct config file path.",
                hint="Example: ~/.oci/config",
            )
            oci["config_file"] = _path_value(value)
            profiles = _profile_names(value)
            if profiles and oci.get("profile") not in profiles:
                oci["profile"] = profiles[0]
        elif selected_key == "profile":
            profiles = _profile_names(oci.get("config_file", ""))
            if profiles:
                oci["profile"] = _select(
                    "Select an existing profile (names only; credentials are never displayed)",
                    profiles,
                    default=oci.get("profile") if oci.get("profile") in profiles else profiles[0],
                )
            else:
                _notice("No readable OCI SDK config file found. Set its path first.")
        elif selected_key == "region":
            current = account.get("home_region", "")
            value = _edit_text(
                "Tenancy home region",
                current,
                validator=lambda item: None if _REGION_RE.fullmatch(item) else
                    "Region format should look like us-phoenix-1 or uk-london-1.",
                hint="Target region follows this automatically to enforce the home-region rule.",
            )
            account["home_region"] = value
            target["region"] = value
        elif selected_key == "ad":
            target["availability_domain"] = _edit_text(
                "Availability domain name",
                target.get("availability_domain", ""),
                hint="Copy the exact AD name shown in your OCI Console for this home region.",
            )
        elif selected_key == "vcn":
            target["vcn_ocid"] = _edit_text(
                "OCID of an existing VCN",
                target.get("vcn_ocid", ""),
                validator=lambda item: None if item.startswith("ocid1.vcn.") else
                    "That does not look like a VCN OCID. It must begin with ocid1.vcn.",
            )
        elif selected_key == "subnet":
            target["subnet_ocid"] = _edit_text(
                "OCID of an existing public subnet (leave blank if not selected yet)",
                target.get("subnet_ocid", ""),
                required=False,
                validator=lambda item: None if not item or item.startswith("ocid1.subnet.") else
                    "That does not look like a subnet OCID. It must begin with ocid1.subnet.",
            )


def _edit_compute(config: dict[str, Any]) -> None:
    while True:
        target = config.setdefault("target", {})
        fields = [
            ("Instance display name", "display"),
            ("Requested OCPU", "ocpus"),
            ("Requested memory (GB)", "memory"),
            ("Boot volume size (GB)", "boot"),
            ("Back to configuration menu", "back"),
        ]
        labels = {
            "display": _field_choice(fields[0][0], target.get("display_name", "")),
            "ocpus": _field_choice(fields[1][0], target.get("ocpus", 2)),
            "memory": _field_choice(fields[2][0], target.get("memory_gb", 4)),
            "boot": _field_choice(fields[3][0], target.get("boot_volume_size_gb", 150)),
            "back": "← Back to configuration menu",
        }
        selected = _select("A1 compute and storage — select a field to edit", [labels[key] for _, key in fields])
        key = next(key for _, key in fields if labels[key] == selected)
        if key == "back":
            return
        if key == "display":
            target["display_name"] = _edit_text("Instance display name", target.get("display_name", "oci-a1-free-instance"))
        elif key == "ocpus":
            target["ocpus"] = _edit_number("Requested OCPU (whole number)", target.get("ocpus", 2), integer=True, minimum=1)
        elif key == "memory":
            target["memory_gb"] = _edit_number("Requested memory in GB (whole number)", target.get("memory_gb", 4), integer=True, minimum=1)
        elif key == "boot":
            target["boot_volume_size_gb"] = _edit_number("Boot volume size in GB (whole number)", target.get("boot_volume_size_gb", 150), integer=True, minimum=50)
        target["shape"] = "VM.Standard.A1.Flex"
        target["operating_system"] = "Canonical Ubuntu"
        target["operating_system_version"] = "24.04"
        target["boot_volume_vpus_per_gb"] = 10
        target["assign_public_ip"] = True


def _edit_budget(config: dict[str, Any]) -> None:
    while True:
        account = config.setdefault("account", {})
        fields = [
            ("Verified A1 OCPU policy cap", "ocpu_cap"),
            ("Verified A1 memory cap (GB)", "memory_cap"),
            ("Combined boot + block volume allowance (GB)", "volume_cap"),
            ("Monthly A1 OCPU-hour budget", "ocpu_budget"),
            ("Monthly A1 GB-hour budget", "memory_budget"),
            ("OCPU-hours already used this month", "ocpu_used"),
            ("GB-hours already used this month", "memory_used"),
            ("Current-month usage reviewed", "usage_reviewed"),
            ("Back to configuration menu", "back"),
        ]
        getters = {
            "ocpu_cap": account.get("a1_free_max_ocpu", 2),
            "memory_cap": account.get("a1_free_max_memory_gb", 12),
            "volume_cap": account.get("combined_free_volume_gb", 200),
            "ocpu_budget": account.get("monthly_a1_ocpu_hours", 1500),
            "memory_budget": account.get("monthly_a1_memory_gb_hours", 9000),
            "ocpu_used": account.get("other_monthly_a1_ocpu_hours", 0),
            "memory_used": account.get("other_monthly_a1_memory_gb_hours", 0),
            "usage_reviewed": "Yes" if account.get("current_month_usage_reviewed") else "No",
            "back": "",
        }
        labels = {key: _field_choice(label, getters[key]) for label, key in fields}
        labels["back"] = "← Back to configuration menu"
        selected = _select("Free Tier policy and monthly usage — select a field to edit", [labels[key] for _, key in fields])
        key = next(key for _, key in fields if labels[key] == selected)
        if key == "back":
            return
        number_fields = {
            "ocpu_cap": ("a1_free_max_ocpu", False, 0.000001),
            "memory_cap": ("a1_free_max_memory_gb", False, 0.000001),
            "volume_cap": ("combined_free_volume_gb", True, 1),
            "ocpu_budget": ("monthly_a1_ocpu_hours", False, 0),
            "memory_budget": ("monthly_a1_memory_gb_hours", False, 0),
            "ocpu_used": ("other_monthly_a1_ocpu_hours", False, 0),
            "memory_used": ("other_monthly_a1_memory_gb_hours", False, 0),
        }
        if key in number_fields:
            config_key, integer, minimum = number_fields[key]
            label = next(label for label, field_key in fields if field_key == key)
            account[config_key] = _edit_number(label, getters[key], integer=integer, minimum=minimum)
        else:
            account["current_month_usage_reviewed"] = _confirm(
                "Have you reviewed this month's A1 compute and storage usage in OCI Cost Analysis?",
                default=account.get("current_month_usage_reviewed") is True,
            )


def _edit_image_access(config: dict[str, Any]) -> None:
    while True:
        target = config.setdefault("target", {})
        entries = [
            ("SSH public-key file", "ssh"),
            ("Pinned Ubuntu 24.04 ARM64 image OCID", "image"),
            ("Image marked Always Free Eligible in Console", "eligible"),
            ("Back to configuration menu", "back"),
        ]
        values = {
            "ssh": _field_choice(entries[0][0], target.get("ssh_public_key_file", "")),
            "image": _field_choice(entries[1][0], target.get("image_ocid", ""), secret=True),
            "eligible": _field_choice(entries[2][0], "Yes" if target.get("image_console_always_free_confirmed") else "No"),
            "back": "← Back to configuration menu",
        }
        selected = _select("Image and SSH access — select a field to edit", [values[key] for _, key in entries])
        key = next(key for _, key in entries if values[key] == selected)
        if key == "back":
            return
        if key == "ssh":
            path_value = _edit_text(
                "Path to your SSH PUBLIC key file (never the private key)",
                target.get("ssh_public_key_file", "~/.ssh/id_ed25519.pub"),
                validator=lambda item: None if _valid_ssh_public_key(item) else
                    "File not found or not an OpenSSH public key. Choose a readable .pub file.",
                hint="Example: ~/.ssh/id_ed25519.pub",
            )
            target["ssh_public_key_file"] = _path_value(path_value)
        elif key == "image":
            target["image_ocid"] = _edit_text(
                "Pinned Ubuntu 24.04 ARM64 image OCID",
                target.get("image_ocid", ""),
                validator=lambda item: None if item.startswith("ocid1.image.") else
                    "That does not look like an image OCID. It must begin with ocid1.image.",
            )
        else:
            target["image_console_always_free_confirmed"] = _confirm(
                "Have you personally checked that this exact image is labelled 'Always Free Eligible' in OCI Console?",
                default=target.get("image_console_always_free_confirmed") is True,
            )


def _edit_runtime(config: dict[str, Any]) -> None:
    while True:
        mode = config.setdefault("mode", {})
        paths = config.setdefault("paths", {})
        logging = config.setdefault("logging", {})
        entries = [
            ("Capacity polling interval (minutes)", "poll"),
            ("Maximum retry backoff (minutes)", "backoff"),
            ("Maximum attempts (0 = unlimited)", "attempts"),
            ("Instance readiness timeout (minutes)", "timeout"),
            ("Instance polling interval (seconds)", "interval"),
            ("Log file path", "log"),
            ("State file path", "state"),
            ("Log level", "level"),
            ("Back to configuration menu", "back"),
        ]
        current = {
            "poll": mode.get("capacity_poll_minutes", 20),
            "backoff": mode.get("max_backoff_minutes", 180),
            "attempts": mode.get("max_attempts", 0),
            "timeout": mode.get("instance_wait_timeout_minutes", 40),
            "interval": mode.get("instance_poll_seconds", 20),
            "log": paths.get("log_file", ""),
            "state": paths.get("state_file", ""),
            "level": logging.get("level", "INFO"),
            "back": "",
        }
        labels = {key: _field_choice(label, current[key]) for label, key in entries}
        labels["back"] = "← Back to configuration menu"
        selected = _select("Monitoring and local paths — select a field to edit", [labels[key] for _, key in entries])
        key = next(key for _, key in entries if labels[key] == selected)
        if key == "back":
            return
        if key in {"poll", "backoff", "attempts", "timeout", "interval"}:
            mapping = {
                "poll": ("capacity_poll_minutes", 1),
                "backoff": ("max_backoff_minutes", 1),
                "attempts": ("max_attempts", 0),
                "timeout": ("instance_wait_timeout_minutes", 1),
                "interval": ("instance_poll_seconds", 1),
            }
            config_key, minimum = mapping[key]
            label = next(label for label, field_key in entries if field_key == key)
            mode[config_key] = _edit_number(label, current[key], integer=True, minimum=minimum)
        elif key == "log":
            paths["log_file"] = _path_value(_edit_text("Log file path (blank disables file logging)", current[key], required=False))
        elif key == "state":
            paths["state_file"] = _path_value(_edit_text("State file path (blank disables state persistence)", current[key], required=False))
        else:
            logging["level"] = _select("Choose a log level", list(_LOG_LEVELS), default=str(current[key]).upper())


def validate_configuration(config: dict[str, Any]) -> list[str]:
    """Return operator-readable local validation issues; never contacts OCI."""
    issues: list[str] = []
    oci = config.get("oci", {})
    account = config.get("account", {})
    target = config.get("target", {})

    sdk_path = Path(str(oci.get("config_file", "")).strip()).expanduser()
    if not str(oci.get("config_file", "")).strip() or not sdk_path.is_file():
        issues.append("OCI SDK config file is missing. Set the path to an existing ~/.oci/config file.")
    elif oci.get("profile", "DEFAULT") not in _profile_names(str(sdk_path)):
        issues.append("Selected OCI profile was not found in the SDK config file.")

    home_region = str(account.get("home_region", "")).strip()
    if not _REGION_RE.fullmatch(home_region):
        issues.append("Enter a valid tenancy home region, for example us-phoenix-1.")
    if target.get("region") != home_region:
        issues.append("Target region must match the tenancy home region.")
    if not str(target.get("availability_domain", "")).strip():
        issues.append("Availability domain is required.")
    if not str(target.get("vcn_ocid", "")).startswith("ocid1.vcn."):
        issues.append("An existing VCN OCID is required and must begin with ocid1.vcn.")
    subnet = str(target.get("subnet_ocid", "")).strip()
    if subnet and not subnet.startswith("ocid1.subnet."):
        issues.append("Subnet OCID must begin with ocid1.subnet.")
    if account.get("account_type") != "FREE_TIER" or account.get("free_tier_only_confirmed") is not True:
        issues.append("Free Tier account confirmation is required.")
    if account.get("allow_paid_resources") is not False:
        issues.append("Paid resources must remain disabled.")

    try:
        ocpu_cap = float(account.get("a1_free_max_ocpu", 0))
        memory_cap = float(account.get("a1_free_max_memory_gb", 0))
        volume_cap = int(account.get("combined_free_volume_gb", 0))
        ocpus = int(target.get("ocpus", 0))
        memory = int(target.get("memory_gb", 0))
        boot = int(target.get("boot_volume_size_gb", 0))
        if not all(math.isfinite(number) for number in (ocpu_cap, memory_cap)):
            raise ValueError
        if ocpu_cap <= 0 or memory_cap <= 0 or volume_cap <= 0:
            raise ValueError
        if ocpus <= 0 or ocpus > ocpu_cap:
            issues.append("Requested OCPU must be positive and within the configured A1 policy cap.")
        if memory <= 0 or memory > memory_cap:
            issues.append("Requested memory must be positive and within the configured A1 policy cap.")
        if boot < 50 or boot > volume_cap:
            issues.append("Boot volume must be at least 50 GB and within the configured combined volume cap.")
    except (TypeError, ValueError, OverflowError):
        issues.append("A1 resource caps and requested compute/storage values must be valid positive numbers.")
    for key in (
        "monthly_a1_ocpu_hours", "monthly_a1_memory_gb_hours",
        "other_monthly_a1_ocpu_hours", "other_monthly_a1_memory_gb_hours",
    ):
        try:
            number = float(account.get(key, 0))
            if not math.isfinite(number) or number < 0:
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            issues.append(f"{key} must be a finite, non-negative number.")
    if target.get("boot_volume_vpus_per_gb", 10) != 10:
        issues.append("This release supports exactly 10 boot-volume VPUs per GB.")
    if target.get("assign_public_ip") is not True:
        issues.append("This release requires public IPv4 assignment to remain enabled.")
    if not _valid_ssh_public_key(str(target.get("ssh_public_key_file", ""))):
        issues.append("Choose a readable OpenSSH PUBLIC key file (.pub); never use a private key.")
    if not str(target.get("image_ocid", "")).startswith("ocid1.image."):
        issues.append("A pinned Ubuntu image OCID is required.")
    return issues


def review_configuration(config_path: Path, config: dict[str, Any]) -> None:
    account = config.get("account", {})
    target = config.get("target", {})
    oci = config.get("oci", {})
    mode = config.get("mode", {})
    print("\n" + "═" * 66)
    print(" CONFIGURATION REVIEW")
    print("═" * 66)
    print(f"Config file          : {config_path}")
    print(f"OCI SDK profile      : {oci.get('profile', 'DEFAULT')}")
    print(f"OCI SDK config       : {oci.get('config_file') or 'Not set'}")
    print(f"Home / target region : {account.get('home_region') or 'Not set'} / {target.get('region') or 'Not set'}")
    print(f"Availability domain  : {target.get('availability_domain') or 'Not set'}")
    print(f"Existing VCN         : {'Configured' if target.get('vcn_ocid') else 'Not set'}")
    print(f"Existing subnet      : {'Configured' if target.get('subnet_ocid') else 'Not set'}")
    print(f"Compute              : {target.get('ocpus', '?')} OCPU / {target.get('memory_gb', '?')} GB RAM")
    print(f"Boot volume          : {target.get('boot_volume_size_gb', '?')} GB")
    print(f"SSH public key       : {target.get('ssh_public_key_file') or 'Not set'}")
    print(f"Image OCID           : {'Configured' if target.get('image_ocid') else 'Not set'}")
    print(f"Image eligibility    : {'Confirmed manually' if target.get('image_console_always_free_confirmed') else 'Not yet confirmed'}")
    print(f"Current-month review : {'Complete' if account.get('current_month_usage_reviewed') else 'Not yet complete'}")
    print(f"Capacity polling     : every {mode.get('capacity_poll_minutes', 20)} minute(s)")
    print(f"Log level            : {config.get('logging', {}).get('level', 'INFO')}")
    print("VM creation           : DISABLED")
    print("Credentials and OCIDs are deliberately not shown.")
    print("═" * 66)
    issues = validate_configuration(config)
    if issues:
        print("\nItems to fix before this configuration is complete:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\nLocal configuration checks: PASS")
    if not account.get("current_month_usage_reviewed"):
        print("NOTE: Review current-month usage before any live capacity/launch workflow.")
    if not target.get("image_console_always_free_confirmed"):
        print("NOTE: Manually check the exact image's Always Free Eligible label in OCI Console.")


def run_config_wizard(
    config_path: Path,
    *,
    default_state_dir: Path,
    read_config: Callable[[Path], dict[str, Any]],
    write_config: Callable[[Path, dict[str, Any]], None],
) -> int:
    """Run a menu-driven local configuration wizard."""
    if config_path.exists():
        config = read_config(config_path)
    else:
        config = json.loads(files("oci_platform").joinpath("templates", "config.example.json").read_text(encoding="utf-8"))
        config.setdefault("paths", {})["log_file"] = str(default_state_dir / "logs" / "oci-free-watch.log")
        config["paths"]["state_file"] = str(default_state_dir / "state" / "state.json")

    config.setdefault("mode", {})["creation_enabled"] = False
    config["mode"]["creation_confirmation"] = ""

    print("\n" + "═" * 66)
    print(" OCI AUTOMATION PLATFORM — CONFIGURATION")
    print(" Local-only setup · no OCI API calls · no cloud resource changes")
    print(" Use ↑/↓ and Enter to select; choose any section to edit its values.")
    print("═" * 66)
    if not _confirm(
        "Do you confirm this tenancy is still on OCI Free Tier (not upgraded to Paid)?",
        default=config.get("account", {}).get("free_tier_only_confirmed") is True,
    ):
        print("Stopped. No changes were saved. Check your account plan first.")
        return 2

    account = config.setdefault("account", {})
    account["account_type"] = "FREE_TIER"
    account["free_tier_only_confirmed"] = True
    account["allow_paid_resources"] = False

    sections = [
        ("Account, region and existing network", _edit_identity),
        ("A1 compute and storage", _edit_compute),
        ("Free Tier policy and monthly usage", _edit_budget),
        ("Ubuntu image and SSH public key", _edit_image_access),
        ("Monitoring, local paths and logging", _edit_runtime),
    ]
    while True:
        choices = [label for label, _ in sections] + [
            "Review configuration and validation",
            "Save configuration",
            "Cancel without saving",
        ]
        selected = _select("Configuration editor — choose a section", choices)
        if selected == "Cancel without saving":
            print("Cancelled. Existing configuration was not changed.")
            return 1
        if selected == "Review configuration and validation":
            review_configuration(config_path, config)
            continue
        if selected == "Save configuration":
            issues = validate_configuration(config)
            if issues:
                _notice("Configuration is not ready to save. Fix these items first:\n" + "\n".join(f"• {item}" for item in issues))
                continue
            review_configuration(config_path, config)
            if not _confirm("Save these settings locally? (VM creation will remain disabled)", default=False):
                continue

            mode = config.setdefault("mode", {})
            mode["creation_enabled"] = False
            mode["creation_confirmation"] = ""
            config.setdefault("account", {})["account_type"] = "FREE_TIER"
            config["account"]["free_tier_only_confirmed"] = True
            config["account"]["allow_paid_resources"] = False

            backup_path = None
            if config_path.exists():
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                backup_path = config_path.with_name(f"{config_path.name}.{stamp}.bak")
                shutil.copy2(config_path, backup_path)
                if config_path.stat().st_mode & 0o077 == 0:
                    backup_path.chmod(0o600)
            write_config(config_path, config)
            for configured_path in (config.get("paths", {}).get("log_file"), config.get("paths", {}).get("state_file")):
                if configured_path:
                    Path(configured_path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            print(f"\nSaved configuration: {config_path}")
            if backup_path:
                print(f"Previous configuration backup: {backup_path}")
            print("VM creation remains DISABLED.")
            print("Next: run oci-platform doctor, then review the read-only audit before any cloud action.")
            return 0

        editor = dict(sections)[selected]
        editor(config)
        _notice("Changes are in memory only. Choose Review or Save when ready.")


def select_home_action() -> str:
    """Return a safe local action from the no-argument CLI home menu."""
    choices = [
        "Configure / edit settings",
        "Run local diagnostics",
        "Show configuration summary",
        "Show local status",
        "Show recent logs",
        "Setup starter configuration",
        "Show command help",
        "Exit",
    ]
    return _select("OCI Automation Platform — what would you like to do?", choices)
