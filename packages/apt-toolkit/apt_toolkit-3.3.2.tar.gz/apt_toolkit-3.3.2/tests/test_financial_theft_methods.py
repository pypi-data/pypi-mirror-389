"""Tests for financial theft methods module."""

import unittest
from datetime import datetime
from unittest.mock import patch

from apt_toolkit.financial_theft_methods import (
    FinancialTheftEngine,
    generate_financial_theft_campaign
)


class TestFinancialTheftEngine(unittest.TestCase):
    """Test the FinancialTheftEngine class."""
    
    def setUp(self):
        self.engine = FinancialTheftEngine(seed=42)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertIsNotNone(self.engine)
    
    def test_get_all_theft_methods(self):
        """Test retrieval of all theft methods."""
        methods = self.engine.get_all_theft_methods()
        
        self.assertIsInstance(methods, dict)
        self.assertGreater(len(methods), 0)
        
        # Check that all expected method categories are present
        expected_categories = [
            "account_takeover", "transaction_manipulation", "cryptocurrency_theft",
            "credit_card_fraud", "investment_fraud", "payment_system_exploitation",
            "insurance_fraud", "loan_fraud", "regulatory_evasion", "data_exfiltration"
        ]
        for category in expected_categories:
            self.assertIn(category, methods)
            self.assertIsInstance(methods[category], list)
            self.assertGreater(len(methods[category]), 0)
    
    def test_get_institution_specific_methods(self):
        """Test retrieval of institution-specific methods."""
        # Test banks
        bank_methods = self.engine.get_institution_specific_methods("banks")
        self.assertIsInstance(bank_methods, list)
        self.assertGreater(len(bank_methods), 0)
        
        # Test cryptocurrency exchanges
        crypto_methods = self.engine.get_institution_specific_methods("cryptocurrency_exchanges")
        self.assertIsInstance(crypto_methods, list)
        self.assertGreater(len(crypto_methods), 0)
        
        # Test unknown institution type (should default to account takeover)
        unknown_methods = self.engine.get_institution_specific_methods("unknown")
        self.assertIsInstance(unknown_methods, list)
        self.assertGreater(len(unknown_methods), 0)
    
    def test_generate_theft_campaign(self):
        """Test theft campaign generation."""
        with patch("apt_toolkit.financial_theft_methods.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            
            campaign = self.engine.generate_theft_campaign(["banks", "cryptocurrency_exchanges"])
        
        self.assertIn("campaign_id", campaign)
        self.assertIn("generated_at", campaign)
        self.assertIn("target_institutions", campaign)
        self.assertIn("primary_theft_method", campaign)
        self.assertIn("selected_methods", campaign)
        self.assertIn("estimated_success_rate", campaign)
        self.assertIn("detection_risk", campaign)
        self.assertIn("financial_impact", campaign)
        self.assertIn("execution_timeline", campaign)
        
        # Check structure of nested data
        success_rate = campaign["estimated_success_rate"]
        self.assertIn("base_rate", success_rate)
        self.assertIn("adjusted_rate", success_rate)
        self.assertIn("confidence_level", success_rate)
        
        detection_risk = campaign["detection_risk"]
        self.assertIn("method_risks", detection_risk)
        self.assertIn("overall_risk", detection_risk)
        self.assertIn("risk_factors", detection_risk)
        
        financial_impact = campaign["financial_impact"]
        self.assertIn("estimated_range", financial_impact)
        self.assertIn("estimated_impact", financial_impact)
        self.assertIn("formatted_impact", financial_impact)
        self.assertIn("impact_category", financial_impact)
        
        timeline = campaign["execution_timeline"]
        self.assertIn("estimated_duration", timeline)
        self.assertIn("complexity_score", timeline)
        self.assertIn("phases", timeline)
    
    def test_estimate_success_rate(self):
        """Test success rate estimation."""
        success_rate = self.engine._estimate_success_rate(["banks", "cryptocurrency_exchanges"], "account_takeover")
        
        self.assertIn("base_rate", success_rate)
        self.assertIn("adjusted_rate", success_rate)
        self.assertIn("confidence_level", success_rate)
        
        # Check that rates are within expected bounds
        self.assertGreaterEqual(success_rate["base_rate"], 0.0)
        self.assertLessEqual(success_rate["base_rate"], 1.0)
        self.assertGreaterEqual(success_rate["adjusted_rate"], 0.0)
        self.assertLessEqual(success_rate["adjusted_rate"], 1.0)
    
    def test_assess_detection_risk(self):
        """Test detection risk assessment."""
        methods = ["SWIFT message manipulation", "Account takeover", "Private key theft"]
        detection_risk = self.engine._assess_detection_risk(methods)
        
        self.assertIn("method_risks", detection_risk)
        self.assertIn("overall_risk", detection_risk)
        self.assertIn("risk_factors", detection_risk)
        
        # Check method risks
        method_risks = detection_risk["method_risks"]
        for method in methods:
            self.assertIn(method, method_risks)
            self.assertIn(method_risks[method], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        # Check overall risk
        self.assertIn(detection_risk["overall_risk"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    
    def test_estimate_financial_impact(self):
        """Test financial impact estimation."""
        impact = self.engine._estimate_financial_impact(["banks", "cryptocurrency_exchanges"])
        
        self.assertIn("estimated_range", impact)
        self.assertIn("estimated_impact", impact)
        self.assertIn("formatted_impact", impact)
        self.assertIn("impact_category", impact)
        
        # Check range values
        range_data = impact["estimated_range"]
        self.assertIn("low", range_data)
        self.assertIn("high", range_data)
        self.assertIn("formatted_low", range_data)
        self.assertIn("formatted_high", range_data)
        
        # Check impact values
        self.assertGreaterEqual(impact["estimated_impact"], range_data["low"])
        self.assertLessEqual(impact["estimated_impact"], range_data["high"])
    
    def test_categorize_impact(self):
        """Test impact categorization."""
        self.assertEqual(self.engine._categorize_impact(150000000), "CATASTROPHIC")
        self.assertEqual(self.engine._categorize_impact(75000000), "SEVERE")
        self.assertEqual(self.engine._categorize_impact(15000000), "MAJOR")
        self.assertEqual(self.engine._categorize_impact(5000000), "MODERATE")
        self.assertEqual(self.engine._categorize_impact(500000), "MINOR")
    
    def test_generate_execution_timeline(self):
        """Test execution timeline generation."""
        timeline = self.engine._generate_execution_timeline(["banks", "investment_firms"])
        
        self.assertIn("estimated_duration", timeline)
        self.assertIn("complexity_score", timeline)
        self.assertIn("phases", timeline)
        
        # Check phases
        phases = timeline["phases"]
        self.assertIsInstance(phases, list)
        self.assertGreater(len(phases), 0)
        
        # Check duration format
        self.assertIn(timeline["estimated_duration"], ["2-4 weeks", "1-3 months", "3-6 months", "6-12 months"])


class TestFinancialTheftFunction(unittest.TestCase):
    """Test the financial theft campaign generation function."""
    
    def test_generate_financial_theft_campaign(self):
        """Test the financial theft campaign function."""
        with patch("apt_toolkit.financial_theft_methods.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            
            campaign = generate_financial_theft_campaign(
                institution_types=["banks", "cryptocurrency_exchanges"],
                primary_method="account_takeover",
                seed=42
            )
        
        self.assertIn("campaign_id", campaign)
        self.assertIn("generated_at", campaign)
        self.assertIn("target_institutions", campaign)
        self.assertIn("primary_theft_method", campaign)
        self.assertIn("selected_methods", campaign)
        
        # Check target institutions
        self.assertEqual(campaign["target_institutions"], ["banks", "cryptocurrency_exchanges"])
        self.assertEqual(campaign["primary_theft_method"], "account_takeover")
    
    def test_generate_financial_theft_campaign_defaults(self):
        """Test the financial theft campaign function with defaults."""
        with patch("apt_toolkit.financial_theft_methods.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)
            
            campaign = generate_financial_theft_campaign(seed=42)
        
        self.assertIn("campaign_id", campaign)
        self.assertIn("target_institutions", campaign)
        
        # Check default target institutions
        self.assertEqual(campaign["target_institutions"], ["banks", "investment_firms", "cryptocurrency_exchanges"])


if __name__ == "__main__":
    unittest.main()