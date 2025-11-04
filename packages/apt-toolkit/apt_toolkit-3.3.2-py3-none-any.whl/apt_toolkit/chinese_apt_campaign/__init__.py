"""
Chinese APT Campaign Toolkit

Advanced tools for orchestrating and executing Chinese APT campaigns
against government, military, and critical infrastructure targets.

⚠️ LEGAL AND ETHICAL NOTICE:
This toolkit is intended for authorized penetration testing, security research, 
and educational purposes only. Unauthorized use is illegal and unethical. 
Always obtain proper permissions before use.
"""

from .advanced_targeting import AdvancedTargetingEngine
from .campaign_orchestrator import CampaignOrchestrator
from .system_exploitation import SystemExploitationEngine

__version__ = "1.0.0"
__author__ = "Security Research Team"

__all__ = [
    "AdvancedTargetingEngine",
    "CampaignOrchestrator", 
    "SystemExploitationEngine"
]

# Security controls
__safety_controls__ = {
    "require_authorization": True,
    "safe_mode_default": False,
    "audit_logging": True,
    "environment_checks": True
}