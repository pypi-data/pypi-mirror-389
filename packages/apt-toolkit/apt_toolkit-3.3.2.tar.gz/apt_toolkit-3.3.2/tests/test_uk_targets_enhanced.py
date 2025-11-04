"""Tests for enhanced UK targets analysis."""

import unittest
from datetime import datetime
from unittest.mock import patch

from apt_toolkit.uk_targets_enhanced import (
    UKTargetsAnalyzer,
    analyze_uk_targets_enhanced
)


class TestUKTargetsAnalyzer(unittest.TestCase):
    """Test the UKTargetsAnalyzer class."""
    
    def setUp(self):
        self.analyzer = UKTargetsAnalyzer(seed=42)
    
    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertIsNotNone(self.analyzer.social_engineering)
        self.assertIsNotNone(self.analyzer.supply_chain)
        self.assertIsInstance(self.analyzer.uk_networks, list)
        self.assertGreater(len(self.analyzer.uk_networks), 0)
    
    def test_get_organization_type(self):
        """Test organization type detection."""
        self.assertEqual(self.analyzer._get_organization_type("army.mod.uk"), "military")
        self.assertEqual(self.analyzer._get_organization_type("gchq.gov.uk"), "government")
        self.assertEqual(self.analyzer._get_organization_type("nhs.uk"), "infrastructure")
        self.assertEqual(self.analyzer._get_organization_type("baesystems.com"), "industry")
        self.assertEqual(self.analyzer._get_organization_type("ox.ac.uk"), "research")
        self.assertEqual(self.analyzer._get_organization_type("homeoffice.gov.uk"), "government")
    
    def test_generate_target_domain(self):
        """Test target domain generation."""
        domain = self.analyzer._generate_target_domain("mod.uk")
        self.assertIn(".mod.uk", domain)
        
        domain = self.analyzer._generate_target_domain("hsbc.co.uk")
        self.assertIn("hsbc.co.uk", domain)
    
    def test_generate_target_email(self):
        """Test target email generation."""
        email = self.analyzer._generate_target_email("gchq.gov.uk", "government")
        self.assertIn("@gchq.gov.uk", email)
        self.assertGreater(len(email.split("@")[0]), 0)
    
    def test_generate_network_segment(self):
        """Test network segment generation."""
        ip_range, gateway_ip = self.analyzer._generate_network_segment("military")
        self.assertIn("/24", ip_range)
        self.assertTrue(gateway_ip.endswith(".1"))

    def test_analyze_uk_targets(self):
        """Test comprehensive target analysis."""
        with patch("apt_toolkit.uk_targets_enhanced.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            analysis = self.analyzer.analyze_uk_targets()
        
        self.assertIn("uk_networks", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("supply_chain_readiness", analysis)
        self.assertIn("threat_assessment", analysis)
        
        self.assertGreater(len(analysis["uk_networks"]), 0)
        self.assertEqual(
            len(analysis["target_profiles"]),
            len(analysis["uk_networks"])
        )
        
        for profile in analysis["target_profiles"]:
            self.assertIn("target_domain", profile)
            self.assertIn("target_email", profile)
            self.assertIn("organization_type", profile)
            self.assertIn("network_segment", profile)
            self.assertIn("gateway_ip", profile)
            self.assertIn("dossier", profile)
            self.assertIn("lure", profile)
    
    def test_threat_assessment_generation(self):
        """Test threat assessment generation."""
        target_profiles = [
            {"organization_type": "military"},
            {"organization_type": "government"},
            {"organization_type": "infrastructure"}
        ]
        
        assessment = self.analyzer._generate_threat_assessment(target_profiles)
        
        self.assertIn("organization_distribution", assessment)
        self.assertIn("total_targets", assessment)
        self.assertIn("overall_risk_score", assessment)
        self.assertIn("risk_assessment", assessment)
        self.assertIn("recommended_approach", assessment)
        self.assertIn("timeline_estimate", assessment)
    
    def test_risk_level_calculation(self):
        """Test risk level calculation."""
        self.assertEqual(self.analyzer._get_risk_level(160), "CRITICAL")
        self.assertEqual(self.analyzer._get_risk_level(120), "HIGH")
        self.assertEqual(self.analyzer._get_risk_level(70), "MEDIUM")
        self.assertEqual(self.analyzer._get_risk_level(30), "LOW")


class TestEnhancedAnalysisFunction(unittest.TestCase):
    """Test the enhanced analysis function."""
    
    def test_analyze_uk_targets_enhanced(self):
        """Test the enhanced analysis function."""
        with patch("apt_toolkit.uk_targets_enhanced.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            analysis = analyze_uk_targets_enhanced(seed=42)
        
        self.assertIn("uk_networks", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("supply_chain_readiness", analysis)
        self.assertIn("threat_assessment", analysis)
        
        threat_assessment = analysis["threat_assessment"]
        self.assertIn("organization_distribution", threat_assessment)
        self.assertIn("overall_risk_score", threat_assessment)


if __name__ == "__main__":
    unittest.main()
