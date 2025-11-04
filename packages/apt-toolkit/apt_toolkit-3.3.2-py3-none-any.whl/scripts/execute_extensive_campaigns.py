#!/usr/bin/env python3
"""
Execute Extensive Campaigns
Demonstrates the full chain of campaigns and tools for extensive and fully realistic campaigns
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from apt_toolkit.campaign_logging import setup_campaign_logging

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS_FILE = PROJECT_ROOT / "config" / "campaign_targets.json"
CAMPAIGNS_ROOT = PROJECT_ROOT / "campaigns"
REPORTS_DIR = PROJECT_ROOT / "reports"

setup_campaign_logging("extensive_campaign_chain")
logger = logging.getLogger(__name__)

class CampaignChainExecutor:
    """Executes a chain of campaigns with comprehensive tool integration"""
    
    def __init__(self, targets_file: Optional[str] = None):
        self.targets_file = Path(targets_file) if targets_file else DEFAULT_TARGETS_FILE
        self.targets = self._load_targets()
        self.execution_results = []
        self.campaign_chain = []
    
    def _load_targets(self):
        """Load target configuration"""
        if not self.targets_file.exists():
            logger.error(f"Targets file {self.targets_file} not found")
            return {}
        
        with self.targets_file.open('r') as f:
            return json.load(f)
    
    def list_available_campaigns(self):
        """List all available campaign types"""
        campaigns_dir = CAMPAIGNS_ROOT
        campaigns = []
        
        if campaigns_dir.exists():
            for campaign_path in campaigns_dir.iterdir():
                if campaign_path.is_dir() and (campaign_path / 'run_campaign.py').exists():
                    campaigns.append(campaign_path.name)
        
        return sorted(campaigns)
    
    def create_campaign_chain(self, target_set, campaign_types=None):
        """Create a chain of campaigns to execute"""
        if campaign_types is None:
            campaign_types = self.list_available_campaigns()
        
        logger.info(f"Creating campaign chain with {len(campaign_types)} campaigns against {target_set}")
        
        for campaign_type in campaign_types:
            campaign_info = {
                'type': campaign_type,
                'target_set': target_set,
                'tools': self._get_campaign_tools(campaign_type),
                'payloads': self._get_campaign_payloads(campaign_type),
                'description': self._get_campaign_description(campaign_type)
            }
            self.campaign_chain.append(campaign_info)
        
        return self.campaign_chain
    
    def _get_campaign_tools(self, campaign_type):
        """Get tools available for a campaign"""
        campaign_path = CAMPAIGNS_ROOT / campaign_type
        tools_path = campaign_path / 'tools'
        
        if not tools_path.exists():
            return []
        
        tools = []
        for tool_file in tools_path.iterdir():
            if tool_file.is_file():
                tools.append(tool_file.name)
        
        return tools
    
    def _get_campaign_payloads(self, campaign_type):
        """Get payloads available for a campaign"""
        campaign_path = CAMPAIGNS_ROOT / campaign_type
        payloads_path = campaign_path / 'payloads'
        
        if not payloads_path.exists():
            return []
        
        payloads = []
        for payload_file in payloads_path.iterdir():
            if payload_file.is_file():
                payloads.append(payload_file.name)
        
        return payloads
    
    def _get_campaign_description(self, campaign_type):
        """Get campaign description"""
        campaign_path = CAMPAIGNS_ROOT / campaign_type
        readme_path = campaign_path / 'README.md'
        
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                first_line = f.readline().strip()
                return first_line.replace('# ', '')
        
        return f"{campaign_type.replace('_', ' ').title()} Campaign"
    
    def execute_campaign_chain(self, dry_run=False):
        """Execute the entire campaign chain"""
        if not self.campaign_chain:
            logger.error("No campaign chain created. Call create_campaign_chain() first.")
            return
        
        logger.info(f"Executing campaign chain with {len(self.campaign_chain)} campaigns")
        
        for i, campaign_info in enumerate(self.campaign_chain, 1):
            logger.info(f"[{i}/{len(self.campaign_chain)}] Executing: {campaign_info['type']}")
            
            result = self._execute_single_campaign(campaign_info, dry_run)
            self.execution_results.append(result)
            
            # Add delay between campaigns
            if not dry_run:
                time.sleep(1)
        
        return self.execution_results
    
    def _execute_single_campaign(self, campaign_info, dry_run):
        """Execute a single campaign"""
        campaign_type = campaign_info['type']
        campaign_path = CAMPAIGNS_ROOT / campaign_type
        run_script = campaign_path / 'run_campaign.py'
        
        if not run_script.exists():
            logger.warning(f"Campaign {campaign_type} has no run script")
            return {
                'campaign': campaign_type,
                'status': 'skipped',
                'reason': 'No run script'
            }
        
        if dry_run:
            logger.info(f"DRY RUN: Would execute {campaign_type}")
            return {
                'campaign': campaign_type,
                'status': 'dry_run',
                'tools': campaign_info['tools'],
                'payloads': campaign_info['payloads']
            }
        
        try:
            # Import and execute the campaign
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"campaign_{campaign_type}", run_script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Execute the campaign
            if hasattr(module, 'main'):
                result = module.main()
                return {
                    'campaign': campaign_type,
                    'status': 'completed',
                    'result': result,
                    'tools_used': campaign_info['tools'],
                    'payloads_used': campaign_info['payloads']
                }
            else:
                logger.warning(f"Campaign {campaign_type} has no main function")
                return {
                    'campaign': campaign_type,
                    'status': 'skipped',
                    'reason': 'No main function'
                }
        except Exception as e:
            logger.error(f"Error executing campaign {campaign_type}: {e}")
            return {
                'campaign': campaign_type,
                'status': 'error',
                'error': str(e)
            }
    
    def generate_comprehensive_report(self, output_file=None):
        """Generate comprehensive execution report"""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = Path(output_file) if output_file else REPORTS_DIR / f"extensive_campaigns_chain_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'report_type': 'Extensive Campaign Chain Execution Report',
            'generated_at': datetime.now().isoformat(),
            'total_campaigns': len(self.execution_results),
            'campaigns_executed': len([r for r in self.execution_results if r['status'] == 'completed']),
            'campaigns_skipped': len([r for r in self.execution_results if r['status'] == 'skipped']),
            'campaigns_failed': len([r for r in self.execution_results if r['status'] == 'error']),
            'execution_results': self.execution_results,
            'campaign_chain': self.campaign_chain,
            'summary': self._generate_summary()
        }
        
        with target_path.open('w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Comprehensive report saved to {target_path}")
        return str(target_path)
    
    def _generate_summary(self):
        """Generate summary statistics"""
        if not self.execution_results:
            return {}
        
        total_tools = sum(len(campaign.get('tools', [])) for campaign in self.campaign_chain)
        total_payloads = sum(len(campaign.get('payloads', [])) for campaign in self.campaign_chain)
        
        return {
            'total_campaigns_in_chain': len(self.campaign_chain),
            'total_tools_available': total_tools,
            'total_payloads_available': total_payloads,
            'execution_success_rate': len([r for r in self.execution_results if r['status'] == 'completed']) / len(self.execution_results)
        }

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Execute extensive campaign chain')
    parser.add_argument('--targets-file', default=str(DEFAULT_TARGETS_FILE),
                       help='Path to the campaign targets configuration file')
    parser.add_argument('--target-set', default='defense_aerospace',
                       help='Target set to use')
    parser.add_argument('--max-campaigns', type=int,
                       help='Maximum number of campaigns to execute')
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without actual execution')
    parser.add_argument('--output', help='Output report file')
    
    args = parser.parse_args()
    
    logger.info("Starting extensive campaign chain execution")
    
    # Create campaign executor
    executor = CampaignChainExecutor(args.targets_file)
    
    # List available campaigns
    available_campaigns = executor.list_available_campaigns()
    logger.info(f"Found {len(available_campaigns)} available campaigns")
    
    # Limit campaigns if specified
    if args.max_campaigns:
        available_campaigns = available_campaigns[:args.max_campaigns]
        logger.info(f"Limiting to {len(available_campaigns)} campaigns")
    
    # Create campaign chain
    campaign_chain = executor.create_campaign_chain(args.target_set, available_campaigns)
    
    # Execute campaign chain
    results = executor.execute_campaign_chain(dry_run=args.dry_run)
    
    # Generate report
    report_file = executor.generate_comprehensive_report(args.output)
    
    # Print summary
    completed = len([r for r in results if r['status'] == 'completed'])
    skipped = len([r for r in results if r['status'] == 'skipped'])
    failed = len([r for r in results if r['status'] == 'error'])
    
    logger.info(f"Execution complete: {completed} completed, {skipped} skipped, {failed} failed")
    logger.info(f"Report saved to: {report_file}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
