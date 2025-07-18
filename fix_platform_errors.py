#!/usr/bin/env python3
"""
Script to fix incorrectly changed platform definitions in Home Assistant YAML files.

BugBot found that the previous script incorrectly changed platform: to trigger: in
non-automation contexts where platform: is required to specify the integration type.
"""

import os
import re
from pathlib import Path

def fix_platform_errors(file_path):
    """Fix incorrectly changed platform definitions in a single file."""
    print(f"Processing: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # Fix sensor platform definitions
        # Pattern: under sensor: or binary_sensor: sections, change trigger: back to platform:
        
        # 1. Fix template platforms
        pattern = r'^(\s+)- trigger: template$'
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            content = re.sub(pattern, r'\1- platform: template', content, flags=re.MULTILINE)
            changes_made.append(f"Fixed {len(matches)} template platform definitions")
        
        # 2. Fix group platforms  
        pattern = r'^(\s+)- trigger: group$'
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            content = re.sub(pattern, r'\1- platform: group', content, flags=re.MULTILINE)
            changes_made.append(f"Fixed {len(matches)} group platform definitions")
        
        # 3. Fix integration platforms
        pattern = r'^(\s+)- trigger: integration$'
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            content = re.sub(pattern, r'\1- platform: integration', content, flags=re.MULTILINE)
            changes_made.append(f"Fixed {len(matches)} integration platform definitions")
        
        # 4. Fix time_date platforms
        pattern = r'^(\s+)- trigger: time_date$'
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            content = re.sub(pattern, r'\1- platform: time_date', content, flags=re.MULTILINE)
            changes_made.append(f"Fixed {len(matches)} time_date platform definitions")
        
        # 5. Fix pirateweather platforms
        pattern = r'^(\s+)- trigger: pirateweather$'
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            content = re.sub(pattern, r'\1- platform: pirateweather', content, flags=re.MULTILINE)
            changes_made.append(f"Fixed {len(matches)} pirateweather platform definitions")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✓ Fixed {file_path}")
            for change in changes_made:
                print(f"    - {change}")
            return True
        else:
            print(f"  - No platform fixes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all YAML files."""
    print("Home Assistant Platform Error Fix")
    print("=" * 50)
    print("Fixing incorrectly changed platform definitions...")
    print()
    
    # Get all YAML files in packages directory
    packages_dir = Path("packages")
    if not packages_dir.exists():
        print("Error: packages directory not found!")
        return
    
    yaml_files = list(packages_dir.rglob("*.yaml"))
    
    if not yaml_files:
        print("No YAML files found in packages directory!")
        return
    
    print(f"Found {len(yaml_files)} YAML files to process...")
    print()
    
    fixed_files = 0
    total_files = len(yaml_files)
    
    for yaml_file in sorted(yaml_files):
        if fix_platform_errors(yaml_file):
            fixed_files += 1
    
    print()
    print("Summary:")
    print(f"Total files processed: {total_files}")
    print(f"Files fixed: {fixed_files}")
    print(f"Files unchanged: {total_files - fixed_files}")
    
    if fixed_files > 0:
        print()
        print("✓ Platform error fixes completed successfully!")
    else:
        print()
        print("No platform errors found to fix.")

if __name__ == "__main__":
    main()