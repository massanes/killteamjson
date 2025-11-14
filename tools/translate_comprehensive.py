#!/usr/bin/env python3
"""
Comprehensive translation script that performs full sentence-level translations.
Uses Google Translate API (free) or DeepL (requires API key) for complete translations.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

def translate_google_translate(text: str, target_lang: str, source_lang: str = "en") -> str:
    """
    Translate text using Google Translate API via requests.
    This uses the unofficial Google Translate web interface.
    """
    try:
        import requests
        import urllib.parse
        
        # Use Google Translate web API
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": source_lang,
            "tl": target_lang,
            "dt": "t",
            "q": text
        }
        
        # Small delay to respect rate limits
        time.sleep(0.2)
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result and result[0]:
                # Extract translated text from nested array structure
                translated_parts = [part[0] for part in result[0] if part[0]]
                return ''.join(translated_parts)
        return text
    except ImportError:
        raise ImportError(
            "requests package not installed. Install with:\n"
            "  pip install requests"
        )
    except Exception as e:
        print(f"    [WARNING] Google Translate error: {e}")
        return text

def translate_deepl(text: str, target_lang: str, source_lang: str = "EN", api_key: str = None) -> str:
    """
    Translate text using DeepL API (requires API key).
    Install: pip install deepl
    """
    try:
        import os
        import deepl
        
        if not api_key:
            api_key = os.getenv("DEEPL_API_KEY")
        
        if not api_key:
            raise ValueError("DeepL API key not provided")
        
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
    except ImportError:
        raise ImportError(
            "deepl package not installed. Install with:\n"
            "  pip install deepl"
        )
    except Exception as e:
        print(f"    [WARNING] DeepL translation error: {e}")
        return text

# Fields that should NOT be translated (IDs, keys, etc.)
NON_TRANSLATABLE_FIELDS = ['id', 'type', 'seq', 'AP', 'APL', 'GA', 'DF', 'SV', 'W', 'M', 
                           'MV', 'APL_base', 'GA_base', 'DF_base', 'SV_base', 'W_base', 
                           'M_base', 'MV_base', 'D', 'A', 'BS', 'WS']

# Fields that should be translated
TRANSLATABLE_FIELDS = ['name', 'description', 'killteamName', 'opTypeName', 'wepName', 
                       'abilityName', 'ployName', 'eqName', 'optionName', 'title', 
                       'profileName', 'composition', 'reveal', 'additionalRules', 
                       'victoryPoints', 'effects', 'conditions', 'packs', 'archetypes',
                       'ability', 'keyword']

def should_translate_field(field_name: str, value: Any) -> bool:
    """Determine if a field should be translated."""
    if field_name in NON_TRANSLATABLE_FIELDS:
        return False
    if field_name in TRANSLATABLE_FIELDS:
        return True
    # For unknown fields, translate if it's a string and not empty
    if isinstance(value, str) and value.strip() and not field_name.startswith('_'):
        # Don't translate if it looks like an ID or code
        if field_name.lower().endswith(('id', '_id', 'code', '_code')):
            return False
        return True
    return False

def translate_value(value: Any, field_name: str, target_lang: str, translate_func) -> Any:
    """Recursively translate JSON values."""
    if isinstance(value, str):
        if should_translate_field(field_name, value) and value.strip():
            try:
                return translate_func(value, target_lang)
            except Exception as e:
                print(f"    [WARNING] Failed to translate {field_name}: {e}")
                return value
        return value
    elif isinstance(value, dict):
        result = {}
        for k, v in value.items():
            # Translate the key if it's a translatable field name
            translated_key = translate_value(k, "", target_lang, translate_func) if k in TRANSLATABLE_FIELDS else k
            result[translated_key if translated_key != k else k] = translate_value(v, k, target_lang, translate_func)
        return result
    elif isinstance(value, list):
        if not value:
            return value
        
        # Check first element to determine list type
        first = value[0] if value else None
        
        # If it's a list of strings (like effects, conditions, packs)
        if isinstance(first, str):
            if field_name in ['effects', 'conditions', 'packs'] or should_translate_field(field_name, first):
                return [translate_func(item, target_lang) if isinstance(item, str) and item.strip() 
                       else item for item in value]
            return value
        # Otherwise, translate each element
        return [translate_value(item, field_name, target_lang, translate_func) for item in value]
    else:
        return value

def translate_file(en_file: Path, target_file: Path, target_lang: str, translate_func, provider_name: str):
    """Translate a JSON file using the specified translation function."""
    print(f"\nTranslating {en_file.name} to {target_lang.upper()} using {provider_name}...")
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to read {en_file}: {e}")
        return False
    
    try:
        translated = translate_value(data, "", target_lang, translate_func)
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
        return False
    
    # Validate JSON structure
    try:
        json.dumps(translated)
    except Exception as e:
        print(f"  [ERROR] Invalid JSON after translation: {e}")
        return False
    
    # Write translated file
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Created {target_file.name}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to write {target_file}: {e}")
        return False

def main():
    """Main translation function."""
    if len(sys.argv) < 2:
        print("Usage: python translate_comprehensive.py <language> [provider]")
        print("\nArguments:")
        print("  language  - Target language: es (Spanish) or fr (French)")
        print("  provider  - Translation provider: google (default) or deepl")
        print("\nExamples:")
        print("  python translate_comprehensive.py es google")
        print("  python translate_comprehensive.py fr deepl")
        print("\nNote:")
        print("  - Google Translate: Free, no API key needed")
        print("  - DeepL: Requires API key (set DEEPL_API_KEY env var)")
        sys.exit(1)
    
    target_lang = sys.argv[1].lower()
    provider = sys.argv[2].lower() if len(sys.argv) > 2 else "google"
    
    if target_lang not in ["es", "fr"]:
        print(f"Error: Unsupported language '{target_lang}'. Use 'es' or 'fr'")
        sys.exit(1)
    
    if provider not in ["google", "deepl"]:
        print(f"Error: Unknown provider '{provider}'. Use 'google' or 'deepl'")
        sys.exit(1)
    
    # Select translation function
    if provider == "google":
        try:
            translate_func = lambda text, lang: translate_google_translate(text, lang)
            provider_name = "Google Translate"
        except ImportError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:  # deepl
        try:
            # Check for API key as 3rd argument or environment variable
            api_key = sys.argv[3] if len(sys.argv) > 3 else None
            if not api_key:
                import os
                api_key = os.getenv("DEEPL_API_KEY")
            translate_func = lambda text, lang: translate_deepl(text, lang, api_key=api_key)
            provider_name = "DeepL"
        except (ImportError, ValueError) as e:
            print(f"Error: {e}")
            sys.exit(1)
    
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
    print(f"Translating all JSON files to {target_lang.upper()} using {provider_name}")
    print("=" * 70)
    print("\nThis will translate all text content (names, descriptions, effects, etc.)")
    print("This may take several minutes due to API rate limits...")
    print()
    
    success_count = 0
    for filename in files:
        en_file = en_dir / filename
        target_file = target_dir / filename
        
        if en_file.exists():
            if translate_file(en_file, target_file, target_lang, translate_func, provider_name):
                success_count += 1
        else:
            print(f"  [WARNING] {en_file} not found, skipping...")
    
    print("\n" + "=" * 70)
    print(f"[OK] Translation complete! {success_count}/{len(files)} files translated.")
    print("=" * 70)
    print("\nNote: Please review the translations for accuracy and Games Workshop terminology.")
    print("Some technical terms or proper nouns may need manual adjustment.")

if __name__ == '__main__':
    main()
