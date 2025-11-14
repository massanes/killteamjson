#!/usr/bin/env python3
"""
Split teams.json into individual team files.
Each team will be saved as a separate JSON file in the teams/ subfolder.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def split_teams_file(source_file: Path, output_dir: Path):
    """
    Split a teams.json file into individual team files.
    
    Args:
        source_file: Path to the source teams.json file
        output_dir: Directory where individual team files will be saved
    """
    print(f"Reading {source_file.name}...")
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            teams = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to read {source_file}: {e}")
        return False
    
    if not isinstance(teams, list):
        print(f"  [ERROR] Expected teams.json to be an array, got {type(teams)}")
        return False
    
    print(f"  Found {len(teams)} teams")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSaving teams to {output_dir}/...")
    
    saved_count = 0
    for i, team in enumerate(teams):
        if not isinstance(team, dict):
            print(f"  [WARNING] Team at index {i} is not a dict, skipping...")
            continue
        
        # Get team identifier for filename
        killteam_id = team.get('killteamId')
        if not killteam_id:
            print(f"  [WARNING] Team at index {i} has no killteamId, skipping...")
            continue
        
        # Create filename from killteamId
        # Replace any invalid filename characters
        safe_filename = killteam_id.replace('/', '_').replace('\\', '_')
        output_file = output_dir / f"{safe_filename}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(team, f, ensure_ascii=False, indent=2)
            saved_count += 1
            if (i + 1) % 10 == 0:
                print(f"    Saved {i + 1}/{len(teams)} teams...")
        except Exception as e:
            print(f"  [ERROR] Failed to save {output_file}: {e}")
            continue
    
    print(f"\n[OK] Successfully split {saved_count}/{len(teams)} teams into separate files")
    return True

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python split_teams.py <language>")
        print("\nArguments:")
        print("  language  - Language folder (e.g., 'en', 'es', 'fr')")
        print("\nExample:")
        print("  python split_teams.py en")
        print("  python split_teams.py es")
        sys.exit(1)
    
    lang = sys.argv[1].lower()
    
    source_file = Path(lang) / 'teams.json'
    output_dir = Path(lang) / 'teams'
    
    if not source_file.exists():
        print(f"Error: {source_file} not found")
        sys.exit(1)
    
    print("=" * 70)
    print(f"Splitting teams.json into individual files")
    print("=" * 70)
    print(f"\nSource: {source_file}")
    print(f"Output: {output_dir}/")
    print()
    
    if split_teams_file(source_file, output_dir):
        print("\n" + "=" * 70)
        print("[OK] Split complete!")
        print("=" * 70)
        print(f"\nIndividual team files are now in: {output_dir}/")
    else:
        print("\n[ERROR] Split failed")
        sys.exit(1)

if __name__ == '__main__':
    main()

