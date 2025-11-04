"""
Tests for the Organization Manager module
"""

import unittest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock, call

from apt_toolkit.organization_manager import OrganizationManager
from apt_toolkit.email_repository import EmailRepository


class TestOrganizationManager(unittest.TestCase):
    """Test cases for OrganizationManager."""

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
        
        # Create email_records table
        cursor.execute("""
            CREATE TABLE email_records (
                id INTEGER PRIMARY KEY,
                email_id INTEGER,
                source_file TEXT,
                source_row INTEGER,
                raw_record TEXT,
                FOREIGN KEY(email_id) REFERENCES emails(id)
            )
        """)
        
        # Create metadata table
        cursor.execute("""
            CREATE TABLE metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Insert test data
        test_emails = [
            (1, 'john.doe@acme.com', 'acme.com', 'Acme Corporation', 'John', 'Doe', 0.9, 1),
            (2, 'jane.smith@acme.com', 'acme.com', 'Acme Corporation', 'Jane', 'Smith', 0.8, 1),
            (3, 'bob.johnson@acme.com', 'acme.com', 'Acme Corporation', 'Bob', 'Johnson', 0.7, 1),
            (4, 'alice.williams@globex.com', 'globex.com', 'Globex Corporation', 'Alice', 'Williams', 0.9, 1),
            (5, 'charlie.brown@globex.com', 'globex.com', 'Globex Corporation', 'Charlie', 'Brown', 0.8, 1),
            (6, 'david.wilson@initech.com', 'initech.com', 'Initech', 'David', 'Wilson', 0.9, 1),
        ]
        
        cursor.executemany("""
            INSERT INTO emails (id, email, domain, organization, first_name, last_name, confidence_score, total_records)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, test_emails)
        
        # Insert sample records
        test_records = [
            (1, 1, 'source1.csv', 1, '{"email": "john.doe@acme.com", "name": "John Doe"}'),
            (2, 2, 'source1.csv', 2, '{"email": "jane.smith@acme.com", "name": "Jane Smith"}'),
            (3, 3, 'source1.csv', 3, '{"email": "bob.johnson@acme.com", "name": "Bob Johnson"}'),
            (4, 4, 'source2.csv', 1, '{"email": "alice.williams@globex.com", "name": "Alice Williams"}'),
            (5, 5, 'source2.csv', 2, '{"email": "charlie.brown@globex.com", "name": "Charlie Brown"}'),
            (6, 6, 'source3.csv', 1, '{"email": "david.wilson@initech.com", "name": "David Wilson"}'),
        ]
        
        cursor.executemany("""
            INSERT INTO email_records (id, email_id, source_file, source_row, raw_record)
            VALUES (?, ?, ?, ?, ?)
        """, test_records)
        
        # Insert metadata
        cursor.execute("INSERT INTO metadata (key, value) VALUES ('total_emails', '6')")
        
        conn.commit()
        conn.close()
        
        # Create organization manager with test database
        self.manager = OrganizationManager(EmailRepository(self.db_path))

    def tearDown(self):
        """Clean up test fixtures."""
        self.manager.close()
        os.unlink(self.db_path)

    def test_list_organizations(self):
        """Test listing organizations."""
        organizations = self.manager.list_organizations(limit=10)
        
        self.assertIsInstance(organizations, list)
        self.assertEqual(len(organizations), 3)  # Acme, Globex, Initech
        self.assertIn('Acme Corporation', organizations)
        self.assertIn('Globex Corporation', organizations)
        self.assertIn('Initech', organizations)

    def test_search_organizations(self):
        """Test searching organizations."""
        # Search for "Acme"
        results = self.manager.search_organizations("Acme", limit=10)
        self.assertEqual(len(results), 1)
        self.assertIn('Acme Corporation', results)
        
        # Search for "Corporation"
        results = self.manager.search_organizations("Corporation", limit=10)
        self.assertEqual(len(results), 2)
        self.assertIn('Acme Corporation', results)
        self.assertIn('Globex Corporation', results)

    def test_get_organization_stats(self):
        """Test getting organization statistics."""
        stats = self.manager.get_organization_stats("Acme Corporation")
        
        self.assertEqual(stats["organization"], "Acme Corporation")
        self.assertEqual(stats["email_count"], 3)
        self.assertEqual(stats["domains"], ["acme.com"])
        self.assertEqual(len(stats["sample_emails"]), 3)
        
        # Test non-existent organization
        stats = self.manager.get_organization_stats("NonExistent Corp")
        self.assertEqual(stats["email_count"], 0)
        self.assertIn("error", stats)

    def test_get_organization_emails(self):
        """Test getting organization emails."""
        emails = self.manager.get_organization_emails("Acme Corporation", limit=10)
        
        self.assertEqual(len(emails), 3)
        self.assertEqual(emails[0]["organization"], "Acme Corporation")
        self.assertEqual(emails[0]["domain"], "acme.com")

    @patch('apt_toolkit.organization_manager.generate_organization_profile')
    def test_generate_organization_profile_with_deepseek(self, mock_generate):
        """Test generating organization profile with deepseek."""
        # Mock the deepseek response
        mock_generate.return_value = {
            "description": "Test description",
            "industry": "Technology",
            "size": "large",
            "key_employees": ["CEO", "CTO", "CFO"],
            "security_posture": "medium",
            "attack_vectors": ["spear_phishing", "supply_chain"]
        }
        
        profile = self.manager.generate_organization_profile("Acme Corporation", use_deepseek=True)
        
        # Check that deepseek was called
        mock_generate.assert_called_once_with("Acme Corporation", True)
        
        # Check profile structure
        self.assertEqual(profile["organization"], "Acme Corporation")
        self.assertEqual(profile["email_count"], 3)
        self.assertEqual(profile["industry"], "Technology")
        self.assertEqual(profile["size"], "large")

    def test_generate_organization_profile_without_deepseek(self):
        """Test generating organization profile without deepseek."""
        profile = self.manager.generate_organization_profile("Acme Corporation", use_deepseek=False)
        
        # Check basic profile structure
        self.assertEqual(profile["organization"], "Acme Corporation")
        self.assertEqual(profile["email_count"], 3)
        self.assertEqual(profile["industry"], "Unknown")
        self.assertEqual(profile["size"], "Unknown")

    @patch('apt_toolkit.organization_manager.generate_unique_attack_plan')
    @patch('apt_toolkit.organization_manager.generate_phishing_email')
    def test_generate_attack_plan_with_deepseek(self, mock_phishing, mock_attack_plan):
        """Test generating attack plan with deepseek."""
        # Mock the deepseek responses
        mock_attack_plan.return_value = {
            "organization": "Acme Corporation",
            "attack_type": "spear_phishing",
            "strategy": "Test strategy",
            "steps": [
                {"phase": "reconnaissance", "action": "Gather intelligence", "tools": ["nmap", "theharvester"]},
                {"phase": "initial_access", "action": "Send phishing email", "tools": ["gophish"]}
            ],
            "techniques": ["spear_phishing", "credential_harvesting"],
            "challenges": ["MFA enabled", "Security awareness training"],
            "mitigations": ["Use trusted domains", "Social engineering"],
            "generated_with_deepseek": True
        }
        
        mock_phishing.return_value = {
            "subject": "URGENT: Security Update Required",
            "body": "Please update your credentials immediately."
        }
        
        attack_plan = self.manager.generate_attack_plan(
            "Acme Corporation", 
            attack_type="spear_phishing", 
            use_deepseek=True
        )
        
        # Check that deepseek was called
        mock_attack_plan.assert_called_once_with("Acme Corporation", "spear_phishing", True)
        
        # Check attack plan structure
        self.assertEqual(attack_plan["organization"], "Acme Corporation")
        self.assertEqual(attack_plan["attack_type"], "spear_phishing")
        self.assertEqual(attack_plan["strategy"], "Test strategy")
        self.assertIn("organization_stats", attack_plan)
        self.assertIn("phishing_email", attack_plan)

    def test_generate_attack_plan_without_deepseek(self):
        """Test generating attack plan without deepseek."""
        attack_plan = self.manager.generate_attack_plan(
            "Acme Corporation", 
            attack_type="spear_phishing", 
            use_deepseek=False
        )
        
        # Check basic attack plan structure
        self.assertEqual(attack_plan["organization"], "Acme Corporation")
        self.assertEqual(attack_plan["attack_type"], "spear_phishing")
        self.assertIn("organization_stats", attack_plan)

    def test_analyze_organization_landscape(self):
        """Test analyzing organization landscape."""
        landscape = self.manager.analyze_organization_landscape(limit=2)
        
        self.assertEqual(landscape["total_organizations_analyzed"], 2)
        self.assertIn("organizations", landscape)
        self.assertIn("industry_distribution", landscape)
        self.assertIn("size_distribution", landscape)
        self.assertIn("security_posture_summary", landscape)

    def test_context_manager(self):
        """Test context manager functionality."""
        with OrganizationManager(EmailRepository(self.db_path)) as manager:
            organizations = manager.list_organizations(limit=5)
            self.assertIsInstance(organizations, list)


