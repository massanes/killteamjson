#!/usr/bin/env python3
"""
Batch translation script that translates all JSON files using Google Translate.
Uses batching and better rate limiting for faster translation.
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, List, Dict

# Fields that should NOT be translated (IDs, keys, etc.)
NON_TRANSLATABLE_FIELDS = {'id', 'type', 'seq', 'AP', 'APL', 'GA', 'DF', 'SV', 'W', 'M', 
                           'MV', 'APL_base', 'GA_base', 'DF_base', 'SV_base', 'W_base', 
                           'M_base', 'MV_base', 'D', 'A', 'BS', 'WS', 'version', 'file'}

# Fields that should be translated
TRANSLATABLE_FIELDS = {'name', 'description', 'killteamName', 'opTypeName', 'wepName', 
                       'abilityName', 'ployName', 'eqName', 'optionName', 'title', 
                       'profileName', 'composition', 'reveal', 'additionalRules', 
                       'victoryPoints', 'effects', 'conditions', 'packs', 'archetypes',
                       'ability', 'keyword', 'team'}

def translate_batch(texts: List[str], target_lang: str, source_lang: str = "en") -> List[str]:
    """
    Translate multiple texts in a single API call using Google Translate web API.
    This is much faster than individual calls.
    """
    try:
        import requests
        
        # Join texts with a delimiter
        # Note: Google Translate has a 5000 char limit, so we may need to split
        max_chars = 4000
        results = []
        
        current_batch = []
        current_size = 0
        
        for text in texts:
            # Estimate size (roughly 2x for URL encoding)
            text_size = len(text) * 2
            
            if current_size + text_size > max_chars and current_batch:
                # Translate current batch
                batch_text = '\n'.join(current_batch)
                translated = translate_text(batch_text, target_lang, source_lang)
                # Split back (Google Translate preserves newlines)
                results.extend(translated.split('\n'))
                current_batch = [text]
                current_size = text_size
                time.sleep(0.5)  # Rate limit delay
            else:
                current_batch.append(text)
                current_size += text_size
        
        # Translate remaining batch
        if current_batch:
            batch_text = '\n'.join(current_batch)
            translated = translate_text(batch_text, target_lang, source_lang)
            results.extend(translated.split('\n'))
            time.sleep(0.5)
        
        # Ensure we have same number of results
        while len(results) < len(texts):
            results.append("")
        
        return results[:len(texts)]
        
    except Exception as e:
        print(f"    [WARNING] Batch translation error: {e}")
        return texts  # Return original on error

def translate_text(text: str, target_lang: str, source_lang: str = "en") -> str:
    """Translate a single text using Google Translate web API."""
    if not text or not text.strip():
        return text
    
    try:
        import requests
        import urllib.parse
        
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": source_lang,
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
        print(f"    [WARNING] Translation error: {e}")
        return text

def collect_translatable_strings(data: Any, field_name: str = "", path: str = "") -> List[Dict]:
    """Collect all translatable strings from JSON with their paths for restoration."""
    strings = []
    
    if isinstance(data, str):
        if should_translate_field(field_name, data) and data.strip():
            strings.append({"path": path, "field": field_name, "value": data})
    elif isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{path}.{k}" if path else k
            strings.extend(collect_translatable_strings(v, k, new_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]" if path else f"[{i}]"
            if isinstance(item, str) and should_translate_field(field_name, item) and item.strip():
                strings.append({"path": new_path, "field": field_name, "value": item})
            else:
                strings.extend(collect_translatable_strings(item, field_name, new_path))
    
    return strings

def should_translate_field(field_name: str, value: Any) -> bool:
    """Determine if a field should be translated."""
    if field_name in NON_TRANSLATABLE_FIELDS:
        return False
    if field_name in TRANSLATABLE_FIELDS:
        return True
    # For unknown fields, translate if it's a string and not empty
    if isinstance(value, str) and value.strip() and not field_name.startswith('_'):
        if field_name.lower().endswith(('id', '_id', 'code', '_code')):
            return False
        return True
    return False

def set_value_by_path(data: Any, path: str, value: str):
    """Set a value in nested dict/list using dot notation path."""
    parts = path.split('.')
    current = data
    
    for i, part in enumerate(parts[:-1]):
        if '[' in part:
            # Handle list indices
            base, idx = part.split('[')
            idx = int(idx.rstrip(']'))
            if base:
                current = current[base][idx]
            else:
                current = current[idx]
        else:
            current = current[part]
    
    # Set final value
    final_part = parts[-1]
    if '[' in final_part:
        base, idx = final_part.split('[')
        idx = int(idx.rstrip(']'))
        if base:
            current[base][idx] = value
        else:
            current[idx] = value
    else:
        current[final_part] = value

def translate_file(en_file: Path, target_file: Path, target_lang: str):
    """Translate a JSON file using batch translation."""
    print(f"\nTranslating {en_file.name} to {target_lang.upper()}...")
    
    try:
        with open(en_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to read {en_file}: {e}")
        return False
    
    # Collect all translatable strings
    print(f"  Collecting translatable strings...")
    translatable_strings = collect_translatable_strings(data)
    
    if not translatable_strings:
        print(f"  [SKIP] No translatable strings found")
        return False
    
    print(f"  Found {len(translatable_strings)} strings to translate")
    
    # Batch translate
    print(f"  Translating in batches (this may take a while)...")
    texts = [s["value"] for s in translatable_strings]
    
    try:
        translated_texts = translate_batch(texts, target_lang)
    except Exception as e:
        print(f"  [ERROR] Translation failed: {e}")
        return False
    
    # Apply translations back to data structure
    print(f"  Applying translations...")
    for i, string_info in enumerate(translatable_strings):
        if i < len(translated_texts):
            set_value_by_path(data, string_info["path"], translated_texts[i])
    
    # Validate and write
    try:
        json.dumps(data)
    except Exception as e:
        print(f"  [ERROR] Invalid JSON after translation: {e}")
        return False
    
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] Created {target_file.name}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to write {target_file}: {e}")
        return False

def main():
    """Main translation function."""
    if len(sys.argv) < 2:
        print("Usage: python translate_batch.py <language>")
        print("\nArguments:")
        print("  language  - Target language: es (Spanish) or fr (French)")
        print("\nExample:")
        print("  python translate_batch.py es")
        print("\nNote: This uses Google Translate web API which is free but has rate limits.")
        print("Translation may take 10-30 minutes depending on file size.")
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
    print(f"Batch Translating all JSON files to {target_lang.upper()}")
    print("=" * 70)
    print("\nThis will translate all text content using Google Translate.")
    print("Due to rate limits, this may take 10-30 minutes...")
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
                print(f"  Completed in {elapsed:.1f} seconds")
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

