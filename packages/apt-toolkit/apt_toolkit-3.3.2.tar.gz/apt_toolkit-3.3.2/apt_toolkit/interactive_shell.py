"""
Interactive shell entry point that consolidates all toolkit features.

Running the module presents an operator-focused shell with rich help and
commands that map to the core capabilities exposed across the package.
"""

from __future__ import annotations

import cmd
import json
import shlex
import textwrap
from copy import deepcopy
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .defense_evasion import DefenseEvader
from .initial_access import SpearPhishingGenerator, deliver_payload, phishing_attack
from .lateral_movement import LateralMover
from .persistence import PersistenceManager
from .privilege_escalation import PrivilegeEscalator
from .settings_manager import (
    get_settings_path,
    load_settings,
    mask_value,
    save_settings,
)


def _format_json(payload: Any) -> str:
    try:
        return json.dumps(payload, indent=2, sort_keys=True, default=str)
    except TypeError:
        return repr(payload)


COMMAND_HELP: Dict[str, Dict[str, Any]] = {
    "configure": {
        "category": "Configuration",
        "summary": "Interactively set the DeepSeek API key and SMTP delivery profile.",
        "usage": [
            "configure",
            "Follow the prompts. Press Enter to keep the current value for any field.",
        ],
        "details": textwrap.dedent(
            """
            This command updates the toolkit configuration that is stored in
            ``config/user_settings.json`` (ignored by git). You will be asked
            for:
              • DeepSeek API key (optional but required for AI-assisted content).
              • SMTP server, port, username, and password used for email delivery.
            The information persists across shell launches and is masked in
            displays. SMTP credentials are required before sending any emails.
            """
        ).strip(),
    },
    "show_config": {
        "category": "Configuration",
        "summary": "Display the current effective configuration with sensitive values masked.",
        "usage": ["show_config"],
        "details": textwrap.dedent(
            """
            Presents the configuration currently loaded by the shell. Sensitive
            values such as passwords and API keys are masked, but you can verify
            which fields are populated. The output includes the path to the
            persisted configuration file.
            """
        ).strip(),
    },
    "generate_email": {
        "category": "Initial Access",
        "summary": "Generate a spear-phishing email with optional domain targeting.",
        "usage": [
            "generate_email",
            "generate_email dod.mil",
        ],
        "details": textwrap.dedent(
            """
            Creates a realistic spear-phishing lure and stores it as the active
            email in the session. You can provide a domain (with or without '@')
            to bias the targeting dataset. The generated email includes subject,
            body, metadata, and an on-disk payload path when attachments are
            requested.
            """
        ).strip(),
    },
    "send_email": {
        "category": "Initial Access",
        "summary": "Deliver a payload to a target email address using the configured SMTP profile.",
        "usage": [
            "send_email target@example.com",
            "send_email  # sends to the last generated email's target",
        ],
        "details": textwrap.dedent(
            """
            Sends the currently generated spear-phishing email (or creates a new
            one) to the specified recipient. The command enforces a minimum delay
            of three seconds between SMTP transmissions to respect the global
            rate limit. Ensure the SMTP settings are configured first.
            """
        ).strip(),
    },
    "phishing_attack": {
        "category": "Initial Access",
        "summary": "Send phishing emails to every address listed in a file.",
        "usage": ["phishing_attack path/to/targets.txt"],
        "details": textwrap.dedent(
            """
            Reads targets from the provided file (one email per line) and sends a
            unique payload to each recipient. The routine respects the email rate
            limiter, so large target lists will progress slowly by design.
            """
        ).strip(),
    },
    "lateral_discover": {
        "category": "Lateral Movement",
        "summary": "Simulate discovery of network subnets within a compromised environment.",
        "usage": ["lateral_discover"],
        "details": textwrap.dedent(
            """
            Executes conceptual reconnaissance to enumerate promising subnets,
            returning prioritised ranges and rationale suitable for planning
            lateral movement engagements.
            """
        ).strip(),
    },
    "lateral_pth": {
        "category": "Lateral Movement",
        "summary": "Perform a simulated Pass-the-Hash attempt against a host.",
        "usage": ["lateral_pth 10.0.0.5 admin_user aad3b435b51404eeaad3b435b51404ee"],
        "details": textwrap.dedent(
            """
            Evaluates the likelihood of success for a Pass-the-Hash technique
            using the supplied target IP, username, and NTLM hash. The command
            returns success/failure indicators along with next steps or failure
            analysis.
            """
        ).strip(),
    },
    "lateral_deploy": {
        "category": "Lateral Movement",
        "summary": "Model the deployment of an implant on a target endpoint.",
        "usage": [
            "lateral_deploy 10.0.0.5",
            "lateral_deploy 10.0.0.5 keylogger",
        ],
        "details": textwrap.dedent(
            """
            Provides tradecraft guidance for dropping beacons, keyloggers, or
            reconnaissance implants on a compromised system. Choose the implant
            type to receive tailored persistence and detection expectations.
            """
        ).strip(),
    },
    "defense_lotl": {
        "category": "Defense Evasion",
        "summary": "Generate Living-Off-The-Land command sequences.",
        "usage": ["defense_lotl"],
        "details": textwrap.dedent(
            """
            Lists curated LOTL commands for download, execution, and intelligence
            gathering phases. Use this to plan evasive techniques that blend in
            with administrative activity.
            """
        ).strip(),
    },
    "defense_lotl_detection": {
        "category": "Defense Evasion",
        "summary": "Review detection considerations for LOTL tooling.",
        "usage": ["defense_lotl_detection"],
        "details": textwrap.dedent(
            """
            Summarises common LOTL tools, detection difficulty, and defensive
            monitoring recommendations to support adversary simulation reports.
            """
        ).strip(),
    },
    "defense_process_hollowing": {
        "category": "Defense Evasion",
        "summary": "Analyse process hollowing tradecraft and detection cues.",
        "usage": ["defense_process_hollowing"],
        "details": textwrap.dedent(
            """
            Produces an in-depth overview of process hollowing, including
            targeted processes, behavioural indicators, and defensive counter
            measures.
            """
        ).strip(),
    },
    "privilege_ad_enum": {
        "category": "Privilege Escalation",
        "summary": "Enumerate high-value Active Directory groups and targets.",
        "usage": ["privilege_ad_enum"],
        "details": textwrap.dedent(
            """
            Simulates enumeration of critical AD groups and surfaces recommended
            escalation targets with associated techniques.
            """
        ).strip(),
    },
    "privilege_vuln_scan": {
        "category": "Privilege Escalation",
        "summary": "Inspect a host for high-impact privilege escalation vulnerabilities.",
        "usage": [
            "privilege_vuln_scan",
            "privilege_vuln_scan dc1.dod.mil",
        ],
        "details": textwrap.dedent(
            """
            Returns a vulnerability assessment highlighting exploits with
            available tooling, severity, and prioritised attack paths.
            """
        ).strip(),
    },
    "persistence_task": {
        "category": "Persistence",
        "summary": "Create a simulated scheduled task for long-term access.",
        "usage": [
            "persistence_task",
            "persistence_task \"System Update\" /tmp/payload.ps1",
        ],
        "details": textwrap.dedent(
            """
            Builds a disguised scheduled task (or cron job) configuration. Supply
            a custom task name and payload path to mirror specific objectives.
            """
        ).strip(),
    },
    "persistence_wmi": {
        "category": "Persistence",
        "summary": "Model a WMI event subscription persistence technique.",
        "usage": ["persistence_wmi"],
        "details": textwrap.dedent(
            """
            Outputs the structure of a WMI event subscription used for stealthy
            persistence on Windows targets, including command triggers and
            detection difficulty.
            """
        ).strip(),
    },
    "persistence_registry": {
        "category": "Persistence",
        "summary": "Outline a registry run-key persistence configuration.",
        "usage": ["persistence_registry", "persistence_registry HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"],
        "details": textwrap.dedent(
            """
            Generates parameters for establishing run key persistence, returning
            the exact registry path, value, and payload details.
            """
        ).strip(),
    },
    "persistence_service": {
        "category": "Persistence",
        "summary": "Describe a Windows service-based persistence strategy.",
        "usage": [
            "persistence_service",
            "persistence_service SystemUpdateService",
        ],
        "details": textwrap.dedent(
            """
            Creates a simulated malicious Windows service entry, outlining the
            binary path, start type, and detection considerations.
            """
        ).strip(),
    },
    "help": {
        "category": "Meta",
        "summary": "Show help for all commands or a specific command.",
        "usage": ["help", "help send_email"],
        "details": textwrap.dedent(
            """
            Use ``help <command>`` to read detailed instructions for an
            individual command. Without arguments, the shell groups commands by
            capability area and provides a quick-start guide.
            """
        ).strip(),
    },
    "exit": {
        "category": "Meta",
        "summary": "Exit the shell (aliases: quit, Ctrl-D, Ctrl-C).",
        "usage": ["exit"],
        "details": "Terminates the interactive session.",
    },
    "quit": {
        "category": "Meta",
        "summary": "Alias for exit.",
        "usage": ["quit"],
        "details": "Terminates the interactive session.",
    },
}


