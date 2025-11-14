#!/usr/bin/env python3
"""
Precise translation script that only translates specified fields per file.
Uses translation_config.py for field definitions.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, List
from translation_config import should_translate_field

def translate_text(text: str, target_lang: str) -> str:
    """Translate a single text using Google Translate web API."""
    if not text or not text.strip():
        return text
    
    try:
        import requests
        
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        
        response = requests.get(url, params=params, timeout=20)
        if response.status_code == 200:
            result = response.json()
            if result and result[0]:
                translated_parts = [part[0] for part in result[0] if part[0]]
                return ''.join(translated_parts)
        return text
    except Exception as e:
        print(f"      [WARNING] Translation error: {e}")
        # Retry once after a short delay
        time.sleep(1)
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                result = response.json()
                if result and result[0]:
                    translated_parts = [part[0] for part in result[0] if part[0]]
                    return ''.join(translated_parts)
        except:
            pass
        return text

def translate_value(value: Any, field_name: str, field_path: List[str], 
                   file_name: str, target_lang: str, progress_callback=None) -> Any:
    """
    Recursively translate JSON values based on precise field rules.
    Field names stay in English - only specified values are translated.
    
    Args:
        value: The value to translate (string, dict, list, etc.)
        field_name: Name of the current field
        field_path: List of parent field names (for nested structures)
        file_name: Name of the JSON file being translated
        target_lang: Target language code
        progress_callback: Optional callback function for progress tracking
    """
    if isinstance(value, str):
        # Check if this field should be translated
        if should_translate_field(file_name, field_path, field_name) and value.strip():
            try:
                result = translate_text(value, target_lang)
                if progress_callback:
                    progress_callback()
                time.sleep(0.3)  # Rate limit delay
                return result
            except Exception as e:
                print(f"      [WARNING] Failed to translate {field_name}: {e}")
                if progress_callback:
                    progress_callback()
                return value
        return value
    elif isinstance(value, dict):
        # Update field path for nested objects
        # Add current field_name to path if it exists (for nested objects)
        new_path = field_path + [field_name] if field_name else field_path
        return {k: translate_value(v, k, new_path, file_name, target_lang, progress_callback) 
                for k, v in value.items()}
    elif isinstance(value, list):
        if not value:
            return value
        
        # Check if this is an array of strings that should be translated
        first = value[0]
        if isinstance(first, str):
            # For arrays like effects, conditions - check if parent field allows translation
            if should_translate_field(file_name, field_path, field_name):
                translated = []
                for item in value:
                    if item.strip():
                        translated.append(translate_text(item, target_lang))
                        if progress_callback:
                            progress_callback()
                        time.sleep(0.3)
                    else:
                        translated.append(item)
                return translated
            return value
        
        # For arrays of objects (like opTypes, weapons, etc.)
        # Add the field_name to path so nested fields can be found
        # Example: opTypes array -> path becomes ['opTypes'], then inside each item we look for 'weapons'
        new_path = field_path + [field_name] if field_name else field_path
        return [translate_value(item, "", new_path, file_name, target_lang, progress_callback) 
                for item in value]
    else:
        return value

def translate_file(en_file: Path, target_file: Path, target_lang: str):
    """Translate a JSON file using precise field rules."""
    # For team files, use the full relative path for rule matching
    if 'teams' in str(en_file):
        file_name = f"teams/{en_file.name}"
    else:
        file_name = en_file.name
    print(f"\nTranslating {en_file.name} to {target_lang.upper()}...")
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to read {en_file}: {e}")
        return False
    
    # Count translatable strings for progress
    def count_strings(obj, field="", path=None):
        if path is None:
            path = []
        count = 0
        if isinstance(obj, str):
            if should_translate_field(file_name, path, field) and obj.strip():
                count += 1
        elif isinstance(obj, dict):
            for k, v in obj.items():
                new_path = path + [field] if field else path
                count += count_strings(v, k, new_path)
        elif isinstance(obj, list):
            for item in obj:
                count += count_strings(item, field, path)
        return count
    
    total_strings = count_strings(data)
    print(f"  Found {total_strings} translatable strings")
    
    if total_strings == 0:
        print(f"  [SKIP] No translatable strings found")
        return False
    
    # Progress tracking
    translated_count = [0]
    last_progress_time = [time.time()]
    
    def progress_callback():
        translated_count[0] += 1
        current_time = time.time()
        
        # Show progress every 50 strings or every 10 seconds
        if (translated_count[0] % 50 == 0) or (current_time - last_progress_time[0] >= 10):
            progress = (translated_count[0] / total_strings) * 100
            elapsed = current_time - last_progress_time[0]
            rate = 50 / max(elapsed, 1) if translated_count[0] % 50 == 0 else translated_count[0] / max(current_time - (time.time() - elapsed), 1)
            remaining = (total_strings - translated_count[0]) / max(rate, 0.1)
            
            print(f"    [{translated_count[0]}/{total_strings}] {progress:.1f}% | "
                  f"ETA: {remaining/60:.1f} min")
            last_progress_time[0] = current_time
    
    print(f"  Starting translation...")
    start_time = time.time()
    
    try:
        translated_data = translate_value(data, "", [], file_name, target_lang, progress_callback)
    except KeyboardInterrupt:
        print(f"\n  [INTERRUPTED] Translation stopped at {translated_count[0]}/{total_strings} strings")
        return False
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Validate JSON
    try:
        json.dumps(translated_data)
    except Exception as e:
        print(f"  [ERROR] Invalid JSON after translation: {e}")
        return False
    
    # Write
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        elapsed = time.time() - start_time
        print(f"  [OK] Created {target_file.name}")
        print(f"      {translated_count[0]} strings translated in {elapsed/60:.1f} minutes")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to write {target_file}: {e}")
        return False

def main():
    """Main translation function."""
    if len(sys.argv) < 2:
        print("Usage: python translate_precise.py <language> [file1] [file2] ...")
        print("\nArguments:")
        print("  language  - Target language: es (Spanish) or fr (French)")
        print("  files     - Optional: specific files to translate (default: all)")
        print("\nExample:")
        print("  python translate_precise.py es")
        print("  python translate_precise.py es teams.json")
        sys.exit(1)
    
    target_lang = sys.argv[1].lower()
    
    if target_lang not in ["es", "fr"]:
        print(f"Error: Unsupported language '{target_lang}'. Use 'es' or 'fr'")
        sys.exit(1)
    
    try:
        import requests
    except ImportError:
        print("Error: requests package not installed. Install with: pip install requests")
        sys.exit(1)
    
    # Determine which files to translate
    if len(sys.argv) > 2:
        files = sys.argv[2:]
    else:
        files = [
            'weapon_rules.json',
            'universal_equipment.json',
            'actions.json',
            'ops_2025.json',
        ]
        # Add individual team files
        teams_dir = Path('en') / 'teams'
        if teams_dir.exists():
            team_files = sorted(teams_dir.glob('*.json'))
            files.extend([f'teams/{f.name}' for f in team_files])
    
    en_dir = Path('en')
    target_dir = Path(target_lang)
    target_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print(f"Translating JSON files to {target_lang.upper()} using precise field rules")
    print("=" * 70)
    print("\nOnly specified fields will be translated (see translation_config.py)")
    print()
    
    success_count = 0
    start_time = time.time()
    
    for filename in files:
        en_file = en_dir / filename
        target_file = target_dir / filename
        
        if en_file.exists():
            if translate_file(en_file, target_file, target_lang):
                success_count += 1
        else:
            print(f"  [WARNING] {en_file} not found, skipping...")
    
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[OK] Translation complete! {success_count}/{len(files)} files translated.")
    print(f"Total time: {total_time/60:.1f} minutes")
    print("=" * 70)

if __name__ == '__main__':
    main()

