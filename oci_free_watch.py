#!/usr/bin/env python3
"""OCI Always Free A1 capacity monitor and guarded instance launcher.

Default behaviour is READ-ONLY. Instance launch requires all of:
  1) config.mode.creation_enabled == true
  2) CLI flag --enable-create
  3) config.mode.creation_confirmation == LAUNCH_ONE_ALWAYS_FREE_INSTANCE

This program never creates/changes VCNs, subnets, gateways, route tables,
security lists, NSGs, reserved IPs, or any non-A1 compute resources.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import random
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

try:
    import oci
except ImportError:  # Friendly message for first run.
    oci = None  # type: ignore[assignment]

APP_DIR = Path(__file__).resolve().parent
STOP_REQUESTED = False
LOG = logging.getLogger("oci_free_watch")


class GuardError(RuntimeError):
    """A non-retryable safety/configuration condition."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GuardError(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise GuardError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GuardError("Top-level configuration must be a JSON object.")
    return value


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def setup_logging(log_file: Path, level: str = "INFO") -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    LOG.setLevel(getattr(logging, level.upper(), logging.INFO))
    LOG.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    LOG.addHandler(file_handler)
    LOG.addHandler(stream_handler)


def notify(cfg: dict[str, Any], message: str) -> None:
    """Optional Telegram notification. Secrets are read only from env vars."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return
    try:
        import urllib.parse
        import urllib.request

        body = urllib.parse.urlencode({"chat_id": chat_id, "text": message[:3500]}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status >= 300:
                LOG.warning("Telegram notification returned HTTP %s", response.status)
    except Exception as exc:  # Notifications must never crash monitoring.
        LOG.warning("Telegram notification failed (%s)", type(exc).__name__)


def on_signal(signum: int, _frame: Any) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    LOG.info("Shutdown requested (signal %s); finishing current API operation.", signum)


def require_config(cfg: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    oci_cfg = cfg.get("oci", {})
    account = cfg.get("account", {})
    target = cfg.get("target", {})
    mode = cfg.get("mode", {})
    for section_name, section in (("oci", oci_cfg), ("account", account), ("target", target), ("mode", mode)):
        if not isinstance(section, dict):
            raise GuardError(f"Config section '{section_name}' must be an object.")
    required = {
        "account.home_region": account.get("home_region"),
        "account.account_type": account.get("account_type"),
        "account.free_tier_only_confirmed": account.get("free_tier_only_confirmed"),
        "target.region": target.get("region"),
        "target.availability_domain": target.get("availability_domain"),
        "target.vcn_ocid": target.get("vcn_ocid"),
        "target.display_name": target.get("display_name"),
        "target.ssh_public_key_file": target.get("ssh_public_key_file"),
    }
    missing = [name for name, value in required.items() if value in (None, "")]
    if missing:
        raise GuardError("Missing required configuration value(s): " + ", ".join(missing))
    return account, target, mode


def check_static_free_tier_policy(account: dict[str, Any], target: dict[str, Any]) -> None:
    """Fail closed against non-A1, out-of-home-region, or over-allocation config."""
    if account.get("account_type") != "FREE_TIER" or account.get("free_tier_only_confirmed") is not True:
        raise GuardError("Config must explicitly confirm account_type=FREE_TIER and free_tier_only_confirmed=true.")
    if account.get("allow_paid_resources", False) is not False:
        raise GuardError("allow_paid_resources must be false.")

    home_region = str(account.get("home_region", "")).strip()
    target_region = str(target.get("region", "")).strip()
    if not home_region or not target_region:
        raise GuardError("Set account.home_region and target.region using your OCI tenancy's home region.")
    if target_region != home_region:
        raise GuardError("Always Free A1 compute must be launched in the tenancy home region.")
    if target.get("shape") != "VM.Standard.A1.Flex":
        raise GuardError("Safety policy permits only VM.Standard.A1.Flex.")

    try:
        ocpus = float(target.get("ocpus", 0))
        memory = float(target.get("memory_gb", 0))
        boot_value = float(target.get("boot_volume_size_gb", 0))
        max_ocpus = float(account.get("a1_free_max_ocpu", 2))
        max_memory = float(account.get("a1_free_max_memory_gb", 12))
        max_storage = int(account.get("combined_free_volume_gb", 200))
        monthly_cpu_budget = float(account.get("monthly_a1_ocpu_hours", 1500))
        monthly_memory_budget = float(account.get("monthly_a1_memory_gb_hours", 9000))
        other_cpu_hours = float(account.get("other_monthly_a1_ocpu_hours", 0))
        other_memory_hours = float(account.get("other_monthly_a1_memory_gb_hours", 0))
    except (TypeError, ValueError, OverflowError) as exc:
        raise GuardError("OCPU, memory, boot volume, and account budgets must be valid numbers.") from exc

    numeric_values = (ocpus, memory, boot_value, max_ocpus, max_memory,
                      monthly_cpu_budget, monthly_memory_budget,
                      other_cpu_hours, other_memory_hours)
    if not all(math.isfinite(value) for value in numeric_values):
        raise GuardError("OCPU, memory, boot volume, and account budgets must be finite numbers.")
    if not boot_value.is_integer():
        raise GuardError("Boot volume size must be a whole number of GB.")
    boot_gb = int(boot_value)
    if max_ocpus <= 0 or max_memory <= 0 or max_storage <= 0:
        raise GuardError("Configured A1 and storage policy limits must be greater than zero.")
    if monthly_cpu_budget <= 0 or monthly_memory_budget <= 0 or other_cpu_hours < 0 or other_memory_hours < 0:
        raise GuardError("Monthly budgets must be positive and previously consumed usage cannot be negative.")
    if ocpus <= 0 or ocpus > max_ocpus:
        raise GuardError(f"Requested OCPU must be greater than zero and no more than the configured A1 limit ({max_ocpus:g}).")
    if memory <= 0 or memory > max_memory:
        raise GuardError(f"Requested memory must be greater than zero and no more than the configured A1 limit ({max_memory:g} GB).")
    if boot_gb < 50 or boot_gb > max_storage:
        raise GuardError(f"Boot volume must be at least 50 GB and no more than the configured combined storage limit ({max_storage} GB).")
    if not str(target.get("operating_system", "")).strip() or not str(target.get("operating_system_version", "")).strip():
        raise GuardError("Set a supported operating_system and operating_system_version.")
    if target.get("assign_public_ip") is not True:
        raise GuardError("This release requires a public IPv4 address and an existing public subnet.")
    if target.get("boot_volume_vpus_per_gb", 10) != 10:
        raise GuardError("Only the standard 10-VPU/GB boot volume performance setting is permitted by this guard.")


def create_clients(config_path: Path, profile: str, expected_region: str) -> tuple[dict[str, Any], Any, Any, Any, Any, Any]:
    if oci is None:
        raise GuardError("OCI SDK is not installed. Run: python -m pip install -r requirements.txt")
    try:
        config = oci.config.from_file(str(config_path), profile)
        oci.config.validate_config(config)
    except Exception as exc:
        raise GuardError(f"OCI configuration could not be loaded/validated ({type(exc).__name__}). Check ~/.oci/config.") from exc
    if config.get("region") != expected_region:
        raise GuardError(f"OCI SDK profile region is {config.get('region')!r}, but target region is {expected_region!r}.")
    key_path = Path(config.get("key_file", "")).expanduser()
    if not key_path.is_file():
        raise GuardError("OCI private key file referenced by ~/.oci/config does not exist.")
    if os.name == "posix" and (key_path.stat().st_mode & 0o077):
        raise GuardError("OCI private key permissions are too open. Run chmod 600 on the private key.")
    # Use the official OCI SDK clients. No credentials are logged.
    identity = oci.identity.IdentityClient(config)
    compute = oci.core.ComputeClient(config)
    network = oci.core.VirtualNetworkClient(config)
    block = oci.core.BlockstorageClient(config)
    limits = oci.limits.LimitsClient(config)
    return config, identity, compute, network, block, limits


def list_compartments_recursive(identity: Any, root_id: str) -> list[str]:
    """Enumerate accessible active compartments so storage/instances are not missed."""
    found = [root_id]
    pending = [root_id]
    seen = {root_id}
    while pending:
        parent = pending.pop()
        response = oci.pagination.list_call_get_all_results(
            identity.list_compartments,
            compartment_id=parent,
            lifecycle_state="ACTIVE",
        )
        for compartment in response.data:
            cid = compartment.id
            if cid not in seen:
                seen.add(cid)
                found.append(cid)
                pending.append(cid)
    return found


def get_availability_domains(identity: Any, tenancy_id: str) -> list[str]:
    return [ad.name for ad in oci.pagination.list_call_get_all_results(
        identity.list_availability_domains, compartment_id=tenancy_id
    ).data]


def verify_home_region(identity: Any, tenancy_id: str, region: str) -> None:
    subscriptions = oci.pagination.list_call_get_all_results(
        identity.list_region_subscriptions, tenancy_id=tenancy_id
    ).data
    matches = [s for s in subscriptions if s.region_name == region]
    if not matches:
        raise GuardError(f"Tenancy has no subscription to region {region}.")
    if not any(s.is_home_region and s.status == "READY" for s in matches):
        raise GuardError(f"{region} is not confirmed as the READY home region. Refusing Always Free compute launch.")
    LOG.info("Home region verified by OCI: %s", region)


def discover_image(compute: Any, tenancy_id: str, target: dict[str, Any]) -> Any:
    images = oci.pagination.list_call_get_all_results(
        compute.list_images,
        compartment_id=tenancy_id,
        operating_system=target["operating_system"],
        operating_system_version=str(target["operating_system_version"]),
        shape=target["shape"],
        sort_by="TIMECREATED",
        sort_order="DESC",
    ).data
    good = [i for i in images if i.lifecycle_state == "AVAILABLE"
            and i.operating_system == target["operating_system"]
            and str(i.operating_system_version) == str(target["operating_system_version"])]
    if not good:
        raise GuardError(f"No AVAILABLE {target['operating_system']} {target['operating_system_version']} image compatible with {target['shape']} was returned by OCI.")
    # OCI's SDK Image model does not expose the Console's 'Always Free Eligible' label.
    # If an OCID is pinned, use only that exact image; otherwise return a candidate for audit.
    pinned_id = str(target.get("image_ocid", "")).strip()
    if pinned_id:
        pinned = [image for image in good if image.id == pinned_id]
        if not pinned:
            raise GuardError(f"Configured image_ocid was not found among AVAILABLE {target['operating_system']} {target['operating_system_version']} images compatible with {target['shape']} in this tenancy/region.")
        return pinned[0]
    return good[0]


def inspect_network(network: Any, tenancy_id: str, target: dict[str, Any]) -> tuple[Any, Any]:
    vcn_id = target["vcn_ocid"]
    subnets = oci.pagination.list_call_get_all_results(
        network.list_subnets,
        compartment_id=tenancy_id,
        vcn_id=vcn_id,
        lifecycle_state="AVAILABLE",
    ).data
    if target.get("subnet_ocid"):
        subnets = [s for s in subnets if s.id == target["subnet_ocid"]]
    eligible = [s for s in subnets if not bool(s.prohibit_public_ip_on_vnic)]
    if len(eligible) != 1:
        raise GuardError(
            f"Expected exactly one public subnet in VCN {vcn_id}; found {len(eligible)}. "
            "Set target.subnet_ocid explicitly after checking the correct subnet."
        )
    subnet = eligible[0]
    igws = oci.pagination.list_call_get_all_results(
        network.list_internet_gateways,
        compartment_id=tenancy_id,
        vcn_id=vcn_id,
    ).data
    enabled_igws = [g for g in igws if g.lifecycle_state == "AVAILABLE" and g.is_enabled]
    if not enabled_igws:
        raise GuardError("No AVAILABLE and enabled Internet Gateway found in the configured VCN.")
    route_table = network.get_route_table(subnet.route_table_id).data
    routes = getattr(route_table, "route_rules", []) or []
    route_ok = any(
        r.destination == "0.0.0.0/0"
        and any(g.id == r.network_entity_id for g in enabled_igws)
        for r in routes
    )
    if not route_ok:
        raise GuardError("Selected public subnet route table has no 0.0.0.0/0 route targeting an enabled Internet Gateway. No network changes were made.")
    LOG.info("Network verified: subnet=%s, public IPv4 allowed, default route to Internet Gateway present.", subnet.id)
    return subnet, route_table


def get_resource_availability(limits: Any, tenancy_id: str, service: str, limit_name: str, scope_type: str, ad: str) -> Any:
    kwargs: dict[str, Any] = {}
    if scope_type == "AD":
        kwargs["availability_domain"] = ad
    return limits.get_resource_availability(
        service_name=service,
        limit_name=limit_name,
        compartment_id=tenancy_id,
        **kwargs,
    ).data


def verify_live_a1_limits(limits: Any, tenancy_id: str, target: dict[str, Any]) -> dict[str, Any]:
    """Verify the standard A1 OCPU/memory limits; ignore DVH and reserved variants."""
    definitions = oci.pagination.list_call_get_all_results(
        limits.list_limit_definitions,
        compartment_id=tenancy_id,
        service_name="compute",
    ).data
    # OCI also returns DVH, regional, reservable and reserved variants. In
    # particular, DVH availability can be zero even when standard A1 quota
    # is available. Only use the ordinary AD-scoped standard A1 limits.
    wanted = {
        "ocpu": "standard-a1-core-count",
        "memory_gb": "standard-a1-memory-count",
    }
    results: dict[str, Any] = {}
    for label, limit_name in wanted.items():
        matches = [
            d for d in definitions
            if (d.name or "").lower() == limit_name
            and d.scope_type == "AD"
            and getattr(d, "is_resource_availability_supported", True)
        ]
        if len(matches) != 1:
            raise GuardError(
                f"Expected exactly one AD-scoped OCI limit named {limit_name}; "
                f"found {len(matches)}. Creation is blocked."
            )
        availability = get_resource_availability(
            limits, tenancy_id, "compute", limit_name, "AD",
            target["availability_domain"],
        )
        remaining = availability.available
        needed = float(target["ocpus"] if label == "ocpu" else target["memory_gb"])
        if remaining is None or float(remaining) < needed:
            raise GuardError(
                f"Insufficient or unknown live A1 {label} availability for {limit_name}: "
                f"{remaining!r} available, {needed:g} required."
            )
        results[label] = {
            "limit_name": limit_name,
            "available": remaining,
            "used": availability.used,
            "scope_type": "AD",
        }
    LOG.info(
        "Live standard A1 limits verified: CPU remaining=%s; memory remaining=%s GB.",
        results["ocpu"]["available"], results["memory_gb"]["available"],
    )
    return results


def sum_volume_usage(block: Any, identity: Any, tenancy_id: str, availability_domains: list[str]) -> dict[str, Any]:
    compartment_ids = list_compartments_recursive(identity, tenancy_id)
    boot_total = 0
    block_total = 0
    volumes = []
    for cid in compartment_ids:
        for ad in availability_domains:
            boot_volumes = oci.pagination.list_call_get_all_results(
                block.list_boot_volumes,
                compartment_id=cid,
                availability_domain=ad,
            ).data
            block_volumes = oci.pagination.list_call_get_all_results(
                block.list_volumes,
                compartment_id=cid,
                availability_domain=ad,
            ).data
            for volume in boot_volumes:
                if volume.lifecycle_state != "DELETED":
                    size = int(volume.size_in_gbs or 0)
                    boot_total += size
                    volumes.append({"kind": "boot", "id": volume.id, "gb": size, "state": volume.lifecycle_state})
            for volume in block_volumes:
                if volume.lifecycle_state != "DELETED":
                    size = int(volume.size_in_gbs or 0)
                    block_total += size
                    volumes.append({"kind": "block", "id": volume.id, "gb": size, "state": volume.lifecycle_state})
    return {"boot_gb": boot_total, "block_gb": block_total, "total_gb": boot_total + block_total, "volumes": volumes, "compartment_count": len(compartment_ids)}


def inspect_instances(compute: Any, identity: Any, tenancy_id: str, target: dict[str, Any]) -> dict[str, Any]:
    compartment_ids = list_compartments_recursive(identity, tenancy_id)
    instances = []
    for cid in compartment_ids:
        page = oci.pagination.list_call_get_all_results(
            compute.list_instances,
            compartment_id=cid,
        ).data
        instances.extend(page)
    # Keep TERMINATING instances in the inventory until OCI reports TERMINATED.
    active = [i for i in instances if i.lifecycle_state != "TERMINATED"]
    a1_instances = [i for i in active if i.shape == "VM.Standard.A1.Flex"]
    used_ocpu = sum(float(getattr(i.shape_config, "ocpus", 0) or 0) for i in a1_instances)
    used_memory = sum(float(getattr(i.shape_config, "memory_in_gbs", 0) or 0) for i in a1_instances)
    name_matches = [i for i in active if i.display_name == target["display_name"]]
    tag_matches = [i for i in active if (getattr(i, "freeform_tags", {}) or {}).get("managed-by") == "oci-free-watch"]
    duplicates = {i.id: i for i in (name_matches + tag_matches)}
    return {
        "instances": active,
        "a1_instances": a1_instances,
        "a1_ocpu_in_use": used_ocpu,
        "a1_memory_in_use_gb": used_memory,
        "target_matches": list(duplicates.values()),
        "compartment_count": len(compartment_ids),
    }


def verify_monthly_allowance(account: dict[str, Any], target: dict[str, Any]) -> dict[str, float]:
    # Budgets are operator-configured. Use Oracle Console and current policy to set them.
    # Max calendar month is 31 days = 744 hours.
    max_hours = 31 * 24
    projected_cpu = float(target["ocpus"]) * max_hours + float(account.get("other_monthly_a1_ocpu_hours", 0))
    projected_memory = float(target["memory_gb"]) * max_hours + float(account.get("other_monthly_a1_memory_gb_hours", 0))
    if projected_cpu > float(account.get("monthly_a1_ocpu_hours", 1500)):
        raise GuardError(f"Worst-case monthly A1 use would exceed the configured OCPU-hour budget ({projected_cpu:.0f} projected).")
    if projected_memory > float(account.get("monthly_a1_memory_gb_hours", 9000)):
        raise GuardError(f"Worst-case monthly A1 use would exceed the configured memory-hour budget ({projected_memory:.0f} projected).")
    return {"max_month_hours": float(max_hours), "projected_ocpu_hours": projected_cpu, "projected_memory_gb_hours": projected_memory}


def run_audit(clients: tuple[Any, Any, Any, Any, Any, Any], cfg: dict[str, Any], account: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    _, identity, compute, network, block, limits = clients
    tenancy_id = clients[0]["tenancy"]
    check_static_free_tier_policy(account, target)
    verify_home_region(identity, tenancy_id, target["region"])
    ads = get_availability_domains(identity, tenancy_id)
    if target["availability_domain"] not in ads:
        raise GuardError(f"Configured availability domain does not exist in this region. Available ADs: {ads}")
    subnet, route_table = inspect_network(network, tenancy_id, target)
    image = discover_image(compute, tenancy_id, target)
    volume_usage = sum_volume_usage(block, identity, tenancy_id, ads)
    if volume_usage["total_gb"] + int(target["boot_volume_size_gb"]) > int(account.get("combined_free_volume_gb", 200)):
        raise GuardError(
            f"Storage guard failed: existing active volumes use {volume_usage['total_gb']} GB; "
            f"adding {target['boot_volume_size_gb']} GB would exceed {account.get('combined_free_volume_gb', 200)} GB."
        )
    instance_usage = inspect_instances(compute, identity, tenancy_id, target)
    if instance_usage["a1_ocpu_in_use"] + float(target["ocpus"]) > float(account.get("a1_free_max_ocpu", 2)):
        raise GuardError("Existing A1 instances plus target would exceed the configured A1 OCPU allowance.")
    if instance_usage["a1_memory_in_use_gb"] + float(target["memory_gb"]) > float(account.get("a1_free_max_memory_gb", 12)):
        raise GuardError("Existing A1 instances plus target would exceed the configured A1 memory allowance.")
    monthly = verify_monthly_allowance(account, target)
    live_limits = None
    try:
        live_limits = verify_live_a1_limits(limits, tenancy_id, target)
    except Exception as exc:
        # Keep read-only audit useful; however, creation is explicitly blocked below.
        LOG.warning("Live Limits API check not complete (%s). Any launch will be blocked until it passes.", type(exc).__name__)
    ssh_path = Path(target["ssh_public_key_file"]).expanduser()
    ssh_ok = ssh_path.is_file() and bool(ssh_path.read_text(encoding="utf-8").strip())
    summary = {
        "home_region": target["region"],
        "availability_domain": target["availability_domain"],
        "subnet_ocid": subnet.id,
        "route_table_ocid": route_table.id,
        "image_ocid": image.id,
        "image_display_name": image.display_name,
        "image_console_always_free_confirmed": bool(
            str(target.get("image_ocid", "")).strip() == image.id
            and target.get("image_console_always_free_confirmed") is True
        ),
        "storage": volume_usage,
        "a1_ocpu_existing": instance_usage["a1_ocpu_in_use"],
        "a1_memory_existing_gb": instance_usage["a1_memory_in_use_gb"],
        "monthly_allowance_projection": monthly,
        "live_a1_limits": live_limits,
        "ssh_public_key_ready": ssh_ok,
        "current_month_usage_reviewed": account.get("current_month_usage_reviewed") is True,
        "creation_preflight_ready": bool(
            live_limits and ssh_ok
            and account.get("current_month_usage_reviewed") is True
            and str(target.get("image_ocid", "")).strip() == image.id
            and target.get("image_console_always_free_confirmed") is True
            and not instance_usage["target_matches"]
        ),
        "target_existing_instances": [
            {"id": i.id, "display_name": i.display_name, "state": i.lifecycle_state, "shape": i.shape}
            for i in instance_usage["target_matches"]
        ],
    }
    LOG.info("Read-only audit summary: %s", json.dumps({k: v for k, v in summary.items() if k != "storage"}, default=str))
    LOG.info("Existing block/boot storage: %s GB (boot=%s, block=%s); new boot volume=%s GB; combined after launch=%s GB.",
             volume_usage["total_gb"], volume_usage["boot_gb"], volume_usage["block_gb"],
             target["boot_volume_size_gb"], volume_usage["total_gb"] + int(target["boot_volume_size_gb"]))
    if not ssh_ok:
        LOG.warning("SSH public key file is not present/readable yet: %s", ssh_path)
    if account.get("current_month_usage_reviewed") is not True:
        LOG.warning("Current-month A1 usage has not been manually reviewed; launch remains blocked even if live quota checks pass.")
    if not summary["image_console_always_free_confirmed"]:
        LOG.warning("The image is only a compatible candidate. Pin its OCID and confirm the 'Always Free Eligible' Console label before enabling creation.")
    return summary


def capacity_available(compute: Any, tenancy_id: str, target: dict[str, Any]) -> tuple[bool, str]:
    shape_details = oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
        instance_shape=target["shape"],
        instance_shape_config=oci.core.models.CapacityReportInstanceShapeConfig(
            ocpus=float(target["ocpus"]), memory_in_gbs=float(target["memory_gb"])
        ),
    )
    details = oci.core.models.CreateComputeCapacityReportDetails(
        compartment_id=tenancy_id,
        availability_domain=target["availability_domain"],
        shape_availabilities=[shape_details],
    )
    response = compute.create_compute_capacity_report(
        details,
        retry_strategy=oci.retry.NoneRetryStrategy(),
    )
    entries = [entry for entry in (response.data.shape_availabilities or [])
               if entry.instance_shape == target["shape"]]
    matching = []
    for entry in entries:
        config = getattr(entry, "instance_shape_config", None)
        if config and abs(float(config.ocpus or 0) - float(target["ocpus"])) < 0.001 and abs(float(config.memory_in_gbs or 0) - float(target["memory_gb"])) < 0.001:
            matching.append(entry)
    if any(e.availability_status == "AVAILABLE" and int(e.available_count or 0) > 0 for e in matching):
        count = max(int(e.available_count or 0) for e in matching)
        return True, f"Capacity report: AVAILABLE (available_count={count}). This is not a reservation."
    statuses = sorted({f"{e.availability_status}:{e.available_count}" for e in matching})
    return False, "Capacity not currently reported for requested configuration (" + (", ".join(statuses) or "no matching shape config") + ")."


def is_capacity_error(exc: Exception) -> bool:
    if oci is None or not isinstance(exc, oci.exceptions.ServiceError):
        return False
    msg = f"{exc.code} {exc.message}".lower()
    return any(s in msg for s in ("out of host capacity", "capacity unavailable", "insufficient capacity", "host capacity"))


def is_transient_api_error(exc: Exception) -> bool:
    if oci is None or not isinstance(exc, oci.exceptions.ServiceError):
        return False
    return exc.status == 429 or exc.status >= 500 or exc.code in ("TooManyRequests", "ServiceUnavailable", "InternalServerError")


def describe_service_error(exc: Exception) -> str:
    if oci is not None and isinstance(exc, oci.exceptions.ServiceError):
        return f"OCI API error status={exc.status} code={exc.code}; request_id={exc.request_id or 'n/a'}"
    return f"{type(exc).__name__}: {exc}"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"created_instance_ocid": None, "launch_pending": None, "attempts": 0, "last_event": None}
    return read_json(path)


def save_state(path: Path, state: dict[str, Any], event: str) -> None:
    state["last_event"] = {"time": utc_now(), "event": event}
    write_json_atomic(path, state)


def wait_for_running(compute: Any, network: Any, instance_id: str, timeout_minutes: int, poll_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_minutes * 60
    last_state = "UNKNOWN"
    while time.monotonic() < deadline and not STOP_REQUESTED:
        instance = compute.get_instance(instance_id).data
        last_state = instance.lifecycle_state
        LOG.info("Instance lifecycle state: %s", last_state)
        if last_state == "RUNNING":
            attachments = oci.pagination.list_call_get_all_results(
                compute.list_vnic_attachments,
                compartment_id=instance.compartment_id,
                instance_id=instance_id,
            ).data
            public_ip = None
            private_ip = None
            for attachment in attachments:
                vnic = network.get_vnic(attachment.vnic_id).data
                public_ip = public_ip or getattr(vnic, "public_ip", None)
                private_ip = private_ip or getattr(vnic, "private_ip", None)
            return {
                "instance_ocid": instance.id,
                "display_name": instance.display_name,
                "lifecycle_state": instance.lifecycle_state,
                "shape": instance.shape,
                "ocpus": getattr(instance.shape_config, "ocpus", None),
                "memory_gb": getattr(instance.shape_config, "memory_in_gbs", None),
                "public_ip": public_ip,
                "private_ip": private_ip,
                "availability_domain": instance.availability_domain,
                "region": instance.region,
            }
        if last_state in ("TERMINATED", "TERMINATING"):
            raise GuardError(f"Instance entered {last_state}; inspect OCI Console. Automation will not relaunch automatically.")
        time.sleep(max(5, poll_seconds))
    raise TimeoutError(f"Instance did not reach RUNNING within {timeout_minutes} minutes (last state: {last_state}).")


def launch_one(compute: Any, tenancy_id: str, target: dict[str, Any], audit: dict[str, Any], state: dict[str, Any], state_path: Path, network: Any, mode: dict[str, Any]) -> dict[str, Any]:
    if not audit.get("creation_preflight_ready"):
        raise GuardError("Creation preflight is not ready (live A1 limits, SSH key, or duplicate check failed).")
    existing = audit.get("target_existing_instances") or []
    if existing:
        raise GuardError("An active instance with the target name/tag already exists. Duplicate launch prevented.")
    # Resolve exact Ubuntu image again immediately before launch.
    image = discover_image(compute, tenancy_id, target)
    ssh_public_key = Path(target["ssh_public_key_file"]).expanduser().read_text(encoding="utf-8").strip()
    if not ssh_public_key.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-")):
        raise GuardError("SSH public key file does not look like an OpenSSH public key.")
    if state.get("launch_pending"):
        pending_time = state["launch_pending"].get("created_at")
        raise GuardError(f"A previous launch is marked pending (created_at={pending_time}); refusing a second launch. Inspect OCI Console and state file manually.")
    token = str(uuid.uuid4())
    state["launch_pending"] = {"created_at": utc_now(), "opc_retry_token": token, "display_name": target["display_name"]}
    save_state(state_path, state, "launch_request_prepared")
    launch_details = oci.core.models.LaunchInstanceDetails(
        availability_domain=target["availability_domain"],
        compartment_id=tenancy_id,
        display_name=target["display_name"],
        shape=target["shape"],
        shape_config=oci.core.models.LaunchInstanceShapeConfigDetails(
            ocpus=float(target["ocpus"]),
            memory_in_gbs=float(target["memory_gb"]),
        ),
        source_details=oci.core.models.InstanceSourceViaImageDetails(
            source_type="image",
            image_id=image.id,
            boot_volume_size_in_gbs=int(target["boot_volume_size_gb"]),
            boot_volume_vpus_per_gb=int(target.get("boot_volume_vpus_per_gb", 10)),
        ),
        create_vnic_details=oci.core.models.CreateVnicDetails(
            subnet_id=audit["subnet_ocid"],
            assign_public_ip=bool(target["assign_public_ip"]),
        ),
        metadata={"ssh_authorized_keys": ssh_public_key},
        freeform_tags={"managed-by": "oci-free-watch", "free-tier-intent": "A1-Always-Free"},
    )
    LOG.warning("Submitting the one explicitly authorized %s launch request.", target["shape"])
    notify({}, f"OCI: launch initiated for {target['display_name']} ({target['ocpus']} OCPU, {target['memory_gb']} GB RAM, {target['boot_volume_size_gb']} GB boot).")
    response = compute.launch_instance(
        launch_details,
        opc_retry_token=token,
        retry_strategy=oci.retry.NoneRetryStrategy(),
    )
    instance_id = response.data.id
    state["launch_pending"]["instance_ocid"] = instance_id
    save_state(state_path, state, "launch_request_accepted")
    result = wait_for_running(
        compute,
        network,
        instance_id,
        int(mode.get("instance_wait_timeout_minutes", 40)),
        int(mode.get("instance_poll_seconds", 20)),
    )
    state["created_instance_ocid"] = instance_id
    state["launch_pending"] = None
    state["created_instance"] = result
    save_state(state_path, state, "instance_running")
    notify({}, f"OCI: instance RUNNING. OCID={result['instance_ocid']} Public IPv4={result['public_ip'] or 'not reported'} Private IP={result['private_ip'] or 'not reported'}")
    return result


def acquire_process_lock(lock_path: Path):
    """Acquire a non-blocking process lock on POSIX and Windows.

    The open handle must remain alive for the duration of the protected work.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write("0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise BlockingIOError("Another automation process already holds the lock.") from exc
    return handle


def calculate_wait_seconds(cfg: dict[str, Any], attempt: int, rate_limited: bool = False, retry_after: int | None = None) -> int:
    mode = cfg.get("mode", {})
    base = max(300, int(mode.get("capacity_poll_minutes", 20)) * 60)
    max_wait = max(base, int(mode.get("max_backoff_minutes", 180)) * 60)
    backoff = min(max_wait, base * (2 ** min(max(attempt - 1, 0), 8)))
    if retry_after is not None:
        backoff = min(max_wait, max(base, retry_after))
    return int(backoff * random.uniform(0.85, 1.15))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configurable OCI Always Free A1 capacity monitor (read-only by default)")
    parser.add_argument("--config", default=str(APP_DIR / "config.json"), help="Path to application JSON config")
    parser.add_argument("--validate-config", action="store_true", help="Validate local config and policy without connecting to OCI")
    parser.add_argument("--audit", action="store_true", help="Perform one read-only audit and exit")
    parser.add_argument("--once", action="store_true", help="Perform one audit and capacity check, then exit")
    parser.add_argument("--monitor", action="store_true", help="Continuously monitor (read-only unless separately armed)")
    parser.add_argument("--enable-create", action="store_true", help="Explicitly arm the single-instance launch path")
    args = parser.parse_args(argv)

    cfg_path = Path(args.config).expanduser().resolve()
    cfg = read_json(cfg_path)
    account, target, mode = require_config(cfg)
    check_static_free_tier_policy(account, target)
    if args.validate_config:
        if args.audit or args.once or args.monitor or args.enable_create:
            raise GuardError("--validate-config is an offline check and cannot be combined with OCI operations or creation flags.")
        print(json.dumps({
            "config_valid": True,
            "account_type": account.get("account_type"),
            "home_region": account.get("home_region"),
            "target": {
                "region": target.get("region"),
                "availability_domain": target.get("availability_domain"),
                "shape": target.get("shape"),
                "ocpus": target.get("ocpus"),
                "memory_gb": target.get("memory_gb"),
                "boot_volume_size_gb": target.get("boot_volume_size_gb"),
                "assign_public_ip": target.get("assign_public_ip"),
            },
            "image_ocid_pinned": bool(str(target.get("image_ocid", "")).strip()),
            "creation_enabled_in_config": mode.get("creation_enabled") is True,
        }, indent=2))
        return 0

    log_file = Path(cfg.get("paths", {}).get("log_file", str(APP_DIR / "logs/oci-free-watch.log"))).expanduser()
    state_file = Path(cfg.get("paths", {}).get("state_file", str(APP_DIR / "state/state.json"))).expanduser()
    setup_logging(log_file, cfg.get("logging", {}).get("level", "INFO"))

    # Single-process lock prevents duplicate monitor processes on POSIX and Windows.
    lock_path = state_file.with_suffix(".lock")
    try:
        lock_handle = acquire_process_lock(lock_path)
    except BlockingIOError:
        LOG.error("Another oci_free_watch process is already running.")
        return 2

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    oci_auth_path = Path(cfg.get("oci", {}).get("config_file", "~/.oci/config")).expanduser()
    profile = cfg.get("oci", {}).get("profile", "DEFAULT")
    clients = create_clients(oci_auth_path, profile, target["region"])
    LOG.info("OCI authentication validated. Tenancy OCID and secret material will not be logged.")
    notify(cfg, "OCI Always Free monitor: OCI API authentication succeeded.")

    if (args.audit or args.once) and args.enable_create:
        raise GuardError("--audit and --once are strictly read-only; do not combine them with --enable-create. Use --monitor for the separately guarded creation mode.")

    if args.audit:
        audit = run_audit(clients, cfg, account, target)
        print(json.dumps(audit, indent=2, default=str))
        LOG.info("Read-only audit completed. No capacity report or launch request was submitted.")
        return 0

    state = load_state(state_file)
    if state.get("created_instance_ocid"):
        LOG.info("A successful instance is already recorded (%s). Monitoring will not launch another instance.", state["created_instance_ocid"])
        return 0

    create_armed = bool(not args.audit and not args.once and args.enable_create
                        and mode.get("creation_enabled") is True
                        and mode.get("creation_confirmation") == "LAUNCH_ONE_ALWAYS_FREE_INSTANCE")
    if args.enable_create and not create_armed:
        raise GuardError("Creation not armed. Set creation_enabled=true AND creation_confirmation=LAUNCH_ONE_ALWAYS_FREE_INSTANCE, then pass --enable-create.")
    if not create_armed:
        LOG.info("READ-ONLY MODE: instance creation is disabled.")
    else:
        LOG.warning("CREATE MODE ARMED: exactly one A1 instance may be launched after all live guards pass.")

    attempt = 0
    LOG.info("Monitoring target: %s | %s OCPU | %s GB RAM | %s GB boot | %s.",
             target["shape"], target["ocpus"], target["memory_gb"], target["boot_volume_size_gb"], target["availability_domain"])
    notify(cfg, "OCI Always Free capacity monitoring started (read-only=" + str(not create_armed) + ").")

    while not STOP_REQUESTED:
        attempt += 1
        max_attempts = int(mode.get("max_attempts", 0))
        if max_attempts > 0 and attempt > max_attempts:
            LOG.warning("Configured maximum attempt count reached (%s). Stopping.", max_attempts)
            return 0
        try:
            LOG.info("Audit/capacity cycle %s started.", attempt)
            audit = run_audit(clients, cfg, account, target)
            existing = audit.get("target_existing_instances") or []
            if state.get("launch_pending") and not existing:
                raise GuardError(
                    "State records a previous launch request but no matching instance is visible. "
                    "The outcome may be ambiguous; inspect OCI Console and the state file before clearing it."
                )
            if existing:
                if len(existing) != 1:
                    raise GuardError("Multiple target instances were found; manual review required.")
                found = existing[0]
                LOG.warning("Found existing target instance %s in state %s; no duplicate will be created.", found["id"], found["state"])
                if found["shape"] != target["shape"]:
                    raise GuardError("An instance with the target display name/tag exists but has a different shape. Manual review required.")
                live_existing = clients[2].get_instance(found["id"]).data
                existing_shape_config = getattr(live_existing, "shape_config", None)
                if (not existing_shape_config
                    or abs(float(existing_shape_config.ocpus or 0) - float(target["ocpus"])) > 0.001
                    or abs(float(existing_shape_config.memory_in_gbs or 0) - float(target["memory_gb"])) > 0.001):
                    raise GuardError("An instance with the target display name/tag exists but has different OCPU/RAM. Manual review required.")
                if found["state"] in ("RUNNING", "PROVISIONING", "STARTING"):
                    result = wait_for_running(clients[2], clients[3], found["id"],
                                              int(mode.get("instance_wait_timeout_minutes", 40)),
                                              int(mode.get("instance_poll_seconds", 20)))
                    state["created_instance_ocid"] = result["instance_ocid"]
                    state["created_instance"] = result
                    state["launch_pending"] = None
                    save_state(state_file, state, "existing_instance_adopted")
                    notify(cfg, f"OCI: existing target VM is RUNNING. OCID={result['instance_ocid']} Public IP={result['public_ip']}")
                    return 0
                raise GuardError(f"Existing target instance is in {found['state']}; refusing to create a duplicate.")
            if not audit.get("live_a1_limits"):
                LOG.warning("Capacity monitoring only: live A1 quota API check is unavailable; launch remains blocked.")
            has_capacity, details = capacity_available(clients[2], clients[0]["tenancy"], target)
            LOG.info(details)
            if has_capacity and create_armed:
                LOG.warning("Capacity currently appears available. Re-running all preflight checks immediately before launch.")
                audit = run_audit(clients, cfg, account, target)
                if not audit.get("creation_preflight_ready"):
                    raise GuardError("Final launch preflight did not pass; no instance was created.")
                result = launch_one(clients[2], clients[0]["tenancy"], target, audit, state, state_file, clients[3], mode)
                LOG.info("SUCCESS: instance RUNNING: %s", json.dumps(result))
                notify(cfg, f"OCI: SUCCESS. Instance RUNNING. OCID={result['instance_ocid']} Public IPv4={result['public_ip'] or 'not assigned'}")
                return 0
            if has_capacity and not create_armed:
                LOG.info("Capacity is available, but READ-ONLY mode prevents launch. To arm later, use all three explicit creation switches.")
            else:
                notify(cfg, f"OCI A1 capacity is not currently reported for {target['ocpus']} OCPU / {target['memory_gb']} GB in the configured AD. Another check will be scheduled.")
            if args.once:
                LOG.info("One-shot capacity check completed. No instance launch occurred.")
                return 0
            wait_seconds = calculate_wait_seconds(cfg, attempt)
            LOG.info("Next check in approximately %s minutes.", round(wait_seconds / 60, 1))
            notify(cfg, f"OCI: next capacity check scheduled in approximately {round(wait_seconds / 60)} minutes.")
            save_state(state_file, state, "capacity_available" if has_capacity else "capacity_unavailable")
        except GuardError as exc:
            LOG.error("SAFETY/CONFIGURATION STOP: %s", exc)
            notify(cfg, f"OCI automation stopped for safety/configuration review: {exc}")
            return 3
        except Exception as exc:
            if is_capacity_error(exc):
                LOG.warning("Capacity-related launch/API error: %s", describe_service_error(exc))
                # A definite OCI capacity response means the launch was rejected, so it is safe to clear the pending marker.
                if state.get("launch_pending") and oci is not None and isinstance(exc, oci.exceptions.ServiceError):
                    state["launch_pending"] = None
                    save_state(state_file, state, "launch_rejected_for_capacity")
                wait_seconds = calculate_wait_seconds(cfg, attempt)
                notify(cfg, f"OCI: capacity-related API error; retry scheduled in approximately {round(wait_seconds / 60)} minutes.")
            elif is_transient_api_error(exc):
                if state.get("launch_pending") and oci is not None and isinstance(exc, oci.exceptions.ServiceError) and exc.status >= 500:
                    # A server error after launch submission can be ambiguous. Never blindly submit again.
                    LOG.error("Launch outcome may be ambiguous after server error; pending marker retained for manual reconciliation.")
                    notify(cfg, "OCI: launch outcome may be ambiguous after a server error. Automation halted to prevent duplicate creation.")
                    return 6
                if state.get("launch_pending") and oci is not None and isinstance(exc, oci.exceptions.ServiceError) and exc.status == 429:
                    state["launch_pending"] = None
                    save_state(state_file, state, "launch_rejected_rate_limited")
                retry_after = None
                if oci is not None and isinstance(exc, oci.exceptions.ServiceError):
                    try:
                        raw = (exc.headers or {}).get("retry-after")
                        retry_after = int(raw) if raw else None
                    except (TypeError, ValueError):
                        retry_after = None
                LOG.warning("Transient/rate-limit API error: %s", describe_service_error(exc))
                wait_seconds = calculate_wait_seconds(cfg, attempt, rate_limited=(getattr(exc, "status", None) == 429), retry_after=retry_after)
                notify(cfg, f"OCI: transient API/rate-limit error; retry scheduled in approximately {round(wait_seconds / 60)} minutes.")
            elif oci is not None and isinstance(exc, oci.exceptions.ServiceError):
                LOG.error("Non-retryable OCI API error: %s", describe_service_error(exc))
                notify(cfg, "OCI automation halted on non-retryable API error: " + describe_service_error(exc))
                return 4
            else:
                LOG.exception("Unexpected error; stopping to avoid blind retries.")
                notify(cfg, "OCI automation stopped after unexpected error: " + type(exc).__name__)
                return 5
        # Interruptible wait in 5-second slices.
        end_at = time.monotonic() + wait_seconds
        while not STOP_REQUESTED and time.monotonic() < end_at:
            time.sleep(min(5, max(0.1, end_at - time.monotonic())))
        if args.audit or args.once:
            return 0

    LOG.info("Shutdown complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GuardError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        raise SystemExit(3)