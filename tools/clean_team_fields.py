#!/usr/bin/env python3
"""
Remove deprecated fields from team JSON files:
- From root: isPublished, isHomebrew, userId
- From opTypes: nameType, isOpType, isActivated, currWOUNDS, opName, opType, opId
- From weapons: isDefault
"""

import json
import sys
from pathlib import Path


def remove_fields_from_dict(obj, fields_to_remove):
    """Recursively remove specified fields from a dictionary."""
    if isinstance(obj, dict):
        # Remove fields at this level
        for field in fields_to_remove:
            obj.pop(field, None)
        # Recursively process nested dictionaries
        for value in obj.values():
            remove_fields_from_dict(value, fields_to_remove)
    elif isinstance(obj, list):
        # Process each item in the list
        for item in obj:
            remove_fields_from_dict(item, fields_to_remove)


def clean_team_file(file_path):
    """Clean a single team file by removing deprecated fields."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Remove fields from root level
        root_fields_to_remove = ['isPublished', 'isHomebrew', 'userId']
        for field in root_fields_to_remove:
            data.pop(field, None)
        
        # Remove fields from opTypes
        if 'opTypes' in data and isinstance(data['opTypes'], list):
            opType_fields_to_remove = ['nameType', 'isOpType', 'isActivated', 'currWOUNDS', 'opName', 'opType', 'opId']
            for opType in data['opTypes']:
                for field in opType_fields_to_remove:
                    opType.pop(field, None)
                
                # Remove isDefault from weapons
                if 'weapons' in opType and isinstance(opType['weapons'], list):
                    for weapon in opType['weapons']:
                        weapon.pop('isDefault', None)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Process all team files in en/teams/ directory."""
    teams_dir = Path('en') / 'teams'
    
    if not teams_dir.exists():
        print(f"Error: {teams_dir} directory not found", file=sys.stderr)
        sys.exit(1)
    
    team_files = sorted(teams_dir.glob('*.json'))
    
    if not team_files:
        print(f"No JSON files found in {teams_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(team_files)} team files...")
    
    success_count = 0
    for team_file in team_files:
        if clean_team_file(team_file):
            print(f"  [OK] {team_file.name}")
            success_count += 1
        else:
            print(f"  [FAIL] {team_file.name} (failed)")
    
    print(f"\nCompleted: {success_count}/{len(team_files)} files processed successfully")


if __name__ == '__main__':
    main()

