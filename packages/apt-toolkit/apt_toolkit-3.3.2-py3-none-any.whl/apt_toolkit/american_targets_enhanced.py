"""Enhanced utilities for analyzing American government and military targets."""

from __future__ import annotations

import ipaddress
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .initial_access_enhanced import AdvancedSocialEngineering, SupplyChainCompromise


class AmericanTargetsAnalyzer:
    """Enhanced analyzer for American government and military targets."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the analyzer with optional seed for deterministic output."""
        if seed is not None:
            random.seed(seed)
        
        self.social_engineering = AdvancedSocialEngineering()
        self.supply_chain = SupplyChainCompromise()
        
        # Expanded list of American government and military domains
        self.american_networks = [
            # Military domains
            "mil", "usmc.mil", "army.mil", "navy.mil", "af.mil", "spaceforce.mil",
            "dod.mil", "defense.gov", "centcom.mil", "eucom.mil", "pacom.mil",
            "socom.mil", "northcom.mil", "southcom.mil", "stratcom.mil",
            "transcom.mil", "cybercom.mil", "nsa.gov", "dia.mil", "ng.mil",
            # Government domains
            "gov", "usa.gov", "whitehouse.gov", "state.gov", "treasury.gov",
            "defense.gov", "justice.gov", "fbi.gov", "cia.gov", "dhs.gov",
            "energy.gov", "commerce.gov", "transportation.gov", "epa.gov",
            "nasa.gov", "nih.gov", "noaa.gov", "usda.gov", "va.gov",
            # Intelligence domains
            "odni.gov", "dni.gov", "nro.gov", "nga.mil", "nro.mil",
            # Critical infrastructure
            "fema.gov", "cisa.gov", "tsa.gov", "usps.gov", "fcc.gov",
            # Research and development
            "darpa.mil", "inl.gov", "anl.gov", "ornl.gov", "llnl.gov",
        ]
        
        # Target organization types
        self.organization_types = {
            "military": ["Command", "Intelligence", "Operations", "Logistics"],
            "government": ["Executive", "Legislative", "Judicial", "Regulatory"],
            "intelligence": ["Analysis", "Collection", "Counterintelligence", "Technical"],
            "infrastructure": ["Energy", "Transportation", "Communications", "Finance"],
            "research": ["Defense", "Energy", "Cybersecurity", "Space"]
        }
        
        # Common job titles by organization type
        self.job_titles = {
            "military": ["Commander", "Intelligence Officer", "Cyber Operations", "Logistics Officer"],
            "government": ["Director", "Policy Analyst", "Program Manager", "Security Specialist"],
            "intelligence": ["Analyst", "Case Officer", "Technical Specialist", "Operations Officer"],
            "infrastructure": ["Systems Administrator", "Security Engineer", "Operations Manager", "Compliance Officer"],
            "research": ["Research Scientist", "Principal Investigator", "Technical Director", "Security Researcher"]
        }

    def _get_organization_type(self, domain: str) -> str:
        """Determine organization type based on domain."""
        if "darpa" in domain:
            return "research"
        elif ".mil" in domain:
            return "military"
        elif "intel" in domain or "cia" in domain or "nsa" in domain or "odni" in domain or "dni" in domain:
            return "intelligence"
        elif "energy" in domain or "transport" in domain or "infra" in domain:
            return "infrastructure"
        elif "research" in domain or "lab" in domain:
            return "research"
        else:
            return "government"

    def _generate_target_domain(self, network_suffix: str) -> str:
        """Construct a plausible government domain for the given suffix."""
        suffix = network_suffix.lstrip(".")
        if "." in suffix:
            return f"secure.{suffix}"
        
        # Add appropriate subdomain based on organization type
        org_type = self._get_organization_type(suffix)
        if org_type == "military":
            subdomains = ["ops", "intel", "cyber", "command"]
        elif org_type == "intelligence":
            subdomains = ["secure", "classified", "ops", "analysis"]
        elif org_type == "infrastructure":
            subdomains = ["ops", "control", "monitoring", "security"]
        elif org_type == "research":
            subdomains = ["research", "lab", "projects", "development"]
        else:
            subdomains = ["secure", "admin", "ops", "internal"]
            
        subdomain = random.choice(subdomains)
        return f"{subdomain}.{suffix}"

    def _generate_target_email(self, domain: str, org_type: str) -> str:
        """Generate a realistic email address for a target domain."""
        job_title = random.choice(self.job_titles[org_type])
        
        # Convert job title to email format
        email_prefix = job_title.lower().replace(" ", ".")
        
        # Add some variation - ensure we have valid prefixes
        variations = [
            email_prefix,
            f"{email_prefix}.{random.randint(1, 9)}",
            f"{email_prefix.replace('.', '_')}",
        ]
        
        # If the prefix has dots, also include just the first part
        if "." in email_prefix:
            variations.append(email_prefix.split(".")[0])
        
        return f"{random.choice(variations)}@{domain}"

    def _generate_network_segment(self, org_type: str) -> Tuple[str, str]:
        """Generate realistic network segments and IP ranges."""
        # Common government/military IP ranges
        base_ranges = {
            "military": ["6.", "7.", "11.", "21.", "22.", "26.", "28.", "29."],
            "government": ["149.", "152.", "161.", "162.", "198.", "199."],
            "intelligence": ["192.", "205.", "206.", "207.", "208."],
            "infrastructure": ["12.", "13.", "14.", "15.", "16."],
            "research": ["128.", "129.", "130.", "131.", "132."]
        }
        
        base = random.choice(base_ranges[org_type])
        ip_range = f"{base}{random.randint(0, 255)}.{random.randint(0, 255)}.0/24"
        gateway_ip = f"{base}{random.randint(0, 255)}.{random.randint(0, 255)}.1"
        
        return ip_range, gateway_ip

    def analyze_american_targets(self) -> Dict[str, Any]:
        """Analyze U.S. government and military targets using enhanced toolkit primitives.

        Returns:
            Dictionary containing comprehensive reconnaissance-ready dossiers and analysis.
        """
        target_domains = [self._generate_target_domain(suffix) for suffix in self.american_networks]

        target_profiles: List[Dict[str, Any]] = []
        for domain in target_domains:
            org_type = self._get_organization_type(domain)
            email = self._generate_target_email(domain, org_type)
            ip_range, gateway_ip = self._generate_network_segment(org_type)
            
            dossier = self.social_engineering.build_target_dossier(email)
            lure = self.social_engineering.create_context_aware_lure(dossier)

            target_profiles.append({
                "target_domain": domain,
                "target_email": email,
                "organization_type": org_type,
                "network_segment": ip_range,
                "gateway_ip": gateway_ip,
                "dossier": dossier,
                "lure": lure,
            })

        supply_chain_readiness: List[Dict[str, Any]] = []
        base_ip = ipaddress.IPv4Address("203.0.113.10")
        for idx, profile in enumerate(target_profiles):
            simulated_ip = str(base_ip + idx)
            readiness = self.supply_chain.malicious_update_check(simulated_ip, profile["target_domain"])
            readiness["implant_outcome"] = self.supply_chain.execute_implant(readiness)
            readiness["organization_type"] = profile["organization_type"]
            supply_chain_readiness.append(readiness)

        # Generate threat assessment
        threat_assessment = self._generate_threat_assessment(target_profiles)

        return {
            "generated_at": datetime.now().isoformat(),
            "american_networks": self.american_networks,
            "target_profiles": target_profiles,
            "supply_chain_readiness": supply_chain_readiness,
            "threat_assessment": threat_assessment,
        }

    def _generate_threat_assessment(self, target_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive threat assessment based on target profiles."""
        
        org_type_counts = {}
        for profile in target_profiles:
            org_type = profile["organization_type"]
            org_type_counts[org_type] = org_type_counts.get(org_type, 0) + 1

        # Calculate risk scores
        risk_factors = {
            "military": 9,
            "intelligence": 10,
            "government": 7,
            "infrastructure": 8,
            "research": 6
        }
        
        total_risk = sum(risk_factors[org_type] * count 
                        for org_type, count in org_type_counts.items())
        
        return {
            "organization_distribution": org_type_counts,
            "total_targets": len(target_profiles),
            "overall_risk_score": total_risk,
            "risk_assessment": self._get_risk_level(total_risk),
            "recommended_approach": self._get_recommended_approach(org_type_counts),
            "timeline_estimate": self._get_timeline_estimate(total_risk)
        }

    def _get_risk_level(self, risk_score: int) -> str:
        """Determine risk level based on score."""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommended_approach(self, org_distribution: Dict[str, int]) -> str:
        """Generate recommended approach based on organization distribution."""
        if org_distribution.get("intelligence", 0) > 0:
            return "Stealth-focused campaign with emphasis on counter-forensics"
        elif org_distribution.get("military", 0) > 0:
            return "Multi-vector approach with supply chain and social engineering"
        elif org_distribution.get("infrastructure", 0) > 0:
            return "Targeted exploitation with focus on operational technology"
        else:
            return "Standard APT campaign with emphasis on persistence"

    def _get_timeline_estimate(self, risk_score: int) -> str:
        """Estimate campaign timeline based on risk."""
        if risk_score >= 80:
            return "6-12 months (complex target environment)"
        elif risk_score >= 60:
            return "3-6 months (moderate complexity)"
        elif risk_score >= 40:
            return "1-3 months (standard campaign)"
        else:
            return "2-4 weeks (limited scope)"


def analyze_american_targets_enhanced(seed: Optional[int] = None) -> Dict[str, Any]:
    """Enhanced analysis of American government and military targets.
    
    Args:
        seed: Optional seed to make the generated content deterministic.
        
    Returns:
        Dictionary containing comprehensive reconnaissance-ready dossiers and analysis.
    """
    analyzer = AmericanTargetsAnalyzer(seed)
    return analyzer.analyze_american_targets()


__all__ = ["analyze_american_targets_enhanced", "AmericanTargetsAnalyzer"]