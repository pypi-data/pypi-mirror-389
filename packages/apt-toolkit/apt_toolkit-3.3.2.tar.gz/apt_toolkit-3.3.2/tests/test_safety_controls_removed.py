"""
Test to verify that safety controls have been removed and toolkit can run on any target
"""

import unittest
import os
import sys

class TestSafetyControlsRemoved(unittest.TestCase):
    
    def test_security_controls_file_removed(self):
        """Test that security_controls.py file has been removed."""
        security_controls_path = os.path.join("apt_toolkit", "security_controls.py")
        self.assertFalse(os.path.exists(security_controls_path), 
                        "security_controls.py should have been removed")
    
    def test_no_security_controls_imports(self):
        """Test that no modules import from security_controls."""
        # Check initial_access.py
        with open("apt_toolkit/initial_access.py", "r") as f:
            initial_access_content = f.read()
        self.assertNotIn("from .security_controls", initial_access_content,
                        "initial_access.py should not import from security_controls")
        self.assertNotIn("@require_authorization", initial_access_content,
                        "initial_access.py should not use authorization decorators")
        
        # Check persistence.py
        with open("apt_toolkit/persistence.py", "r") as f:
            persistence_content = f.read()
        self.assertNotIn("from .security_controls", persistence_content,
                        "persistence.py should not import from security_controls")
        self.assertNotIn("@require_authorization", persistence_content,
                        "persistence.py should not use authorization decorators")
    
    def test_cli_runs_without_authorization(self):
        """Test that CLI commands run without requiring authorization."""
        from apt_toolkit.cli import handle_command
        from argparse import Namespace
        
        # Test initial access command
        args = Namespace(
            module="initial-access",
            generate_email=True,
            analyze_campaign=False,
            supply_chain=False
        )
        
        result = handle_command(args)
        self.assertIn("spear_phishing_email", result)
        self.assertIsNotNone(result["spear_phishing_email"])
        
        # Test persistence command
        args = Namespace(
            module="persistence",
            analyze=True,
            generate_report=False
        )
        
        result = handle_command(args)
        self.assertIn("persistence_analysis", result)
        self.assertIsNotNone(result["persistence_analysis"])
    
    def test_campaign_simulation_runs(self):
        """Test that campaign simulation runs without safety controls."""
        from apt_toolkit.campaign import APTCampaignSimulator, CampaignConfig
        
        simulator = APTCampaignSimulator(seed=42)
        config = CampaignConfig(target_domain="test.corp", seed=42)
        
        report = simulator.simulate(config)
        
        self.assertIn("initial_access", report)
        self.assertIn("persistence", report)
        self.assertIn("privilege_escalation", report)
        self.assertIn("campaign_timeline", report)


if __name__ == "__main__":
    unittest.main()