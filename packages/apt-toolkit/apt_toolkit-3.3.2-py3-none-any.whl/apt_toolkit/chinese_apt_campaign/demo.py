"""
Demonstration script for Chinese APT campaign tools.

This script demonstrates the capabilities of the enhanced Chinese APT
campaign toolkit for targeting government, military, and critical
infrastructure systems.
"""

import json
from typing import Dict, Any

from .advanced_targeting import AdvancedTargetingEngine
from .campaign_orchestrator import CampaignOrchestrator
from .system_exploitation import SystemExploitationEngine


def demonstrate_targeting() -> Dict[str, Any]:
    """Demonstrate advanced targeting capabilities."""
    
    print("=== ADVANCED TARGETING DEMONSTRATION ===\n")
    
    targeting_engine = AdvancedTargetingEngine(seed=42)
    
    # Generate government targets
    print("1. Government Targets:")
    gov_targets = targeting_engine.generate_government_targets()
    for target in gov_targets[:3]:  # Show first 3
        print(f"   - {target['domain']}: {target['sensitivity_level']} ({target['priority_level']})")
    
    # Generate military targets
    print("\n2. Military Targets:")
    mil_targets = targeting_engine.generate_military_targets()
    for target in mil_targets[:3]:  # Show first 3
        print(f"   - {target['domain']}: {target['mission_type']} ({target['geographic_region']})")
    
    # Generate infrastructure targets
    print("\n3. Critical Infrastructure Targets:")
    infra_targets = targeting_engine.generate_critical_infrastructure_targets()
    for target in infra_targets[:3]:  # Show first 3
        print(f"   - {target['domain']}: {target['sector']} ({target['criticality_level']})")
    
    return {
        "government_targets": gov_targets[:3],
        "military_targets": mil_targets[:3],
        "infrastructure_targets": infra_targets[:3]
    }


def demonstrate_exploitation(targets: Dict[str, Any]) -> Dict[str, Any]:
    """Demonstrate system-specific exploitation capabilities."""
    
    print("\n=== SYSTEM EXPLOITATION DEMONSTRATION ===\n")
    
    exploitation_engine = SystemExploitationEngine(seed=42)
    
    exploitation_plans = {}
    
    # Government exploitation
    if targets["government_targets"]:
        gov_target = targets["government_targets"][0]
        print("1. Government System Exploitation:")
        gov_plan = exploitation_engine.exploit_government_systems(gov_target)
        print(f"   Target: {gov_plan['target_domain']}")
        print(f"   Primary Vectors: {', '.join(gov_plan['exploitation_vectors'][:3])}")
        print(f"   Persistence: {', '.join(gov_plan['persistence_mechanisms'][:2])}")
        exploitation_plans["government"] = gov_plan
    
    # Military exploitation
    if targets["military_targets"]:
        mil_target = targets["military_targets"][0]
        print("\n2. Military System Exploitation:")
        mil_plan = exploitation_engine.exploit_military_systems(mil_target)
        print(f"   Target: {mil_plan['target_domain']}")
        print(f"   Mission Type: {mil_plan['mission_type']}")
        print(f"   C2 Methods: {', '.join(mil_plan['command_control'][:3])}")
        exploitation_plans["military"] = mil_plan
    
    # Infrastructure exploitation
    if targets["infrastructure_targets"]:
        infra_target = targets["infrastructure_targets"][0]
        print("\n3. Infrastructure System Exploitation:")
        infra_plan = exploitation_engine.exploit_infrastructure_systems(infra_target)
        print(f"   Target: {infra_plan['target_domain']}")
        print(f"   Sector: {infra_plan['sector']}")
        print(f"   Control Methods: {', '.join(infra_plan['system_control'][:3])}")
        exploitation_plans["infrastructure"] = infra_plan
    
    return exploitation_plans


