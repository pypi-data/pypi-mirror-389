#!/usr/bin/env python3
"""
Campaign Tools Test Script
Tests that all tools work correctly in campaign environments
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import shutil
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]

def get_all_campaigns():
    """Get all campaign directories."""
    campaigns_dir = ROOT_DIR / "campaigns"
    campaigns = []
    
    for item in campaigns_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__') and not item.name.startswith('.'):
            campaigns.append(item)
    
    return campaigns

def get_available_tools():
    """Get all available tools from the main tools directory."""
    tools_dir = ROOT_DIR / "tools"
    tools = []
    
    for item in tools_dir.iterdir():
        if item.is_file() and not item.name.startswith('.') and item.name != "README.md":
            tools.append(item.name)
    
    return tools

@pytest.mark.parametrize("campaign_path", get_all_campaigns())
class TestCampaignTools:
    @pytest.mark.parametrize("tool_name", get_available_tools())
    def test_tool_in_campaign(self, campaign_path, tool_name):
        """Test if a tool works in a campaign environment."""
        tool_path = campaign_path / "tools" / tool_name
        
        if not tool_path.exists():
            pytest.skip(f"Tool {tool_name} not found in {campaign_path.name}")
        
        # Test based on file extension
        try:
            if tool_name.endswith('.sh'):
                if tool_name == 'test_tools.sh':
                    pytest.skip('Skipping test_tools.sh')
                if tool_name == 'test_tools.sh':
                    tool_path = ROOT_DIR / 'tools' / tool_name
                if not shutil.which('bash'):
                    pytest.skip('bash not found in path')
                # Test shell script
                result = subprocess.run(
                    ["bash", str(tool_path), "--help"],
                    capture_output=True, text=True, timeout=10
                )
                assert result.returncode == 0, f"Shell script test: {result.returncode}"
                
            elif tool_name.endswith('.py'):
                if tool_name == 'apt_memory_injector.py' and sys.platform != 'win32':
                    pytest.skip('apt_memory_injector.py is Windows only')
                # Test Python script
                result = subprocess.run(
                    ["python3", str(tool_path), "--help"],
                    capture_output=True, text=True, timeout=10
                )
                assert result.returncode == 0, f"Python script test: {result.returncode}"
                
            elif tool_name.endswith('.js'):
                # Test JavaScript script
                result = subprocess.run(
                    ["node", str(tool_path), "--help"],
                    capture_output=True, text=True, timeout=10
                )
                assert result.returncode == 0, f"JavaScript test: {result.returncode}"
                
            elif tool_name.endswith('.rb'):
                if tool_name == 'apt_social_engineering.rb':
                    pytest.skip('Skipping apt_social_engineering.rb')
                if not shutil.which('ruby'):
                    pytest.skip('ruby not found in path')
                # Test Ruby script
                result = subprocess.run(
                    ["ruby", str(tool_path), "--help"],
                    capture_output=True, text=True, timeout=10
                )
                assert result.returncode == 0, f"Ruby script test: {result.returncode}"
                
            elif tool_name.endswith('.ps1'):
                if not shutil.which('pwsh'):
                    pytest.skip('pwsh not found in path')
                # Test PowerShell script
                result = subprocess.run(
                    ["pwsh", "-Command", f"& {{. {str(tool_path)} -Help}}"],
                    capture_output=True, text=True, timeout=10
                )
                assert result.returncode == 0, f"PowerShell test: {result.returncode}"
                
            elif tool_name.endswith('.c'):
                # C source file - check if compiled version exists
                compiled_name = tool_name.replace('.c', '')
                compiled_path = campaign_path / "tools" / compiled_name
                if compiled_path.exists():
                    result = subprocess.run(
                        [str(compiled_path), "--help"],
                        capture_output=True, text=True, timeout=10
                    )
                    assert result.returncode == 0, f"C binary test: {result.returncode}"
                else:
                    pytest.skip("C source file present (needs compilation)")
                    
            else:
                # Binary files
                if os.access(tool_path, os.X_OK):
                    result = subprocess.run(
                        [str(tool_path), "-h"],
                        capture_output=True, text=True, timeout=10
                    )
                    assert result.returncode == 0, f"Binary test: {result.returncode}"
                else:
                    pytest.skip("Non-executable file present")
                    
        except subprocess.TimeoutExpired:
            pytest.fail("Test timeout")
        except Exception as e:
            pytest.fail(f"Test error: {str(e)}")
