#!/usr/bin/env python3
"""
Campaign Tools Management Script
Ensures all campaigns have access to all available tools
"""

import os
import sys
import shutil
import stat
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS_DIR = PROJECT_ROOT / "campaigns"
TOOLS_DIR = PROJECT_ROOT / "tools"


def get_all_campaigns():
    """Get all campaign directories."""
    campaigns_dir = CAMPAIGNS_DIR
    campaigns = []
    
    for item in campaigns_dir.iterdir():
        if item.is_dir() and not item.name.startswith('__') and not item.name.startswith('.'):
            campaigns.append(item)
    
    return campaigns

def get_available_tools():
    """Get all available tools from the main tools directory."""
    tools_dir = TOOLS_DIR
    tools = []
    
    for item in tools_dir.iterdir():
        if item.is_file() and not item.name.startswith('.') and item.name != "README.md":
            tools.append(item.name)
    
    return tools

def ensure_campaign_tools_directory(campaign_path):
    """Ensure campaign has a tools directory."""
    tools_dir = campaign_path / "tools"
    tools_dir.mkdir(exist_ok=True)
    return tools_dir

def copy_tool_to_campaign(source_tool, campaign_tools_dir):
    """Copy a tool to campaign tools directory."""
    target_path = campaign_tools_dir / source_tool.name
    
    # Skip if already exists and is up to date
    if target_path.exists():
        source_mtime = source_tool.stat().st_mtime
        target_mtime = target_path.stat().st_mtime
        if source_mtime <= target_mtime:
            return False
    
    # Copy the tool
    shutil.copy2(source_tool, target_path)
    
    # Make executable if it's a script
    if source_tool.suffix in ['.sh', '.py', '.rb', '.js']:
        target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC)
    
    return True

def create_tool_symlink(source_tool, campaign_tools_dir):
    """Create a symbolic link to the tool using absolute path."""
    target_path = campaign_tools_dir / source_tool.name
    
    # Check if symlink already exists and points to correct location
    if target_path.exists():
        if target_path.is_symlink():
            try:
                current_target = target_path.resolve()
                expected_target = source_tool.resolve()
                if current_target == expected_target:
                    return False  # Already correctly linked
            except (FileNotFoundError, RuntimeError):
                # Symlink is broken, remove it
                pass
        
        # Remove existing file/link
        target_path.unlink()
    
    # Create symbolic link with absolute path
    absolute_source = source_tool.resolve()
    target_path.symlink_to(absolute_source)
    return True

def get_campaign_specific_tools(campaign_path):
    """Get campaign-specific tools that should be preserved."""
    tools_dir = campaign_path / "tools"
    if not tools_dir.exists():
        return []
    
    campaign_tools = []
    for item in tools_dir.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            # Only consider it campaign-specific if it's not a symlink
            if not item.is_symlink():
                campaign_tools.append(item.name)
    
    return campaign_tools

def main():
    """Main function to ensure all campaigns have full tools."""
    print("[*] Starting campaign tools management...")
    
    # Get all campaigns and available tools
    campaigns = get_all_campaigns()
    available_tools = get_available_tools()
    
    print(f"[*] Found {len(campaigns)} campaigns")
    print(f"[*] Available tools: {', '.join(available_tools)}")
    
    # Strategy: Use symbolic links for efficiency
    use_symlinks = True
    
    for campaign in campaigns:
        print(f"\n[*] Processing campaign: {campaign.name}")
        
        # Ensure tools directory exists
        campaign_tools_dir = ensure_campaign_tools_directory(campaign)
        
        # Get campaign-specific tools
        campaign_specific_tools = get_campaign_specific_tools(campaign)
        print(f"    Campaign-specific tools: {campaign_specific_tools}")
        
        # Process each available tool
        tools_added = 0
        tools_updated = 0
        
        for tool_name in available_tools:
            source_tool = Path("tools") / tool_name
            
            # Skip if it's a campaign-specific tool (preserve custom implementations)
            if tool_name in campaign_specific_tools:
                print(f"    Preserving campaign-specific tool: {tool_name}")
                continue
            
            if use_symlinks:
                # Create symbolic link
                if create_tool_symlink(source_tool, campaign_tools_dir):
                    tools_added += 1
            else:
                # Copy tool
                if copy_tool_to_campaign(source_tool, campaign_tools_dir):
                    tools_added += 1
        
        print(f"    Tools {'linked' if use_symlinks else 'copied'}: {tools_added}")
    
    print(f"\n[*] Campaign tools management completed!")
    print(f"[*] Total campaigns processed: {len(campaigns)}")
    print(f"[*] Strategy: {'Symbolic links' if use_symlinks else 'File copies'}")
    print(f"\n[*] Next steps:")
    print(f"    1. Run 'python scripts/ensure_campaign_tools.py' to update tools")
    print(f"    2. Tools are now available in each campaign's tools/ directory")
    print(f"    3. Campaign-specific tools are preserved")

if __name__ == "__main__":
    main()
