import unittest
from argparse import Namespace
from datetime import datetime
from unittest.mock import patch
from click.testing import CliRunner

from apt_toolkit.american_targets import analyze_american_targets
from apt_toolkit.cli_new import apt


class AmericanTargetsAnalysisTests(unittest.TestCase):
    def test_analysis_includes_profiles_and_supply_chain(self):
        with patch("apt_toolkit.american_targets.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)

            analysis = analyze_american_targets()

        self.assertIn("american_networks", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("supply_chain_readiness", analysis)
        self.assertGreater(len(analysis["american_networks"]), 0)
        self.assertEqual(
            len(analysis["target_profiles"]), len(analysis["american_networks"])
        )
        self.assertEqual(
            len(analysis["supply_chain_readiness"]),
            len(analysis["american_networks"]),
        )
        for profile in analysis["target_profiles"]:
            self.assertIn("target_domain", profile)
            self.assertIn("target_email", profile)
            self.assertIn("lure", profile)

    def test_handle_command_routes_to_american_targets(self):
        runner = CliRunner()
        with patch("apt_toolkit.cli_new.analyze_american_targets", return_value={"mock": True}) as mock_analyze:
            result = runner.invoke(apt, ["american", "targets"])

        self.assertEqual(result.exit_code, 0)
        mock_analyze.assert_called_once_with()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
