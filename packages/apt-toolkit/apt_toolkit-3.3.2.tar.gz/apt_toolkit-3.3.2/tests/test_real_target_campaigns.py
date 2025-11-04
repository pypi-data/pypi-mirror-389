#!/usr/bin/env python3
"""
Test suite for real target campaign execution
"""

import unittest
import json
import os
import sys
import socket
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.real_target_campaign_runner import (
    TargetValidator,
    CampaignExecutor
)

class TestTargetValidator(unittest.TestCase):
    """Test target validation functionality"""
    
    def setUp(self):
        self.validator = TargetValidator()
    
    @patch('socket.gethostbyname')
    def test_validate_domain_success(self, mock_gethostbyname):
        """Test successful domain validation"""
        mock_gethostbyname.return_value = '192.168.1.1'
        
        result = self.validator.validate_domain('test.example.com')
        
        self.assertTrue(result)
        self.assertIn('test.example.com', self.validator.validation_results)
        self.assertEqual(
            self.validator.validation_results['test.example.com']['status'],
            'reachable'
        )
    
    @patch('socket.gethostbyname')
    def test_validate_domain_failure(self, mock_gethostbyname):
        """Test failed domain validation"""
        mock_gethostbyname.side_effect = socket.gaierror("Domain not found")
        
        result = self.validator.validate_domain('nonexistent.example.com')
        
        self.assertFalse(result)
        self.assertEqual(
            self.validator.validation_results['nonexistent.example.com']['status'],
            'unreachable'
        )
    
    @patch('subprocess.run')
    def test_validate_ip_success(self, mock_run):
        """Test successful IP validation"""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.validator.validate_ip('10.0.1.10')
        
        self.assertTrue(result)
        self.assertEqual(
            self.validator.validation_results['10.0.1.10']['status'],
            'reachable'
        )
    
    @patch('subprocess.run')
    def test_validate_ip_failure(self, mock_run):
        """Test failed IP validation"""
        mock_run.return_value = MagicMock(returncode=1)
        
        result = self.validator.validate_ip('10.0.1.99')
        
        self.assertFalse(result)
        self.assertEqual(
            self.validator.validation_results['10.0.1.99']['status'],
            'unreachable'
        )
    
    @patch('socket.socket')
    def test_validate_port_open(self, mock_socket_class):
        """Test port validation for open port"""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0
        mock_socket_class.return_value = mock_socket
        
        result = self.validator.validate_port('test.example.com', 443)
        
        self.assertTrue(result)
        self.assertEqual(
            self.validator.validation_results['test.example.com:443']['status'],
            'open'
        )
    
    @patch('socket.socket')
    def test_validate_port_closed(self, mock_socket_class):
        """Test port validation for closed port"""
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 1
        mock_socket_class.return_value = mock_socket
        
        result = self.validator.validate_port('test.example.com', 445)
        
        self.assertFalse(result)
        self.assertEqual(
            self.validator.validation_results['test.example.com:445']['status'],
            'closed'
        )

