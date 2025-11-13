#!/usr/bin/env python3
"""
Faster translation script that batches strings and uses proper structure preservation.
Field names stay in English - only values are translated.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Fields that should NOT be translated
NON_TRANSLATABLE = {'id', 'type', 'seq', 'AP', 'APL', 'GA', 'DF', 'SV', 'W', 'M', 
                    'MV', 'version', 'file', 'D', 'A', 'BS', 'WS'}

# Fields that should be translated
TRANSLATABLE = {'name', 'description', 'killteamName', 'opTypeName', 'wepName', 
                'abilityName', 'ployName', 'eqName', 'optionName', 'title', 
                'profileName', 'composition', 'reveal', 'additionalRules', 
                'victoryPoints', 'ability', 'keyword', 'team'}

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
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if result and result[0]:
                translated_parts = [part[0] for part in result[0] if part[0]]
                return ''.join(translated_parts)
        return text
    except Exception as e:
        print(f"      [WARNING] Translation error: {e}")
        return text

def translate_value_recursive(value: Any, field_name: str, target_lang: str, translate_func) -> Any:
    """Recursively translate JSON values - field names stay in English!"""
    if isinstance(value, str):
        # Check if this field should be translated
        if field_name in TRANSLATABLE or (field_name not in NON_TRANSLATABLE and value.strip()):
            # Don't translate IDs or codes
            if field_name.lower().endswith(('id', '_id', 'code', '_code')):
                return value
            # Translate the value
            if value.strip():
                try:
                    return translate_func(value, target_lang)
                except Exception as e:
                    print(f"      [WARNING] Failed to translate {field_name}: {e}")
                    return value
        return value
    elif isinstance(value, dict):
        # Keep field names in English, only translate values
        return {k: translate_value_recursive(v, k, target_lang, translate_func) 
                for k, v in value.items()}
    elif isinstance(value, list):
        if not value:
            return value
        
        first = value[0]
        
        # Translate array elements
        if isinstance(first, str):
            # For effects, conditions, packs arrays
            if field_name in {'effects', 'conditions', 'packs'}:
                return [translate_func(item, target_lang) if item.strip() else item 
                       for item in value]
            # For archetypes or other string arrays
            elif field_name == 'archetypes':
                # Map archetypes
                archetype_map = {
                    "es": {"Security": "Seguridad", "Seek & Destroy": "Buscar y Destruir", 
                          "Recon": "Reconocimiento", "Infiltration": "Infiltración"},
                    "fr": {"Security": "Sécurité", "Seek & Destroy": "Rechercher et Détruire",
                          "Recon": "Reconnaissance", "Infiltration": "Infiltration"}
                }
                return [archetype_map.get(target_lang, {}).get(item, translate_func(item, target_lang))
                       for item in value]
            # Generic string array
            elif value and value[0].strip():
                return [translate_func(item, target_lang) if item.strip() else item 
                       for item in value]
        
        # Recursive for nested objects
        return [translate_value_recursive(item, field_name, target_lang, translate_func) 
                for item in value]
    else:
        return value

def translate_file(en_file: Path, target_file: Path, target_lang: str):
    """Translate a JSON file."""
    print(f"\nTranslating {en_file.name} to {target_lang.upper()}...")
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to read {en_file}: {e}")
        return False
    
    # Count translatable strings for progress
    def count_strings(obj, field=""):
        count = 0
        if isinstance(obj, str):
            if field in TRANSLATABLE or (field not in NON_TRANSLATABLE and obj.strip()):
                if not field.lower().endswith(('id', '_id', 'code', '_code')):
                    count += 1
        elif isinstance(obj, dict):
            for k, v in obj.items():
                count += count_strings(v, k)
        elif isinstance(obj, list):
            for item in obj:
                count += count_strings(item, field)
        return count
    
    total_strings = count_strings(data)
    print(f"  Found {total_strings} translatable strings (this will take time)...")
    
    # Translate with progress indication
    translated_count = [0]
    
    def translate_with_progress(text, lang):
        result = translate_text(text, lang)
        translated_count[0] += 1
        if translated_count[0] % 10 == 0:
            print(f"    Progress: {translated_count[0]}/{total_strings} strings translated...")
        time.sleep(0.3)  # Rate limit delay
        return result
    
    try:
        translated_data = translate_value_recursive(data, "", target_lang, 
                                                   lambda t, l: translate_with_progress(t, l))
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
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
        print(f"  [OK] Created {target_file.name}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to write {target_file}: {e}")
        return False

def main():
    """Main translation function."""
    if len(sys.argv) < 2:
        print("Usage: python translate_fast.py <language>")
        print("\nArguments:")
        print("  language  - Target language: es (Spanish) or fr (French)")
        print("\nExample:")
        print("  python translate_fast.py es")
        print("\nWARNING: Google Translate has rate limits.")
        print("Large files like teams.json may take 30-60 minutes to translate.")
        print("Consider using DeepL API for faster results (requires API key).")
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
    
    files = [
        'weapon_rules.json',
        'universal_equipment.json',
        'universal_actions.json',
        'mission_actions.json',
        'ops_2025.json',
        'teams.json'
    ]
    
    en_dir = Path('en')
    target_dir = Path(target_lang)
    target_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print(f"Translating all JSON files to {target_lang.upper()}")
    print("=" * 70)
    print("\nThis will translate all text VALUES (field names stay in English).")
    print("Due to Google Translate rate limits, this may take 30-60 minutes...")
    print("Progress will be shown during translation.")
    print()
    
    success_count = 0
    start_time = time.time()
    
    for filename in files:
        en_file = en_dir / filename
        target_file = target_dir / filename
        
        if en_file.exists():
            file_start = time.time()
            if translate_file(en_file, target_file, target_lang):
                success_count += 1
                elapsed = time.time() - file_start
                print(f"  Completed in {elapsed/60:.1f} minutes")
        else:
            print(f"  [WARNING] {en_file} not found, skipping...")
    
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[OK] Translation complete! {success_count}/{len(files)} files translated.")
    print(f"Total time: {total_time/60:.1f} minutes")
    print("=" * 70)

if __name__ == '__main__':
    main()

