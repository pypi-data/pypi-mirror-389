"""
Tests for enhanced Chinese APT campaign tools.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from apt_toolkit.chinese_apt_campaign import (
    AdvancedTargetingEngine,
    CampaignOrchestrator,
    SystemExploitationEngine
)


class TestAdvancedTargetingEngine(unittest.TestCase):
    """Test the AdvancedTargetingEngine class."""
    
    def setUp(self):
        self.engine = AdvancedTargetingEngine(seed=42)
    
    def test_generate_government_targets(self):
        """Test government target generation."""
        targets = self.engine.generate_government_targets()
        
        self.assertIsInstance(targets, list)
        self.assertGreater(len(targets), 0)
        
        # Check structure of first target
        first_target = targets[0]
        self.assertIn("domain", first_target)
        self.assertIn("ip_range", first_target)
        self.assertIn("organization_type", first_target)
        self.assertIn("sensitivity_level", first_target)
        self.assertIn("primary_technologies", first_target)
        self.assertIn("attack_vectors", first_target)
        self.assertIn("priority_level", first_target)
    
    def test_generate_military_targets(self):
        """Test military target generation."""
        targets = self.engine.generate_military_targets()
        
        self.assertIsInstance(targets, list)
        self.assertGreater(len(targets), 0)
        
        # Check structure of first target
        first_target = targets[0]
        self.assertIn("domain", first_target)
        self.assertIn("ip_range", first_target)
        self.assertIn("command_level", first_target)
        self.assertIn("geographic_region", first_target)
        self.assertIn("mission_type", first_target)
        self.assertIn("primary_technologies", first_target)
    
    def test_generate_critical_infrastructure_targets(self):
        """Test critical infrastructure target generation."""
        targets = self.engine.generate_critical_infrastructure_targets()
        
        self.assertIsInstance(targets, list)
        self.assertGreater(len(targets), 0)
        
        # Check structure of first target
        first_target = targets[0]
        self.assertIn("domain", first_target)
        self.assertIn("sector", first_target)
        self.assertIn("ip_range", first_target)
        self.assertIn("criticality_level", first_target)
        self.assertIn("primary_technologies", first_target)
        self.assertIn("attack_vectors", first_target)


class TestCampaignOrchestrator(unittest.TestCase):
    """Test the CampaignOrchestrator class."""
    
    def setUp(self):
        self.orchestrator = CampaignOrchestrator(seed=42)
    
    def test_orchestrate_comprehensive_campaign(self):
        """Test comprehensive campaign orchestration."""
        campaign = self.orchestrator.orchestrate_comprehensive_campaign()
        
        self.assertIsInstance(campaign, dict)
        self.assertIn("campaign_id", campaign)
        self.assertIn("start_date", campaign)
        self.assertIn("duration_days", campaign)
        self.assertIn("target_types", campaign)
        self.assertIn("targets", campaign)
        self.assertIn("risk_assessment", campaign)
        self.assertIn("success_metrics", campaign)
        
        # Check targets structure
        targets = campaign["targets"]
        self.assertIn("government", targets)
        self.assertIn("military", targets)
        self.assertIn("infrastructure", targets)
    
    def test_orchestrate_focused_campaign(self):
        """Test focused campaign orchestration."""
        campaign = self.orchestrator.orchestrate_focused_campaign(
            target_sector="government",
            primary_objectives=["data_theft", "network_access"]
        )
        
        self.assertIsInstance(campaign, dict)
        self.assertIn("campaign_id", campaign)
        self.assertIn("campaign_type", campaign)
        self.assertEqual(campaign["campaign_type"], "focused")
        self.assertEqual(campaign["target_sector"], "government")
        self.assertEqual(campaign["primary_objectives"], ["data_theft", "network_access"])
        self.assertIn("targets", campaign)
        self.assertIn("risk_assessment", campaign)
        self.assertIn("success_metrics", campaign)


class TestSystemExploitationEngine(unittest.TestCase):
    """Test the SystemExploitationEngine class."""
    
    def setUp(self):
        self.engine = SystemExploitationEngine(seed=42)
    
    def test_exploit_government_systems(self):
        """Test government system exploitation planning."""
        target = {
            "domain": "state.gov",
            "primary_technologies": ["Active Directory", "Exchange", "Windows Server"]
        }
        
        exploitation_plan = self.engine.exploit_government_systems(target)
        
        self.assertIsInstance(exploitation_plan, dict)
        self.assertEqual(exploitation_plan["target_domain"], "state.gov")
        self.assertIn("exploitation_vectors", exploitation_plan)
        self.assertIn("payload_delivery", exploitation_plan)
        self.assertIn("persistence_mechanisms", exploitation_plan)
        self.assertIn("lateral_movement", exploitation_plan)
        self.assertIn("data_exfiltration", exploitation_plan)
        self.assertIn("detection_evasion", exploitation_plan)
    
    def test_exploit_military_systems(self):
        """Test military system exploitation planning."""
        target = {
            "domain": "centcom.mil",
            "primary_technologies": ["Military Networks", "Tactical Systems"],
            "mission_type": "CYBER_OPERATIONS"
        }
        
        exploitation_plan = self.engine.exploit_military_systems(target)
        
        self.assertIsInstance(exploitation_plan, dict)
        self.assertEqual(exploitation_plan["target_domain"], "centcom.mil")
        self.assertEqual(exploitation_plan["mission_type"], "CYBER_OPERATIONS")
        self.assertIn("exploitation_vectors", exploitation_plan)
        self.assertIn("payload_delivery", exploitation_plan)
        self.assertIn("persistence_mechanisms", exploitation_plan)
        self.assertIn("command_control", exploitation_plan)
    
    def test_exploit_infrastructure_systems(self):
        """Test infrastructure system exploitation planning."""
        target = {
            "domain": "doe.gov",
            "sector": "energy",
            "primary_technologies": ["SCADA", "ICS", "Smart Grid"]
        }
        
        exploitation_plan = self.engine.exploit_infrastructure_systems(target)
        
        self.assertIsInstance(exploitation_plan, dict)
        self.assertEqual(exploitation_plan["target_domain"], "doe.gov")
        self.assertEqual(exploitation_plan["sector"], "energy")
        self.assertIn("exploitation_vectors", exploitation_plan)
        self.assertIn("payload_delivery", exploitation_plan)
        self.assertIn("persistence_mechanisms", exploitation_plan)
        self.assertIn("system_control", exploitation_plan)


class TestIntegration(unittest.TestCase):
    """Integration tests for the Chinese APT campaign toolkit."""
    
    def test_end_to_end_campaign_planning(self):
        """Test end-to-end campaign planning workflow."""
        
        # Create engines
        targeting_engine = AdvancedTargetingEngine(seed=42)
        exploitation_engine = SystemExploitationEngine(seed=42)
        orchestrator = CampaignOrchestrator(seed=42)
        
        # Generate targets
        government_targets = targeting_engine.generate_government_targets()
        military_targets = targeting_engine.generate_military_targets()
        
        # Create exploitation plans
        gov_exploitation = exploitation_engine.exploit_government_systems(government_targets[0])
        mil_exploitation = exploitation_engine.exploit_military_systems(military_targets[0])
        
        # Orchestrate campaign
        campaign = orchestrator.orchestrate_comprehensive_campaign()
        
        # Verify results
        self.assertIsInstance(government_targets, list)
        self.assertIsInstance(military_targets, list)
        self.assertIsInstance(gov_exploitation, dict)
        self.assertIsInstance(mil_exploitation, dict)
        self.assertIsInstance(campaign, dict)
        
        # Check campaign structure
        self.assertIn("targets", campaign)
        self.assertIn("government", campaign["targets"])
        self.assertIn("military", campaign["targets"])
        self.assertIn("infrastructure", campaign["targets"])


if __name__ == "__main__":
    unittest.main()