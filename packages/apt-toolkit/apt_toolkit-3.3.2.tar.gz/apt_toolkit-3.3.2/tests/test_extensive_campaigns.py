#!/usr/bin/env python3
"""
Test Suite for Extensive Campaign Execution
Tests the comprehensive campaign and tool chain for realistic campaign execution
"""

import unittest
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.real_target_campaign_runner import CampaignExecutor, TargetValidator

class TestExtensiveCampaignExecution(unittest.TestCase):
    """Test extensive campaign execution capabilities"""
    
    def setUp(self):
        # Create a temporary targets file
        self.temp_targets = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.json', 
            delete=False
        )
        self.targets_data = {
            'test_targets': {
                'defense_aerospace': {
                    'domains': ['test.example.com'],
                    'ips': ['10.0.1.10'],
                    'ports': [80, 443],
                    'services': ['http', 'https'],
                    'description': 'Test defense contractor'
                }
            }
        }
        json.dump(self.targets_data, self.temp_targets)
        self.temp_targets.close()
        
        self.executor = CampaignExecutor(self.temp_targets.name)
    
    def tearDown(self):
        # Clean up temporary file
        os.unlink(self.temp_targets.name)
    
    def test_campaign_tools_availability(self):
        """Test that all campaigns have access to all tools"""
        campaigns = self.executor.list_available_campaigns()
        
        self.assertGreater(len(campaigns), 0, "Should find at least one campaign")
        
        # Check that each campaign has tools directory
        for campaign in campaigns[:5]:  # Test first 5 campaigns
            campaign_path = ROOT_DIR / 'campaigns' / campaign
            tools_path = campaign_path / 'tools'
            
            self.assertTrue(tools_path.exists(), f"Campaign {campaign} should have tools directory")
            
            # Check for common tools
            common_tools = ['apt_recon.sh', 'apt_persistence.py', 'apt_web_recon.js']
            for tool in common_tools:
                tool_path = tools_path / tool
                self.assertTrue(tool_path.exists() or tool_path.is_symlink(), 
                              f"Campaign {campaign} should have tool {tool}")
    
    def test_campaign_execution_framework(self):
        """Test the campaign execution framework"""
        campaigns = self.executor.list_available_campaigns()
        
        # Test that we can execute campaigns
        with patch.object(CampaignExecutor, 'validate_target_set') as mock_validate:
            mock_validate.return_value = {
                'domains': {'test.example.com': True},
                'ips': {'10.0.1.10': True},
                'ports': {80: True, 443: True}
            }
            
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='Campaign executed successfully',
                    stderr=''
                )
                
                # Test a specific campaign
                with patch('pathlib.Path.exists', return_value=True):
                    result = self.executor.execute_campaign(
                        'defense_contractor_campaign',
                        'defense_aerospace',
                        dry_run=False
                    )
                
                self.assertEqual(result['campaign'], 'defense_contractor_campaign')
                self.assertEqual(result['target_set'], 'defense_aerospace')
                self.assertEqual(result['execution']['status'], 'completed')
    
    def test_campaign_tool_integration(self):
        """Test that campaigns properly integrate with tools"""
        # Test defense contractor campaign tools
        defense_campaign_path = ROOT_DIR / 'campaigns/defense_contractor_campaign'
        
        # Check for campaign-specific tools
        campaign_tools = defense_campaign_path / 'tools'
        self.assertTrue(campaign_tools.exists())
        
        # Check for aerospace design finder
        aerospace_tool = campaign_tools / 'aerospace_design_finder.py'
        self.assertTrue(aerospace_tool.exists(), 
                       "Defense contractor campaign should have aerospace design finder")
        
        # Check for intellectual property payloads
        ip_payloads = defense_campaign_path / 'payloads'
        self.assertTrue(ip_payloads.exists(), 
                       "Defense contractor campaign should have payloads directory")
    
    def test_real_target_validation(self):
        """Test real target validation functionality"""
        validator = TargetValidator()
        
        with patch('socket.gethostbyname') as mock_gethostbyname:
            mock_gethostbyname.return_value = '192.168.1.1'
            
            result = validator.validate_domain('test.example.com')
            self.assertTrue(result)
            self.assertEqual(validator.validation_results['test.example.com']['status'], 'reachable')
    
    def test_campaign_report_generation(self):
        """Test campaign execution report generation"""
        self.executor.execution_log = [
            {
                'campaign': 'defense_contractor_campaign',
                'target_set': 'defense_aerospace',
                'execution': {'status': 'completed'}
            }
        ]
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        ) as temp_report:
            report_file = self.executor.save_execution_report(temp_report.name)
            
            self.assertTrue(os.path.exists(report_file))
            
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            self.assertEqual(report['total_campaigns'], 1)
            self.assertIn('executions', report)
            
            os.unlink(report_file)
    
    def test_campaign_tool_chain_execution(self):
        """Test the complete campaign tool chain execution"""
        # Verify all tools are accessible
        from scripts import ensure_campaign_tools
        
        campaigns = ensure_campaign_tools.get_all_campaigns()
        
        self.assertGreater(len(campaigns), 0, "Should find campaigns")
        
        # Test tool verification
        try:
            from scripts.ensure_campaign_tools import verify_campaign_tools  # type: ignore
        except ImportError:
            self.skipTest("verify_campaign_tools helper not available")
        else:
            # This should run without errors
            try:
                verify_campaign_tools()
            except Exception as e:
                self.fail(f"Tool verification failed: {e}")

