#!/usr/bin/env python3
"""
Script to update Home Assistant YAML syntax changes from versions 2024.8 and 2024.10.

Changes applied:
1. 2024.8: service: -> action:
2. 2024.10: trigger: -> triggers:, condition: -> conditions:, action: -> actions:
3. 2024.10: platform: -> trigger: (in trigger definitions)
"""

import os
import re
import sys
from pathlib import Path

def update_yaml_syntax(file_path):
    """Update YAML syntax in a single file."""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Track changes made
        changes_made = []
        
        # 1. Update service calls to actions (2024.8 change)
        # Match service: followed by optional whitespace and service name
        service_pattern = r'^(\s+)service:\s*(.+)$'
        service_matches = re.findall(service_pattern, content, re.MULTILINE)
        if service_matches:
            content = re.sub(service_pattern, r'\1action: \2', content, flags=re.MULTILINE)
            changes_made.append(f"Updated {len(service_matches)} service calls to actions")
        
        # 2. Update automation structure to use plural keys (2024.10 changes)
        # These need to be at the automation level (not nested)
        
        # Update trigger: to triggers: for automations
        trigger_pattern = r'^(\s+)trigger:\s*$'
        trigger_matches = re.findall(trigger_pattern, content, re.MULTILINE)
        if trigger_matches:
            content = re.sub(trigger_pattern, r'\1triggers:', content, flags=re.MULTILINE)
            changes_made.append(f"Updated {len(trigger_matches)} trigger sections to triggers")
        
        # Update condition: to conditions: for automations (at automation level)
        condition_pattern = r'^(\s+)condition:\s*$'
        condition_matches = re.findall(condition_pattern, content, re.MULTILINE)
        if condition_matches:
            content = re.sub(condition_pattern, r'\1conditions:', content, flags=re.MULTILINE)
            changes_made.append(f"Updated {len(condition_matches)} condition sections to conditions")
        
        # Update action: to actions: for automations
        action_pattern = r'^(\s+)action:\s*$'
        action_matches = re.findall(action_pattern, content, re.MULTILINE)
        if action_matches:
            content = re.sub(action_pattern, r'\1actions:', content, flags=re.MULTILINE)
            changes_made.append(f"Updated {len(action_matches)} action sections to actions")
        
        # 3. Update platform: to trigger: in trigger definitions
        # This is more complex as we need to identify platform within trigger blocks
        # Look for patterns like "- platform: xyz" within trigger blocks
        platform_in_trigger_pattern = r'^(\s+)- platform:\s*(.+)$'
        platform_matches = re.findall(platform_in_trigger_pattern, content, re.MULTILINE)
        if platform_matches:
            content = re.sub(platform_in_trigger_pattern, r'\1- trigger: \2', content, flags=re.MULTILINE)
            changes_made.append(f"Updated {len(platform_matches)} platform definitions to trigger")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✓ Updated {file_path}")
            for change in changes_made:
                print(f"    - {change}")
            return True
        else:
            print(f"  - No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all YAML files."""
    print("Home Assistant YAML Syntax Updater")
    print("=" * 50)
    print("Updating syntax for 2024.8 and 2024.10 changes...")
    print()
    
    # Get all YAML files in packages directory
    packages_dir = Path("packages")
    if not packages_dir.exists():
        print("Error: packages directory not found!")
        sys.exit(1)
    
    yaml_files = list(packages_dir.rglob("*.yaml"))
    
    if not yaml_files:
        print("No YAML files found in packages directory!")
        sys.exit(1)
    
    print(f"Found {len(yaml_files)} YAML files to process...")
    print()
    
    updated_files = 0
    total_files = len(yaml_files)
    
    for yaml_file in sorted(yaml_files):
        if update_yaml_syntax(yaml_file):
            updated_files += 1
    
    print()
    print("Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Files updated: {updated_files}")
    print(f"Files unchanged: {total_files - updated_files}")
    
    if updated_files > 0:
        print()
        print("✓ YAML syntax update completed successfully!")
        print("Please review the changes and test your Home Assistant configuration.")
    else:
        print()
        print("No files needed updating.")

if __name__ == "__main__":
    main()