class AptToolkitShell(cmd.Cmd):
    intro = (
        "Advanced Persistent Threat Toolkit interactive shell. "
        "Type 'help' to explore available capabilities."
    )
    prompt = "apt> "

    def __init__(self) -> None:
        super().__init__()
        self.settings: Dict[str, Any] = load_settings()
        self.email_generator = SpearPhishingGenerator()
        self.lateral_mover = LateralMover()
        self.defense_evader = DefenseEvader()
        self.privilege_escalator = PrivilegeEscalator()
        self.persistence_manager = PersistenceManager()
        self._last_generated_email: Optional[Dict[str, Any]] = None

    # Utility helpers -----------------------------------------------------

    def _persist_settings(self) -> None:
        path = save_settings(self.settings)
        print(f"[+] Settings saved to {path}")

    def _require_smtp_config(self) -> Optional[Dict[str, Any]]:
        smtp = self.settings.get("smtp") or {}
        required = {"server", "port", "user", "password"}
        if not all(smtp.get(field) for field in required):
            print("[-] SMTP configuration incomplete. Run 'configure' first.")
            return None
        return smtp

    def _display(self, title: str, payload: Any) -> None:
        print(f"\n=== {title} ===")
        print(_format_json(payload))
        print()

    def _parse_args(self, arg: str) -> List[str]:
        return shlex.split(arg)

    def emptyline(self) -> None:
        # Prevent repeating last command when an empty line is entered.
        pass

    # Configuration commands ---------------------------------------------

    def do_configure(self, arg: str) -> None:
        """Interactively configure persistent settings."""
        print("\nConfigure toolkit settings (press Enter to keep current values).")

        current_api = self.settings.get("DEEPSEEK_API_KEY", "")
        prompt_api = (
            f"DeepSeek API Key [{mask_value(current_api)}]: "
            if current_api
            else "DeepSeek API Key: "
        )
        new_api = getpass(prompt_api)
        if new_api:
            self.settings["DEEPSEEK_API_KEY"] = new_api

        smtp = deepcopy(self.settings.get("smtp") or {})
        smtp["server"] = input(
            f"SMTP Server [{smtp.get('server', '')}]: "
        ).strip() or smtp.get("server")

        port_input = input(f"SMTP Port [{smtp.get('port', '')}]: ").strip()
        if port_input:
            try:
                smtp["port"] = int(port_input)
            except ValueError:
                print("[-] Invalid port. Keeping existing value.")
        elif "port" not in smtp:
            smtp["port"] = None

        smtp["user"] = input(f"SMTP User [{smtp.get('user', '')}]: ").strip() or smtp.get(
            "user"
        )
        password_prompt = (
            f"SMTP Password [{mask_value(smtp.get('password', ''))}]: "
            if smtp.get("password")
            else "SMTP Password: "
        )
        new_password = getpass(password_prompt)
        if new_password:
            smtp["password"] = new_password

        self.settings["smtp"] = smtp
        self._persist_settings()

    def do_show_config(self, arg: str) -> None:
        """Display the current configuration with masked secrets."""
        sanitized = deepcopy(self.settings)
        if "DEEPSEEK_API_KEY" in sanitized:
            sanitized["DEEPSEEK_API_KEY"] = mask_value(sanitized["DEEPSEEK_API_KEY"])
        if "smtp" in sanitized:
            smtp = dict(sanitized["smtp"])
            if smtp.get("password"):
                smtp["password"] = mask_value(smtp["password"])
            sanitized["smtp"] = smtp

        config_path = get_settings_path()
        self._display(f"Configuration ({config_path})", sanitized)

    # Initial access commands --------------------------------------------

    def do_generate_email(self, arg: str) -> None:
        """Generate a spear-phishing email."""
        domain = arg.strip() or None
        email = self.email_generator.generate_email(
            target_domain=domain, include_payload=True
        )
        self._last_generated_email = email
        self._display("Generated Email", email)

    def do_send_email(self, arg: str) -> None:
        """Send a spear-phishing email to a target."""
        args = self._parse_args(arg)
        target = args[0] if args else None

        if not target:
            if self._last_generated_email:
                target = self._last_generated_email.get("target_email")
                print(f"[i] No target provided; using {target} from last generation.")
            else:
                print("[-] Usage: send_email target@example.com")
                return

        smtp = self._require_smtp_config()
        if not smtp:
            return

        result = deliver_payload(target, smtp)
        self._display("Email Delivery", result)

    def do_phishing_attack(self, arg: str) -> None:
        """Send phishing emails to a list of targets."""
        args = self._parse_args(arg)
        if not args:
            print("[-] Usage: phishing_attack /path/to/targets.txt")
            return

        smtp = self._require_smtp_config()
        if not smtp:
            return

        path = Path(args[0]).expanduser()
        if not path.exists():
            print(f"[-] Target list not found: {path}")
            return

        result = phishing_attack(str(path), smtp)
        self._display("Phishing Campaign Summary", result)

    # Lateral movement commands ------------------------------------------

    def do_lateral_discover(self, arg: str) -> None:
        """Discover potential lateral movement segments."""
        result = self.lateral_mover.discover_network_segments()
        self._display("Lateral Movement - Discovery", result)

    def do_lateral_pth(self, arg: str) -> None:
        """Simulate Pass-the-Hash against a target."""
        args = self._parse_args(arg)
        if len(args) != 3:
            print("[-] Usage: lateral_pth <target_ip> <username> <ntlm_hash>")
            return

        target_ip, username, ntlm_hash = args
        # Update mover's stolen hashes context for realism
        self.lateral_mover.stolen_hashes = [{"username": username, "hash": ntlm_hash}]
        result = self.lateral_mover.pass_the_hash_lateral(target_ip, username, ntlm_hash)
        self._display("Lateral Movement - Pass-the-Hash", result)

    def do_lateral_deploy(self, arg: str) -> None:
        """Deploy a simulated implant on a host."""
        args = self._parse_args(arg)
        if not args:
            print("[-] Usage: lateral_deploy <target_ip> [implant_type]")
            return

        target_ip = args[0]
        implant_type = args[1] if len(args) > 1 else "beacon"
        result = self.lateral_mover.deploy_implant(target_ip, implant_type)
        self._display("Lateral Movement - Implant Deployment", result)

    # Defense evasion commands -------------------------------------------

    def do_defense_lotl(self, arg: str) -> None:
        """Generate Living-Off-The-Land commands."""
        result = self.defense_evader.generate_lotl_commands()
        self._display("Defense Evasion - LOTL Commands", result)

    def do_defense_lotl_detection(self, arg: str) -> None:
        """Summarise LOTL detection strategies."""
        result = self.defense_evader.analyze_lotl_detection()
        self._display("Defense Evasion - LOTL Detection", result)

    def do_defense_process_hollowing(self, arg: str) -> None:
        """Analyse process hollowing behaviour."""
        result = self.defense_evader.process_hollowing_analysis()
        self._display("Defense Evasion - Process Hollowing", result)

    # Privilege escalation commands --------------------------------------

    def do_privilege_ad_enum(self, arg: str) -> None:
        """Enumerate Active Directory privileges."""
        result = self.privilege_escalator.enumerate_ad_privileges()
        self._display("Privilege Escalation - AD Enumeration", result)

    def do_privilege_vuln_scan(self, arg: str) -> None:
        """Analyse privilege escalation vulnerabilities."""
        args = self._parse_args(arg)
        target = args[0] if args else "dc1.dod.mil"
        result = self.privilege_escalator.check_vulnerabilities(target_system=target)
        self._display("Privilege Escalation - Vulnerability Scan", result)

    # Persistence commands ------------------------------------------------

    def do_persistence_task(self, arg: str) -> None:
        """Create a scheduled persistence task."""
        args = self._parse_args(arg)
        task_name = args[0] if args else None
        payload_path = args[1] if len(args) > 1 else None
        result = self.persistence_manager.create_scheduled_task(
            task_name=task_name, payload_path=payload_path
        )
        self._display("Persistence - Scheduled Task", result)

    def do_persistence_wmi(self, arg: str) -> None:
        """Create a WMI event subscription for persistence."""
        result = self.persistence_manager.create_wmi_event_subscription()
        self._display("Persistence - WMI Subscription", result)

    def do_persistence_registry(self, arg: str) -> None:
        """Create registry-based persistence."""
        args = self._parse_args(arg)
        registry_key = args[0] if args else None
        result = self.persistence_manager.create_registry_persistence(
            registry_key=registry_key
        )
        self._display("Persistence - Registry Run Key", result)

    def do_persistence_service(self, arg: str) -> None:
        """Create service-based persistence."""
        args = self._parse_args(arg)
        service_name = args[0] if args else None
        result = self.persistence_manager.create_service_persistence(
            service_name=service_name
        )
        self._display("Persistence - Service Persistence", result)

    # Meta commands -------------------------------------------------------

    def do_exit(self, arg: str) -> bool:
        """Exit the shell."""
        print("Exiting APT Toolkit shell.")
        return True

    def do_quit(self, arg: str) -> bool:
        """Alias for exit."""
        return self.do_exit(arg)

    def do_help(self, arg: str) -> None:
        """Custom help output with extensive usage guidance."""
        topic = arg.strip()
        if topic:
            entry = COMMAND_HELP.get(topic)
            if not entry:
                print(f"No help available for '{topic}'.")
                return
            print(f"\n{topic} — {entry['summary']}")
            for line in entry.get("details", "").splitlines():
                print(line)
            usage = entry.get("usage")
            if usage:
                print("\nUsage examples:")
                for example in usage:
                    print(f"  {example}")
            print()
            return

        print("\nAPT Toolkit Interactive Shell Help\n")
        categories: Dict[str, List[str]] = {}
        for name, info in COMMAND_HELP.items():
            categories.setdefault(info["category"], []).append(name)

        for category, commands in sorted(categories.items()):
            print(f"{category}:")
            for name in sorted(commands):
                summary = COMMAND_HELP[name]["summary"]
                print(f"  {name:<24} {summary}")
            print()
        print("Use 'help <command>' for detailed usage and examples.\n")


def main() -> None:
    """Entry point for launching the interactive shell."""
    shell = AptToolkitShell()
    try:
        shell.cmdloop()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting APT Toolkit shell.")


if __name__ == "__main__":
    main()
