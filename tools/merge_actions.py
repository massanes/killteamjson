#!/usr/bin/env python3
"""
Merge mission_actions.json and universal_actions.json into a single actions.json file.
"""

import json
import sys
from pathlib import Path

def merge_actions(lang_dir: Path):
    """Merge mission_actions.json and universal_actions.json into actions.json."""
    universal_file = lang_dir / 'universal_actions.json'
    mission_file = lang_dir / 'mission_actions.json'
    output_file = lang_dir / 'actions.json'
    
    print(f"Merging actions in {lang_dir.name}/...")
    
    # Read universal actions
    universal_actions = []
    if universal_file.exists():
        try:
            with open(universal_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                universal_actions = data.get('actions', [])
            print(f"  Found {len(universal_actions)} universal actions")
        except Exception as e:
            print(f"  [ERROR] Failed to read {universal_file}: {e}")
            return False
    else:
        print(f"  [WARNING] {universal_file} not found")
    
    # Read mission actions
    mission_actions = []
    if mission_file.exists():
        try:
            with open(mission_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                mission_actions = data.get('actions', [])
            print(f"  Found {len(mission_actions)} mission actions")
        except Exception as e:
            print(f"  [ERROR] Failed to read {mission_file}: {e}")
            return False
    else:
        print(f"  [WARNING] {mission_file} not found")
    
    # Merge actions (universal first, then mission)
    all_actions = universal_actions + mission_actions
    
    # Create merged file
    merged_data = {
        "actions": all_actions
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Created {output_file.name} with {len(all_actions)} total actions")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to write {output_file}: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python merge_actions.py <language>")
        print("\nArguments:")
        print("  language  - Language folder (e.g., 'en', 'es', 'fr')")
        print("\nExample:")
        print("  python merge_actions.py en")
        sys.exit(1)
    
    lang = sys.argv[1].lower()
    lang_dir = Path(lang)
    
    if not lang_dir.exists():
        print(f"Error: {lang_dir} directory not found")
        sys.exit(1)
    
    print("=" * 70)
    print(f"Merging mission_actions.json and universal_actions.json")
    print("=" * 70)
    print()
    
    if merge_actions(lang_dir):
        print("\n" + "=" * 70)
        print("[OK] Merge complete!")
        print("=" * 70)
        print(f"\nCreated: {lang_dir}/actions.json")
        print("\nYou can now delete the original files if desired:")
        print(f"  - {lang_dir}/universal_actions.json")
        print(f"  - {lang_dir}/mission_actions.json")
    else:
        print("\n[ERROR] Merge failed")
        sys.exit(1)

if __name__ == '__main__':
    main()