def demonstrate_campaign_orchestration() -> Dict[str, Any]:
    """Demonstrate campaign orchestration capabilities."""
    
    print("\n=== CAMPAIGN ORCHESTRATION DEMONSTRATION ===\n")
    
    orchestrator = CampaignOrchestrator(seed=42)
    
    # Comprehensive campaign
    print("1. Comprehensive Campaign:")
    comp_campaign = orchestrator.orchestrate_comprehensive_campaign()
    print(f"   Campaign ID: {comp_campaign['campaign_id']}")
    print(f"   Duration: {comp_campaign['duration_days']} days")
    print(f"   Target Types: {', '.join(comp_campaign['target_types'])}")
    
    # Risk assessment
    risks = comp_campaign['risk_assessment']
    print(f"   Detection Risk: {risks['detection_risk']}")
    print(f"   Attribution Risk: {risks['attribution_risk']}")
    
    # Success metrics
    metrics = comp_campaign['success_metrics']
    print(f"   Target Penetration: {metrics['target_penetration']}")
    print(f"   Data Exfiltration: {metrics['data_exfiltration']}")
    
    # Focused campaign
    print("\n2. Focused Campaign (Government Sector):")
    focused_campaign = orchestrator.orchestrate_focused_campaign(
        target_sector="government",
        primary_objectives=["data_theft", "network_access"]
    )
    print(f"   Campaign ID: {focused_campaign['campaign_id']}")
    print(f"   Objectives: {', '.join(focused_campaign['primary_objectives'])}")
    
    focused_risks = focused_campaign['risk_assessment']
    print(f"   Detection Risk: {focused_risks['detection_risk']}")
    
    focused_metrics = focused_campaign['success_metrics']
    print(f"   Objective Completion: {focused_metrics['objective_completion']}")
    
    return {
        "comprehensive_campaign": comp_campaign,
        "focused_campaign": focused_campaign
    }


def demonstrate_end_to_end_workflow():
    """Demonstrate complete end-to-end workflow."""
    
    print("\n=== END-TO-END WORKFLOW DEMONSTRATION ===\n")
    
    # Initialize all engines
    targeting_engine = AdvancedTargetingEngine(seed=42)
    exploitation_engine = SystemExploitationEngine(seed=42)
    orchestrator = CampaignOrchestrator(seed=42)
    
    # Step 1: Target identification
    print("Step 1: Target Identification")
    print("-" * 40)
    
    gov_targets = targeting_engine.generate_government_targets()
    primary_target = gov_targets[0]
    
    print(f"Primary Target: {primary_target['domain']}")
    print(f"Organization Type: {primary_target['organization_type']}")
    print(f"Sensitivity Level: {primary_target['sensitivity_level']}")
    print(f"Technologies: {', '.join(primary_target['primary_technologies'][:3])}")
    
    # Step 2: Exploitation planning
    print("\nStep 2: Exploitation Planning")
    print("-" * 40)
    
    exploitation_plan = exploitation_engine.exploit_government_systems(primary_target)
    
    print(f"Exploitation Vectors: {', '.join(exploitation_plan['exploitation_vectors'][:3])}")
    print(f"Payload Delivery: {', '.join(exploitation_plan['payload_delivery'][:2])}")
    print(f"Persistence: {', '.join(exploitation_plan['persistence_mechanisms'][:2])}")
    
    # Step 3: Campaign orchestration
    print("\nStep 3: Campaign Orchestration")
    print("-" * 40)
    
    campaign = orchestrator.orchestrate_focused_campaign(
        target_sector="government",
        primary_objectives=["data_theft", "persistence"]
    )
    
    print(f"Campaign ID: {campaign['campaign_id']}")
    print(f"Objectives: {', '.join(campaign['primary_objectives'])}")
    
    risks = campaign['risk_assessment']
    print(f"Risk Assessment:")
    print(f"  - Detection: {risks['detection_risk']}")
    print(f"  - Attribution: {risks['attribution_risk']}")
    print(f"  - Operational: {risks['operational_risk']}")
    
    metrics = campaign['success_metrics']
    print(f"Success Metrics:")
    print(f"  - {metrics['target_penetration']}")
    print(f"  - {metrics['data_exfiltration']}")
    print(f"  - {metrics['persistence_duration']}")
    
    print("\n=== WORKFLOW COMPLETED ===")
    
    return {
        "target": primary_target,
        "exploitation_plan": exploitation_plan,
        "campaign": campaign
    }


def main():
    """Main demonstration function."""
    
    print("CHINESE APT CAMPAIGN TOOLKIT DEMONSTRATION")
    print("=" * 50)
    print("\nThis demonstration showcases enhanced tools for Chinese APT")
    print("campaigns targeting government, military, and critical infrastructure.")
    print("\n⚠️  FOR AUTHORIZED SECURITY TESTING AND RESEARCH ONLY\n")
    
    try:
        # Run demonstrations
        targets = demonstrate_targeting()
        exploitation_plans = demonstrate_exploitation(targets)
        campaigns = demonstrate_campaign_orchestration()
        workflow_results = demonstrate_end_to_end_workflow()
        
        print("\n" + "=" * 50)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("=" * 50)
        
        # Save results for reference
        results = {
            "targets": targets,
            "exploitation_plans": exploitation_plans,
            "campaigns": campaigns,
            "workflow_results": workflow_results
        }
        
        with open("chinese_apt_demo_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("\nResults saved to: chinese_apt_demo_results.json")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    main()