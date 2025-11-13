#!/usr/bin/env python3
"""
DeepL translation script - fast translation using DeepL API.
Usage: python translate_deepl.py <language> <api_key>
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

def translate_deepl(text: str, target_lang: str, api_key: str) -> str:
    """Translate text using DeepL API."""
    try:
        import deepl
        
        if not text or not text.strip():
            return text
        
        translator = deepl.Translator(api_key)
        
        # Map language codes for DeepL
        deepl_lang_map = {
            "es": "ES",
            "fr": "FR",
            "de": "DE",
            "it": "IT",
            "pt": "PT"
        }
        
        deepl_target = deepl_lang_map.get(target_lang.lower(), target_lang.upper())
        
        result = translator.translate_text(text, target_lang=deepl_target)
        return result.text
    except Exception as e:
        print(f"      [WARNING] DeepL translation error: {e}")
        return text

# Fields that should NOT be translated
NON_TRANSLATABLE = {'id', 'type', 'seq', 'AP', 'APL', 'GA', 'DF', 'SV', 'W', 'M', 
                    'MV', 'version', 'file', 'D', 'A', 'BS', 'WS'}

# Fields that should be translated
TRANSLATABLE = {'name', 'description', 'killteamName', 'opTypeName', 'wepName', 
                'abilityName', 'ployName', 'eqName', 'optionName', 'title', 
                'profileName', 'composition', 'reveal', 'additionalRules', 
                'victoryPoints', 'ability', 'keyword', 'team'}

def should_translate_field(field_name: str, value: Any) -> bool:
    """Determine if a field should be translated."""
    if field_name in NON_TRANSLATABLE:
        return False
    if field_name in TRANSLATABLE:
        return True
    if isinstance(value, str) and value.strip() and not field_name.startswith('_'):
        if field_name.lower().endswith(('id', '_id', 'code', '_code')):
            return False
        return True
    return False

def translate_value(value: Any, field_name: str, target_lang: str, api_key: str) -> Any:
    """Recursively translate JSON values - field names stay in English!"""
    if isinstance(value, str):
        if should_translate_field(field_name, value) and value.strip():
            try:
                return translate_deepl(value, target_lang, api_key)
            except Exception as e:
                print(f"      [WARNING] Failed to translate {field_name}: {e}")
                return value
        return value
    elif isinstance(value, dict):
        return {k: translate_value(v, k, target_lang, api_key) 
                for k, v in value.items()}
    elif isinstance(value, list):
        if not value:
            return value
        
        first = value[0]
        
        if isinstance(first, str):
            # Translate array elements
            if field_name in {'effects', 'conditions', 'packs'}:
                return [translate_deepl(item, target_lang, api_key) if item.strip() else item 
                       for item in value]
            elif field_name == 'archetypes':
                # Map archetypes
                archetype_map = {
                    "es": {"Security": "Seguridad", "Seek & Destroy": "Buscar y Destruir", 
                          "Recon": "Reconocimiento", "Infiltration": "Infiltración"},
                    "fr": {"Security": "Sécurité", "Seek & Destroy": "Rechercher et Détruire",
                          "Recon": "Reconnaissance", "Infiltration": "Infiltration"}
                }
                translated = []
                for item in value:
                    if item in archetype_map.get(target_lang, {}):
                        translated.append(archetype_map[target_lang][item])
                    else:
                        translated.append(translate_deepl(item, target_lang, api_key))
                return translated
            elif value and value[0].strip():
                return [translate_deepl(item, target_lang, api_key) if item.strip() else item 
                       for item in value]
        
        return [translate_value(item, field_name, target_lang, api_key) 
                for item in value]
    else:
        return value

def translate_file(en_file: Path, target_file: Path, target_lang: str, api_key: str):
    """Translate a JSON file."""
    print(f"\nTranslating {en_file.name} to {target_lang.upper()} using DeepL...")
    
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
            if should_translate_field(field, obj):
                count += 1
        elif isinstance(obj, dict):
            for k, v in obj.items():
                count += count_strings(v, k)
        elif isinstance(obj, list):
            for item in obj:
                count += count_strings(item, field)
        return count
    
    total_strings = count_strings(data)
    print(f"  Found {total_strings} translatable strings")
    
    # Translate with progress
    translated_count = [0]
    last_progress = [0]
    
    def translate_with_progress(text, lang, key):
        result = translate_deepl(text, lang, key)
        translated_count[0] += 1
        # Show progress every 50 strings
        if translated_count[0] - last_progress[0] >= 50:
            progress = (translated_count[0] / total_strings) * 100
            print(f"    Progress: {translated_count[0]}/{total_strings} strings ({progress:.1f}%)...")
            last_progress[0] = translated_count[0]
        return result
    
    try:
        translated_data = translate_value(data, "", target_lang, api_key)
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
        print(f"  [OK] Created {target_file.name} ({translated_count[0]} strings translated)")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to write {target_file}: {e}")
        return False

def main():
    """Main translation function."""
    if len(sys.argv) < 3:
        print("Usage: python translate_deepl.py <language> <api_key>")
        print("\nArguments:")
        print("  language  - Target language: es (Spanish) or fr (French)")
        print("  api_key   - Your DeepL API key")
        print("\nExample:")
        print("  python translate_deepl.py es 06238e61-30f8-445a-9188-56ea16902f56:fx")
        sys.exit(1)
    
    target_lang = sys.argv[1].lower()
    api_key = sys.argv[2]
    
    if target_lang not in ["es", "fr"]:
        print(f"Error: Unsupported language '{target_lang}'. Use 'es' or 'fr'")
        sys.exit(1)
    
    try:
        import deepl
        # Test API key
        translator = deepl.Translator(api_key)
        usage = translator.get_usage()
        print(f"DeepL API Usage: {usage.character.count}/{usage.character.limit} characters used")
    except ImportError:
        print("Error: deepl package not installed. Install with: pip install deepl")
        sys.exit(1)
    except Exception as e:
        print(f"Error: DeepL API key validation failed: {e}")
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
    print(f"Translating all JSON files to {target_lang.upper()} using DeepL")
    print("=" * 70)
    print("\nField names stay in English - only values are translated.")
    print()
    
    success_count = 0
    start_time = time.time()
    
    for filename in files:
        en_file = en_dir / filename
        target_file = target_dir / filename
        
        if en_file.exists():
            file_start = time.time()
            if translate_file(en_file, target_file, target_lang, api_key):
                success_count += 1
                elapsed = time.time() - file_start
                print(f"  Completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        else:
            print(f"  [WARNING] {en_file} not found, skipping...")
    
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[OK] Translation complete! {success_count}/{len(files)} files translated.")
    print(f"Total time: {total_time/60:.1f} minutes")
    print("=" * 70)
    print("\nNote: Please review translations for accuracy and Games Workshop terminology.")

if __name__ == '__main__':
    main()

