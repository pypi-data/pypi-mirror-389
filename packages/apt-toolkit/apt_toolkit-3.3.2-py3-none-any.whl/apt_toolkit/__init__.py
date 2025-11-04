"""
APT Toolkit - Advanced Persistent Threat Offensive Toolkit

A comprehensive framework for red team operations, penetration testing, and advanced adversary simulation.
This toolkit provides real-world offensive security capabilities for authorized security testing.

⚠️ LEGAL AND ETHICAL NOTICE:
This toolkit is intended for authorized penetration testing, security research, and educational purposes only.
Unauthorized use is illegal and unethical. Always obtain proper permissions before use.
"""

__version__ = "3.3.2"
__author__ = "Security Research Team"

# Core modules - import functions that actually exist
from .american_targets import analyze_american_targets
from .initial_access import SpearPhishingGenerator, SupplyChainCompromise, phishing_attack
from .persistence import PersistenceManager, add_startup_script
from .privilege_escalation import PrivilegeEscalator, exploit_kernel_vulnerability
from .defense_evasion import DefenseEvader, clear_logs
from .lateral_movement import LateralMover, pass_the_hash
from .command_control import start_c2_server, send_beacon
from .exfiltration import DataExfiltrator, exfiltrate_data
from .email_repository import EmailRepository, EmailRepositoryError

# Enhanced modules with sophisticated tradecraft
from .campaign import APTCampaignSimulator, CampaignConfig, simulate_campaign
from .exploit_intel import (
    ExploitDBIndex,
    ExploitDBNotAvailableError,
    ExploitEntry,
    enrich_with_exploit_intel,
    module_recommendations,
)
from .offensive_playbooks import generate_offensive_playbook

# Chinese APT Campaign modules
from .chinese_apt_campaign import (
    AdvancedTargetingEngine,
    CampaignOrchestrator,
    SystemExploitationEngine
)
from .interactive_shell import main as launch_shell

__all__ = [
    # Core modules
    "SpearPhishingGenerator",
    "SupplyChainCompromise", 
    "PersistenceManager",
    "PrivilegeEscalator",
    "DefenseEvader",
    "LateralMover",
    "DataExfiltrator",
    
    # Core functions
    "phishing_attack",
    "add_startup_script",
    "exploit_kernel_vulnerability",
    "clear_logs",
    "pass_the_hash",
    "start_c2_server",
    "send_beacon",
    "exfiltrate_data",

    # Email dataset
    "EmailRepository",
    "EmailRepositoryError",

    # Campaign orchestration
    "CampaignConfig",
    "APTCampaignSimulator",
    "simulate_campaign",

    # ExploitDB intelligence
    "ExploitDBIndex",
    "ExploitEntry",
    "ExploitDBNotAvailableError",
    "enrich_with_exploit_intel",
    "module_recommendations",
    "generate_offensive_playbook",

    # Chinese APT Campaign modules
    "AdvancedTargetingEngine",
    "CampaignOrchestrator", 
    "SystemExploitationEngine",
    
    # Analysis functions
    "analyze_american_targets",
    "launch_shell",
]
