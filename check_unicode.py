#!/usr/bin/env python3
"""
Script to detect and optionally fix ambiguous Unicode characters in JSON files.
"""

import json
import sys
from collections import Counter

# Mapping of ambiguous Unicode characters to ASCII equivalents
UNICODE_TO_ASCII = {
    '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK (curly apostrophe)
    '\u2018': "'",  # LEFT SINGLE QUOTATION MARK (curly opening quote)
    '\u201C': '"',  # LEFT DOUBLE QUOTATION MARK (curly opening quote)
    '\u201D': '"',  # RIGHT DOUBLE QUOTATION MARK (curly closing quote)
    '\u2013': '-',  # EN DASH
    '\u2014': '-',  # EM DASH
    '\u00A0': ' ',  # NON-BREAKING SPACE
    '\u2026': '...', # HORIZONTAL ELLIPSIS
    '\u00C2': 'A',  # LATIN CAPITAL LETTER A WITH CIRCUMFLEX
    '\u00D4': 'O',  # LATIN CAPITAL LETTER O WITH CIRCUMFLEX
    '\u00E2': 'a',  # LATIN SMALL LETTER A WITH CIRCUMFLEX
    '\u00F4': 'o',  # LATIN SMALL LETTER O WITH CIRCUMFLEX
}

def analyze_file(filename):
    """Analyze a file for ambiguous Unicode characters."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Find all non-ASCII characters
    ambiguous_chars = {}
    for i, char in enumerate(content):
        if ord(char) > 127 and char not in '\n\r\t':
            ambiguous_chars[i] = char
    
    if not ambiguous_chars:
        print(f"[OK] {filename}: No ambiguous Unicode characters found")
        return
    
    # Count occurrences
    char_counts = Counter(ambiguous_chars.values())
    
    print(f"\n{filename}: Found {len(ambiguous_chars)} ambiguous Unicode characters")
    print("\nTop ambiguous characters:")
    for char, count in char_counts.most_common(10):
        ascii_equiv = UNICODE_TO_ASCII.get(char, '?')
        print(f"  {repr(char)} (U+{ord(char):04X}) -> '{ascii_equiv}': {count} occurrences")
    
    # Show sample locations
    print("\nSample locations (first 5):")
    for i, (pos, char) in enumerate(list(ambiguous_chars.items())[:5]):
        line_num = content[:pos].count('\n') + 1
        col_num = pos - content.rfind('\n', 0, pos) - 1
        context = content[max(0, pos-20):pos+20].replace('\n', '\\n')
        print(f"  Line {line_num}, Col {col_num}: {repr(context)}")

def fix_string_value(value, replacements_count):
    """Recursively fix ambiguous Unicode characters in JSON values."""
    if isinstance(value, str):
        original = value
        fixed = value
        for unicode_char, ascii_char in UNICODE_TO_ASCII.items():
            if unicode_char in fixed:
                count = fixed.count(unicode_char)
                fixed = fixed.replace(unicode_char, ascii_char)
                replacements_count[0] += count
                if count > 0:
                    print(f"  Replaced {count} occurrences of {repr(unicode_char)} (U+{ord(unicode_char):04X}) with '{ascii_char}'")
        return fixed
    elif isinstance(value, dict):
        return {key: fix_string_value(val, replacements_count) for key, val in value.items()}
    elif isinstance(value, list):
        return [fix_string_value(item, replacements_count) for item in value]
    else:
        return value

def fix_file(filename, backup=True):
    """Fix ambiguous Unicode characters in a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Parse JSON first to validate
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON before fixing: {e}")
        return False
    
    # Create backup
    if backup:
        backup_filename = filename + '.backup'
        with open(backup_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created backup: {backup_filename}")
    
    # Fix ambiguous characters only in string values
    replacements_count = [0]
    print("Fixing ambiguous characters in JSON string values...")
    fixed_data = fix_string_value(data, replacements_count)
    
    if replacements_count[0] == 0:
        print("No replacements needed")
        return False
    
    # Validate JSON after fixing
    try:
        # This will validate the structure is still valid
        json.dumps(fixed_data)
        print("[OK] JSON is valid after replacements")
    except Exception as e:
        print(f"[ERROR] JSON validation failed: {e}")
        return False
    
    # Write fixed content with proper JSON formatting
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Fixed {replacements_count[0]} ambiguous characters in {filename}")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_unicode.py <filename> [--fix]")
        print("  --fix: Actually fix the file (creates a backup first)")
        sys.exit(1)
    
    filename = sys.argv[1]
    fix = '--fix' in sys.argv
    
    if fix:
        print(f"Fixing ambiguous Unicode characters in {filename}...")
        fix_file(filename)
    else:
        print(f"Analyzing {filename} for ambiguous Unicode characters...")
        analyze_file(filename)
        print("\nTo fix these issues, run with --fix flag")
        print("Example: python check_unicode.py teams.json --fix")

