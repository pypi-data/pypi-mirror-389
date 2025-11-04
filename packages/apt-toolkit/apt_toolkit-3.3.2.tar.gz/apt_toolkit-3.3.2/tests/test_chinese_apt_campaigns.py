"""
Tests for Chinese APT Campaign Simulations
"""

import unittest
import sys
import os

# Add the campaigns directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from campaigns.chinese_apts.apt41_campaign import APT41CampaignSimulator, APT41CampaignConfig
from campaigns.chinese_apts.apt1_campaign import APT1CampaignSimulator, APT1CampaignConfig
from campaigns.chinese_apts.apt10_campaign import APT10CampaignSimulator, APT10CampaignConfig
from campaigns.chinese_apts.apt12_campaign import APT12CampaignSimulator, APT12CampaignConfig
from campaigns.chinese_apts.chinese_apt_orchestrator import (
    ChineseAPTCampaignOrchestrator, 
    ChineseAPTCampaignConfig
)


class TestAPT41Campaign(unittest.TestCase):
    """Test APT41 (Winnti) campaign simulation."""
    
    def setUp(self):
        self.seed = 1234
        self.simulator = APT41CampaignSimulator(seed=self.seed)
    
    def test_apt41_gaming_campaign(self):
        """Test APT41 gaming industry campaign simulation."""
        config = APT41CampaignConfig(
            target_domain="test.gaming.com",
            seed=self.seed
        )
        
        report = self.simulator.simulate_gaming_industry_campaign(config)
        
        # Verify basic structure
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT41 (Winnti)")
        self.assertEqual(report["campaign_type"], "Gaming Industry Targeting")
        
        # Verify APT41-specific content
        self.assertIn("apt41_specific", report)
        apt41_specific = report["apt41_specific"]
        
        self.assertIn("initial_access", apt41_specific)
        self.assertIn("persistence", apt41_specific)
        self.assertIn("defense_evasion", apt41_specific)
        self.assertIn("malware_families", apt41_specific)
        
        # Verify gaming industry targeting
        initial_access = apt41_specific["initial_access"]
        self.assertIn("target_emails", initial_access)
        self.assertTrue(any("developer" in email for email in initial_access["target_emails"]))
    
    def test_apt41_supply_chain_attack(self):
        """Test APT41 supply chain attack simulation."""
        
        report = self.simulator.simulate_supply_chain_attack()
        
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT41 (Winnti)")
        self.assertEqual(report["attack_type"], "Software Supply Chain Compromise")
        
        self.assertIn("target_software", report)
        self.assertIn("compromise_methods", report)
        self.assertIn("implantation_techniques", report)


class TestAPT1Campaign(unittest.TestCase):
    """Test APT1 (Comment Crew) campaign simulation."""
    
    def setUp(self):
        self.seed = 1234
        self.simulator = APT1CampaignSimulator(seed=self.seed)
    
    def test_apt1_government_campaign(self):
        """Test APT1 government espionage campaign simulation."""
        config = APT1CampaignConfig(
            target_domain="test.gov",
            seed=self.seed
        )
        
        report = self.simulator.simulate_government_espionage_campaign(config)
        
        # Verify basic structure
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT1 (Comment Crew)")
        self.assertEqual(report["campaign_type"], "Government and Defense Espionage")
        
        # Verify APT1-specific content
        self.assertIn("apt1_specific", report)
        apt1_specific = report["apt1_specific"]
        
        self.assertIn("initial_access", apt1_specific)
        self.assertIn("persistence", apt1_specific)
        self.assertIn("command_control", apt1_specific)
        self.assertIn("espionage_focus", apt1_specific)
    
    def test_apt1_long_term_campaign(self):
        """Test APT1 long-term campaign simulation."""
        
        report = self.simulator.simulate_long_term_campaign(duration_days=180)
        
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT1 (Comment Crew)")
        self.assertEqual(report["campaign_type"], "Long-Term Espionage Operation")
        
        self.assertIn("campaign_phases", report)
        self.assertEqual(report["total_duration_days"], 180)


class TestAPT10Campaign(unittest.TestCase):
    """Test APT10 (Stone Panda) campaign simulation."""
    
    def setUp(self):
        self.seed = 1234
        self.simulator = APT10CampaignSimulator(seed=self.seed)
    
    def test_apt10_msp_campaign(self):
        """Test APT10 MSP compromise campaign simulation."""
        config = APT10CampaignConfig(
            target_domain="test.msp.com",
            seed=self.seed
        )
        
        report = self.simulator.simulate_msp_compromise_campaign(config)
        
        # Verify basic structure
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT10 (Stone Panda)")
        self.assertEqual(report["campaign_type"], "Managed Service Provider Compromise")
        
        # Verify APT10-specific content
        self.assertIn("apt10_specific", report)
        apt10_specific = report["apt10_specific"]
        
        self.assertIn("initial_access", apt10_specific)
        self.assertIn("lateral_movement", apt10_specific)
        self.assertIn("exfiltration", apt10_specific)
        self.assertIn("msp_compromise_details", apt10_specific)
    
    def test_apt10_cloud_attack(self):
        """Test APT10 cloud infrastructure attack simulation."""
        
        report = self.simulator.simulate_cloud_infrastructure_attack()
        
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT10 (Stone Panda)")
        self.assertEqual(report["attack_type"], "Cloud Infrastructure Compromise")
        
        self.assertIn("target_cloud_platforms", report)
        self.assertIn("attack_vectors", report)
        self.assertIn("exploitation_techniques", report)


