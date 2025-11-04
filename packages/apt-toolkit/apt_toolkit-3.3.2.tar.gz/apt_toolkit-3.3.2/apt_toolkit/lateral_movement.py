"""
Lateral Movement Module - Techniques for moving within compromised networks.

This module contains conceptual implementations of common APT lateral movement techniques
including Pass-the-Hash and network reconnaissance.
"""

import random
from typing import List, Dict, Any

from .exploit_intel import enrich_with_exploit_intel

class LateralMover:
    """Manage lateral movement techniques within enterprise networks."""
    
    def __init__(self, stolen_hashes: List[Dict[str, str]] = None):
        self.stolen_hashes = stolen_hashes or []
        self.visited_subnets = []
        self.gov_subnets = [
            "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
            "134.228.0.0/16", "137.229.0.0/16"  # Common .mil ranges
        ]
    
    def discover_network_segments(self) -> Dict[str, Any]:
        """Conceptual network segment discovery."""
        
        discovered_subnets = []
        for subnet in self.gov_subnets:
            # Simulated subnet discovery
            if random.choice([True, False, True]):  # Bias toward discovery
                discovered_subnets.append(subnet)
                self.visited_subnets.append(subnet)
        
        result = {
            "discovered_subnets": discovered_subnets,
            "total_subnets_found": len(discovered_subnets),
            "common_government_ranges": self.gov_subnets,
            "recommended_targets": self._prioritize_subnets(discovered_subnets)
        }
        search_terms = discovered_subnets or self.gov_subnets
        return enrich_with_exploit_intel(
            "lateral-movement",
            result,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )
    
    def _prioritize_subnets(self, subnets: List[str]) -> List[Dict[str, str]]:
        """Prioritize subnets for lateral movement."""
        prioritized = []
        
        for subnet in subnets:
            priority = "High" if ".mil" in subnet or "134.228" in subnet else "Medium"
            target_info = {
                "subnet": subnet,
                "priority": priority,
                "rationale": "Military network" if ".mil" in subnet else "Government range",
                "estimated_hosts": random.randint(50, 1000)
            }
            prioritized.append(target_info)
        
        # Sort by priority
        prioritized.sort(key=lambda x: 0 if x["priority"] == "High" else 1)
        return prioritized
    
    def pass_the_hash_lateral(self, target_ip: str, username: str, ntlm_hash: str) -> Dict[str, Any]:
        """Conceptual Pass-the-Hash lateral movement attempt."""
        
        # Simulate success based on various factors
        success_factors = {
            "hash_valid": ntlm_hash in [h["hash"] for h in self.stolen_hashes],
            "target_reachable": random.choice([True, False, True]),
            "admin_privileges": username.endswith("admin") or "admin" in username.lower(),
            "defenses_present": random.choice([True, False])
        }
        
        success = all(success_factors.values())
        
        result = {
            "target_ip": target_ip,
            "username": username,
            "technique": "Pass-the-Hash",
            "success": success,
            "success_factors": success_factors,
            "command_used": f'psexec.py -hashes "{ntlm_hash}" {username}@{target_ip} "cmd /c whoami"'
        }
        
        if success:
            result["next_steps"] = [
                "Deploy persistent implant",
                "Conduct local reconnaissance", 
                "Attempt privilege escalation"
            ]
        else:
            result["failure_reason"] = self._analyze_failure(success_factors)
        
        return enrich_with_exploit_intel(
            "lateral-movement",
            result,
            search_terms=[target_ip, username, "pass-the-hash"],
            platform="windows",
            include_payloads=True,
        )
    
    def _analyze_failure(self, factors: Dict[str, bool]) -> str:
        """Analyze why PTH attempt failed."""
        failed_factors = [factor for factor, present in factors.items() if not present]
        
        if "hash_valid" in failed_factors:
            return "Invalid or expired hash"
        elif "target_reachable" in failed_factors:
            return "Target system unreachable"
        elif "admin_privileges" in failed_factors:
            return "Insufficient privileges on target"
        elif "defenses_present" in failed_factors:
            return "Defenses detected and blocked the attempt"
        else:
            return "Unknown failure reason"
    
    def deploy_implant(self, target_ip: str, implant_type: str = "beacon") -> Dict[str, str]:
        """Conceptual implant deployment on compromised system."""
        
        implants = {
            "beacon": {
                "type": "Command & Control Beacon",
                "persistence": "Scheduled Task",
                "communication": "HTTPS to cloud front",
                "detection_difficulty": "Medium"
            },
            "keylogger": {
                "type": "Input Capture",
                "persistence": "Registry Run Key", 
                "communication": "DNS exfiltration",
                "detection_difficulty": "High"
            },
            "recon": {
                "type": "Network Reconnaissance",
                "persistence": "WMI Event Subscription",
                "communication": "ICMP covert channel",
                "detection_difficulty": "Very High"
            }
        }
        
        implant = implants.get(implant_type, implants["beacon"])
        
        result = {
            "target": target_ip,
            "implant_deployed": implant_type,
            **implant,
            "deployment_status": "Success" if random.choice([True, True, False]) else "Failed"
        }
        search_terms = [implant_type, implant.get("persistence"), implant.get("communication")]
        return enrich_with_exploit_intel(
            "lateral-movement",
            result,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )
    
    def analyze_lateral_movement_techniques(self) -> Dict[str, Any]:
        """Analyze various lateral movement techniques."""
        
        techniques = [
            {
                "name": "Pass-the-Hash",
                "effectiveness": "High",
                "stealth": "Medium",
                "common_in_apt": ["APT29", "APT28", "APT41"],
                "detection": "Monitor for anomalous authentication events"
            },
            {
                "name": "Windows Management Instrumentation (WMI)",
                "effectiveness": "Medium", 
                "stealth": "High",
                "common_in_apt": ["APT32", "APT34"],
                "detection": "Monitor WMI process creation events"
            },
            {
                "name": "PsExec",
                "effectiveness": "High",
                "stealth": "Low",
                "common_in_apt": ["Multiple APTs"],
                "detection": "Monitor for PsExec usage and service creation"
            }
        ]
        
        result = {
            "techniques": techniques,
            "recommended_approach": "Use combination of techniques to avoid pattern detection",
            "defense_measures": [
                "Implement network segmentation",
                "Monitor lateral movement patterns",
                "Use privileged access management",
                "Regular credential rotation"
            ]
        }
        search_terms = [tech.get("name") for tech in techniques]
        return enrich_with_exploit_intel(
            "lateral-movement",
            result,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )


