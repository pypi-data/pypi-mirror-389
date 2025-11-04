"""Enhanced utilities for analyzing UK government and high-value targets."""

from __future__ import annotations

import ipaddress
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .initial_access_enhanced import AdvancedSocialEngineering, SupplyChainCompromise


class UKTargetsAnalyzer:
    """Enhanced analyzer for UK government and high-value targets."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the analyzer with optional seed for deterministic output."""
        if seed is not None:
            random.seed(seed)
        
        self.social_engineering = AdvancedSocialEngineering()
        self.supply_chain = SupplyChainCompromise()
        
        # Expanded list of UK government, military, and high-value industry domains
        self.uk_networks = [
            # Government domains
            "gov.uk", "parliament.uk", "mod.uk", "homeoffice.gov.uk", "cabinet-office.gov.uk",
            "digital.cabinet-office.gov.uk", "ncsc.gov.uk", "gchq.gov.uk", "mi6.gov.uk",
            "mi5.gov.uk", "fco.gov.uk", "hmtreasury.gov.uk", "beis.gov.uk", "defra.gov.uk",
            # Military domains
            "army.mod.uk", "royalnavy.mod.uk", "raf.mod.uk", "dstl.gov.uk",
            # Critical infrastructure
            "nhs.uk", "networkrail.co.uk", "nationalgrid.com", "bt.com", "vodafone.co.uk",
            "thameswater.co.uk", "sellafieldsites.com", "edfenergy.com",
            # High-value industries
            "baesystems.com", "rolls-royce.com", "airbus.com", "gsk.com", "astrazeneca.com",
            "hsbc.co.uk", "barclays.co.uk", "lloydsbankinggroup.com", "londonstockexchange.com",
            # Research and development
            "ox.ac.uk", "cam.ac.uk", "imperial.ac.uk", "turing.ac.uk", "alan-turing.ac.uk"
        ]
        
        # Target organization types
        self.organization_types = {
            "government": ["Executive", "Legislative", "Intelligence", "Security"],
            "military": ["Army", "Navy", "Air Force", "Research"],
            "infrastructure": ["Healthcare", "Transport", "Energy", "Communications"],
            "industry": ["Defence", "Aerospace", "Pharmaceuticals", "Finance"],
            "research": ["University", "AI", "Biotechnology", "Quantum Computing"]
        }
        
        # Common job titles by organization type
        self.job_titles = {
            "government": ["Permanent Secretary", "Policy Advisor", "Intelligence Analyst", "Security Officer"],
            "military": ["Commanding Officer", "Intelligence Corps", "Cyber Security Specialist", "Defence Scientist"],
            "infrastructure": ["Clinical Director", "Network Operations Manager", "Grid Control Engineer", "Chief Security Officer"],
            "industry": ["Chief Technology Officer", "Aerospace Engineer", "Research Scientist", "Financial Analyst"],
            "research": ["Professor", "Postdoctoral Researcher", "AI Specialist", "Quantum Physicist"]
        }

    def _get_organization_type(self, domain: str) -> str:
        """Determine organization type based on domain."""
        if "mod.uk" in domain or "dstl" in domain:
            return "military"
        elif "gchq" in domain or "mi6" in domain or "mi5" in domain or "ncsc" in domain:
            return "government" # Intelligence is a sub-type of government
        elif any(keyword in domain for keyword in ["nhs", "networkrail", "nationalgrid", "bt", "vodafone", "thameswater", "sellafieldsites", "edfenergy"]):
            return "infrastructure"
        elif any(keyword in domain for keyword in ["baesystems", "rolls-royce", "airbus", "gsk", "astrazeneca", "hsbc", "barclays", "lloyds", "londonstockexchange"]):
            return "industry"
        elif any(keyword in domain for keyword in ["ac.uk", "turing"]):
            return "research"
        else:
            return "government"

    def _generate_target_domain(self, network_suffix: str) -> str:
        """Construct a plausible government or corporate domain for the given suffix."""
        suffix = network_suffix.lstrip(".")
        if "." in suffix:
            return f"secure.{suffix}"
        
        org_type = self._get_organization_type(suffix)
        if org_type == "military":
            subdomains = ["ops", "intel", "cyber", "command"]
        elif org_type == "government":
            subdomains = ["secure", "internal", "ops", "analysis"]
        elif org_type == "infrastructure":
            subdomains = ["ops", "control", "monitoring", "security"]
        elif org_type == "industry":
            subdomains = ["corp", "internal", "rd", "security"]
        elif org_type == "research":
            subdomains = ["research", "projects", "development", "labs"]
        else:
            subdomains = ["secure", "admin", "ops", "internal"]
            
        subdomain = random.choice(subdomains)
        return f"{subdomain}.{suffix}"

    def _generate_target_email(self, domain: str, org_type: str) -> str:
        """Generate a realistic email address for a target domain."""
        job_title = random.choice(self.job_titles[org_type])
        
        email_prefix = job_title.lower().replace(" ", ".")
        
        variations = [
            email_prefix,
            f"{email_prefix}{random.randint(1, 9)}",
            f"{email_prefix.replace('.', '_')}",
        ]
        
        if "." in email_prefix:
            variations.append(email_prefix.split(".")[0])
        
        return f"{random.choice(variations)}@{domain}"

    def _generate_network_segment(self, org_type: str) -> Tuple[str, str]:
        """Generate realistic network segments and IP ranges for the UK."""
        # Common UK IP ranges
        base_ranges = {
            "military": ["25.", "30."],
            "government": ["51.", "81.", "141.", "157."],
            "infrastructure": ["82.", "87.", "92.", "212."],
            "industry": ["80.", "85.", "90.", "213."],
            "research": ["143.", "144.", "158.", "193."]
        }
        
        base = random.choice(base_ranges.get(org_type, ["217."]))
        ip_range = f"{base}{random.randint(0, 255)}.{random.randint(0, 255)}.0/24"
        gateway_ip = f"{base}{random.randint(0, 255)}.{random.randint(0, 255)}.1"
        
        return ip_range, gateway_ip

    def analyze_uk_targets(self) -> Dict[str, Any]:
        """Analyze U.K. government and high-value targets using enhanced toolkit primitives.

        Returns:
            Dictionary containing comprehensive reconnaissance-ready dossiers and analysis.
        """
        target_domains = [self._generate_target_domain(suffix) for suffix in self.uk_networks]

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
        base_ip = ipaddress.IPv4Address("81.134.160.0")
        for idx, profile in enumerate(target_profiles):
            simulated_ip = str(base_ip + idx)
            readiness = self.supply_chain.malicious_update_check(simulated_ip, profile["target_domain"])
            readiness["implant_outcome"] = self.supply_chain.execute_implant(readiness)
            readiness["organization_type"] = profile["organization_type"]
            supply_chain_readiness.append(readiness)

        threat_assessment = self._generate_threat_assessment(target_profiles)

        return {
            "generated_at": datetime.now().isoformat(),
            "uk_networks": self.uk_networks,
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

        risk_factors = {
            "military": 9,
            "government": 8, # Intelligence is included here
            "infrastructure": 10,
            "industry": 7,
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
        if risk_score >= 150:
            return "CRITICAL"
        elif risk_score >= 100:
            return "HIGH"
        elif risk_score >= 50:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommended_approach(self, org_distribution: Dict[str, int]) -> str:
        """Generate recommended approach based on organization distribution."""
        if org_distribution.get("infrastructure", 0) > 0:
            return "Stealth-focused campaign targeting OT/ICS systems with a focus on long-term persistence."
        elif org_distribution.get("government", 0) > 0:
            return "Multi-vector approach using social engineering and supply chain attacks, targeting sensitive data."
        elif org_distribution.get("military", 0) > 0:
            return "Advanced persistent threat campaign with custom malware and C2 infrastructure."
        else:
            return "Standard APT campaign with emphasis on data exfiltration."

    def _get_timeline_estimate(self, risk_score: int) -> str:
        """Estimate campaign timeline based on risk."""
        if risk_score >= 150:
            return "9-18 months (highly complex and sensitive environment)"
        elif risk_score >= 100:
            return "6-9 months (complex target environment)"
        elif risk_score >= 50:
            return "3-6 months (standard campaign)"
        else:
            return "1-3 months (limited scope)"


def analyze_uk_targets_enhanced(seed: Optional[int] = None) -> Dict[str, Any]:
    """Enhanced analysis of UK government and high-value targets.
    
    Args:
        seed: Optional seed to make the generated content deterministic.
        
    Returns:
        Dictionary containing comprehensive reconnaissance-ready dossiers and analysis.
    """
    analyzer = UKTargetsAnalyzer(seed)
    return analyzer.analyze_uk_targets()


__all__ = ["analyze_uk_targets_enhanced", "UKTargetsAnalyzer"]
