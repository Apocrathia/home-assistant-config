#!/usr/bin/env python3
"""
Validation script to check that all Home Assistant YAML syntax changes were applied correctly.
"""

import re
import sys
from pathlib import Path

def validate_yaml_syntax(file_path):
    """Validate YAML syntax in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        
        # Check for old syntax patterns that should have been updated
        
        # 1. Check for service: calls (should be action:)
        service_pattern = r'^\s+service:\s*.+$'
        service_matches = re.findall(service_pattern, content, re.MULTILINE)
        if service_matches:
            issues.append(f"Found {len(service_matches)} remaining 'service:' calls (should be 'action:')")
        
        # 2. Check for automation-level trigger: (should be triggers:)
        # Look for trigger: at automation level (not nested in conditions/choose)
        trigger_pattern = r'^\s+trigger:\s*$'
        trigger_matches = re.findall(trigger_pattern, content, re.MULTILINE)
        if trigger_matches:
            issues.append(f"Found {len(trigger_matches)} automation-level 'trigger:' (should be 'triggers:')")
        
        # 3. Check for automation-level condition: (should be conditions:)
        condition_pattern = r'^\s+condition:\s*$'
        condition_matches = re.findall(condition_pattern, content, re.MULTILINE)
        if condition_matches:
            issues.append(f"Found {len(condition_matches)} automation-level 'condition:' (should be 'conditions:')")
        
        # 4. Check for automation-level action: (should be actions:)
        action_pattern = r'^\s+action:\s*$'
        action_matches = re.findall(action_pattern, content, re.MULTILINE)
        if action_matches:
            issues.append(f"Found {len(action_matches)} automation-level 'action:' (should be 'actions:')")
        
        # 5. Check for platform: in trigger definitions (should be trigger:)
        platform_pattern = r'^\s+- platform:\s*.+$'
        platform_matches = re.findall(platform_pattern, content, re.MULTILINE)
        if platform_matches:
            issues.append(f"Found {len(platform_matches)} 'platform:' in triggers (should be 'trigger:')")
        
        return issues
        
    except Exception as e:
        return [f"Error reading file: {e}"]

def main():
    """Main validation function."""
    print("Home Assistant YAML Syntax Validator")
    print("=" * 50)
    print("Checking for any remaining old syntax patterns...")
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
    
    print(f"Validating {len(yaml_files)} YAML files...")
    print()
    
    total_issues = 0
    files_with_issues = 0
    
    for yaml_file in sorted(yaml_files):
        issues = validate_yaml_syntax(yaml_file)
        if issues:
            files_with_issues += 1
            print(f"❌ {yaml_file}:")
            for issue in issues:
                print(f"    - {issue}")
                total_issues += 1
            print()
        else:
            print(f"✅ {yaml_file}: OK")
    
    print()
    print("Validation Summary:")
    print(f"Total files checked: {len(yaml_files)}")
    print(f"Files with issues: {files_with_issues}")
    print(f"Total issues found: {total_issues}")
    
    if total_issues == 0:
        print()
        print("🎉 All YAML files have been successfully updated!")
        print("No old syntax patterns detected.")
    else:
        print()
        print("⚠️  Some files still contain old syntax patterns.")
        print("Please review and fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()