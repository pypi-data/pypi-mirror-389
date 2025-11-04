import random
import unittest
from datetime import datetime
from unittest.mock import patch

from apt_toolkit.initial_access_enhanced import AdvancedSocialEngineering, SupplyChainCompromise


class _FixedDateTime(datetime):
    """Deterministic datetime replacement for testing."""

    @classmethod
    def now(cls, tz=None):  # pragma: no cover - simple wrapper
        return cls(2024, 5, 17, 12, 0, 0, tzinfo=tz)


class AdvancedSocialEngineeringTests(unittest.TestCase):
    def test_create_context_aware_lure_includes_quarter_label(self):
        random.seed(0)
        social_engineering = AdvancedSocialEngineering()
        dossier = social_engineering.build_target_dossier("security.admin@dod.mil")

        with patch("apt_toolkit.initial_access_enhanced.datetime", _FixedDateTime):
            lure = social_engineering.create_context_aware_lure(dossier)

        self.assertIn("Q2 2024", lure["subject"])
        self.assertEqual(
            lure["timing"],
            dossier["engagement_windows"]["optimal_engagement"],
        )


class SupplyChainCompromiseTests(unittest.TestCase):
    def setUp(self):
        self.supply_chain = SupplyChainCompromise()

    def test_malicious_update_defers_during_business_hours(self):
        with patch("apt_toolkit.initial_access_enhanced.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 5, 17, 10, 0, 0)
            result = self.supply_chain.malicious_update_check("10.0.0.5", "secure.dod.mil")

        self.assertFalse(result["should_activate"])
        self.assertEqual(result["activation_reason"], "Deferred during business hours")
        self.assertEqual(result["sleep_duration"], 3600 * 8)

    def test_malicious_update_activates_after_hours(self):
        with patch("apt_toolkit.initial_access_enhanced.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 5, 17, 20, 0, 0)
            result = self.supply_chain.malicious_update_check("10.0.0.5", "secure.dod.mil")

        self.assertTrue(result["should_activate"])
        self.assertEqual(result["activation_reason"], "Government network detected")
        self.assertNotIn("sleep_duration", result)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
