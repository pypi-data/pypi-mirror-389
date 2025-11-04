#!/usr/bin/env python3
"""
Real Target Campaign Runner
Executes APT campaigns against configured real targets with proper controls
"""

import argparse
import json
import logging
import os
import sys
import time
import socket
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from apt_toolkit.campaign_logging import setup_campaign_logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS_FILE = PROJECT_ROOT / "config" / "campaign_targets.json"
CAMPAIGNS_ROOT = PROJECT_ROOT / "campaigns"
REPORTS_DIR = PROJECT_ROOT / "reports"

setup_campaign_logging("real_target_campaign")
logger = logging.getLogger(__name__)

class TargetValidator:
    """Validates targets before campaign execution"""
    
    def __init__(self):
        self.validation_results = {}
    
    def validate_domain(self, domain: str) -> bool:
        """Validate domain is reachable"""
        try:
            socket.gethostbyname(domain)
            self.validation_results[domain] = {'type': 'domain', 'status': 'reachable'}
            return True
        except socket.gaierror:
            self.validation_results[domain] = {'type': 'domain', 'status': 'unreachable'}
            return False
    
    def validate_ip(self, ip: str) -> bool:
        """Validate IP is reachable"""
        try:
            # Simple ping test (platform independent)
            param = '-n' if sys.platform == 'win32' else '-c'
            result = subprocess.run(
                ['ping', param, '1', ip],
                capture_output=True,
                timeout=5
            )
            reachable = result.returncode == 0
            self.validation_results[ip] = {
                'type': 'ip', 
                'status': 'reachable' if reachable else 'unreachable'
            }
            return reachable
        except (subprocess.TimeoutExpired, Exception) as e:
            self.validation_results[ip] = {'type': 'ip', 'status': f'error: {str(e)}'}
            return False
    
    def validate_port(self, host: str, port: int) -> bool:
        """Check if port is open on target"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            port_status = 'open' if result == 0 else 'closed'
            self.validation_results[f"{host}:{port}"] = {
                'type': 'port',
                'status': port_status
            }
            return result == 0
        except Exception as e:
            self.validation_results[f"{host}:{port}"] = {
                'type': 'port',
                'status': f'error: {str(e)}'
            }
            return False

class CampaignExecutor:
    """Executes campaigns against real targets"""
    
    def __init__(self, targets_file: Optional[str] = None):
        self.targets_file = Path(targets_file) if targets_file else DEFAULT_TARGETS_FILE
        self.targets = self._load_targets()
        self.validator = TargetValidator()
        self.execution_log = []
        
    def _load_targets(self) -> Dict:
        """Load target configuration"""
        if not self.targets_file.exists():
            logger.error(f"Targets file {self.targets_file} not found")
            return {}
        
        with self.targets_file.open('r') as f:
            return json.load(f)
    
    def list_available_campaigns(self) -> List[str]:
        """List all available campaign types"""
        campaigns_dir = CAMPAIGNS_ROOT
        campaigns = []
        
        if campaigns_dir.exists():
            for campaign_path in campaigns_dir.iterdir():
                if campaign_path.is_dir() and (campaign_path / 'run_campaign.py').exists():
                    campaigns.append(campaign_path.name)
        
        return sorted(campaigns)
    
    def validate_target_set(self, target_set_name: str) -> Dict[str, Any]:
        """Validate all targets in a target set"""
        if target_set_name not in self.targets.get('test_targets', {}):
            logger.error(f"Target set '{target_set_name}' not found")
            return {}
        
        target_set = self.targets['test_targets'][target_set_name]
        validation_results = {
            'domains': {},
            'ips': {},
            'ports': {}
        }
        
        # Validate domains
        for domain in target_set.get('domains', []):
            logger.info(f"Validating domain: {domain}")
            validation_results['domains'][domain] = self.validator.validate_domain(domain)
        
        # Validate IPs
        for ip in target_set.get('ips', []):
            logger.info(f"Validating IP: {ip}")
            validation_results['ips'][ip] = self.validator.validate_ip(ip)
        
        # Validate ports on first valid domain or IP
        test_host = None
        if validation_results['domains']:
            for domain, is_valid in validation_results['domains'].items():
                if is_valid:
                    test_host = domain
                    break
        
        if not test_host and validation_results['ips']:
            for ip, is_valid in validation_results['ips'].items():
                if is_valid:
                    test_host = ip
                    break
        
        if test_host:
            for port in target_set.get('ports', []):
                logger.info(f"Validating port {port} on {test_host}")
                validation_results['ports'][port] = self.validator.validate_port(test_host, port)
        
        return validation_results
    
    def execute_campaign(self, campaign_type: str, target_set: str, 
                        dry_run: bool = False) -> Dict[str, Any]:
        """Execute a specific campaign against a target set"""
        
        # Validate campaign exists
        campaign_path = CAMPAIGNS_ROOT / campaign_type
        if not campaign_path.exists():
            logger.error(f"Campaign '{campaign_type}' not found")
            return {'error': f"Campaign '{campaign_type}' not found"}
        
        run_script = campaign_path / 'run_campaign.py'
        if not run_script.exists():
            logger.error(f"Campaign runner script not found for {campaign_type}")
            return {'error': 'Campaign runner script not found'}
        
        # Get target configuration
        if target_set not in self.targets.get('test_targets', {}):
            logger.error(f"Target set '{target_set}' not found")
            return {'error': f"Target set '{target_set}' not found"}
        
        target_config = self.targets['test_targets'][target_set]
        
        # Validate targets first
        logger.info(f"Validating targets for {target_set}")
        validation_results = self.validate_target_set(target_set)
        
        # Check if we have at least one valid target
        has_valid_target = False
        for category in validation_results.values():
            if any(category.values()):
                has_valid_target = True
                break
        
        if not has_valid_target:
            logger.error("No valid targets found")
            return {
                'error': 'No valid targets found',
                'validation_results': validation_results
            }
        
        execution_result = {
            'campaign': campaign_type,
            'target_set': target_set,
            'timestamp': datetime.now().isoformat(),
            'validation': validation_results,
            'execution': {}
        }
        
        if dry_run:
            logger.info("DRY RUN - Not executing actual campaign")
            execution_result['execution'] = {
                'status': 'dry_run',
                'message': 'Campaign would be executed with validated targets'
            }
            return execution_result
        
        # Execute the campaign
        logger.info(f"Executing {campaign_type} campaign against {target_set}")
        
        try:
            # Prepare environment with target information
            env = os.environ.copy()
            env['TARGET_DOMAINS'] = json.dumps(target_config.get('domains', []))
            env['TARGET_IPS'] = json.dumps(target_config.get('ips', []))
            env['TARGET_PORTS'] = json.dumps(target_config.get('ports', []))
            env['TARGET_SERVICES'] = json.dumps(target_config.get('services', []))
            
            # Run the campaign
            result = subprocess.run(
                [sys.executable, str(run_script)],
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )
            
            execution_result['execution'] = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            # Log execution
            self.execution_log.append(execution_result)
            
        except subprocess.TimeoutExpired:
            execution_result['execution'] = {
                'status': 'timeout',
                'message': 'Campaign execution timed out after 5 minutes'
            }
        except Exception as e:
            execution_result['execution'] = {
                'status': 'error',
                'message': str(e)
            }
        
        return execution_result
    
    def execute_all_campaigns(self, target_set: str, 
                            dry_run: bool = False) -> List[Dict[str, Any]]:
        """Execute all available campaigns against a target set"""
        campaigns = self.list_available_campaigns()
        results = []
        
        logger.info(f"Executing {len(campaigns)} campaigns against {target_set}")
        
        for campaign in campaigns:
            logger.info(f"Running campaign: {campaign}")
            result = self.execute_campaign(campaign, target_set, dry_run)
            results.append(result)
            
            # Add delay between campaigns to avoid overwhelming targets
            if not dry_run:
                time.sleep(5)
        
        return results
    
    def save_execution_report(self, filename: Optional[str] = None) -> str:
        """Save execution report to file"""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = Path(filename) if filename else REPORTS_DIR / f"campaign_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
        report = {
            'execution_timestamp': datetime.now().isoformat(),
            'total_campaigns': len(self.execution_log),
            'executions': self.execution_log,
            'validator_results': self.validator.validation_results
        }
        
        with target_path.open('w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Execution report saved to {target_path}")
        return str(target_path)

def main():
    parser = argparse.ArgumentParser(
        description='Execute APT campaigns against real targets'
    )
    
    parser.add_argument(
        '--targets-file',
        default=str(DEFAULT_TARGETS_FILE),
        help='Path to the campaign targets configuration file'
    )
    
    parser.add_argument(
        '--campaign',
        help='Specific campaign to run (or "all" for all campaigns)'
    )
    
    parser.add_argument(
        '--target-set',
        default='defense_contractor',
        help='Target set to use from configuration'
    )
    
    parser.add_argument(
        '--list-campaigns',
        action='store_true',
        help='List available campaigns'
    )
    
    parser.add_argument(
        '--list-targets',
        action='store_true',
        help='List available target sets'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate targets without executing campaigns'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform dry run without actual execution'
    )
    
    parser.add_argument(
        '--output',
        help='Output file for execution report'
    )
    
    args = parser.parse_args()
    
    executor = CampaignExecutor(args.targets_file)
    
    # Handle list operations
    if args.list_campaigns:
        campaigns = executor.list_available_campaigns()
        print("\nAvailable Campaigns:")
        for campaign in campaigns:
            print(f"  - {campaign}")
        return
    
    if args.list_targets:
        if 'test_targets' in executor.targets:
            print("\nAvailable Target Sets:")
            for target_set in executor.targets['test_targets']:
                desc = executor.targets['test_targets'][target_set].get('description', '')
                print(f"  - {target_set}: {desc}")
        return
    
    # Handle validation only
    if args.validate_only:
        results = executor.validate_target_set(args.target_set)
        print(f"\nValidation Results for {args.target_set}:")
        print(json.dumps(results, indent=2))
        return
    
    # Execute campaigns
    if args.campaign:
        if args.campaign.lower() == 'all':
            results = executor.execute_all_campaigns(args.target_set, args.dry_run)
            print(f"\nExecuted {len(results)} campaigns")
        else:
            result = executor.execute_campaign(args.campaign, args.target_set, args.dry_run)
            print(f"\nCampaign Execution Result:")
            print(json.dumps(result, indent=2))
    else:
        print("Please specify --campaign or use --list-campaigns to see available options")
        return
    
    # Save report if requested
    if args.output:
        executor.save_execution_report(args.output)

if __name__ == '__main__':
    main()
