"""
Tests for the Organization CLI
"""

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from apt_toolkit.cli_enhanced import handle_organization_command, print_pretty_result


class TestOrganizationCLI(unittest.TestCase):
    """Test cases for Organization CLI."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        
        # Create test database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create emails table
        cursor.execute("""
            CREATE TABLE emails (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                domain TEXT,
                organization TEXT,
                first_name TEXT,
                last_name TEXT,
                confidence_score REAL,
                total_records INTEGER
            )
        """)
        
        # Insert test data
        test_emails = [
            (1, 'john.doe@acme.com', 'acme.com', 'Acme Corporation', 'John', 'Doe', 0.9, 1),
            (2, 'jane.smith@acme.com', 'acme.com', 'Acme Corporation', 'Jane', 'Smith', 0.8, 1),
            (3, 'alice.williams@globex.com', 'globex.com', 'Globex Corporation', 'Alice', 'Williams', 0.9, 1),
        ]
        
        cursor.executemany("""
            INSERT INTO emails (id, email, domain, organization, first_name, last_name, confidence_score, total_records)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, test_emails)
        
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.db_path)

    @patch('apt_toolkit.cli_enhanced.OrganizationManager')
    def test_cli_list_organizations(self, mock_manager_class):
        """Test CLI list organizations command."""
        # Mock the organization manager
        mock_manager = MagicMock()
        mock_manager_class.return_value.__enter__.return_value = mock_manager
        mock_manager.list_organizations.return_value = ['Acme Corporation', 'Globex Corporation']
        
        # Create mock args
        class Args:
            command = "list"
            limit = 10
            json = False
        
        args = Args()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result = handle_organization_command(args)
            print_pretty_result(result)
            
            # Check result
            self.assertEqual(result["command"], "list_organizations")
            self.assertEqual(result["count"], 2)
            
            # Check printed output
            output = captured_output.getvalue()
            self.assertIn("Available Organizations", output)
            self.assertIn("Acme Corporation", output)
            self.assertIn("Globex Corporation", output)
            
        finally:
            sys.stdout = sys.__stdout__

    @patch('apt_toolkit.cli_enhanced.OrganizationManager')
    def test_cli_search_organizations(self, mock_manager_class):
        """Test CLI search organizations command."""
        # Mock the organization manager
        mock_manager = MagicMock()
        mock_manager_class.return_value.__enter__.return_value = mock_manager
        mock_manager.search_organizations.return_value = ['Acme Corporation']
        
        # Create mock args
        class Args:
            command = "search"
            term = "Acme"
            limit = 10
            json = False
        
        args = Args()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result = handle_organization_command(args)
            print_pretty_result(result)
            
            # Check result
            self.assertEqual(result["command"], "search_organizations")
            self.assertEqual(result["search_term"], "Acme")
            self.assertEqual(result["count"], 1)
            
            # Check printed output
            output = captured_output.getvalue()
            self.assertIn("Search Results for 'Acme'", output)
            self.assertIn("Acme Corporation", output)
            
        finally:
            sys.stdout = sys.__stdout__

    @patch('apt_toolkit.cli_enhanced.OrganizationManager')
    def test_cli_organization_profile(self, mock_manager_class):
        """Test CLI organization profile command."""
        # Mock the organization manager
        mock_manager = MagicMock()
        mock_manager_class.return_value.__enter__.return_value = mock_manager
        mock_manager.generate_organization_profile.return_value = {
            "organization": "Acme Corporation",
            "email_count": 2,
            "domains": ["acme.com"],
            "description": "A leading technology company",
            "industry": "Technology",
            "size": "large",
            "key_employees": ["CEO", "CTO"],
            "security_posture": "medium",
            "attack_vectors": ["spear_phishing", "supply_chain"]
        }
        
        # Create mock args
        class Args:
            command = "profile"
            organization = "Acme Corporation"
            no_deepseek = False
            json = False
        
        args = Args()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result = handle_organization_command(args)
            print_pretty_result(result)
            
            # Check result
            self.assertEqual(result["command"], "organization_profile")
            self.assertEqual(result["organization"], "Acme Corporation")
            
            # Check printed output
            output = captured_output.getvalue()
            self.assertIn("Organization Profile: Acme Corporation", output)
            self.assertIn("Email Count: 2", output)
            self.assertIn("Industry: Technology", output)
            self.assertIn("Size: large", output)
            
        finally:
            sys.stdout = sys.__stdout__

    @patch('apt_toolkit.cli_enhanced.OrganizationManager')
    def test_cli_attack_plan(self, mock_manager_class):
        """Test CLI attack plan command."""
        # Mock the organization manager
        mock_manager = MagicMock()
        mock_manager_class.return_value.__enter__.return_value = mock_manager
        mock_manager.generate_attack_plan.return_value = {
            "organization": "Acme Corporation",
            "attack_type": "spear_phishing",
            "strategy": "Target key executives with tailored phishing emails",
            "steps": [
                {"phase": "reconnaissance", "action": "Gather intelligence on key employees", "tools": ["theharvester", "linkedin"]},
                {"phase": "initial_access", "action": "Send targeted phishing emails", "tools": ["gophish", "setoolkit"]}
            ],
            "techniques": ["spear_phishing", "credential_harvesting"],
            "challenges": ["MFA enabled", "Security awareness training"],
            "mitigations": ["Use trusted domains", "Social engineering techniques"]
        }
        
        # Create mock args
        class Args:
            command = "attack-plan"
            organization = "Acme Corporation"
            type = "spear_phishing"
            no_deepseek = False
            json = False
        
        args = Args()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result = handle_organization_command(args)
            print_pretty_result(result)
            
            # Check result
            self.assertEqual(result["command"], "attack_plan")
            self.assertEqual(result["organization"], "Acme Corporation")
            self.assertEqual(result["attack_type"], "spear_phishing")
            
            # Check printed output
            output = captured_output.getvalue()
            self.assertIn("Attack Plan: Acme Corporation - spear_phishing", output)
            self.assertIn("Strategy:", output)
            self.assertIn("Execution Steps:", output)
            
        finally:
            sys.stdout = sys.__stdout__

    @patch('apt_toolkit.cli_enhanced.OrganizationManager')
    def test_cli_organization_stats(self, mock_manager_class):
        """Test CLI organization stats command."""
        # Mock the organization manager
        mock_manager = MagicMock()
        mock_manager_class.return_value.__enter__.return_value = mock_manager
        mock_manager.get_organization_stats.return_value = {
            "organization": "Acme Corporation",
            "email_count": 2,
            "domains": ["acme.com"],
            "sample_emails": ["john.doe@acme.com", "jane.smith@acme.com"]
        }
        
        # Create mock args
        class Args:
            command = "stats"
            organization = "Acme Corporation"
            json = False
        
        args = Args()
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        try:
            result = handle_organization_command(args)
            print_pretty_result(result)
            
            # Check result
            self.assertEqual(result["command"], "organization_stats")
            self.assertEqual(result["organization"], "Acme Corporation")
            
            # Check printed output
            output = captured_output.getvalue()
            self.assertIn("Organization Statistics: Acme Corporation", output)
            self.assertIn("Email Count: 2", output)
            self.assertIn("Sample Emails:", output)
            
        finally:
            sys.stdout = sys.__stdout__

    @patch('apt_toolkit.cli_enhanced.OrganizationManager')
    def test_cli_json_output(self, mock_manager_class):
        """Test CLI JSON output."""
        # Mock the organization manager
        mock_manager = MagicMock()
        mock_manager_class.return_value.__enter__.return_value = mock_manager
        mock_manager.list_organizations.return_value = ['Acme Corporation']
        
        # Create mock args
        class Args:
            command = "list"
            limit = 10
            json = True
        
        args = Args()
        
        result = handle_organization_command(args)
        
        # Check result is a dictionary (will be printed as JSON by main)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["command"], "list_organizations")
        self.assertEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()