class TestDeepseekIntegration(unittest.TestCase):
    """Test cases for Deepseek integration."""

    @patch('apt_toolkit.deepseek_integration.load_api_key')
    @patch('apt_toolkit.deepseek_integration.OpenAI')
    def test_generate_organization_profile_with_api(self, mock_openai, mock_load_key):
        """Test generating organization profile with API."""
        from apt_toolkit.deepseek_integration import generate_organization_profile
        
        # Mock API key
        mock_load_key.return_value = "test_api_key"
        
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''{
            "description": "A leading technology company",
            "industry": "Technology",
            "size": "large",
            "key_employees": ["CEO", "CTO", "Head of Security"],
            "security_posture": "high",
            "attack_vectors": ["spear_phishing", "supply_chain"]
        }'''
        mock_client.chat.completions.create.return_value = mock_response
        
        profile = generate_organization_profile("Test Corp", use_deepseek=True)
        
        # Check profile structure
        self.assertEqual(profile["organization_name"], "Test Corp")
        self.assertEqual(profile["description"], "A leading technology company")
        self.assertEqual(profile["industry"], "Technology")
        self.assertEqual(profile["size"], "large")
        self.assertEqual(profile["security_posture"], "high")
        self.assertTrue(profile["generated_with_deepseek"])

    @patch('apt_toolkit.deepseek_integration.load_api_key')
    def test_generate_organization_profile_without_api_key(self, mock_load_key):
        """Test generating organization profile without API key."""
        from apt_toolkit.deepseek_integration import generate_organization_profile
        
        # Mock no API key
        mock_load_key.return_value = None
        
        profile = generate_organization_profile("Test Corp", use_deepseek=True)
        
        # Should fall back to basic profile
        self.assertEqual(profile["organization_name"], "Test Corp")
        self.assertEqual(profile["industry"], "Unknown")
        self.assertEqual(profile["size"], "Unknown")
        self.assertFalse(profile.get("generated_with_deepseek", False))


if __name__ == "__main__":
    unittest.main()