class TestCampaignExecutor(unittest.TestCase):
    """Test campaign execution functionality"""
    
    def setUp(self):
        # Create a temporary targets file
        self.temp_targets = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.json', 
            delete=False
        )
        self.targets_data = {
            'test_targets': {
                'test_target': {
                    'domains': ['test.example.com'],
                    'ips': ['10.0.1.10'],
                    'ports': [80, 443],
                    'services': ['http', 'https'],
                    'description': 'Test target'
                }
            }
        }
        json.dump(self.targets_data, self.temp_targets)
        self.temp_targets.close()
        
        self.executor = CampaignExecutor(self.temp_targets.name)
    
    def tearDown(self):
        # Clean up temporary file
        os.unlink(self.temp_targets.name)
    
    def test_load_targets(self):
        """Test target configuration loading"""
        self.assertIn('test_targets', self.executor.targets)
        self.assertIn('test_target', self.executor.targets['test_targets'])
    
    def test_list_available_campaigns(self):
        """Test listing available campaigns"""
        campaigns = self.executor.list_available_campaigns()
        
        self.assertIsInstance(campaigns, list)
        # Should find at least some campaigns
        self.assertGreater(len(campaigns), 0)
    
    @patch.object(TargetValidator, 'validate_domain')
    @patch.object(TargetValidator, 'validate_ip')
    @patch.object(TargetValidator, 'validate_port')
    def test_validate_target_set(self, mock_port, mock_ip, mock_domain):
        """Test target set validation"""
        mock_domain.return_value = True
        mock_ip.return_value = True
        mock_port.return_value = True
        
        results = self.executor.validate_target_set('test_target')
        
        self.assertIn('domains', results)
        self.assertIn('ips', results)
        self.assertIn('ports', results)
        
        mock_domain.assert_called_with('test.example.com')
        mock_ip.assert_called_with('10.0.1.10')
    
    @patch('subprocess.run')
    @patch.object(CampaignExecutor, 'validate_target_set')
    def test_execute_campaign_success(self, mock_validate, mock_run):
        """Test successful campaign execution"""
        mock_validate.return_value = {
            'domains': {'test.example.com': True},
            'ips': {'10.0.1.10': True},
            'ports': {80: True, 443: True}
        }
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Campaign executed successfully',
            stderr=''
        )
        
        # Create a mock campaign directory
        with patch('pathlib.Path.exists', return_value=True):
            result = self.executor.execute_campaign(
                'defense_contractor_campaign',
                'test_target',
                dry_run=False
            )
        
        self.assertEqual(result['campaign'], 'defense_contractor_campaign')
        self.assertEqual(result['target_set'], 'test_target')
        self.assertEqual(result['execution']['status'], 'completed')
    
    @patch.object(CampaignExecutor, 'validate_target_set')
    def test_execute_campaign_dry_run(self, mock_validate):
        """Test campaign execution in dry run mode"""
        mock_validate.return_value = {
            'domains': {'test.example.com': True},
            'ips': {'10.0.1.10': True},
            'ports': {80: True}
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.executor.execute_campaign(
                'defense_contractor_campaign',
                'test_target',
                dry_run=True
            )
        
        self.assertEqual(result['execution']['status'], 'dry_run')
        self.assertIn('message', result['execution'])
    
    @patch.object(CampaignExecutor, 'validate_target_set')
    def test_execute_campaign_no_valid_targets(self, mock_validate):
        """Test campaign execution with no valid targets"""
        mock_validate.return_value = {
            'domains': {},
            'ips': {},
            'ports': {}
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.executor.execute_campaign(
                'defense_contractor_campaign',
                'test_target',
                dry_run=False
            )
        
        self.assertEqual(result['error'], 'No valid targets found')
    
    @patch.object(CampaignExecutor, 'execute_campaign')
    def test_execute_all_campaigns(self, mock_execute):
        """Test executing all campaigns"""
        mock_execute.return_value = {
            'campaign': 'test_campaign',
            'status': 'success'
        }
        
        with patch.object(
            CampaignExecutor, 
            'list_available_campaigns',
            return_value=['campaign1', 'campaign2']
        ):
            results = self.executor.execute_all_campaigns(
                'test_target',
                dry_run=True
            )
        
        self.assertEqual(len(results), 2)
        self.assertEqual(mock_execute.call_count, 2)
    
    def test_save_execution_report(self):
        """Test saving execution report"""
        self.executor.execution_log = [
            {
                'campaign': 'test',
                'status': 'success'
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

class TestChineseAPTRealTargets(unittest.TestCase):
    """Test Chinese APT campaign execution"""
    
    def setUp(self):
        self.temp_targets = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.json', 
            delete=False
        )
        self.targets_data = {
            'test_targets': {
                'test': {
                    'domains': ['test.com'],
                    'ips': ['10.0.0.1']
                }
            }
        }
        json.dump(self.targets_data, self.temp_targets)
        self.temp_targets.close()
    
    def tearDown(self):
        os.unlink(self.temp_targets.name)

    def test_load_real_targets(self):
        """Test loading real targets"""
        from campaigns.chinese_apt_real_targets import RealTargetChineseAPT
        
        runner = RealTargetChineseAPT()
        targets = runner.load_real_targets(self.temp_targets.name)
        
        self.assertIn('test', targets)
        self.assertIn('domains', targets['test'])
    
    @patch('socket.gethostbyname')
    def test_validate_target_domain(self, mock_gethostbyname):
        """Test domain target validation"""
        from campaigns.chinese_apt_real_targets import RealTargetChineseAPT
        
        mock_gethostbyname.return_value = '192.168.1.1'
        
        runner = RealTargetChineseAPT()
        result = runner.validate_target('test.example.com', 'domain')
        
        self.assertTrue(result)
    
    def test_apt41_gaming_campaign(self):
        """Test APT41 gaming campaign execution"""
        from campaigns.chinese_apt_real_targets import RealTargetChineseAPT
        
        runner = RealTargetChineseAPT()
        target_set = {
            'domains': ['game.example.com'],
            'ips': ['10.0.1.1']
        }
        
        with patch.object(runner, 'validate_target', return_value=True):
            result = runner.execute_apt41_gaming_campaign(target_set)
        
        self.assertEqual(result['campaign'], 'APT41 Gaming Industry')
        self.assertIn('phases', result)
        self.assertIn('reconnaissance', result['phases'])
        self.assertIn('supply_chain', result['phases'])
    
    def test_comprehensive_report_generation(self):
        """Test comprehensive report generation"""
        from campaigns.chinese_apt_real_targets import RealTargetChineseAPT
        
        runner = RealTargetChineseAPT()
        runner.execution_results = [
            {
                'campaign': 'test',
                'targets': {
                    'domains': ['test.com'],
                    'ips': ['10.0.0.1']
                }
            }
        ]
        
        report = runner.generate_comprehensive_report()
        
        self.assertEqual(report['report_type'], 'Chinese APT Campaign Execution')
        self.assertEqual(report['total_campaigns'], 1)
        self.assertIn('summary', report)
        self.assertIn('recommendations', report)

if __name__ == '__main__':
    unittest.main()
