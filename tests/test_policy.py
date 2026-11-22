import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "oci_free_watch.py"
spec = importlib.util.spec_from_file_location("oci_free_watch", MODULE_PATH)
app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(app)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.account = {
            "account_type": "FREE_TIER", "free_tier_only_confirmed": True,
            "allow_paid_resources": False, "home_region": "us-phoenix-1",
            "a1_free_max_ocpu": 2, "a1_free_max_memory_gb": 12,
            "combined_free_volume_gb": 200,
            "monthly_a1_ocpu_hours": 1500, "monthly_a1_memory_gb_hours": 9000,
            "other_monthly_a1_ocpu_hours": 0, "other_monthly_a1_memory_gb_hours": 0,
        }
        self.target = {
            "region": "us-phoenix-1", "availability_domain": "ABCD:US-PHOENIX-1-AD-1",
            "shape": "VM.Standard.A1.Flex", "ocpus": 2, "memory_gb": 4,
            "boot_volume_size_gb": 150, "operating_system": "Canonical Ubuntu",
            "operating_system_version": "24.04", "assign_public_ip": True,
            "boot_volume_vpus_per_gb": 10,
        }

    def test_approved_target_passes_static_guard(self):
        app.check_static_free_tier_policy(self.account, self.target)
        result = app.verify_monthly_allowance(self.account, self.target)
        self.assertEqual(result["projected_ocpu_hours"], 1488)
        self.assertEqual(result["projected_memory_gb_hours"], 2976)

    def test_paid_resource_is_rejected(self):
        self.target["shape"] = "VM.Standard.E5.Flex"
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)

    def test_wrong_region_is_rejected(self):
        self.target["region"] = "us-ashburn-1"
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)

    def test_configurable_a1_target_within_limits_passes(self):
        self.target["ocpus"] = 1
        self.target["memory_gb"] = 6
        self.target["boot_volume_size_gb"] = 100
        app.check_static_free_tier_policy(self.account, self.target)

    def test_target_above_configured_cpu_limit_is_rejected(self):
        self.target["ocpus"] = 3
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)

    def test_target_above_configured_memory_limit_is_rejected(self):
        self.target["memory_gb"] = 13
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)

    def test_boot_volume_below_minimum_is_rejected(self):
        self.target["boot_volume_size_gb"] = 49
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)

    def test_empty_home_region_is_rejected(self):
        self.account["home_region"] = ""
        self.target["region"] = ""
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)

    def test_paid_upgrade_attestation_is_required(self):
        self.account["account_type"] = "PAYG"
        with self.assertRaises(app.GuardError):
            app.check_static_free_tier_policy(self.account, self.target)


if __name__ == "__main__":
    unittest.main()
