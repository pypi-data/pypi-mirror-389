"""Campaign orchestration utilities for the APT Toolkit.

This module connects the standalone primitives (initial access, persistence,
privilege escalation, defense evasion, lateral movement, command and control,
and exfiltration) into a coherent end-to-end campaign simulator. The output is
conceptual and intended for defensive research, purple teaming exercises, and
training scenarios only.
"""

from __future__ import annotations

import hashlib
import ipaddress
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .defense_evasion import DefenseEvader
from .exfiltration import DataExfiltrator
from .lateral_movement import LateralMover
from .privilege_escalation import PrivilegeEscalator
from .exploit_intel import enrich_with_exploit_intel


@dataclass
class CampaignConfig:
    """Configuration options for a simulated APT campaign."""

    target_domain: str = "secure.dod.mil"
    target_ip: str = "203.0.113.10"
    beacon_duration_hours: int = 48
    include_supply_chain: bool = True
    include_counter_forensics: bool = True
    seed: Optional[int] = None


class APTCampaignSimulator:
    """Orchestrate the toolkit's primitives into a full campaign narrative."""

    def __init__(self, seed: Optional[int] = None):
        self._base_seed = seed
        self._privilege_escalator = PrivilegeEscalator()
        self._defense_evader = DefenseEvader()
        self._exfiltrator = DataExfiltrator()

    def simulate(self, config: Optional[CampaignConfig] = None) -> Dict[str, Any]:
        """Run the end-to-end simulation and return a structured report."""

        config = config or CampaignConfig()
        seed = config.seed if config.seed is not None else self._base_seed
        if seed is not None:
            random.seed(seed)

        initial_access = self._simulate_initial_access(config)
        persistence = self._simulate_persistence(config)
        privilege_escalation = self._simulate_privilege_escalation(config)
        defense_evasion = self._simulate_defense_evasion()
        lateral_movement = self._simulate_lateral_movement(
            privilege_escalation, config
        )
        command_control = self._simulate_command_control(config)
        exfiltration = self._simulate_exfiltration()

        timeline = self._build_timeline(
            initial_access,
            persistence,
            privilege_escalation,
            defense_evasion,
            lateral_movement,
            command_control,
            exfiltration,
        )

        return {
            "config": config.__dict__,
            "initial_access": initial_access,
            "persistence": persistence,
            "privilege_escalation": privilege_escalation,
            "defense_evasion": defense_evasion,
            "lateral_movement": lateral_movement,
            "command_control": command_control,
            "exfiltration": exfiltration,
            "campaign_timeline": timeline,
            "key_takeaways": self._summarize_takeaways(
                initial_access,
                persistence,
                privilege_escalation,
                lateral_movement,
                exfiltration,
            ),
        }

    # ------------------------------------------------------------------
    # Phase simulators

    def _simulate_initial_access(self, config: CampaignConfig) -> Dict[str, Any]:
        """Simulate initial access phase."""
        from .initial_access_enhanced import (
            AdvancedSocialEngineering,
            PolyglotPayloadEngine,
        )

        social_engineering = AdvancedSocialEngineering()
        payload_engine = PolyglotPayloadEngine()

        target_email = f"admin@{config.target_domain}"
        dossier = social_engineering.build_target_dossier(target_email)
        lure = social_engineering.create_context_aware_lure(dossier)
        payload = payload_engine.create_advanced_polyglot(
            {"target_environment": "windows"}
        )

        result = {
            "target_domain": config.target_domain,
            "target_ip": config.target_ip,
            "target_email": target_email,
            "technique": "Advanced Spear-Phishing",
            "success": True,
            "dossier": dossier,
            "lure": lure,
            "payload": payload,
        }

        # Add supply chain if enabled
        if config.include_supply_chain:
            from .initial_access import SupplyChainCompromise

            supply_chain = SupplyChainCompromise()
            result["supply_chain"] = supply_chain.malicious_update_check(
                config.target_ip, config.target_domain
            )
        else:
            result["supply_chain"] = None

        return enrich_with_exploit_intel(
            "initial-access",
            result,
            search_terms=[config.target_domain, "initial access"],
            platform="windows",
            include_payloads=True,
        )

    def _simulate_persistence(self, config: CampaignConfig) -> Dict[str, Any]:
        """Simulate persistence phase."""
        from .persistence_enhanced import AdvancedPersistenceFramework

        persistence_framework = AdvancedPersistenceFramework()
        persistence_results = persistence_framework.install_multi_layer_persistence(
            {"target_ip": config.target_ip, "edr_present": True}
        )

        result = {
            "technique": "Advanced Multi-Layer Persistence",
            "mechanisms": persistence_results,
            "success": True,
        }

        # Add counter forensics if enabled
        if config.include_counter_forensics:
            from .persistence_enhanced import CounterForensics

            counter_forensics = CounterForensics()
            result[
                "counter_forensics"
            ] = counter_forensics.implement_counter_forensics()
        else:
            result["counter_forensics"] = None

        return enrich_with_exploit_intel(
            "persistence",
            result,
            search_terms=["persistence", "wmi", "fileless"],
            platform="windows",
            include_payloads=True,
        )

    def _simulate_privilege_escalation(
        self, config: CampaignConfig
    ) -> Dict[str, Any]:
        """Simulate privilege escalation phase."""
        from .privilege_escalation_enhanced import (
            ADCSExploitationSuite,
            AdvancedKerberosAttacks,
        )

        adcs_exploit = ADCSExploitationSuite()
        kerberos_attacks = AdvancedKerberosAttacks()

        ad_enum = self._privilege_escalator.enumerate_ad_privileges()
        vuln_scan = self._privilege_escalator.check_vulnerabilities(
            f"dc1.{config.target_domain}"
        )
        adcs_scan = adcs_exploit.perform_adcs_escalation_scan(
            {"domain": config.target_domain}
        )
        kerberos_results = kerberos_attacks.perform_kerberos_attack_suite(
            {"domain": config.target_domain}
        )

        result = {
            "active_directory": {
                "enumeration": ad_enum,
                "vulnerabilities": vuln_scan,
                "adcs_scan": adcs_scan,
                "kerberos_attacks": kerberos_results,
            },
            "technique": "Advanced Privilege Escalation",
            "success": True,
        }
        return enrich_with_exploit_intel(
            "privilege-escalation",
            result,
            search_terms=["adcs", "kerberoasting", config.target_domain],
            platform="windows",
            include_payloads=True,
        )

    def _simulate_defense_evasion(self) -> Dict[str, Any]:
        """Simulate defense evasion phase."""
        from .defense_evasion_enhanced import (
            AdvancedEDREvasion,
            AdvancedProcessInjection,
        )

        edr_evasion = AdvancedEDREvasion()
        process_injection = AdvancedProcessInjection()

        lotl = self._defense_evader.generate_lotl_commands()
        lotl_detection = self._defense_evader.analyze_lotl_detection()
        edr_bypass = edr_evasion.execute_stealthy_payload(
            {"technique": "syscall_direct"}
        )
        injection_result = process_injection.perform_stealthy_injection(
            {"technique": "process_herpaderping"}
        )

        result = {
            "lotl": lotl,
            "lotl_detection": lotl_detection,
            "edr_bypass": edr_bypass,
            "process_injection": injection_result,
            "technique": "Advanced Defense Evasion",
            "success": True,
        }
        return enrich_with_exploit_intel(
            "defense-evasion",
            result,
            search_terms=["edr evasion", "process injection", "syscall"],
            platform="windows",
            include_payloads=True,
        )

    def _simulate_lateral_movement(
        self, privilege_escalation: Dict[str, Any], config: CampaignConfig
    ) -> Dict[str, Any]:
        """Simulate lateral movement phase."""
        lateral = LateralMover()
        network_map = lateral.discover_network_segments()

        stolen_hashes = self._derive_stolen_hashes(privilege_escalation)

        pth_results = []
        for stolen_hash in stolen_hashes:
            for target_host in self._derive_target_hosts(network_map):
                pth_results.append(
                    lateral.pass_the_hash_lateral(
                        {
                            "nt_hash": stolen_hash["hash"],
                            "target_ip": target_host,
                            "target_user": stolen_hash["username"],
                        }
                    )
                )

        result = {
            "network_map": network_map,
            "stolen_hashes": stolen_hashes,
            "pass_the_hash_results": pth_results,
            "technique": "Pass-the-Hash",
            "success": any(r["success"] for r in pth_results),
        }
        return enrich_with_exploit_intel(
            "lateral-movement",
            result,
            search_terms=["lateral movement", "pass-the-hash", config.target_domain],
            platform="windows",
            include_payloads=True,
        )

    def _simulate_command_control(self, config: CampaignConfig) -> Dict[str, Any]:
        """Simulate command and control phase."""
        from .command_control import C2Communicator

        c2_communicator = C2Communicator()
        beacon_results = c2_communicator.send_beacon(
            {"hostname": "compromised-host", "ip": config.target_ip}
        )

        result = {
            "technique": "Advanced C2 Communication",
            "beacon_results": beacon_results,
            "channels": ["HTTPS", "DNS"],
            "success": beacon_results.get("status") == "Sent",
        }
        return enrich_with_exploit_intel(
            "command-control",
            result,
            search_terms=["c2", "beacon", "dns tunneling"],
            platform=None,
            include_payloads=True,
        )

    def _simulate_exfiltration(self) -> Dict[str, Any]:
        """Simulate exfiltration phase."""
        discovery = self._exfiltrator.find_sensitive_data()
        strategy = self._exfiltrator.generate_exfiltration_strategy(discovery)
        exfil_results = self._exfiltrator.slow_exfiltrate(
            discovery["files_discovered"][0]
        ) if discovery.get("files_discovered") else {"success": False}

        result = {
            "discovery": discovery,
            "strategy": strategy,
            "exfil_results": exfil_results,
            "technique": "Slow Drip Exfiltration",
            "success": exfil_results.get("successful_chunks", 0) > 0,
        }
        return enrich_with_exploit_intel(
            "exfiltration",
            result,
            search_terms=["data exfiltration", "dns tunneling", "steganography"],
            platform="windows",
            include_payloads=True,
        )

    # ------------------------------------------------------------------
    # Helpers

    def _derive_stolen_hashes(self, privilege_escalation: Dict[str, Any]) -> List[Dict[str, str]]:
        """Derive stolen hashes from the privilege escalation phase."""
        hashes = []
        kerberos_attacks = privilege_escalation.get("active_directory", {}).get("kerberos_attacks", {})
        
        # Extract hashes from kerberos attack results
        kerberos_results = kerberos_attacks.get("kerberos_attack_results", {})
        for attack_name, attack_result in kerberos_results.items():
            if attack_result.get("success") and attack_result.get("hashes"):
                hashes.extend(attack_result["hashes"])
        
        # If no hashes found, return some mock hashes for testing
        if not hashes:
            hashes = [{"username": "svc_sql", "hash": "aad3b435b51404eeaad3b435b51404ee:e19ccf75ee54e06b06a5907af13cef42"}]
        
        return hashes

    def _derive_target_hosts(self, network_map: Dict[str, Any]) -> List[str]:
        """Derive target hosts from the network map."""
        hosts = []
        for segment in network_map.get("discovered_segments", []):
            try:
                net = ipaddress.ip_network(segment["segment"])
                for i, host in enumerate(net.hosts()):
                    if i > 5:  # Limit to 5 hosts per segment
                        break
                    hosts.append(str(host))
            except ValueError:
                continue
        return hosts

    def _build_timeline(self, *phases: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build a campaign timeline from phase results."""
        timeline = []
        phase_names = [
            "Initial Access", "Persistence", "Privilege Escalation",
            "Defense Evasion", "Lateral Movement", "Command & Control",
            "Exfiltration"
        ]
        
        for i, (phase_name, phase_data) in enumerate(zip(phase_names, phases)):
            timeline.append({
                "phase": phase_name,
                "order": i + 1,
                "status": "Completed",
                "success": phase_data.get("success", True),
                "summary": phase_data.get("description", f"Completed {phase_name} phase")
            })
        
        return timeline

    def _summarize_takeaways(
        self,
        initial_access: Dict[str, Any],
        persistence: Dict[str, Any],
        privilege_escalation: Dict[str, Any],
        lateral_movement: Dict[str, Any],
        exfiltration: Dict[str, Any],
    ) -> List[str]:
        """Summarize key campaign takeaways."""
        takeaways = []

        if initial_access.get("success"):
            takeaways.append(
                f"Initial access was successful using '{initial_access.get('technique')}' against '{initial_access.get('target_email')}'"
            )

        if persistence.get("success"):
            takeaways.append(
                f"Persistence was established using '{persistence.get('technique')}' with {len(persistence.get('mechanisms', []))} mechanisms."
            )

        if privilege_escalation.get("success"):
            takeaways.append(
                f"Privilege escalation succeeded, with {len(privilege_escalation.get('active_directory', {}).get('vulnerabilities', []))} vulnerabilities found."
            )

        if lateral_movement.get("success"):
            successful_pth = [r for r in lateral_movement.get("pass_the_hash_results", []) if r.get("success")]
            takeaways.append(
                f"Lateral movement was successful to {len(successful_pth)} hosts via Pass-the-Hash."
            )

        if exfiltration.get("success"):
            takeaways.append(
                f"Data exfiltration was successful using '{exfiltration.get('technique')}' via '{exfiltration.get('strategy', {}).get('method')}'"
            )

        if not takeaways:
            return [
                "Campaign simulation completed, but no definitive success or failure takeaways were generated."
            ]

        return takeaways


def simulate_campaign(config: Optional[CampaignConfig] = None) -> Dict[str, Any]:
    """Convenience function to run a campaign simulation."""
    simulator = APTCampaignSimulator()
    return simulator.simulate(config)