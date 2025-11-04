"""
Catalog metadata describing the toolkit's modules and campaign scenarios.

The interactive shell renders this information to help operators discover the
available functionality without having to memorize every analyzer flag.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

ToolEntry = Dict[str, str]
CampaignEntry = Dict[str, str]

_TOOL_CATALOG: List[ToolEntry] = [
    {
        "category": "Initial Access & Recon",
        "module": "initial-access",
        "description": "Generate spear-phishing content, emulate phishing campaigns, and explore supply-chain compromises.",
        "command_hint": "apt analyzer initial-access --generate-email",
        "requires_chinese_support": "false",
    },
    {
        "category": "Initial Access & Recon",
        "module": "exploitdb",
        "description": "Query the bundled exploit intelligence snapshot and craft tailored offensive playbooks.",
        "command_hint": "apt analyzer exploitdb --search exchange --limit 5",
        "requires_chinese_support": "false",
    },
    {
        "category": "Persistence & Privilege",
        "module": "persistence",
        "description": "Assess long-term footholds, persistence reports, and authorized startup modifications.",
        "command_hint": "apt analyzer persistence --generate-report",
        "requires_chinese_support": "false",
    },
    {
        "category": "Persistence & Privilege",
        "module": "privilege-escalation",
        "description": "Enumerate Active Directory, surface kernel weaknesses, and model privilege advancement paths.",
        "command_hint": "apt analyzer privilege-escalation --ad-enum",
        "requires_chinese_support": "false",
    },
    {
        "category": "Defense & Movement",
        "module": "defense-evasion",
        "description": "Design living-off-the-land tradecraft and evaluate process hollowing countermeasures.",
        "command_hint": "apt analyzer defense-evasion --lotl",
        "requires_chinese_support": "false",
    },
    {
        "category": "Defense & Movement",
        "module": "lateral-movement",
        "description": "Map network segments, simulate Pass-the-Hash operations, and pressure detection coverage.",
        "command_hint": "apt analyzer lateral-movement --discover",
        "requires_chinese_support": "false",
    },
    {
        "category": "Command, Control & Exfiltration",
        "module": "command-control",
        "description": "Model resilient beaconing, channel discovery, and full C2 lifecycle rehearsals.",
        "command_hint": "apt analyzer command-control --simulate-lifecycle",
        "requires_chinese_support": "false",
    },
    {
        "category": "Command, Control & Exfiltration",
        "module": "exfiltration",
        "description": "Identify sensitive datasets, rehearse staged exfiltration, and stress-test DLP coverage.",
        "command_hint": "apt analyzer exfiltration --find-data",
        "requires_chinese_support": "false",
    },
    {
        "category": "Campaign Orchestration",
        "module": "campaign",
        "description": "Launch full kill-chain simulations across all modules with deterministic seeding support.",
        "command_hint": "apt analyzer campaign --domain secure.dod.mil --seed 1337",
        "requires_chinese_support": "false",
    },
    {
        "category": "Specialized Targeting",
        "module": "american",
        "description": "Explore U.S. government targeting profiles and supporting supply-chain intelligence.",
        "command_hint": "apt analyzer american targets --json",
        "requires_chinese_support": "false",
    },
    {
        "category": "Specialized Targeting",
        "module": "financial",
        "description": "Model theft vectors across banking, investment, and cryptocurrency sectors.",
        "command_hint": "apt analyzer financial banks --json",
        "requires_chinese_support": "false",
    },
    {
        "category": "Operational Disruption",
        "module": "hardware-disruption",
        "description": "Stress precision disruption tooling against defense, logistics, and critical infrastructure targets.",
        "command_hint": "apt analyzer hardware-disruption --tool gps_jammer",
        "requires_chinese_support": "false",
    },
    {
        "category": "Chinese APT Tradecraft",
        "module": "chinese-apt",
        "description": "Simulate historic APT41, APT1, APT10, and APT12 operations with comparative analytics.",
        "command_hint": "apt analyzer chinese-apt --campaign comparative",
        "requires_chinese_support": "true",
    },
]

_CAMPAIGN_CATALOG: List[CampaignEntry] = [
    {
        "category": "Global Operations",
        "name": "End-to-End Campaign (APTCampaignSimulator)",
        "description": "Chain every core module into a cohesive red-team narrative with configurable scope.",
        "command_hint": "apt analyzer campaign --domain secure.dod.mil",
        "requires_chinese_support": "false",
    },
    {
        "category": "Chinese APT Campaigns",
        "name": "APT41 Gaming & Supply Chain",
        "description": "Blend dual-use espionage and supply-chain compromises modelled after APT41 tradecraft.",
        "command_hint": "apt analyzer chinese-apt --campaign apt41_supply_chain",
        "requires_chinese_support": "true",
    },
    {
        "category": "Chinese APT Campaigns",
        "name": "APT1 Government & Military",
        "description": "Survey long-term strategic espionage targeting U.S. government and defense contractors.",
        "command_hint": "apt analyzer chinese-apt --campaign apt1_long_term",
        "requires_chinese_support": "true",
    },
    {
        "category": "Chinese APT Campaigns",
        "name": "APT10 Cloud & MSP Intrusions",
        "description": "Exercise managed service provider compromise paths and long-haul data theft patterns.",
        "command_hint": "apt analyzer chinese-apt --campaign apt10_cloud",
        "requires_chinese_support": "true",
    },
    {
        "category": "Chinese APT Campaigns",
        "name": "APT12 Diplomatic Operations",
        "description": "Mirror strategic diplomatic intrusions with heavy operational security considerations.",
        "command_hint": "apt analyzer chinese-apt --campaign apt12_diplomatic",
        "requires_chinese_support": "true",
    },
    {
        "category": "Chinese APT Campaigns",
        "name": "Comparative Campaign Intelligence",
        "description": "Stack campaign outputs side-by-side to study overlapping TTPs and defensive gaps.",
        "command_hint": "apt analyzer chinese-apt --campaign comparative",
        "requires_chinese_support": "true",
    },
]


def _supports(entry: Dict[str, str], chinese_support: bool) -> bool:
    """Return True if an entry should be shown given Chinese APT support."""

    flag = entry.get("requires_chinese_support", "false").lower()
    if flag not in {"true", "false"}:
        return True
    requires = flag == "true"
    return chinese_support or not requires


def _clone(entry: Dict[str, str]) -> Dict[str, str]:
    """Return a shallow copy so callers can mutate without side effects."""

    return dict(entry)


def get_tool_catalog(chinese_support: bool) -> List[ToolEntry]:
    """Return a filtered list of tool metadata."""

    return [
        _clone(entry)
        for entry in _TOOL_CATALOG
        if _supports(entry, chinese_support)
    ]


def get_campaign_catalog(chinese_support: bool) -> List[CampaignEntry]:
    """Return a filtered list of campaign metadata."""

    return [
        _clone(entry)
        for entry in _CAMPAIGN_CATALOG
        if _supports(entry, chinese_support)
    ]
