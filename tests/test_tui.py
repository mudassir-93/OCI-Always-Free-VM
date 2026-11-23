import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from oci_platform.cli import read_config, write_config
from oci_platform.tui import (
    UserCancelled,
    run_config_wizard,
    select_home_action,
    validate_configuration,
)


def valid_config(root: Path) -> dict:
    sdk_config = root / "oci-config"
    sdk_config.write_text(
        "[DEFAULT]\nuser=local-placeholder\nfingerprint=00:00\nkey_file=/local/private-key.pem\n"
        "tenancy=local-placeholder\nregion=us-phoenix-1\n",
        encoding="utf-8",
    )
    public_key = root / "id_ed25519.pub"
    public_key.write_text("ssh-ed25519 AAAA-local-placeholder user@machine\n", encoding="utf-8")
    state_dir = root / "state"
    return {
        "oci": {"config_file": str(sdk_config), "profile": "DEFAULT"},
        "account": {
            "account_type": "FREE_TIER",
            "free_tier_only_confirmed": True,
            "allow_paid_resources": False,
            "home_region": "us-phoenix-1",
            "a1_free_max_ocpu": 2,
            "a1_free_max_memory_gb": 12,
            "combined_free_volume_gb": 200,
            "monthly_a1_ocpu_hours": 1500,
            "monthly_a1_memory_gb_hours": 9000,
            "other_monthly_a1_ocpu_hours": 0,
            "other_monthly_a1_memory_gb_hours": 0,
            "current_month_usage_reviewed": False,
        },
        "target": {
            "region": "us-phoenix-1",
            "availability_domain": "example-ad",
            "vcn_ocid": "ocid1.vcn.local-placeholder",
            "subnet_ocid": "",
            "display_name": "local-test-instance",
            "shape": "VM.Standard.A1.Flex",
            "ocpus": 2,
            "memory_gb": 4,
            "operating_system": "Canonical Ubuntu",
            "operating_system_version": "24.04",
            "boot_volume_size_gb": 150,
            "boot_volume_vpus_per_gb": 10,
            "assign_public_ip": True,
            "ssh_public_key_file": str(public_key),
            "image_ocid": "ocid1.image.local-placeholder",
            "image_console_always_free_confirmed": False,
        },
        "mode": {
            "creation_enabled": False,
            "creation_confirmation": "",
            "capacity_poll_minutes": 20,
            "max_backoff_minutes": 180,
            "max_attempts": 0,
            "instance_wait_timeout_minutes": 40,
            "instance_poll_seconds": 20,
        },
        "paths": {
            "log_file": str(state_dir / "logs" / "app.log"),
            "state_file": str(state_dir / "state" / "state.json"),
        },
        "logging": {"level": "INFO"},
    }


class TuiValidationTests(unittest.TestCase):
    def test_complete_local_configuration_passes_without_oci_calls(self):
        with tempfile.TemporaryDirectory() as temp:
            config = valid_config(Path(temp))
            self.assertEqual(validate_configuration(config), [])

    def test_bad_region_and_region_mismatch_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            config = valid_config(Path(temp))
            config["account"]["home_region"] = "u7euw"
            config["target"]["region"] = "eu-frankfurt-1"
            issues = validate_configuration(config)
            self.assertTrue(any("valid tenancy home region" in item for item in issues))
            self.assertTrue(any("must match" in item for item in issues))

    def test_non_a1_shape_and_fractional_compute_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            config = valid_config(Path(temp))
            config["target"]["shape"] = "VM.Standard.E5.Flex"
            config["target"]["ocpus"] = 1.5
            issues = validate_configuration(config)
            self.assertTrue(any("only VM.Standard.A1.Flex" in item for item in issues))
            self.assertTrue(any("whole numbers" in item for item in issues))

    def test_invalid_ssh_path_and_vcn_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            config = valid_config(Path(temp))
            config["target"]["ssh_public_key_file"] = str(Path(temp) / "missing.pub")
            config["target"]["vcn_ocid"] = "not-an-ocid"
            issues = validate_configuration(config)
            self.assertTrue(any("VCN OCID" in item for item in issues))
            self.assertTrue(any("PUBLIC key file" in item for item in issues))


class TuiPersistenceTests(unittest.TestCase):
    def test_save_creates_backup_and_always_disarms_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "config.json"
            config = valid_config(root)
            config["mode"]["creation_enabled"] = True
            config["mode"]["creation_confirmation"] = "LAUNCH_ONE_ALWAYS_FREE_INSTANCE"
            write_config(config_path, config)

            with patch("oci_platform.tui._confirm", side_effect=[True, True]), patch(
                "oci_platform.tui._select", return_value="Save configuration"
            ):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = run_config_wizard(
                        config_path,
                        default_state_dir=root / "state",
                        read_config=read_config,
                        write_config=write_config,
                    )

            self.assertEqual(result, 0)
            updated = read_config(config_path)
            self.assertFalse(updated["mode"]["creation_enabled"])
            self.assertEqual(updated["mode"]["creation_confirmation"], "")
            backups = list(root.glob("config.json.*.bak"))
            self.assertEqual(len(backups), 1)
            previous = read_config(backups[0])
            self.assertTrue(previous["mode"]["creation_enabled"])
            self.assertEqual(previous["mode"]["creation_confirmation"], "LAUNCH_ONE_ALWAYS_FREE_INSTANCE")
            self.assertIn("VM creation remains DISABLED", output.getvalue())
            output.getvalue().encode("cp1252")

    def test_cancel_leaves_existing_file_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config_path = root / "config.json"
            config = valid_config(root)
            config["mode"]["creation_enabled"] = True
            config["mode"]["creation_confirmation"] = "LAUNCH_ONE_ALWAYS_FREE_INSTANCE"
            write_config(config_path, config)
            original = read_config(config_path)

            output = io.StringIO()
            with patch("oci_platform.tui._confirm", return_value=True), patch(
                "oci_platform.tui._select", return_value="Cancel without saving"
            ), contextlib.redirect_stdout(output):
                result = run_config_wizard(
                    config_path,
                    default_state_dir=root / "state",
                    read_config=read_config,
                    write_config=write_config,
                )

            # The UI is intentionally printable on the default Windows cp1252 console.
            output.getvalue().encode("cp1252")
            self.assertEqual(result, 1)
            self.assertEqual(read_config(config_path), original)
            self.assertEqual(list(root.glob("config.json.*.bak")), [])

    def test_escape_or_ctrl_c_cancellation_is_reported_as_clean_cancel(self):
        with patch("oci_platform.tui.questionary.select") as prompt:
            prompt.return_value.ask.return_value = None
            with self.assertRaises(UserCancelled):
                select_home_action()


if __name__ == "__main__":
    unittest.main()
