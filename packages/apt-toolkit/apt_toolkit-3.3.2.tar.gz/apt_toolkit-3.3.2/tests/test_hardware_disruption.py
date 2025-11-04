"""Tests for hardware disruption tools."""

import unittest
from unittest.mock import patch, MagicMock

# Import hardware disruption tools
from apt_toolkit.hardware_disruption_tools.gps_jammer import generate_gps_jamming_signal
from apt_toolkit.hardware_disruption_tools.drone_hijacker import hijack_drone
from apt_toolkit.hardware_disruption_tools.power_grid_disruption_tool import disrupt_power_grid
from apt_toolkit.hardware_disruption_tools.radar_jammer import jam_radar
from apt_toolkit.hardware_disruption_tools.radio_jammer import jam_radio
from apt_toolkit.hardware_disruption_tools.satellite_disruption_tool import disrupt_satellite
from apt_toolkit.hardware_disruption_tools.naval_vessel_disruption_tool import disrupt_naval_vessel
from apt_toolkit.hardware_disruption_tools.military_vehicle_disruption_tool import disrupt_military_vehicle
from apt_toolkit.hardware_disruption_tools.water_supply_disruption_tool import disrupt_water_supply
from apt_toolkit.hardware_disruption_tools.logistics_disruption_tool import disrupt_logistics


class TestHardwareDisruptionTools(unittest.TestCase):
    """Test hardware disruption tools functionality."""

    def test_gps_jammer_generates_signal(self):
        """Test GPS jamming signal generation."""
        signal = generate_gps_jamming_signal()
        self.assertIsNotNone(signal)

    @patch('apt_toolkit.hardware_disruption_tools.drone_hijacker.socket.socket')
    def test_drone_hijacker_attempts_connection(self, mock_socket):
        """Test drone hijacker connection attempt."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        hijack_drone("192.168.1.100")
        
        mock_socket_instance.connect.assert_called_once_with(("192.168.1.100", 5555))

    @patch('apt_toolkit.hardware_disruption_tools.power_grid_disruption_tool.ModbusTcpClient')
    def test_power_grid_disruption_attempt(self, mock_modbus):
        """Test power grid disruption attempt."""
        mock_client = MagicMock()
        mock_modbus.return_value = mock_client
        
        disrupt_power_grid("192.168.1.200")
        
        mock_modbus.assert_called_once_with("192.168.1.200", port=502)
        mock_client.connect.assert_called_once()

    def test_radar_jammer_functionality(self):
        """Test radar jammer functionality."""
        result = jam_radar()
        self.assertIsNotNone(result)

    def test_radio_jammer_functionality(self):
        """Test radio jammer functionality."""
        result = jam_radio()
        self.assertIsNotNone(result)

    @patch('apt_toolkit.hardware_disruption_tools.satellite_disruption_tool.socket.socket')
    def test_satellite_disruption_functionality(self, mock_socket):
        """Test satellite disruption functionality."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        result = disrupt_satellite("192.168.1.100")
        
        mock_socket_instance.connect.assert_called_once_with(("192.168.1.100", 4000))
        self.assertIsNone(result)

    @patch('apt_toolkit.hardware_disruption_tools.naval_vessel_disruption_tool.socket.socket')
    def test_naval_vessel_disruption_functionality(self, mock_socket):
        """Test naval vessel disruption functionality."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        result = disrupt_naval_vessel("192.168.1.100")
        
        mock_socket_instance.connect.assert_called_once_with(("192.168.1.100", 2000))
        self.assertIsNone(result)

    @patch('apt_toolkit.hardware_disruption_tools.military_vehicle_disruption_tool.socket.socket')
    def test_military_vehicle_disruption_functionality(self, mock_socket):
        """Test military vehicle disruption functionality."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        result = disrupt_military_vehicle("192.168.1.100")
        
        mock_socket_instance.connect.assert_called_once_with(("192.168.1.100", 3000))
        self.assertIsNone(result)

    @patch('apt_toolkit.hardware_disruption_tools.water_supply_disruption_tool.ModbusTcpClient')
    def test_water_supply_disruption_functionality(self, mock_modbus):
        """Test water supply disruption functionality."""
        mock_client = MagicMock()
        mock_modbus.return_value = mock_client
        
        result = disrupt_water_supply("192.168.1.200")
        
        mock_modbus.assert_called_once_with("192.168.1.200", port=502)
        mock_client.connect.assert_called_once()
        self.assertIsNone(result)

    @patch('apt_toolkit.hardware_disruption_tools.logistics_disruption_tool.socket.socket')
    def test_logistics_disruption_functionality(self, mock_socket):
        """Test logistics disruption functionality."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        result = disrupt_logistics("192.168.1.100")
        
        mock_socket_instance.connect.assert_called_once_with(("192.168.1.100", 8000))
        self.assertIsNone(result)


class TestHardwareDisruptionIntegration(unittest.TestCase):
    """Test hardware disruption tools integration."""

    def test_all_tools_importable(self):
        """Test that all hardware disruption tools can be imported."""
        # This test verifies that the imports work correctly
        tools = [
            generate_gps_jamming_signal,
            hijack_drone,
            disrupt_power_grid,
            jam_radar,
            jam_radio,
            disrupt_satellite,
            disrupt_naval_vessel,
            disrupt_military_vehicle,
            disrupt_water_supply,
            disrupt_logistics
        ]
        
        for tool in tools:
            self.assertTrue(callable(tool))


if __name__ == "__main__":
    unittest.main()