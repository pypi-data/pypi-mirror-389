"""
Advanced targeting tools for Chinese APT campaigns.
"""

import random
from typing import Dict, List, Optional, Any


class AdvancedTargetingEngine:
    """Advanced targeting engine for Chinese APT campaigns."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate_government_targets(self) -> List[Dict[str, Any]]:
        """Generate realistic government targets."""
        
        government_domains = [
            "state.gov", "dod.mil", "cia.gov", "nsa.gov", "fbi.gov",
            "treasury.gov", "energy.gov", "defense.gov", "army.mil",
            "navy.mil", "airforce.mil", "usmc.mil", "dhs.gov"
        ]
        
        targets = []
        for domain in government_domains:
            target = {
                "domain": domain,
                "ip_range": self._generate_government_ip_range(),
                "organization_type": self._get_organization_type(domain),
                "sensitivity_level": self._get_sensitivity_level(domain),
                "primary_technologies": self._get_government_technologies(domain),
                "attack_vectors": self._get_attack_vectors(domain),
                "priority_level": self._get_priority_level(domain),
                "last_known_activity": self._generate_random_date(),
                "vulnerability_assessment": self._assess_vulnerabilities(domain)
            }
            targets.append(target)
        
        return targets
    
    def generate_military_targets(self) -> List[Dict[str, Any]]:
        """Generate military-specific targets."""
        
        military_domains = [
            "centcom.mil", "eucom.mil", "pacom.mil", "socom.mil",
            "stratcom.mil", "transcom.mil", "northcom.mil",
            "africom.mil", "cybercom.mil", "spacecom.mil"
        ]
        
        targets = []
        for domain in military_domains:
            target = {
                "domain": domain,
                "ip_range": self._generate_military_ip_range(),
                "command_level": self._get_command_level(domain),
                "geographic_region": self._get_geographic_region(domain),
                "mission_type": self._get_mission_type(domain),
                "primary_technologies": self._get_military_technologies(domain),
                "attack_vectors": self._get_military_attack_vectors(domain),
                "priority_level": "HIGH",
                "last_known_activity": self._generate_random_date(),
                "vulnerability_assessment": self._assess_military_vulnerabilities(domain)
            }
            targets.append(target)
        
        return targets
    
    def generate_critical_infrastructure_targets(self) -> List[Dict[str, Any]]:
        """Generate critical infrastructure targets."""
        
        infrastructure_sectors = {
            "energy": ["doe.gov", "ferc.gov", "nerc.com"],
            "finance": ["treasury.gov", "federalreserve.gov", "sec.gov"],
            "transportation": ["dot.gov", "faa.gov", "tsa.gov"],
            "healthcare": ["hhs.gov", "cdc.gov", "fda.gov"],
            "communications": ["fcc.gov", "ntia.gov"],
            "water": ["epa.gov", "usace.army.mil"]
        }
        
        targets = []
        for sector, domains in infrastructure_sectors.items():
            for domain in domains:
                target = {
                    "domain": domain,
                    "sector": sector,
                    "ip_range": self._generate_infrastructure_ip_range(sector),
                    "criticality_level": self._get_criticality_level(sector),
                    "primary_technologies": self._get_infrastructure_technologies(sector),
                    "attack_vectors": self._get_infrastructure_attack_vectors(sector),
                    "priority_level": self._get_infrastructure_priority(sector),
                    "last_known_activity": self._generate_random_date(),
                    "vulnerability_assessment": self._assess_infrastructure_vulnerabilities(sector)
                }
                targets.append(target)
        
        return targets
    
    def _generate_government_ip_range(self) -> str:
        ranges = [
            "192.84.0.0/16", "192.124.0.0/16", "192.150.0.0/16",
            "198.0.0.0/8", "199.0.0.0/8", "205.0.0.0/8"
        ]
        return random.choice(ranges)
    
    def _generate_military_ip_range(self) -> str:
        ranges = [
            "134.0.0.0/8", "136.0.0.0/8", "137.0.0.0/8",
            "138.0.0.0/8", "139.0.0.0/8", "140.0.0.0/8"
        ]
        return random.choice(ranges)
    
    def _generate_infrastructure_ip_range(self, sector: str) -> str:
        ranges = {
            "energy": ["198.18.0.0/15", "198.20.0.0/14"],
            "finance": ["192.152.0.0/16", "192.153.0.0/16"],
            "transportation": ["192.154.0.0/16", "192.155.0.0/16"],
            "healthcare": ["192.156.0.0/16", "192.157.0.0/16"],
            "communications": ["192.158.0.0/16", "192.159.0.0/16"],
            "water": ["192.160.0.0/16", "192.161.0.0/16"]
        }
        return random.choice(ranges.get(sector, ["192.168.0.0/16"]))
    
    def _get_organization_type(self, domain: str) -> str:
        if ".gov" in domain:
            return "government"
        elif ".mil" in domain:
            return "military"
        else:
            return "other"
    
    def _get_sensitivity_level(self, domain: str) -> str:
        high_sensitivity = ["cia.gov", "nsa.gov", "dod.mil", "fbi.gov"]
        medium_sensitivity = ["state.gov", "treasury.gov", "energy.gov"]
        
        if domain in high_sensitivity:
            return "TOP SECRET"
        elif domain in medium_sensitivity:
            return "SECRET"
        else:
            return "CONFIDENTIAL"
    
    def _get_command_level(self, domain: str) -> str:
        combatant_commands = ["centcom", "eucom", "pacom", "socom", "stratcom"]
        if any(cmd in domain for cmd in combatant_commands):
            return "COMBATANT_COMMAND"
        elif "cybercom" in domain:
            return "CYBER_COMMAND"
        elif "spacecom" in domain:
            return "SPACE_COMMAND"
        else:
            return "SERVICE_COMPONENT"
    
    def _get_geographic_region(self, domain: str) -> str:
        regions = {
            "centcom": "Middle East",
            "eucom": "Europe",
            "pacom": "Asia-Pacific",
            "socom": "Global",
            "stratcom": "Global",
            "northcom": "North America",
            "africom": "Africa",
            "cybercom": "Global",
            "spacecom": "Global"
        }
        
        for cmd, region in regions.items():
            if cmd in domain:
                return region
        return "Unknown"
    
    def _get_mission_type(self, domain: str) -> str:
        if "cybercom" in domain:
            return "CYBER_OPERATIONS"
        elif "spacecom" in domain:
            return "SPACE_OPERATIONS"
        elif "socom" in domain:
            return "SPECIAL_OPERATIONS"
        else:
            return "CONVENTIONAL_OPERATIONS"
    
    def _get_criticality_level(self, sector: str) -> str:
        criticality = {
            "energy": "CRITICAL",
            "finance": "CRITICAL",
            "transportation": "HIGH",
            "healthcare": "HIGH",
            "communications": "CRITICAL",
            "water": "CRITICAL"
        }
        return criticality.get(sector, "MEDIUM")
    
    def _get_government_technologies(self, domain: str) -> List[str]:
        base_tech = ["Active Directory", "Windows Server", "SharePoint", "Exchange"]
        
        if "cia" in domain or "nsa" in domain:
            base_tech.extend(["Classified Networks", "Secure Communications", "Encrypted Storage"])
        elif "dod" in domain:
            base_tech.extend(["Military Networks", "SIPRNet", "JWICS"])
        
        return base_tech
    
    def _get_military_technologies(self, domain: str) -> List[str]:
        tech = ["Military Networks", "Tactical Systems", "Command & Control"]
        
        if "cybercom" in domain:
            tech.extend(["Cyber Defense Systems", "Incident Response", "Threat Intelligence"])
        elif "spacecom" in domain:
            tech.extend(["Satellite Systems", "Space Operations", "GPS Infrastructure"])
        
        return tech
    
    def _get_infrastructure_technologies(self, sector: str) -> List[str]:
        technologies = {
            "energy": ["SCADA", "ICS", "Smart Grid", "Power Management"],
            "finance": ["Banking Systems", "Payment Processing", "Financial Networks"],
            "transportation": ["Traffic Control", "Logistics", "Transport Management"],
            "healthcare": ["Medical Records", "Healthcare Systems", "Patient Data"],
            "communications": ["Telecom Infrastructure", "Network Operations", "Communication Systems"],
            "water": ["Water Treatment", "SCADA", "Distribution Systems"]
        }
        return technologies.get(sector, ["General IT Systems"])
    
    def _get_attack_vectors(self, domain: str) -> List[str]:
        vectors = ["Spear Phishing", "Watering Hole", "Supply Chain"]
        
        if ".mil" in domain:
            vectors.extend(["Credential Theft", "Network Intrusion"])
        
        return vectors
    
    def _get_military_attack_vectors(self, domain: str) -> List[str]:
        return ["Credential Theft", "Network Intrusion", "Supply Chain", "Insider Threat"]
    
    def _get_infrastructure_attack_vectors(self, sector: str) -> List[str]:
        vectors = {
            "energy": ["SCADA Exploitation", "ICS Attacks", "Supply Chain"],
            "finance": ["Credential Theft", "API Abuse", "Supply Chain"],
            "transportation": ["System Manipulation", "Data Corruption", "Supply Chain"],
            "healthcare": ["Data Theft", "Ransomware", "Supply Chain"],
            "communications": ["Network Manipulation", "Traffic Interception", "Supply Chain"],
            "water": ["SCADA Manipulation", "System Disruption", "Supply Chain"]
        }
        return vectors.get(sector, ["General Attack Vectors"])
    
    def _get_priority_level(self, domain: str) -> str:
        high_priority = ["cia.gov", "nsa.gov", "dod.mil", "state.gov"]
        medium_priority = ["fbi.gov", "treasury.gov", "energy.gov"]
        
        if domain in high_priority:
            return "HIGH"
        elif domain in medium_priority:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_infrastructure_priority(self, sector: str) -> str:
        priorities = {
            "energy": "HIGH",
            "finance": "HIGH",
            "transportation": "MEDIUM",
            "healthcare": "MEDIUM",
            "communications": "HIGH",
            "water": "HIGH"
        }
        return priorities.get(sector, "LOW")
    
    def _generate_random_date(self) -> str:
        year = 2024
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return f"{year}-{month:02d}-{day:02d}"
    
    def _assess_vulnerabilities(self, domain: str) -> Dict[str, Any]:
        return {
            "network_security": random.choice(["STRONG", "MODERATE", "WEAK"]),
            "patch_management": random.choice(["TIMELY", "DELAYED", "POOR"]),
            "user_training": random.choice(["COMPREHENSIVE", "BASIC", "NONE"]),
            "incident_response": random.choice(["ROBUST", "AVERAGE", "WEAK"])
        }
    
    def _assess_military_vulnerabilities(self, domain: str) -> Dict[str, Any]:
        return {
            "network_security": random.choice(["VERY STRONG", "STRONG", "MODERATE"]),
            "physical_security": random.choice(["HIGH", "MODERATE", "LOW"]),
            "cyber_defense": random.choice(["ADVANCED", "STANDARD", "BASIC"]),
            "insider_threat": random.choice(["LOW", "MEDIUM", "HIGH"])
        }
    
    def _assess_infrastructure_vulnerabilities(self, sector: str) -> Dict[str, Any]:
        return {
            "system_security": random.choice(["STRONG", "MODERATE", "WEAK"]),
            "physical_access": random.choice(["RESTRICTED", "CONTROLLED", "OPEN"]),
            "backup_systems": random.choice(["REDUNDANT", "BASIC", "NONE"]),
            "recovery_capability": random.choice(["RAPID", "SLOW", "MINIMAL"])
        }
    
    def _has_relationship(self, domain1: str, domain2: str) -> bool:
        """Check if two domains have a relationship."""
        # Simple relationship logic based on domain patterns
        gov_domains = ["state.gov", "dod.mil", "treasury.gov"]
        mil_domains = ["centcom.mil", "eucom.mil", "pacom.mil"]
        
        return (domain1 in gov_domains and domain2 in mil_domains) or \
               (domain2 in gov_domains and domain1 in mil_domains)