class TestAPT12Campaign(unittest.TestCase):
    """Test APT12 (Numbered Panda) campaign simulation."""
    
    def setUp(self):
        self.seed = 1234
        self.simulator = APT12CampaignSimulator(seed=self.seed)
    
    def test_apt12_diplomatic_campaign(self):
        """Test APT12 diplomatic espionage campaign simulation."""
        config = APT12CampaignConfig(
            target_domain="test.diplomatic.org",
            seed=self.seed
        )
        
        report = self.simulator.simulate_diplomatic_espionage_campaign(config)
        
        # Verify basic structure
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT12 (Numbered Panda)")
        self.assertEqual(report["campaign_type"], "Diplomatic and Government Espionage")
        
        # Verify APT12-specific content
        self.assertIn("apt12_specific", report)
        apt12_specific = report["apt12_specific"]
        
        self.assertIn("initial_access", apt12_specific)
        self.assertIn("persistence", apt12_specific)
        self.assertIn("defense_evasion", apt12_specific)
        self.assertIn("intelligence_collection_focus", apt12_specific)
    
    def test_apt12_strategic_operation(self):
        """Test APT12 strategic intelligence operation simulation."""
        
        report = self.simulator.simulate_strategic_intelligence_operation(duration_months=12)
        
        self.assertIn("apt_group", report)
        self.assertEqual(report["apt_group"], "APT12 (Numbered Panda)")
        self.assertEqual(report["operation_type"], "Strategic Intelligence Collection")
        
        self.assertIn("strategic_objectives", report)
        self.assertEqual(report["operation_duration_months"], 12)


class TestChineseAPTOrchestrator(unittest.TestCase):
    """Test Chinese APT campaign orchestrator."""
    
    def setUp(self):
        self.seed = 1234
        self.orchestrator = ChineseAPTCampaignOrchestrator(seed=self.seed)
    
    def test_comparative_analysis(self):
        """Test comparative analysis of Chinese APT campaigns."""
        config = ChineseAPTCampaignConfig(
            target_domain="test.com",
            seed=self.seed,
            run_apt41=True,
            run_apt1=True,
            run_apt10=False,  # Test partial execution
            run_apt12=False
        )
        
        report = self.orchestrator.run_comparative_analysis(config)
        
        # Verify basic structure
        self.assertIn("campaign_config", report)
        self.assertIn("individual_campaigns", report)
        self.assertIn("comparative_analysis", report)
        self.assertIn("chinese_apt_overview", report)
        
        # Verify individual campaigns
        individual_campaigns = report["individual_campaigns"]
        self.assertIn("apt41", individual_campaigns)
        self.assertIn("apt1", individual_campaigns)
        self.assertNotIn("apt10", individual_campaigns)
        self.assertNotIn("apt12", individual_campaigns)
        
        # Verify comparative analysis
        comparative = report["comparative_analysis"]
        self.assertIn("targeting_focus", comparative)
        self.assertIn("tactical_approaches", comparative)
        self.assertIn("malware_characteristics", comparative)
    
    def test_specific_campaign_types(self):
        """Test specific campaign type execution."""
        
        # Test APT41 gaming campaign
        report = self.orchestrator.simulate_specific_campaign_type("apt41_gaming")
        self.assertEqual(report["apt_group"], "APT41 (Winnti)")
        
        # Test APT1 government campaign
        report = self.orchestrator.simulate_specific_campaign_type("apt1_government")
        self.assertEqual(report["apt_group"], "APT1 (Comment Crew)")
        
        # Test APT10 MSP campaign
        report = self.orchestrator.simulate_specific_campaign_type("apt10_msp")
        self.assertEqual(report["apt_group"], "APT10 (Stone Panda)")
        
        # Test APT12 diplomatic campaign
        report = self.orchestrator.simulate_specific_campaign_type("apt12_diplomatic")
        self.assertEqual(report["apt_group"], "APT12 (Numbered Panda)")
    
    def test_available_campaign_types(self):
        """Test retrieval of available campaign types."""
        
        available = self.orchestrator.get_available_campaign_types()
        
        self.assertIn("apt41_winnti", available)
        self.assertIn("apt1_comment_crew", available)
        self.assertIn("apt10_stone_panda", available)
        self.assertIn("apt12_numbered_panda", available)
        
        # Verify each group has campaign types
        for group, campaigns in available.items():
            self.assertIsInstance(campaigns, list)
            self.assertGreater(len(campaigns), 0)
    
    def test_chinese_apt_overview(self):
        """Test Chinese APT overview generation."""
        
        overview = self.orchestrator._get_chinese_apt_overview()
        
        self.assertIn("chinese_apt_landscape", overview)
        self.assertIn("common_characteristics", overview)
        self.assertIn("defensive_considerations", overview)
        
        # Verify all major Chinese APT groups are covered
        landscape = overview["chinese_apt_landscape"]
        self.assertIn("apt41_winnti", landscape)
        self.assertIn("apt1_comment_crew", landscape)
        self.assertIn("apt10_stone_panda", landscape)
        self.assertIn("apt12_numbered_panda", landscape)


if __name__ == "__main__":
    unittest.main()