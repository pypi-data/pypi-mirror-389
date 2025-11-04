"""
Enhanced Command Line Interface for APT Toolkit with Organization Support
"""

import argparse
import json
import sys
from .organization_manager import OrganizationManager


def main():
    """Main CLI entry point for organization management."""
    parser = argparse.ArgumentParser(
        description="APT Toolkit Organization Management - Discover, profile, and target organizations"
    )

    subparsers = parser.add_subparsers(dest="command", help="Organization management commands")

    # List organizations
    list_parser = subparsers.add_parser("list", help="List available organizations")
    list_parser.add_argument("--limit", type=int, default=50, help="Limit number of results")

    # Search organizations
    search_parser = subparsers.add_parser("search", help="Search for organizations")
    search_parser.add_argument("term", help="Search term")
    search_parser.add_argument("--limit", type=int, default=20, help="Limit number of results")

    # Profile organization
    profile_parser = subparsers.add_parser("profile", help="Generate organization profile")
    profile_parser.add_argument("organization", help="Organization name")
    profile_parser.add_argument("--no-deepseek", action="store_true", help="Disable deepseek integration")

    # Attack plan
    attack_parser = subparsers.add_parser("attack-plan", help="Generate attack plan")
    attack_parser.add_argument("organization", help="Organization name")
    attack_parser.add_argument("--type", choices=["spear_phishing", "supply_chain", "lateral_movement", "persistence"], 
                              default="spear_phishing", help="Attack type")
    attack_parser.add_argument("--no-deepseek", action="store_true", help="Disable deepseek integration")

    # Organization stats
    stats_parser = subparsers.add_parser("stats", help="Get organization statistics")
    stats_parser.add_argument("organization", help="Organization name")

    # Organization emails
    emails_parser = subparsers.add_parser("emails", help="Get organization emails")
    emails_parser.add_argument("organization", help="Organization name")
    emails_parser.add_argument("--limit", type=int, default=20, help="Limit number of emails")

    # Landscape analysis
    landscape_parser = subparsers.add_parser("landscape", help="Analyze organization landscape")
    landscape_parser.add_argument("--limit", type=int, default=10, help="Number of organizations to analyze")

    # Common arguments
    for subparser in [list_parser, search_parser, profile_parser, attack_parser, stats_parser, emails_parser, landscape_parser]:
        subparser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        result = handle_organization_command(args)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_pretty_result(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def handle_organization_command(args) -> dict:
    """Handle organization management commands."""
    
    with OrganizationManager() as manager:
        
        if args.command == "list":
            organizations = manager.list_organizations(limit=args.limit)
            return {
                "command": "list_organizations",
                "organizations": organizations,
                "count": len(organizations)
            }
            
        elif args.command == "search":
            organizations = manager.search_organizations(args.term, limit=args.limit)
            return {
                "command": "search_organizations",
                "search_term": args.term,
                "organizations": organizations,
                "count": len(organizations)
            }
            
        elif args.command == "profile":
            profile = manager.generate_organization_profile(
                args.organization, 
                use_deepseek=not args.no_deepseek
            )
            return {
                "command": "organization_profile",
                "organization": args.organization,
                "profile": profile
            }
            
        elif args.command == "attack-plan":
            attack_plan = manager.generate_attack_plan(
                args.organization,
                attack_type=args.type,
                use_deepseek=not args.no_deepseek
            )
            return {
                "command": "attack_plan",
                "organization": args.organization,
                "attack_type": args.type,
                "plan": attack_plan
            }
            
        elif args.command == "stats":
            stats = manager.get_organization_stats(args.organization)
            return {
                "command": "organization_stats",
                "organization": args.organization,
                "stats": stats
            }
            
        elif args.command == "emails":
            emails = manager.get_organization_emails(args.organization, limit=args.limit)
            return {
                "command": "organization_emails",
                "organization": args.organization,
                "emails": emails,
                "count": len(emails)
            }
            
        elif args.command == "landscape":
            landscape = manager.analyze_organization_landscape(limit=args.limit)
            return {
                "command": "organization_landscape",
                "landscape": landscape
            }


def print_pretty_result(result):
    """Print results in a human-readable format."""
    command = result.get("command", "")
    
    if command == "list_organizations":
        print(f"\nAvailable Organizations ({result['count']}):")
        print("-" * 40)
        for org in result["organizations"]:
            print(f"• {org}")
            
    elif command == "search_organizations":
        print(f"\nSearch Results for '{result['search_term']}' ({result['count']}):")
        print("-" * 40)
        for org in result["organizations"]:
            print(f"• {org}")
            
    elif command == "organization_profile":
        profile = result["profile"]
        print(f"\nOrganization Profile: {result['organization']}")
        print("=" * 50)
        print(f"Email Count: {profile.get('email_count', 0)}")
        print(f"Domains: {', '.join(profile.get('domains', []))}")
        print(f"Industry: {profile.get('industry', 'Unknown')}")
        print(f"Size: {profile.get('size', 'Unknown')}")
        print(f"Security Posture: {profile.get('security_posture', 'Unknown')}")
        print(f"\nDescription: {profile.get('description', 'No description available')}")
        print(f"\nKey Employee Roles:")
        for role in profile.get('key_employees', []):
            print(f"  • {role}")
        print(f"\nAttack Vectors:")
        for vector in profile.get('attack_vectors', []):
            print(f"  • {vector}")
            
    elif command == "attack_plan":
        plan = result["plan"]
        print(f"\nAttack Plan: {result['organization']} - {result['attack_type']}")
        print("=" * 50)
        print(f"Strategy: {plan.get('strategy', 'No strategy available')}")
        print(f"\nExecution Steps:")
        for step in plan.get('steps', []):
            print(f"  • {step.get('phase', 'Unknown')}: {step.get('action', 'No action')}")
            if step.get('tools'):
                print(f"    Tools: {', '.join(step['tools'])}")
        print(f"\nTechniques:")
        for technique in plan.get('techniques', []):
            print(f"  • {technique}")
        print(f"\nChallenges:")
        for challenge in plan.get('challenges', []):
            print(f"  • {challenge}")
        print(f"\nMitigations:")
        for mitigation in plan.get('mitigations', []):
            print(f"  • {mitigation}")
            
    elif command == "organization_stats":
        stats = result["stats"]
        print(f"\nOrganization Statistics: {result['organization']}")
        print("=" * 50)
        print(f"Email Count: {stats.get('email_count', 0)}")
        print(f"Domains: {', '.join(stats.get('domains', []))}")
        print(f"\nSample Emails:")
        for email in stats.get('sample_emails', [])[:5]:
            print(f"  • {email}")
            
    elif command == "organization_emails":
        emails = result["emails"]
        print(f"\nOrganization Emails: {result['organization']} ({result['count']})")
        print("=" * 50)
        for email in emails:
            print(f"• {email.get('email', 'Unknown')}")
            if email.get('first_name') or email.get('last_name'):
                print(f"  Name: {email.get('first_name', '')} {email.get('last_name', '')}".strip())
            if email.get('domain'):
                print(f"  Domain: {email.get('domain')}")
            print()
            
    elif command == "organization_landscape":
        landscape = result["landscape"]
        print(f"\nOrganization Landscape Analysis")
        print("=" * 50)
        print(f"Total Organizations Analyzed: {landscape.get('total_organizations_analyzed', 0)}")
        
        print(f"\nIndustry Distribution:")
        for industry, count in landscape.get('industry_distribution', {}).items():
            print(f"  • {industry}: {count}")
            
        print(f"\nSize Distribution:")
        for size, count in landscape.get('size_distribution', {}).items():
            print(f"  • {size}: {count}")
            
        print(f"\nSecurity Posture Summary:")
        for posture, count in landscape.get('security_posture_summary', {}).items():
            print(f"  • {posture}: {count}")


if __name__ == "__main__":
    sys.exit(main())