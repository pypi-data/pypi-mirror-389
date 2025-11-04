#!/usr/bin/env python3
"""
Red Team Real Targets Campaign Runner
Executes APT campaigns against real targets with retry logic until success
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

setup_campaign_logging("red_team_campaign")
logger = logging.getLogger(__name__)

class RedTeamCampaignExecutor:
    """Enhanced campaign executor with retry logic and success criteria"""
    
    def __init__(self, targets_file: Optional[str] = None):
        self.targets_file = Path(targets_file) if targets_file else DEFAULT_TARGETS_FILE
        self.targets = self._load_targets()
        self.execution_log = []
        self.successful_campaigns = []
        self.failed_campaigns = []
        
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
    
    def execute_campaign_with_retry(self, campaign_type: str, target_set: str, 
                                   max_retries: int = 3, 
                                   retry_delay: int = 30,
                                   dry_run: bool = False) -> Dict[str, Any]:
        """Execute a campaign with retry logic until success"""
        
        for attempt in range(max_retries + 1):
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1} for campaign {campaign_type}")
            
            result = self._execute_single_campaign_attempt(campaign_type, target_set, dry_run)
            
            # Check if campaign was successful
            if self._is_campaign_successful(result):
                logger.info(f"Campaign {campaign_type} SUCCESSFUL on attempt {attempt + 1}")
                result['attempts'] = attempt + 1
                result['final_status'] = 'success'
                self.successful_campaigns.append(result)
                return result
            
            # If not last attempt, wait and retry
            if attempt < max_retries:
                logger.warning(f"Campaign {campaign_type} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Campaign {campaign_type} FAILED after {max_retries + 1} attempts")
                result['attempts'] = max_retries + 1
                result['final_status'] = 'failed'
                self.failed_campaigns.append(result)
                return result
    
    def _execute_single_campaign_attempt(self, campaign_type: str, target_set: str, 
                                        dry_run: bool = False) -> Dict[str, Any]:
        """Execute a single campaign attempt"""
        
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
        
        execution_result = {
            'campaign': campaign_type,
            'target_set': target_set,
            'timestamp': datetime.now().isoformat(),
            'target_config': target_config,
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
            env['RED_TEAM_MODE'] = 'true'
            env['MAX_RETRIES'] = '3'
            
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
                'stderr': result.stderr,
                'success_indicators': self._analyze_success_indicators(result.stdout)
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
    
    def _is_campaign_successful(self, result: Dict) -> bool:
        """Determine if a campaign execution was successful"""
        execution = result.get('execution', {})
        
        # In dry-run mode, always consider it successful
        if execution.get('status') == 'dry_run':
            return True
        
        if execution.get('status') != 'completed':
            return False
        
        # Check return code
        if execution.get('return_code') != 0:
            return False
        
        # Check for success indicators in output (optional)
        stdout = execution.get('stdout', '').lower()
        success_indicators = ['success', 'completed', 'finished', 'done', 'achieved']
        
        for indicator in success_indicators:
            if indicator in stdout:
                return True
        
        # If no clear indicators but return code is 0, still consider it successful
        return True
    
    def _analyze_success_indicators(self, stdout: str) -> List[str]:
        """Analyze stdout for success indicators"""
        indicators = []
        stdout_lower = stdout.lower()
        
        success_phrases = [
            'success', 'completed', 'finished', 'done', 'achieved',
            'compromised', 'accessed', 'obtained', 'installed',
            'established', 'exfiltrated', 'harvested'
        ]
        
        for phrase in success_phrases:
            if phrase in stdout_lower:
                indicators.append(phrase)
        
        return indicators
    
    def execute_all_campaigns_until_success(self, target_set: str, 
                                          max_retries_per_campaign: int = 3,
                                          max_total_attempts: int = 10,
                                          dry_run: bool = False) -> List[Dict[str, Any]]:
        """Execute all available campaigns against a target set until at least one succeeds"""
        campaigns = self.list_available_campaigns()
        results = []
        total_attempts = 0
        
        logger.info(f"Executing {len(campaigns)} campaigns against {target_set} until success")
        
        for campaign in campaigns:
            if total_attempts >= max_total_attempts:
                logger.warning(f"Reached maximum total attempts ({max_total_attempts})")
                break
                
            logger.info(f"Running campaign: {campaign}")
            result = self.execute_campaign_with_retry(
                campaign, 
                target_set, 
                max_retries=max_retries_per_campaign,
                dry_run=dry_run
            )
            results.append(result)
            
            total_attempts += result.get('attempts', 1)
            
            # If we have at least one successful campaign, we can stop
            if self._is_campaign_successful(result):
                logger.info(f"Success achieved with campaign {campaign}!")
                break
            
            # Add delay between campaigns to avoid overwhelming targets
            if not dry_run:
                time.sleep(10)
        
        return results
    
    def save_comprehensive_report(self, filename: Optional[str] = None) -> str:
        """Save comprehensive execution report to file"""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = Path(filename) if filename else REPORTS_DIR / f"red_team_campaign_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'report_type': 'Red Team Campaign Execution Report',
            'generated': datetime.now().isoformat(),
            'total_campaigns_executed': len(self.execution_log),
            'successful_campaigns': len(self.successful_campaigns),
            'failed_campaigns': len(self.failed_campaigns),
            'success_rate': f"{len(self.successful_campaigns) / len(self.execution_log) * 100:.1f}%" if self.execution_log else "0%",
            'executions': self.execution_log,
            'successful_campaigns_list': self.successful_campaigns,
            'failed_campaigns_list': self.failed_campaigns,
            'summary': {
                'total_attempts': sum(r.get('attempts', 1) for r in self.execution_log),
                'average_attempts_per_campaign': sum(r.get('attempts', 1) for r in self.execution_log) / len(self.execution_log) if self.execution_log else 0,
                'first_successful_campaign': self.successful_campaigns[0]['campaign'] if self.successful_campaigns else None,
                'execution_time': f"{len(self.execution_log) * 5} minutes (estimated)"
            }
        }
        
        with target_path.open('w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Comprehensive execution report saved to {target_path}")
        return str(target_path)

def main():
    parser = argparse.ArgumentParser(
        description='Execute APT campaigns against real targets with retry logic until success'
    )
    
    parser.add_argument(
        '--targets-file',
        default=str(DEFAULT_TARGETS_FILE),
        help='Path to the campaign targets configuration file'
    )
    
    parser.add_argument(
        '--campaign',
        help='Specific campaign to run (or "all" for all campaigns with retry logic)'
    )
    
    parser.add_argument(
        '--target-set',
        default='defense_aerospace',
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
        '--max-retries',
        type=int,
        default=3,
        help='Maximum number of retry attempts per campaign'
    )
    
    parser.add_argument(
        '--max-total-attempts',
        type=int,
        default=10,
        help='Maximum total attempts across all campaigns'
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
    
    executor = RedTeamCampaignExecutor(args.targets_file)
    
    if args.list_campaigns:
        campaigns = executor.list_available_campaigns()
        print("Available Campaigns:")
        for campaign in campaigns:
            print(f"  - {campaign}")
        return
    
    if args.list_targets:
        targets = executor.targets.get('test_targets', {})
        print("Available Target Sets:")
        for target_name, target_config in targets.items():
            print(f"  - {target_name}: {target_config.get('description', 'No description')}")
        return
    
    if not args.campaign:
        print("Error: --campaign argument is required")
        parser.print_help()
        return
    
    if args.campaign == 'all':
        # Execute all campaigns until success
        results = executor.execute_all_campaigns_until_success(
            args.target_set,
            max_retries_per_campaign=args.max_retries,
            max_total_attempts=args.max_total_attempts,
            dry_run=args.dry_run
        )
        
        # Generate summary
        successful = [r for r in results if executor._is_campaign_successful(r)]
        failed = [r for r in results if not executor._is_campaign_successful(r)]
        
        print(f"\n=== RED TEAM CAMPAIGN EXECUTION SUMMARY ===")
        print(f"Total Campaigns Executed: {len(results)}")
        print(f"Successful Campaigns: {len(successful)}")
        print(f"Failed Campaigns: {len(failed)}")
        
        if successful:
            print(f"\nFirst Successful Campaign: {successful[0]['campaign']}")
            print(f"Attempts Required: {successful[0].get('attempts', 1)}")
        
    else:
        # Execute single campaign with retry
        result = executor.execute_campaign_with_retry(
            args.campaign,
            args.target_set,
            max_retries=args.max_retries,
            dry_run=args.dry_run
        )
        
        print(f"\n=== CAMPAIGN EXECUTION RESULT ===")
        print(json.dumps(result, indent=2))
    
    # Save comprehensive report
    report_file = executor.save_comprehensive_report(args.output)
    print(f"\nDetailed report saved to: {report_file}")

if __name__ == '__main__':
    main()
