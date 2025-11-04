"""Hardware Disruption Module for APT Toolkit."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

# Import hardware disruption tools
from .hardware_disruption_tools.gps_jammer import generate_gps_jamming_signal
from .hardware_disruption_tools.drone_hijacker import hijack_drone
from .hardware_disruption_tools.power_grid_disruption_tool import disrupt_power_grid
from .hardware_disruption_tools.radar_jammer import jam_radar
from .hardware_disruption_tools.radio_jammer import jam_radio
from .hardware_disruption_tools.satellite_disruption_tool import disrupt_satellite
from .hardware_disruption_tools.naval_vessel_disruption_tool import disrupt_naval_vessel
from .hardware_disruption_tools.military_vehicle_disruption_tool import disrupt_military_vehicle
from .hardware_disruption_tools.water_supply_disruption_tool import disrupt_water_supply
from .hardware_disruption_tools.logistics_disruption_tool import disrupt_logistics


class HardwareDisruptionEngine:
    """Advanced hardware disruption engine for military and infrastructure targets."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the hardware disruption engine."""
        if seed is not None:
            random.seed(seed)
        
        # Available disruption tools
        self.disruption_tools = {
            "gps_jammer": "GPS signal disruption",
            "drone_hijacker": "Military drone takeover",
            "power_grid_disruption": "Power grid disruption",
            "radar_jammer": "Radar system jamming",
            "radio_jammer": "Radio communication jamming",
            "satellite_disruption": "Satellite communication disruption",
            "naval_vessel_disruption": "Naval vessel system disruption",
            "military_vehicle_disruption": "Military vehicle disruption",
            "water_supply_disruption": "Water supply system disruption",
            "logistics_disruption": "Military logistics disruption"
        }
        
        # Target types
        self.target_types = {
            "military_bases": ["gps_jammer", "radar_jammer", "radio_jammer", "drone_hijacker"],
            "naval_facilities": ["naval_vessel_disruption", "satellite_disruption", "gps_jammer"],
            "power_infrastructure": ["power_grid_disruption"],
            "water_systems": ["water_supply_disruption"],
            "logistics_networks": ["logistics_disruption"],
            "military_vehicles": ["military_vehicle_disruption", "gps_jammer"]
        }

    def _get_tool_function(self, tool_name: str):
        """Get the function for a specific disruption tool."""
        tool_mapping = {
            "gps_jammer": generate_gps_jamming_signal,
            "drone_hijacker": hijack_drone,
            "power_grid_disruption": disrupt_power_grid,
            "radar_jammer": jam_radar,
            "radio_jammer": jam_radio,
            "satellite_disruption": disrupt_satellite,
            "naval_vessel_disruption": disrupt_naval_vessel,
            "military_vehicle_disruption": disrupt_military_vehicle,
            "water_supply_disruption": disrupt_water_supply,
            "logistics_disruption": disrupt_logistics
        }
        return tool_mapping.get(tool_name)

    def _generate_target_ip(self, target_type: str) -> str:
        """Generate a realistic target IP based on target type."""
        ip_ranges = {
            "military_bases": ["192.168.1.", "10.10.", "172.16."],
            "naval_facilities": ["192.168.2.", "10.20.", "172.17."],
            "power_infrastructure": ["192.168.3.", "10.30.", "172.18."],
            "water_systems": ["192.168.4.", "10.40.", "172.19."],
            "logistics_networks": ["192.168.5.", "10.50.", "172.20."],
            "military_vehicles": ["192.168.6.", "10.60.", "172.21."]
        }
        
        base_ip = random.choice(ip_ranges.get(target_type, ["192.168.1."]))
        return f"{base_ip}{random.randint(1, 254)}"

    def _assess_impact_level(self, tool_name: str) -> str:
        """Assess the impact level of a disruption tool."""
        impact_levels = {
            "gps_jammer": "HIGH",
            "drone_hijacker": "CRITICAL",
            "power_grid_disruption": "CRITICAL",
            "radar_jammer": "HIGH",
            "radio_jammer": "MEDIUM",
            "satellite_disruption": "CRITICAL",
            "naval_vessel_disruption": "HIGH",
            "military_vehicle_disruption": "MEDIUM",
            "water_supply_disruption": "HIGH",
            "logistics_disruption": "MEDIUM"
        }
        return impact_levels.get(tool_name, "MEDIUM")

    def _get_detection_likelihood(self, tool_name: str) -> str:
        """Get detection likelihood for a disruption tool."""
        detection_levels = {
            "gps_jammer": "LOW",
            "drone_hijacker": "HIGH",
            "power_grid_disruption": "HIGH",
            "radar_jammer": "MEDIUM",
            "radio_jammer": "LOW",
            "satellite_disruption": "HIGH",
            "naval_vessel_disruption": "HIGH",
            "military_vehicle_disruption": "MEDIUM",
            "water_supply_disruption": "HIGH",
            "logistics_disruption": "MEDIUM"
        }
        return detection_levels.get(tool_name, "MEDIUM")

    def execute_disruption(self, tool_name: str, target_ip: str = None) -> Dict[str, Any]:
        """Execute a specific disruption tool."""
        if tool_name not in self.disruption_tools:
            return {"error": f"Unknown disruption tool: {tool_name}"}

        tool_function = self._get_tool_function(tool_name)
        if not tool_function:
            return {"error": f"Tool function not found: {tool_name}"}

        try:
            # Tools that require target IP
            if tool_name in ["drone_hijacker", "power_grid_disruption", "satellite_disruption",
                            "naval_vessel_disruption", "military_vehicle_disruption",
                            "water_supply_disruption", "logistics_disruption"]:
                if not target_ip:
                    if tool_name == "drone_hijacker":
                        target_ip = "127.0.0.1"
                    else:
                        target_ip = self._generate_target_ip("military_bases")
                result = tool_function(target_ip)
            else:
                # Tools that don't require target IP
                result = tool_function()

            # Convert numpy arrays to lists for JSON serialization
            if hasattr(result, 'tolist'):
                result = result.tolist()
            elif hasattr(result, 'shape'):  # numpy array
                result = result.tolist()

            return {
                "tool": tool_name,
                "description": self.disruption_tools[tool_name],
                "target_ip": target_ip,
                "result": "Signal generated successfully" if result is not None else "Operation completed",
                "impact_level": self._assess_impact_level(tool_name),
                "detection_likelihood": self._get_detection_likelihood(tool_name),
                "status": "SUCCESS"
            }

        except Exception as e:
            return {
                "tool": tool_name,
                "description": self.disruption_tools[tool_name],
                "target_ip": target_ip,
                "error": str(e),
                "status": "FAILED"
            }

    def analyze_target_type(self, target_type: str) -> Dict[str, Any]:
        """Analyze disruption capabilities for a specific target type."""
        if target_type not in self.target_types:
            return {"error": f"Unknown target type: {target_type}"}

        available_tools = self.target_types[target_type]

        analysis = {
            "target_type": target_type,
            "available_tools": [],
            "recommended_approach": self._get_recommended_approach(target_type),
            "estimated_success_rate": self._estimate_success_rate(target_type),
            "risk_assessment": self._assess_risk_level(target_type)
        }

        for tool_name in available_tools:
            analysis["available_tools"].append({
                "tool": tool_name,
                "description": self.disruption_tools[tool_name],
                "impact_level": self._assess_impact_level(tool_name),
                "detection_likelihood": self._get_detection_likelihood(tool_name)
            })

        return analysis

    def _get_recommended_approach(self, target_type: str) -> str:
        """Get recommended approach for a target type."""
        approaches = {
            "military_bases": "Focus on communication disruption and drone takeover",
            "naval_facilities": "Target vessel systems and satellite communications",
            "power_infrastructure": "Direct grid disruption for maximum impact",
            "water_systems": "Supply disruption affecting military operations",
            "logistics_networks": "Disrupt supply chains and transportation",
            "military_vehicles": "GPS disruption and vehicle system interference"
        }
        return approaches.get(target_type, "Standard disruption approach")

    def _estimate_success_rate(self, target_type: str) -> str:
        """Estimate success rate for a target type."""
        success_rates = {
            "military_bases": "60-80%",
            "naval_facilities": "40-60%",
            "power_infrastructure": "70-90%",
            "water_systems": "80-95%",
            "logistics_networks": "50-70%",
            "military_vehicles": "30-50%"
        }
        return success_rates.get(target_type, "50-70%")

    def _assess_risk_level(self, target_type: str) -> str:
        """Assess risk level for a target type."""
        risk_levels = {
            "military_bases": "HIGH",
            "naval_facilities": "VERY_HIGH",
            "power_infrastructure": "CRITICAL",
            "water_systems": "HIGH",
            "logistics_networks": "MEDIUM",
            "military_vehicles": "MEDIUM"
        }
        return risk_levels.get(target_type, "MEDIUM")

    def get_all_tools(self) -> Dict[str, Any]:
        """Get information about all available disruption tools."""
        tools_info = []
        
        for tool_name, description in self.disruption_tools.items():
            tools_info.append({
                "tool": tool_name,
                "description": description,
                "impact_level": self._assess_impact_level(tool_name),
                "detection_likelihood": self._get_detection_likelihood(tool_name),
                "target_types": [ttype for ttype, tools in self.target_types.items() 
                                if tool_name in tools]
            })
        
        return {
            "total_tools": len(self.disruption_tools),
            "tools": tools_info,
            "target_types": list(self.target_types.keys())
        }


def analyze_hardware_disruption(target_type: str = None, tool_name: str = None, 
                               seed: Optional[int] = None) -> Dict[str, Any]:
    """Analyze hardware disruption capabilities.
    
    Args:
        target_type: Specific target type to analyze
        tool_name: Specific tool to execute
        seed: Optional seed for deterministic output
        
    Returns:
        Dictionary containing hardware disruption analysis
    """
    engine = HardwareDisruptionEngine(seed)
    
    if tool_name:
        return {"disruption_execution": engine.execute_disruption(tool_name)}
    elif target_type:
        return {"target_analysis": engine.analyze_target_type(target_type)}
    else:
        return {"hardware_disruption_overview": engine.get_all_tools()}


__all__ = ["HardwareDisruptionEngine", "analyze_hardware_disruption"]
