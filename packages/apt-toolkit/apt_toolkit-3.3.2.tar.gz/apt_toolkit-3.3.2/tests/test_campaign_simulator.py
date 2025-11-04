import unittest

from apt_toolkit.campaign import APTCampaignSimulator, CampaignConfig


class CampaignSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.seed = 1234
        self.simulator = APTCampaignSimulator(seed=self.seed)

    def test_campaign_simulation_produces_all_phases(self):
        report = self.simulator.simulate(CampaignConfig(seed=self.seed))

        self.assertIn("initial_access", report)
        self.assertIn("campaign_timeline", report)
        self.assertEqual(len(report["campaign_timeline"]), 7)
        self.assertTrue(report["initial_access"]["target_email"].endswith("secure.dod.mil"))
        self.assertGreater(len(report["lateral_movement"]["stolen_hashes"]), 0)
        for credential in report["lateral_movement"]["stolen_hashes"]:
            self.assertIn("username", credential)
            self.assertIn("hash", credential)

    def test_campaign_respects_config_toggles(self):
        report = self.simulator.simulate(
            CampaignConfig(
                seed=self.seed,
                include_supply_chain=False,
                include_counter_forensics=False,
            )
        )

        self.assertIsNone(report["initial_access"]["supply_chain"])
        self.assertIsNone(report["persistence"]["counter_forensics"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