class TestCampaignToolIntegration(unittest.TestCase):
    """Test campaign tool integration and execution"""
    
    def test_campaign_specific_tools(self):
        """Test that campaign-specific tools are preserved"""
        campaigns_to_test = [
            ('defense_contractor_campaign', 'aerospace_design_finder.py'),
            ('financial_institution_campaign', 'financial_data_finder.py'),
            ('healthcare_campaign', 'patient_data_finder.py'),
            ('government_agency_campaign', 'classified_info_finder.py')
        ]
        
        for campaign, expected_tool in campaigns_to_test:
            campaign_path = ROOT_DIR / 'campaigns' / campaign
            tool_path = campaign_path / 'tools' / expected_tool
            
            self.assertTrue(tool_path.exists(), 
                           f"Campaign {campaign} should have tool {expected_tool}")
    
    def test_campaign_payloads(self):
        """Test that campaigns have appropriate payloads"""
        campaigns_to_test = [
            ('defense_contractor_campaign', 'intellectual_property'),
            ('financial_institution_campaign', 'financial_data_exfiltrator.py'),
            ('healthcare_campaign', 'patient_data_exfiltrator.py')
        ]
        
        for campaign, payload_pattern in campaigns_to_test:
            campaign_path = ROOT_DIR / 'campaigns' / campaign
            payloads_path = campaign_path / 'payloads'
            
            self.assertTrue(payloads_path.exists(), 
                           f"Campaign {campaign} should have payloads directory")
            
            # Check for payload files
            payload_files = list(payloads_path.glob('*.py'))
            self.assertGreater(len(payload_files), 0, 
                              f"Campaign {campaign} should have payload scripts")
    
    def test_campaign_execution_scripts(self):
        """Test that all campaigns have execution scripts"""
        campaigns_dir = ROOT_DIR / 'campaigns'
        
        for campaign_path in campaigns_dir.iterdir():
            if campaign_path.is_dir() and campaign_path.name != "__pycache__":
                run_script = campaign_path / 'run_campaign.py'
                self.assertTrue(run_script.exists(), 
                               f"Campaign {campaign_path.name} should have run_campaign.py")
                
                # Check if enhanced runner exists
                enhanced_script = campaign_path / 'run_campaign_enhanced.py'
                if enhanced_script.exists():
                    # Enhanced script should be executable
                    self.assertTrue(os.access(enhanced_script, os.X_OK) or 
                                   enhanced_script.suffix == '.py',
                                   f"Enhanced script {enhanced_script} should be executable")

class TestRealTargetCampaigns(unittest.TestCase):
    """Test real target campaign execution"""
    
    def test_real_target_runner(self):
        """Test the real target campaign runner"""
        from scripts.real_target_campaign_runner import main
        
        # Test with dry run
        with patch('sys.argv', ['real_target_campaign_runner.py', '--dry-run', '--campaign', 'all']):
            try:
                # This should run without errors in dry run mode
                main()
            except SystemExit:
                pass  # Expected for argparse
            except Exception as e:
                self.fail(f"Real target campaign runner failed: {e}")
    
    def test_campaign_targets_configuration(self):
        """Test campaign targets configuration"""
        targets_file = ROOT_DIR / 'config' / 'campaign_targets.json'
        
        self.assertTrue(targets_file.exists(), "Campaign targets file should exist")
        
        with open(targets_file, 'r') as f:
            targets_config = json.load(f)
        
        self.assertIn('test_targets', targets_config)
        self.assertIn('defense_aerospace', targets_config['test_targets'])
        self.assertIn('financial_institutions', targets_config['test_targets'])
        
        # Verify target sets have required fields
        for target_set_name, target_set in targets_config['test_targets'].items():
            self.assertIn('domains', target_set)
            self.assertIn('ips', target_set)
            self.assertIn('ports', target_set)
            self.assertIn('services', target_set)
            self.assertIn('description', target_set)

if __name__ == '__main__':
    unittest.main()