def analyze_lateral_movement_campaign() -> Dict[str, Any]:
    """Analyze a conceptual lateral movement campaign."""
    
    # Simulate stolen hashes
    stolen_hashes = [
        {"username": "admin1", "hash": "aad3b435b51404eeaad3b435b51404ee"},
        {"username": "backup_operator", "hash": "8846f7eaee8fb117ad06bdd830b7586c"}
    ]
    
    mover = LateralMover(stolen_hashes)
    
    campaign = {
        "network_discovery": mover.discover_network_segments(),
        "lateral_attempts": [
            mover.pass_the_hash_lateral("192.168.1.100", "admin1", "aad3b435b51404eeaad3b435b51404ee"),
            mover.pass_the_hash_lateral("192.168.1.150", "backup_operator", "8846f7eaee8fb117ad06bdd830b7586c")
        ],
        "implant_deployments": [
            mover.deploy_implant("192.168.1.100", "beacon"),
            mover.deploy_implant("192.168.1.150", "recon")
        ],
        "technique_analysis": mover.analyze_lateral_movement_techniques()
    }

    return enrich_with_exploit_intel(
        "lateral-movement",
        campaign,
        search_terms=["pass-the-hash", "psexec", "wmi"],
        platform="windows",
        include_payloads=True,
    )


def pass_the_hash(username: str, ntlm_hash: str) -> Dict[str, Any]:
    """Simulate Pass-the-Hash lateral movement."""
    print(f"[+] Attempting Pass-the-Hash with user: {username}")
    
    mover = LateralMover()
    
    # Simulate target selection
    targets = ["192.168.1.100", "192.168.1.150", "192.168.1.200"]
    target_ip = random.choice(targets)
    
    result = mover.pass_the_hash_lateral(target_ip, username, ntlm_hash)
    
    if result["success"]:
        print(f"[+] Successfully moved to {target_ip}")
    else:
        print(f"[-] Failed to move to {target_ip}: {result.get('failure_reason', 'Unknown error')}")
    
    return result