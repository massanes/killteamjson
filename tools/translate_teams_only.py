#!/usr/bin/env python3
"""
Translate only teams.json using Google Translate.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

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

def translate_value(value: Any, field_name: str, target_lang: str, progress_callback=None) -> Any:
    """Recursively translate JSON values - field names stay in English!"""
    if isinstance(value, str):
        if should_translate_field(field_name, value) and value.strip():
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
        return {k: translate_value(v, k, target_lang, progress_callback) 
                for k, v in value.items()}
    elif isinstance(value, list):
        if not value:
            return value
        
        first = value[0]
        
        if isinstance(first, str):
            if field_name in {'effects', 'conditions', 'packs'}:
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
            elif field_name == 'archetypes':
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
                        translated.append(translate_text(item, target_lang))
                        if progress_callback:
                            progress_callback()
                        time.sleep(0.3)
                return translated
            elif value and value[0].strip():
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
        
        return [translate_value(item, field_name, target_lang, progress_callback) 
                for item in value]
    else:
        return value

def main():
    """Translate teams.json only."""
    target_lang = "es"
    
    en_file = Path('en/teams.json')
    target_file = Path('es/teams.json')
    
    print("=" * 70)
    print(f"Translating teams.json to {target_lang.upper()} using Google Translate")
    print("=" * 70)
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to read {en_file}: {e}")
        return
    
    # Count translatable strings
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
    print(f"  This will take approximately {total_strings * 0.3 / 60:.1f} minutes")
    print()
    
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
        translated_data = translate_value(data, "", target_lang, progress_callback)
    except KeyboardInterrupt:
        print(f"\n  [INTERRUPTED] Translation stopped at {translated_count[0]}/{total_strings} strings")
        print(f"  Saving partial translation...")
        # Save partial translation
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)
            print(f"  [OK] Partial translation saved to {target_file.name}")
        except Exception as e:
            print(f"  [ERROR] Failed to save: {e}")
        return
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Validate JSON
    try:
        json.dumps(translated_data)
    except Exception as e:
        print(f"  [ERROR] Invalid JSON after translation: {e}")
        return
    
    # Write
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        elapsed = time.time() - start_time
        print(f"  [OK] Created {target_file.name}")
        print(f"      {translated_count[0]} strings translated in {elapsed/60:.1f} minutes")
    except Exception as e:
        print(f"  [ERROR] Failed to write {target_file}: {e}")

if __name__ == '__main__':
    main()

