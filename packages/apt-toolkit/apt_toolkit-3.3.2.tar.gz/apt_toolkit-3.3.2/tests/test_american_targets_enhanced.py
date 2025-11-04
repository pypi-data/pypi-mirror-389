"""Tests for enhanced American targets analysis."""

import unittest
from datetime import datetime
from unittest.mock import patch

from apt_toolkit.american_targets_enhanced import (
    AmericanTargetsAnalyzer,
    analyze_american_targets_enhanced
)


class TestAmericanTargetsAnalyzer(unittest.TestCase):
    """Test the AmericanTargetsAnalyzer class."""
    
    def setUp(self):
        self.analyzer = AmericanTargetsAnalyzer(seed=42)
    
    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertIsNotNone(self.analyzer.social_engineering)
        self.assertIsNotNone(self.analyzer.supply_chain)
        self.assertIsInstance(self.analyzer.american_networks, list)
        self.assertGreater(len(self.analyzer.american_networks), 0)
    
    def test_get_organization_type(self):
        """Test organization type detection."""
        self.assertEqual(self.analyzer._get_organization_type("army.mil"), "military")
        self.assertEqual(self.analyzer._get_organization_type("cia.gov"), "intelligence")
        self.assertEqual(self.analyzer._get_organization_type("energy.gov"), "infrastructure")
        self.assertEqual(self.analyzer._get_organization_type("darpa.mil"), "research")
        self.assertEqual(self.analyzer._get_organization_type("state.gov"), "government")
    
    def test_generate_target_domain(self):
        """Test target domain generation."""
        domain = self.analyzer._generate_target_domain("mil")
        self.assertIn(".mil", domain)
        
        domain = self.analyzer._generate_target_domain("cia.gov")
        self.assertIn("cia.gov", domain)
    
    def test_generate_target_email(self):
        """Test target email generation."""
        email = self.analyzer._generate_target_email("cia.gov", "intelligence")
        self.assertIn("@cia.gov", email)
        # Email prefix should be non-empty
        self.assertGreater(len(email.split("@")[0]), 0)
    
    def test_generate_network_segment(self):
        """Test network segment generation."""
        ip_range, gateway_ip = self.analyzer._generate_network_segment("military")
        self.assertIn("/24", ip_range)
        self.assertIn(".1", gateway_ip)
    
    def test_analyze_american_targets(self):
        """Test comprehensive target analysis."""
        with patch("apt_toolkit.american_targets_enhanced.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            analysis = self.analyzer.analyze_american_targets()
        
        self.assertIn("american_networks", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("supply_chain_readiness", analysis)
        self.assertIn("threat_assessment", analysis)
        
        # Check structure
        self.assertGreater(len(analysis["american_networks"]), 0)
        self.assertEqual(
            len(analysis["target_profiles"]), 
            len(analysis["american_networks"])
        )
        
        # Check target profiles structure
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
            {"organization_type": "intelligence"},
            {"organization_type": "government"}
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
        self.assertEqual(self.analyzer._get_risk_level(85), "CRITICAL")
        self.assertEqual(self.analyzer._get_risk_level(65), "HIGH")
        self.assertEqual(self.analyzer._get_risk_level(45), "MEDIUM")
        self.assertEqual(self.analyzer._get_risk_level(25), "LOW")


class TestEnhancedAnalysisFunction(unittest.TestCase):
    """Test the enhanced analysis function."""
    
    def test_analyze_american_targets_enhanced(self):
        """Test the enhanced analysis function."""
        with patch("apt_toolkit.american_targets_enhanced.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            analysis = analyze_american_targets_enhanced(seed=42)
        
        self.assertIn("american_networks", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("supply_chain_readiness", analysis)
        self.assertIn("threat_assessment", analysis)
        
        # Verify enhanced features
        threat_assessment = analysis["threat_assessment"]
        self.assertIn("organization_distribution", threat_assessment)
        self.assertIn("overall_risk_score", threat_assessment)


if __name__ == "__main__":
    unittest.main()