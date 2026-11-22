import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from oci_platform.cli import (
    default_config_path,
    initialize_config,
    main,
    read_config,
    write_config,
)

import oci_free_watch as engine


class CliSetupTests(unittest.TestCase):
    def test_setup_creates_creation_disabled_user_config(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            with patch("oci_platform.cli.default_state_dir", return_value=Path(temp) / "state"):
                self.assertTrue(initialize_config(config_path))
            config = read_config(config_path)
            self.assertFalse(config["mode"]["creation_enabled"])
            self.assertEqual(config["mode"]["creation_confirmation"], "")
            self.assertTrue(Path(config["paths"]["log_file"]).is_absolute())
            self.assertTrue(Path(config["paths"]["state_file"]).is_absolute())
            self.assertTrue(Path(config["paths"]["log_file"]).parent.is_dir())
            self.assertTrue(Path(config["paths"]["state_file"]).parent.is_dir())

    def test_setup_never_overwrites_existing_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            original = {"operator_setting": "keep-me"}
            write_config(config_path, original)
            self.assertFalse(initialize_config(config_path))
            self.assertEqual(read_config(config_path), original)

    def test_setup_command_is_local_and_does_not_contact_oci(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["--config", str(config_path), "setup"])
            self.assertEqual(result, 0)
            self.assertTrue(config_path.is_file())
            self.assertIn("creation-disabled", output.getvalue())

    def test_setup_command_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            config_path.write_text('{"keep": true}', encoding="utf-8")
            result = main(["--config", str(config_path), "setup"])
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8")), {"keep": True})

    def test_config_show_does_not_print_ocids(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            config = {
                "oci": {"profile": "DEFAULT"},
                "account": {"home_region": "us-phoenix-1"},
                "target": {
                    "region": "us-phoenix-1",
                    "availability_domain": "example-ad",
                    "shape": "VM.Standard.A1.Flex",
                    "ocpus": 2,
                    "memory_gb": 4,
                    "boot_volume_size_gb": 100,
                    "vcn_ocid": "ocid1.vcn.secret-example",
                },
                "mode": {"creation_enabled": False},
            }
            write_config(config_path, config)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["--config", str(config_path), "config", "show"])
            self.assertEqual(result, 0)
            self.assertNotIn("ocid1.vcn.secret-example", output.getvalue())
            self.assertIn("Credentials and OCIDs are not displayed.", output.getvalue())

    def test_profile_list_displays_names_not_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            oci_config = root / "oci-config"
            oci_config.write_text(
                "[DEFAULT]\nuser=ocid1.user.secret\nkey_file=/private/key.pem\n"
                "[SECONDARY]\nuser=ocid1.user.other\nkey_file=/other/key.pem\n",
                encoding="utf-8",
            )
            app_config = root / "app.json"
            write_config(app_config, {
                "oci": {"config_file": str(oci_config), "profile": "DEFAULT"}
            })
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(["--config", str(app_config), "profile", "list"])
            self.assertEqual(result, 0)
            self.assertIn("DEFAULT", output.getvalue())
            self.assertIn("SECONDARY", output.getvalue())
            self.assertNotIn("ocid1.user.secret", output.getvalue())
            self.assertNotIn("/private/key.pem", output.getvalue())

    def test_profile_use_changes_only_selected_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            oci_config = root / "oci-config"
            oci_config.write_text(
                "[DEFAULT]\nuser=placeholder\n[SECONDARY]\nuser=another-placeholder\n",
                encoding="utf-8",
            )
            app_config = root / "app.json"
            write_config(app_config, {
                "oci": {"config_file": str(oci_config), "profile": "DEFAULT"},
                "mode": {"creation_enabled": False},
            })
            result = main(["--config", str(app_config), "profile", "use", "SECONDARY"])
            self.assertEqual(result, 0)
            updated = read_config(app_config)
            self.assertEqual(updated["oci"]["profile"], "SECONDARY")
            self.assertFalse(updated["mode"]["creation_enabled"])

    def test_default_config_environment_override(self):
        with tempfile.TemporaryDirectory() as temp:
            expected = Path(temp) / "custom.json"
            with patch.dict(os.environ, {"OCI_PLATFORM_CONFIG": str(expected)}):
                self.assertEqual(default_config_path(), expected)


class CliEngineIntegrationTests(unittest.TestCase):
    def _valid_config(self, path: Path) -> None:
        config = {
            "oci": {"config_file": str(path.parent / "oci-config"), "profile": "DEFAULT"},
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
                "vcn_ocid": "placeholder-vcn",
                "subnet_ocid": "",
                "display_name": "test-a1-instance",
                "shape": "VM.Standard.A1.Flex",
                "ocpus": 2,
                "memory_gb": 4,
                "operating_system": "Canonical Ubuntu",
                "operating_system_version": "24.04",
                "boot_volume_size_gb": 150,
                "boot_volume_vpus_per_gb": 10,
                "assign_public_ip": True,
                "ssh_public_key_file": "~/.ssh/id_ed25519.pub",
                "image_ocid": "",
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
            "paths": {"log_file": str(path.parent / "app.log"), "state_file": str(path.parent / "state.json")},
            "logging": {"level": "INFO"},
        }
        write_config(path, config)

    def test_engine_main_accepts_explicit_argv_for_offline_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            self._valid_config(config_path)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = engine.main(["--config", str(config_path), "--validate-config"])
            self.assertEqual(result, 0)
            self.assertIn('"config_valid": true', output.getvalue())

    def test_vm_audit_maps_to_read_only_engine_arguments(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            write_config(config_path, {"oci": {}, "mode": {"creation_enabled": False}})
            captured = {}

            def fake_engine(arguments):
                captured["arguments"] = arguments
                return 0

            with patch("oci_platform.cli._engine_main", side_effect=fake_engine):
                result = main(["--config", str(config_path), "vm", "audit"])
            self.assertEqual(result, 0)
            self.assertIn("--audit", captured["arguments"])
            self.assertNotIn("--enable-create", captured["arguments"])

    def test_vm_monitor_is_read_only_unless_explicit_flag_is_passed(self):
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            write_config(config_path, {"oci": {}, "mode": {"creation_enabled": False}})
            captured = []

            with patch("oci_platform.cli._engine_main", side_effect=lambda args: captured.append(args) or 0):
                self.assertEqual(main(["--config", str(config_path), "vm", "monitor"]), 0)
                self.assertEqual(main(["--config", str(config_path), "vm", "monitor", "--enable-create"]), 0)

            self.assertNotIn("--enable-create", captured[0])
            self.assertIn("--enable-create", captured[1])

    def test_process_lock_is_exclusive_and_released_on_close(self):
        with tempfile.TemporaryDirectory() as temp:
            lock_path = Path(temp) / "automation.lock"
            first = engine.acquire_process_lock(lock_path)
            try:
                child_code = """
import sys
from pathlib import Path
import oci_free_watch
try:
    handle = oci_free_watch.acquire_process_lock(Path(sys.argv[1]))
except BlockingIOError:
    raise SystemExit(23)
handle.close()
raise SystemExit(0)
"""
                child = subprocess.run(
                    [sys.executable, "-c", child_code, str(lock_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(child.returncode, 23, child.stdout + child.stderr)
            finally:
                first.close()
            second = engine.acquire_process_lock(lock_path)
            second.close()


if __name__ == "__main__":
    unittest.main()
