#!/usr/bin/env python3
"""
Test Tool Setup Script
Tests that the campaign tools setup is working correctly
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

def test_tool_links():
    """Test that symbolic links are properly set up."""
    print("[*] Testing tool symbolic links...")
    
    # Test a few sample campaigns
    test_campaigns = [
        "campaigns/3d_printing_campaign",
        "campaigns/accounting_firm_campaign", 
        "campaigns/aerospace_company_campaign"
    ]
    
    all_passed = True
    
    for campaign_path in test_campaigns:
        campaign_dir = ROOT_DIR / campaign_path
        print(f"\n[*] Testing campaign: {campaign_dir}")
        
        tools_dir = campaign_dir / "tools"
        if not tools_dir.exists():
            print(f"    [-] Tools directory not found: {tools_dir}")
            all_passed = False
            continue
        
        # Check for expected tools
        expected_tools = [
            "apt_recon.sh",
            "APT-PowerShell-Toolkit.ps1", 
            "apt_persistence.py",
            "apt_network_scanner",
            "apt_web_recon.js",
            "apt_social_engineering.rb"
        ]
        
        for tool in expected_tools:
            tool_path = tools_dir / tool
            if not tool_path.exists():
                print(f"    [-] Tool not found: {tool}")
                all_passed = False
            elif tool_path.is_symlink():
                try:
                    target = tool_path.resolve()
                    if target.exists():
                        print(f"    [+] {tool}: Symlink OK -> {target}")
                    else:
                        print(f"    [-] {tool}: Broken symlink -> {target}")
                        all_passed = False
                except Exception as e:
                    print(f"    [-] {tool}: Symlink error: {e}")
                    all_passed = False
            else:
                print(f"    [+] {tool}: Local file")
    
    return all_passed

def test_campaign_specific_tools():
    """Test that campaign-specific tools are preserved."""
    print("\n[*] Testing campaign-specific tools preservation...")
    
    test_campaigns = {
        ROOT_DIR / "campaigns" / "3d_printing_campaign": ["3d_model_finder.py"],
        ROOT_DIR / "campaigns" / "accounting_firm_campaign": ["financial_record_finder.py"],
        ROOT_DIR / "campaigns" / "aerospace_company_campaign": ["aerospace_design_finder.py"]
    }
    
    all_passed = True
    
    for campaign_dir, expected_tools in test_campaigns.items():
        print(f"\n[*] Testing campaign: {campaign_dir}")
        
        tools_dir = campaign_dir / "tools"
        
        for tool in expected_tools:
            tool_path = tools_dir / tool
            if tool_path.exists() and not tool_path.is_symlink():
                print(f"    [+] Campaign-specific tool preserved: {tool}")
            else:
                print(f"    [-] Campaign-specific tool missing or symlink: {tool}")
                all_passed = False
    
    return all_passed

def test_tool_management_script():
    """Test the tool management script."""
    print("\n[*] Testing tool management script...")
    
    try:
        result = subprocess.run(
            ["python3", str(ROOT_DIR / "scripts" / "ensure_campaign_tools.py")],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            print("    [+] Tool management script runs successfully")
            return True
        else:
            print(f"    [-] Tool management script failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"    [-] Tool management script error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("CAMPAIGN TOOLS SETUP TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Tool Symbolic Links", test_tool_links),
        ("Campaign-Specific Tools", test_campaign_specific_tools),
        ("Tool Management Script", test_tool_management_script)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n[*] Running test: {test_name}")
        print("-" * 40)
        
        try:
            passed = test_func()
            if passed:
                print(f"\n[+] {test_name}: PASSED")
            else:
                print(f"\n[-] {test_name}: FAILED")
                all_passed = False
        except Exception as e:
            print(f"\n[-] {test_name}: ERROR - {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[+] ALL TESTS PASSED - Campaign tools setup is working correctly!")
    else:
        print("[-] SOME TESTS FAILED - Please check the campaign tools setup")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
