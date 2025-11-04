"""
Command Line Interface for APT Toolkit
"""

import argparse
import json
import sys
from .american_targets_enhanced import analyze_american_targets_enhanced

from .american_targets import analyze_american_targets
from .american_targets_enhanced import analyze_american_targets_enhanced
from .campaign import APTCampaignSimulator, CampaignConfig

# Chinese APT campaign imports
try:
    from campaigns.chinese_apts.chinese_apt_orchestrator import (
        ChineseAPTCampaignOrchestrator, ChineseAPTCampaignConfig
    )
    CHINESE_APT_SUPPORT = True
except ImportError:
    CHINESE_APT_SUPPORT = False

# Chinese APT campaign imports
try:
    from campaigns.chinese_apts.chinese_apt_orchestrator import (
        ChineseAPTCampaignOrchestrator, ChineseAPTCampaignConfig
    )
    CHINESE_APT_SUPPORT = True
except ImportError:
    CHINESE_APT_SUPPORT = False
from .exploit_intel import ExploitDBIndex, ExploitDBNotAvailableError
from .offensive_playbooks import generate_offensive_playbook
from .initial_access import (
    SpearPhishingGenerator,
    SupplyChainCompromise,
    analyze_spear_phishing_campaign
)
from .persistence import PersistenceManager, generate_persistence_report
from .privilege_escalation import PrivilegeEscalator, analyze_privilege_escalation_landscape
from .defense_evasion import DefenseEvader, analyze_defense_evasion_landscape
from .lateral_movement import LateralMover, analyze_lateral_movement_campaign
from .command_control import C2Communicator, analyze_c2_infrastructure
from .exfiltration import DataExfiltrator, analyze_exfiltration_campaign
from .financial_targeting import FinancialTargetingEngine, analyze_financial_targets
from .hardware_disruption import HardwareDisruptionEngine, analyze_hardware_disruption


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="APT Toolkit - Analyze Advanced Persistent Threat techniques",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  apt-analyzer initial-access --generate-email
  apt-analyzer persistence --analyze
  apt-analyzer privilege-escalation --ad-enum
  apt-analyzer defense-evasion --lotl
  apt-analyzer lateral-movement --discover
  apt-analyzer command-control --beacon
  apt-analyzer exfiltration --find-data
  apt-analyzer campaign --domain secure.dod.mil --seed 1337
  apt-analyzer exploitdb --search exchange --limit 5
  apt-analyzer financial targets --banks --crypto
        """
    )

    subparsers = parser.add_subparsers(dest="module", help="APT module to analyze")

    # Initial Access subparser
    ia_parser = subparsers.add_parser("initial-access", help="Initial access techniques")
    ia_parser.add_argument("--generate-email", action="store_true", help="Generate spear-phishing email")
    ia_parser.add_argument("--analyze-campaign", action="store_true", help="Analyze spear-phishing campaign")
    ia_parser.add_argument("--supply-chain", action="store_true", help="Analyze supply chain compromise")

    # Persistence subparser
    per_parser = subparsers.add_parser("persistence", help="Persistence techniques")
    per_parser.add_argument("--analyze", action="store_true", help="Analyze persistence techniques")
    per_parser.add_argument("--generate-report", action="store_true", help="Generate persistence report")

    # Privilege Escalation subparser
    pe_parser = subparsers.add_parser("privilege-escalation", help="Privilege escalation techniques")
    pe_parser.add_argument("--ad-enum", action="store_true", help="Enumerate AD privileges")
    pe_parser.add_argument("--vuln-scan", action="store_true", help="Scan for vulnerabilities")
    pe_parser.add_argument("--analyze-landscape", action="store_true", help="Analyze privilege escalation landscape")

    # Defense Evasion subparser
    de_parser = subparsers.add_parser("defense-evasion", help="Defense evasion techniques")
    de_parser.add_argument("--lotl", action="store_true", help="Generate LOTL commands")
    de_parser.add_argument("--analyze-evasion", action="store_true", help="Analyze evasion techniques")
    de_parser.add_argument("--process-hollowing", action="store_true", help="Analyze process hollowing")

    # Lateral Movement subparser
    lm_parser = subparsers.add_parser("lateral-movement", help="Lateral movement techniques")
    lm_parser.add_argument("--discover", action="store_true", help="Discover network segments")
    lm_parser.add_argument("--pth-simulate", action="store_true", help="Simulate Pass-the-Hash")
    lm_parser.add_argument("--analyze-campaign", action="store_true", help="Analyze lateral movement campaign")

    # Command & Control subparser
    cc_parser = subparsers.add_parser("command-control", help="C2 communication techniques")
    cc_parser.add_argument("--beacon", action="store_true", help="Send simulated beacon")
    cc_parser.add_argument("--analyze-channels", action="store_true", help="Analyze C2 channels")
    cc_parser.add_argument("--simulate-lifecycle", action="store_true", help="Simulate C2 lifecycle")

    # Exfiltration subparser
    ex_parser = subparsers.add_parser("exfiltration", help="Data exfiltration techniques")
    ex_parser.add_argument("--find-data", action="store_true", help="Find sensitive data")
    ex_parser.add_argument("--slow-exfil", action="store_true", help="Simulate slow exfiltration")
    ex_parser.add_argument("--analyze-campaign", action="store_true", help="Analyze exfiltration campaign")

    # Campaign orchestration subparser
    campaign_parser = subparsers.add_parser(
        "campaign",
        help="Simulate an end-to-end APT campaign using all modules",
    )
    campaign_parser.add_argument(
        "--domain",
        default="secure.dod.mil",
        help="Target domain for campaign simulation",
    )
    campaign_parser.add_argument(
        "--ip",
        default="203.0.113.10",
        help="Initial foothold IP address",
    )
    campaign_parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="Duration in hours for the C2 lifecycle simulation",
    )
    campaign_parser.add_argument(
        "--seed",
        type=int,
        help="Seed random number generation for deterministic output",
    )
    campaign_parser.add_argument(
        "--skip-supply-chain",
        action="store_true",
        help="Disable supply chain pre-positioning",
    )
    campaign_parser.add_argument(
        "--skip-counter-forensics",
        action="store_true",
        help="Disable counter-forensic persistence measures",
    )

    # ExploitDB subparser
    exploit_parser = subparsers.add_parser(
        "exploitdb",
        help="Query the bundled ExploitDB intelligence snapshot",
    )
    exploit_parser.add_argument("--search", help="Keyword search across exploit metadata")
    exploit_parser.add_argument("--cve", help="Lookup exploits by CVE identifier")
    exploit_parser.add_argument(
        "--platform",
        help="Filter results by platform (e.g. windows, linux, exchange)",
    )
    exploit_parser.add_argument(
        "--type",
        dest="exploit_type",
        help="Filter results by exploit type (remote, local, dos, webapps)",
    )
    exploit_parser.add_argument(
        "--recent",
        type=int,
        help="Show activity published within the last N days",
    )
    exploit_parser.add_argument(
        "--product",
        help="Generate an exploit-surface report for a product/technology",
    )
    exploit_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit the number of returned results",
    )
    exploit_parser.add_argument(
        "--playbook",
        action="store_true",
        help="Generate an offensive playbook aligned with toolkit modules",
    )
    exploit_parser.add_argument(
        "--playbook-modules",
        help="Comma-separated module list for playbook generation",
    )

    # American targets subparser
    american_parser = subparsers.add_parser(
        "american",
        help="U.S. government and military targeting simulations",
    )
    american_parser.add_argument(
        "action",
        choices=["targets", "targets-enhanced"],
        help="Run american targets reconnaissance (basic or enhanced)",
    )

    # Financial targeting subparser
    financial_parser = subparsers.add_parser(
        "financial",
        help="Financial institution targeting and money theft simulations",
    )
    financial_parser.add_argument(
        "action",
        choices=["targets", "banks", "investment", "crypto", "all"],
        help="Financial targeting scope",
    )

    # Hardware disruption subparser
    hardware_parser = subparsers.add_parser(
        "hardware-disruption",
        help="Hardware disruption techniques for military and infrastructure",
    )
    hardware_parser.add_argument(
        "--target-type",
        choices=[
            "military_bases", "naval_facilities", "power_infrastructure",
            "water_systems", "logistics_networks", "military_vehicles"
        ],
        help="Specific target type to analyze",
    )
    hardware_parser.add_argument(
        "--tool",
        choices=[
            "gps_jammer", "drone_hijacker", "power_grid_disruption", "radar_jammer",
            "radio_jammer", "satellite_disruption", "naval_vessel_disruption",
            "military_vehicle_disruption", "water_supply_disruption", "logistics_disruption"
        ],
        help="Specific disruption tool to execute",
    )

    # Chinese APT campaigns subparser
    if CHINESE_APT_SUPPORT:
        chinese_parser = subparsers.add_parser(
            "chinese-apt",
            help="Chinese APT campaign simulations (APT41, APT1, APT10, APT12)",
        )
        chinese_parser.add_argument(
            "--campaign",
            choices=[
                "apt41_gaming", "apt41_supply_chain",
                "apt1_government", "apt1_long_term",
                "apt10_msp", "apt10_cloud",
                "apt12_diplomatic", "apt12_strategic",
                "comparative"
            ],
            help="Specific Chinese APT campaign type to simulate",
        )
        chinese_parser.add_argument(
            "--domain",
            default="secure.dod.mil",
            help="Target domain for campaign simulation",
        )
        chinese_parser.add_argument(
            "--seed",
            type=int,
            help="Seed random number generation for deterministic output",
        )

    # Common arguments
    subparser_list = [
        ia_parser,
        per_parser,
        pe_parser,
        de_parser,
        lm_parser,
        cc_parser,
        ex_parser,
        campaign_parser,
        exploit_parser,
        american_parser,
        financial_parser,
        hardware_parser,
    ]

    if CHINESE_APT_SUPPORT:
        subparser_list.append(chinese_parser)

    for subparser in subparser_list:
        subparser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.module:
        parser.print_help()
        return 1

    try:
        result = handle_command(args)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_pretty_result(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def handle_command(args) -> dict:
    """Handle CLI commands and return results."""

    if args.module == "initial-access":
        if args.generate_email:
            generator = SpearPhishingGenerator()
            return {"spear_phishing_email": generator.generate_email()}
        elif args.analyze_campaign:
            return {"campaign_analysis": analyze_spear_phishing_campaign()}
        elif args.supply_chain:
            compromise = SupplyChainCompromise()
            target_info = compromise.malicious_update_check("192.168.1.100", "dod.mil")
            return {"supply_chain_analysis": target_info}

    elif args.module == "persistence":
        if args.analyze:
            manager = PersistenceManager()
            return {"persistence_analysis": manager.analyze_persistence_techniques()}
        elif args.generate_report:
            return {"persistence_report": generate_persistence_report()}

    elif args.module == "privilege-escalation":
        if args.ad_enum:
            escalator = PrivilegeEscalator()
            return {"ad_enumeration": escalator.enumerate_ad_privileges()}
        elif args.vuln_scan:
            escalator = PrivilegeEscalator()
            return {"vulnerability_scan": escalator.check_vulnerabilities()}
        elif args.analyze_landscape:
            return {"privilege_escalation_landscape": analyze_privilege_escalation_landscape()}

    elif args.module == "defense-evasion":
        if args.lotl:
            evader = DefenseEvader()
            return {"lotl_commands": evader.generate_lotl_commands()}
        elif args.analyze_evasion:
            evader = DefenseEvader()
            return {"evasion_analysis": evader.analyze_lotl_detection()}
        elif args.process_hollowing:
            evader = DefenseEvader()
            return {"process_hollowing": evader.process_hollowing_analysis()}

    elif args.module == "lateral-movement":
        if args.discover:
            mover = LateralMover()
            return {"network_discovery": mover.discover_network_segments()}
        elif args.pth_simulate:
            mover = LateralMover([{"username": "admin1", "hash": "test_hash"}])
            return {"pth_attempt": mover.pass_the_hash_lateral("192.168.1.100", "admin1", "test_hash")}
        elif args.analyze_campaign:
            return {"lateral_movement_campaign": analyze_lateral_movement_campaign()}

    elif args.module == "command-control":
        if args.beacon:
            communicator = C2Communicator()
            return {"c2_beacon": communicator.send_beacon({"test": "data"})}
        elif args.analyze_channels:
            communicator = C2Communicator()
            return {"c2_channels": communicator.analyze_c2_channels()}
        elif args.simulate_lifecycle:
            communicator = C2Communicator()
            return {"c2_lifecycle": communicator.simulate_c2_lifecycle(24)}

    elif args.module == "exfiltration":
        if args.find_data:
            exfiltrator = DataExfiltrator()
            return {"sensitive_data": exfiltrator.find_sensitive_data()}
        elif args.slow_exfil:
            exfiltrator = DataExfiltrator()
            return {"slow_exfiltration": exfiltrator.slow_exfiltrate("C:\\test\\file.txt")}
        elif args.analyze_campaign:
            return {"exfiltration_campaign": analyze_exfiltration_campaign()}

    elif args.module == "campaign":
        config = CampaignConfig(
            target_domain=args.domain,
            target_ip=args.ip,
            beacon_duration_hours=args.hours,
            include_supply_chain=not args.skip_supply_chain,
            include_counter_forensics=not args.skip_counter_forensics,
            seed=args.seed,
        )
        simulator = APTCampaignSimulator(seed=args.seed)
        return {"campaign_report": simulator.simulate(config)}

    elif args.module == "chinese-apt" and CHINESE_APT_SUPPORT:
        if not args.campaign:
            orchestrator = ChineseAPTCampaignOrchestrator(seed=args.seed)
            return {
                "available_campaigns": orchestrator.get_available_campaign_types(),
                "chinese_apt_overview": orchestrator._get_chinese_apt_overview()
            }
        
        config = ChineseAPTCampaignConfig(
            target_domain=args.domain,
            seed=args.seed
        )
        orchestrator = ChineseAPTCampaignOrchestrator(seed=args.seed)
        
        if args.campaign == "comparative":
            return orchestrator.run_comparative_analysis(config)
        else:
            return orchestrator.simulate_specific_campaign_type(args.campaign, config)

    elif args.module == "chinese-apt" and not CHINESE_APT_SUPPORT:
        return {"error": "Chinese APT campaign support not available"}

    elif args.module == "chinese-apt" and CHINESE_APT_SUPPORT:
        if not args.campaign:
            orchestrator = ChineseAPTCampaignOrchestrator(seed=args.seed)
            return {
                "available_campaigns": orchestrator.get_available_campaign_types(),
                "chinese_apt_overview": orchestrator._get_chinese_apt_overview()
            }

        config = ChineseAPTCampaignConfig(
            target_domain=args.domain,
            seed=args.seed
        )
        orchestrator = ChineseAPTCampaignOrchestrator(seed=args.seed)

        if args.campaign == "comparative":
            return orchestrator.run_comparative_analysis(config)
        else:
            return orchestrator.simulate_specific_campaign_type(args.campaign, config)

    elif args.module == "chinese-apt" and not CHINESE_APT_SUPPORT:
        return {"error": "Chinese APT campaign support not available"}

    elif args.module == "exploitdb":
        try:
            index = ExploitDBIndex()
        except ExploitDBNotAvailableError as exc:
            return {"error": str(exc)}

        response: dict = {}
        if getattr(args, "playbook", False):
            module_list = None
            modules_arg = getattr(args, "playbook_modules", None)
            if modules_arg:
                module_list = [module.strip() for module in modules_arg.split(",") if module.strip()]
                if not module_list:
                    module_list = None
            response["offensive_playbook"] = generate_offensive_playbook(
                target_product=args.product or args.search,
                target_platform=args.platform,
                modules=module_list,
                limit=args.limit,
            )

        if args.product:
            report = index.analyze_exploit_surface(
                args.product,
                limit=args.limit,
                platform=args.platform,
            )
            response["exploit_surface"] = report

        if args.search or args.platform or args.exploit_type:
            results = index.search_exploits(
                term=args.search,
                platform=args.platform,
                exploit_type=args.exploit_type,
                limit=args.limit,
            )
            response["search_results"] = [r.to_dict() for r in results]
        if args.cve:
            response["cve_lookup"] = index.search_by_cve(args.cve, limit=args.limit)
        if args.recent:
            response["recent_activity"] = index.get_recent_activity(args.recent, limit=args.limit)
        if not response:
            response["hint"] = "Specify --search, --cve, --recent, or --product to query ExploitDB."
        return response

    elif args.module == "financial":
        if getattr(args, "action", None) == "targets":
            return {"financial_targets": analyze_financial_targets()}
        elif getattr(args, "action", None) == "banks":
            return {"financial_targets": analyze_financial_targets(["banks"])}
        elif getattr(args, "action", None) == "investment":
            return {"financial_targets": analyze_financial_targets(["investment_firms"])}
        elif getattr(args, "action", None) == "crypto":
            return {"financial_targets": analyze_financial_targets(["cryptocurrency_exchanges"])}
        elif getattr(args, "action", None) == "all":
            return {"financial_targets": analyze_financial_targets([
                "banks",
                "investment_firms",
                "payment_processors",
                "cryptocurrency_exchanges"
            ])}

    elif args.module == "american":
        if getattr(args, "action", None) == "targets":
            return {"american_targets": analyze_american_targets()}
        elif getattr(args, "action", None) == "targets-enhanced":
            return {"american_targets_enhanced": analyze_american_targets_enhanced()}

    elif args.module == "hardware-disruption":
        target_type = getattr(args, "target_type", None)
        tool_name = getattr(args, "tool", None)

        return {"hardware_disruption": analyze_hardware_disruption(
            target_type=target_type, tool_name=tool_name)}

def print_pretty_result(result: dict):
    """Print results in a human-readable format."""
    for key, value in result.items():
        print(f"\n{'='*50}")
        print(f"{key.upper().replace('_', ' ')}")
        print(f"{'='*50}")

        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                if isinstance(subvalue, (dict, list)):
                    print(f"\n{subkey}:")
                    print(json.dumps(subvalue, indent=2))
                else:
                    print(f"{subkey}: {subvalue}")
        elif isinstance(value, list):
            for item in value:
                print(f"- {item}")
        else:
            print(value)


if __name__ == "__main__":
    sys.exit(main())