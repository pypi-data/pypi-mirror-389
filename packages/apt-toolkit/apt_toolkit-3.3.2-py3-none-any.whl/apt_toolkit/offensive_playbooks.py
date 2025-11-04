"""Offensive playbook generation using the bundled ExploitDB snapshot."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from .exploit_intel import module_recommendations

_DEFAULT_MODULES = [
    "initial-access",
    "persistence",
    "privilege-escalation",
    "defense-evasion",
    "lateral-movement",
    "command-control",
    "exfiltration",
]

_DEFAULT_SEARCH_TERMS: Dict[str, List[str]] = {
    "initial-access": ["rce", "remote"],
    "persistence": ["persistence", "backdoor"],
    "privilege-escalation": ["privilege", "escalation"],
    "defense-evasion": ["bypass", "evasion"],
    "lateral-movement": ["pth", "wmic", "remote"],
    "command-control": ["c2", "backdoor"],
    "exfiltration": ["exfil", "data"],
}


def _normalise_modules(modules: Optional[Sequence[str]]) -> List[str]:
    if not modules:
        return list(_DEFAULT_MODULES)
    ordered: List[str] = []
    seen = set()
    for item in modules:
        module = item.strip().lower()
        if not module:
            continue
        if module not in seen:
            ordered.append(module)
            seen.add(module)
    return ordered


def generate_offensive_playbook(
    *,
    target_product: Optional[str] = None,
    target_platform: Optional[str] = None,
    modules: Optional[Sequence[str]] = None,
    limit: int = 5,
    payload_limit: int = 3,
    snippet_chars: int = 800,
) -> Dict[str, object]:
    """Produce a module-aligned offensive playbook enriched with exploit payloads."""

    selected_modules = _normalise_modules(modules)
    playbook: Dict[str, object] = {
        "target_product": target_product,
        "target_platform": target_platform,
        "modules": [],
    }

    for module in selected_modules:
        search_terms: List[str] = []
        if target_product:
            search_terms.append(target_product)
        search_terms.extend(_DEFAULT_SEARCH_TERMS.get(module, []))

        intel = module_recommendations(
            module,
            search_terms=search_terms,
            platform=target_platform,
            limit=limit,
            include_payloads=True,
            payload_limit=payload_limit,
            snippet_chars=snippet_chars,
        )
        if intel:
            playbook["modules"].append(intel)

    return playbook


__all__ = ["generate_offensive_playbook"]
