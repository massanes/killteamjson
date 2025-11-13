#!/usr/bin/env python3
"""
Translation script using automated translation APIs.
Supports DeepL, Google Translate, and others for full sentence-level translations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Translation API integration functions
# These can be implemented with actual API calls

def translate_text_deepl(text: str, target_lang: str, source_lang: str = "EN") -> str:
    """
    Translate text using DeepL API.
    Requires: pip install deepl
    
    Usage:
        import deepl
        translator = deepl.Translator("YOUR_API_KEY")
        return translator.translate_text(text, target_lang=target_lang).text
    """
    try:
        import deepl
        # Uncomment and configure with your API key:
        # translator = deepl.Translator(os.getenv("DEEPL_API_KEY"))
        # result = translator.translate_text(text, target_lang=target_lang)
        # return result.text
        raise NotImplementedError("DeepL API not configured. Install deepl package and set API key.")
    except ImportError:
        raise ImportError("DeepL package not installed. Run: pip install deepl")
    except Exception as e:
        print(f"DeepL translation error: {e}")
        return text

def translate_text_google(text: str, target_lang: str, source_lang: str = "en") -> str:
    """
    Translate text using Google Translate API.
    Requires: pip install googletrans==4.0.0rc1
    
    Usage:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=target_lang)
        return result.text
    """
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=target_lang, src=source_lang)
        return result.text
    except ImportError:
        raise ImportError("googletrans package not installed. Run: pip install googletrans==4.0.0rc1")
    except Exception as e:
        print(f"Google Translate error: {e}")
        return text

def translate_text_manual_spanish(text: str) -> str:
    """Manual translation for Spanish - basic implementation."""
    # This is a placeholder - in production, use actual translation API
    # For now, return as-is with note that API translation needed
    return text

def translate_text_manual_french(text: str) -> str:
    """Manual translation for French - basic implementation."""
    # This is a placeholder - in production, use actual translation API
    return text

# Language code mappings
LANG_CODES = {
    "es": "es",  # Spanish
    "fr": "fr",  # French
    "de": "de",  # German
    "it": "it",  # Italian
    "pt": "pt",  # Portuguese
}

def translate_value(value: Any, field_name: str, target_lang: str, translate_func) -> Any:
    """Recursively translate JSON values."""
    if isinstance(value, str):
        # Only translate certain fields
        translatable_fields = ['name', 'description', 'killteamName', 'opTypeName', 
                              'wepName', 'abilityName', 'ployName', 'eqName', 
                              'optionName', 'title', 'profileName', 'composition',
                              'reveal', 'additionalRules', 'victoryPoints']
        
        if field_name in translatable_fields and value and value.strip():
            try:
                translated = translate_func(value, target_lang)
                print(f"    Translated {field_name}: {value[:50]}... -> {translated[:50]}...")
                return translated
            except Exception as e:
                print(f"    [WARNING] Translation failed for {field_name}: {e}")
                return value
        return value
    elif isinstance(value, dict):
        return {k: translate_value(v, k, target_lang, translate_func) for k, v in value.items()}
    elif isinstance(value, list):
        if field_name == 'archetypes' and value and isinstance(value[0], str):
            # Translate archetype values
            archetype_map = {
                "es": {"Security": "Seguridad", "Seek & Destroy": "Buscar y Destruir", 
                      "Recon": "Reconocimiento", "Infiltration": "Infiltración"},
                "fr": {"Security": "Sécurité", "Seek & Destroy": "Rechercher et Détruire",
                      "Recon": "Reconnaissance", "Infiltration": "Infiltration"}
            }
            return [archetype_map.get(target_lang, {}).get(v, translate_func(v, target_lang)) 
                   if isinstance(v, str) else v for v in value]
        elif field_name in ['effects', 'conditions'] and value and isinstance(value[0], str):
            return [translate_func(v, target_lang) if isinstance(v, str) and v.strip() else v 
                   for v in value]
        elif field_name == 'packs' and value and isinstance(value[0], str):
            # Translate pack names
            return [translate_func(v, target_lang) if isinstance(v, str) else v for v in value]
        return [translate_value(item, field_name, target_lang, translate_func) for item in value]
    else:
        return value

def translate_file(en_file: Path, target_file: Path, target_lang: str, translate_func, api_name: str):
    """Translate a JSON file using the specified translation function."""
    print(f"\nTranslating {en_file.name} to {target_lang} using {api_name}...")
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Reading {en_file}: {e}")
        return False
    
    # Translate
    try:
        translated = translate_value(data, "", target_lang, translate_func)
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
        return False
    
    # Validate JSON
    try:
        json.dumps(translated)
    except Exception as e:
        print(f"  [ERROR] Invalid JSON after translation: {e}")
        return False
    
    # Write
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(translated, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Created {target_file.name}")
        return True
    except Exception as e:
        print(f"  [ERROR] Writing {target_file}: {e}")
        return False

def main():
    """Main translation function."""
    if len(sys.argv) < 2:
        print("Usage: python translate_with_api.py <language> [provider]")
        print("  language: es (Spanish) or fr (French)")
        print("  provider: deepl, google, or manual (default: google)")
        print("\nExample:")
        print("  python translate_with_api.py es google")
        print("  python translate_with_api.py fr deepl")
        sys.exit(1)
    
    target_lang = sys.argv[1].lower()
    provider = sys.argv[2].lower() if len(sys.argv) > 2 else "google"
    
    if target_lang not in ["es", "fr"]:
        print(f"Error: Unsupported language '{target_lang}'. Use 'es' or 'fr'")
        sys.exit(1)
    
    # Select translation function
    if provider == "deepl":
        translate_func = lambda text, lang: translate_text_deepl(text, lang.upper())
        api_name = "DeepL"
    elif provider == "google":
        translate_func = lambda text, lang: translate_text_google(text, lang)
        api_name = "Google Translate"
    elif provider == "manual":
        if target_lang == "es":
            translate_func = lambda text, lang: translate_text_manual_spanish(text)
        else:
            translate_func = lambda text, lang: translate_text_manual_french(text)
        api_name = "Manual (placeholder)"
    else:
        print(f"Error: Unknown provider '{provider}'. Use 'deepl', 'google', or 'manual'")
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
    
    print("=" * 60)
    print(f"Translating all JSON files to {target_lang.upper()} using {api_name}")
    print("=" * 60)
    
    for filename in files:
        en_file = en_dir / filename
        target_file = target_dir / filename
        
        if en_file.exists():
            translate_file(en_file, target_file, target_lang, translate_func, api_name)
        else:
            print(f"  [WARNING] {en_file} not found")
    
    print("\n" + "=" * 60)
    print("[OK] Translation complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

