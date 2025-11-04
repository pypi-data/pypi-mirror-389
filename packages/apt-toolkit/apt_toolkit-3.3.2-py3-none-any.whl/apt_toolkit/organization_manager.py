"""
Organization management system for APT Toolkit.
Provides organization discovery, profiling, and attack planning capabilities.
"""

import json
from typing import Dict, List, Optional
from .email_repository import EmailRepository
from .deepseek_integration import (
    generate_organization_profile,
    generate_unique_attack_plan,
    generate_phishing_email
)


class OrganizationManager:
    """Manages organization discovery and profiling for targeting."""

    def __init__(self, email_repository: Optional[EmailRepository] = None):
        """Initialize the organization manager.
        
        Args:
            email_repository: Optional EmailRepository instance. If None, creates a new one.
        """
        self.email_repository = email_repository or EmailRepository()

    def list_organizations(self, limit: int = 50) -> List[str]:
        """List unique organizations from the email database.
        
        Args:
            limit: Maximum number of organizations to return.
            
        Returns:
            List of organization names.
        """
        cursor = self.email_repository._conn.execute(
            """
            SELECT DISTINCT organization 
            FROM emails 
            WHERE organization IS NOT NULL AND organization != ''
            ORDER BY organization
            LIMIT ?
            """,
            (limit,)
        )
        return [row["organization"] for row in cursor.fetchall()]

    def search_organizations(self, search_term: str, limit: int = 20) -> List[str]:
        """Search for organizations by name.
        
        Args:
            search_term: Term to search for in organization names.
            limit: Maximum number of results to return.
            
        Returns:
            List of matching organization names.
        """
        search_like = f"%{search_term.lower()}%"
        cursor = self.email_repository._conn.execute(
            """
            SELECT DISTINCT organization
            FROM emails
            WHERE lower(organization) LIKE ?
            ORDER BY organization
            LIMIT ?
            """,
            (search_like, limit)
        )
        return [row["organization"] for row in cursor.fetchall()]

    def get_organization_stats(self, organization_name: str) -> Dict:
        """Get statistics for a specific organization.
        
        Args:
            organization_name: Name of the organization.
            
        Returns:
            Dictionary with organization statistics.
        """
        emails = self.email_repository.emails_by_organization(organization_name)
        
        if not emails:
            return {
                "organization": organization_name,
                "email_count": 0,
                "domains": [],
                "error": "Organization not found"
            }

        domains = list(set(email["domain"] for email in emails))
        
        return {
            "organization": organization_name,
            "email_count": len(emails),
            "domains": domains,
            "sample_emails": [email["email"] for email in emails[:5]]
        }

    def generate_organization_profile(
        self, 
        organization_name: str, 
        use_deepseek: bool = True
    ) -> Dict:
        """Generate a detailed profile for an organization.
        
        Args:
            organization_name: Name of the organization.
            use_deepseek: Whether to use deepseek-reasoner for enhanced profiling.
            
        Returns:
            Dictionary with organization profile.
        """
        stats = self.get_organization_stats(organization_name)
        
        if stats.get("error"):
            return stats

        # Generate enhanced profile using deepseek
        deepseek_profile = generate_organization_profile(organization_name, use_deepseek)
        
        # Merge stats with deepseek profile
        profile = {
            **stats,
            **deepseek_profile
        }
        
        return profile

    def generate_attack_plan(
        self, 
        organization_name: str, 
        attack_type: str = "spear_phishing",
        use_deepseek: bool = True
    ) -> Dict:
        """Generate an attack plan for a specific organization.
        
        Args:
            organization_name: Name of the target organization.
            attack_type: Type of attack to plan.
            use_deepseek: Whether to use deepseek-reasoner for enhanced planning.
            
        Returns:
            Dictionary with attack plan details.
        """
        stats = self.get_organization_stats(organization_name)
        
        if stats.get("error"):
            return stats

        # Generate attack plan using deepseek
        attack_plan = generate_unique_attack_plan(organization_name, attack_type, use_deepseek)
        
        # Add organization-specific data
        attack_plan["organization_stats"] = stats
        
        # Generate phishing email if applicable
        if attack_type == "spear_phishing" and stats.get("domains"):
            primary_domain = stats["domains"][0] if stats["domains"] else "example.com"
            phishing_email = generate_phishing_email(primary_domain)
            attack_plan["phishing_email"] = phishing_email
        
        return attack_plan

    def analyze_organization_landscape(self, limit: int = 10) -> Dict:
        """Analyze the organization landscape from available data.
        
        Args:
            limit: Number of organizations to analyze.
            
        Returns:
            Dictionary with landscape analysis.
        """
        organizations = self.list_organizations(limit)
        
        analysis = {
            "total_organizations_analyzed": len(organizations),
            "organizations": [],
            "industry_distribution": {},
            "size_distribution": {},
            "security_posture_summary": {}
        }
        
        for org in organizations:
            profile = self.generate_organization_profile(org, use_deepseek=False)
            analysis["organizations"].append(profile)
            
            # Update distributions
            industry = profile.get("industry", "Unknown")
            size = profile.get("size", "Unknown")
            security = profile.get("security_posture", "Unknown")
            
            analysis["industry_distribution"][industry] = analysis["industry_distribution"].get(industry, 0) + 1
            analysis["size_distribution"][size] = analysis["size_distribution"].get(size, 0) + 1
            analysis["security_posture_summary"][security] = analysis["security_posture_summary"].get(security, 0) + 1
        
        return analysis

    def get_organization_emails(
        self, 
        organization_name: str, 
        limit: int = 20
    ) -> List[Dict]:
        """Get email addresses for a specific organization.
        
        Args:
            organization_name: Name of the organization.
            limit: Maximum number of emails to return.
            
        Returns:
            List of email dictionaries.
        """
        return self.email_repository.emails_by_organization(organization_name)[:limit]

    def close(self):
        """Close the email repository connection."""
        if self.email_repository:
            self.email_repository.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()