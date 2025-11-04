"""Tests for financial institution targeting module."""

import unittest
from datetime import datetime
from unittest.mock import patch

from apt_toolkit.financial_targeting import (
    FinancialTargetingEngine,
    analyze_financial_targets
)


class TestFinancialTargetingEngine(unittest.TestCase):
    """Test the FinancialTargetingEngine class."""
    
    def setUp(self):
        self.engine = FinancialTargetingEngine(seed=42)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertIsNotNone(self.engine.social_engineering)
        self.assertIsInstance(self.engine.financial_institutions, dict)
        self.assertGreater(len(self.engine.financial_institutions), 0)
        
        # Check that all expected institution types are present
        expected_types = ["banks", "investment_firms", "payment_processors", 
                         "cryptocurrency_exchanges", "regulatory_bodies",
                         "insurance_companies", "fintech_companies",
                         "wealth_management", "mortgage_lenders"]
        for inst_type in expected_types:
            self.assertIn(inst_type, self.engine.financial_institutions)
    
    def test_get_institution_type(self):
        """Test institution type detection."""
        self.assertEqual(self.engine._get_institution_type("jpmorganchase.com"), "banks")
        self.assertEqual(self.engine._get_institution_type("blackrock.com"), "investment_firms")
        self.assertEqual(self.engine._get_institution_type("visa.com"), "payment_processors")
        self.assertEqual(self.engine._get_institution_type("coinbase.com"), "cryptocurrency_exchanges")
        self.assertEqual(self.engine._get_institution_type("federalreserve.gov"), "regulatory_bodies")
        self.assertEqual(self.engine._get_institution_type("aig.com"), "insurance_companies")
        self.assertEqual(self.engine._get_institution_type("robinhood.com"), "fintech_companies")
        self.assertEqual(self.engine._get_institution_type("northwesternmutual.com"), "wealth_management")
        self.assertEqual(self.engine._get_institution_type("quickenloans.com"), "mortgage_lenders")
        self.assertEqual(self.engine._get_institution_type("unknown.com"), "banks")  # default
    
    def test_generate_financial_domain(self):
        """Test financial domain generation."""
        domain = self.engine._generate_financial_domain("jpmorganchase.com")
        self.assertIn("jpmorganchase.com", domain)
        
        domain = self.engine._generate_financial_domain("coinbase.com")
        self.assertIn("coinbase.com", domain)
    
    def test_generate_target_email(self):
        """Test target email generation."""
        email = self.engine._generate_target_email("jpmorganchase.com", "banks")
        self.assertIn("@jpmorganchase.com", email)
        # Email prefix should be non-empty
        self.assertGreater(len(email.split("@")[0]), 0)
    
    def test_estimate_target_value(self):
        """Test target value estimation."""
        value_info = self.engine._estimate_target_value("banks")
        self.assertIn("estimated_value", value_info)
        self.assertIn("currency", value_info)
        self.assertIn("value_category", value_info)
        
        # Check value ranges
        self.assertGreaterEqual(value_info["estimated_value"], 1000000)
        self.assertLessEqual(value_info["estimated_value"], 50000000)
        
        # Test cryptocurrency exchanges (highest value)
        crypto_value = self.engine._estimate_target_value("cryptocurrency_exchanges")
        self.assertGreaterEqual(crypto_value["estimated_value"], 10000000)
        self.assertLessEqual(crypto_value["estimated_value"], 200000000)
        
        # Test new institution types
        fintech_value = self.engine._estimate_target_value("fintech_companies")
        self.assertGreaterEqual(fintech_value["estimated_value"], 3000000)
        self.assertLessEqual(fintech_value["estimated_value"], 80000000)
    
    def test_categorize_value(self):
        """Test value categorization."""
        self.assertEqual(self.engine._categorize_value(150000000), "EXTREMELY_HIGH")
        self.assertEqual(self.engine._categorize_value(75000000), "VERY_HIGH")
        self.assertEqual(self.engine._categorize_value(15000000), "HIGH")
        self.assertEqual(self.engine._categorize_value(5000000), "MEDIUM")
        self.assertEqual(self.engine._categorize_value(500000), "LOW")
    
    def test_analyze_financial_targets(self):
        """Test comprehensive financial target analysis."""
        with patch("apt_toolkit.financial_targeting.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            analysis = self.engine.analyze_financial_targets()
        
        self.assertIn("generated_at", analysis)
        self.assertIn("target_types", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("threat_assessment", analysis)
        
        # Check structure
        self.assertGreater(len(analysis["target_types"]), 0)
        self.assertGreater(len(analysis["target_profiles"]), 0)
        
        # Check target profiles structure
        for profile in analysis["target_profiles"]:
            self.assertIn("institution_type", profile)
            self.assertIn("target_domain", profile)
            self.assertIn("target_email", profile)
            self.assertIn("dossier", profile)
            self.assertIn("estimated_value", profile)
    
    def test_analyze_specific_target_types(self):
        """Test analysis with specific target types."""
        with patch("apt_toolkit.financial_targeting.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            # Test banks only
            analysis = self.engine.analyze_financial_targets(["banks"])
        
        self.assertEqual(analysis["target_types"], ["banks"])
        
        # All profiles should be banks
        for profile in analysis["target_profiles"]:
            self.assertEqual(profile["institution_type"], "banks")
    
    def test_financial_threat_assessment_generation(self):
        """Test financial threat assessment generation."""
        target_profiles = [
            {
                "institution_type": "banks",
                "estimated_value": {"estimated_value": 10000000}
            },
            {
                "institution_type": "cryptocurrency_exchanges", 
                "estimated_value": {"estimated_value": 50000000}
            }
        ]
        
        assessment = self.engine._generate_financial_threat_assessment(target_profiles)
        
        self.assertIn("institution_distribution", assessment)
        self.assertIn("total_targets", assessment)
        self.assertIn("total_estimated_value", assessment)
        self.assertIn("overall_risk_score", assessment)
        self.assertIn("risk_assessment", assessment)
        self.assertIn("recommended_approach", assessment)
        self.assertIn("timeline_estimate", assessment)
        self.assertIn("detection_likelihood", assessment)
        
        # Check specific values
        self.assertEqual(assessment["total_targets"], 2)
        self.assertEqual(assessment["total_estimated_value"]["amount"], 60000000)
    
    def test_financial_risk_level_calculation(self):
        """Test financial risk level calculation."""
        self.assertEqual(self.engine._get_financial_risk_level(85), "CRITICAL")
        self.assertEqual(self.engine._get_financial_risk_level(65), "HIGH")
        self.assertEqual(self.engine._get_financial_risk_level(45), "MEDIUM")
        self.assertEqual(self.engine._get_financial_risk_level(25), "LOW")


class TestFinancialAnalysisFunction(unittest.TestCase):
    """Test the financial analysis function."""
    
    def test_analyze_financial_targets(self):
        """Test the financial analysis function."""
        with patch("apt_toolkit.financial_targeting.datetime") as mock_datetime, patch(
            "apt_toolkit.initial_access_enhanced.datetime"
        ) as mock_initial_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            mock_initial_datetime.now.return_value = datetime(2024, 1, 1, 20, 0, 0)
            
            analysis = analyze_financial_targets(seed=42)
        
        self.assertIn("generated_at", analysis)
        self.assertIn("target_types", analysis)
        self.assertIn("target_profiles", analysis)
        self.assertIn("threat_assessment", analysis)
        
        # Verify financial-specific features
        threat_assessment = analysis["threat_assessment"]
        self.assertIn("institution_distribution", threat_assessment)
        self.assertIn("total_estimated_value", threat_assessment)


if __name__ == "__main__":
    unittest.main()