# Translation Guide - Automated Translation Solutions

## Problem: Google Translate Rate Limits

The Google Translate free API has strict rate limits (approximately 1 request per 0.3-0.5 seconds). For large files like `teams.json` with thousands of translatable strings, this means:
- **Estimated time**: 30-60+ minutes per large file
- **Risk**: API blocks/errors if rate limits exceeded

## Solutions

### Option 1: DeepL API (Recommended for Speed & Quality)

**Pros:**
- Much faster (no strict rate limits for paid tier)
- Better translation quality
- Official API support

**Cons:**
- Requires API key (free tier: 500,000 chars/month)
- Costs money for heavy usage

**Setup:**
1. Get API key from https://www.deepl.com/pro-api
2. Set environment variable: `export DEEPL_API_KEY=your_key_here`
3. Install: `pip install deepl`
4. Run: `python tools/translate_comprehensive.py es deepl`

### Option 2: Google Translate (Free but Slow)

**Pros:**
- Free
- No API key needed

**Cons:**
- Very slow (30-60+ minutes for large files)
- Rate limits may cause errors
- Lower quality than DeepL

**Usage:**
```bash
python tools/translate_fast.py es
```

**Note**: This will take a very long time. Consider running in background:
```bash
nohup python tools/translate_fast.py es > translation.log 2>&1 &
```

### Option 3: Manual Translation + Scripts

For best quality, translate manually using the existing tools:

1. **Extract translatables**: `python tools/extract_translatables.py en/teams.json > translatables.txt`
2. **Translate manually** using Google Translate website or DeepL
3. **Validate**: `python tools/validate_translation.py en/teams.json es/teams.json`
4. **Check completeness**: `python tools/check_translation_completeness.py es/teams.json en/teams.json`

## Important: Field Names Stay in English

**Critical**: JSON field names must remain in English for API compatibility:
- ✅ `"name": "Operar Escotilla"` (value translated)
- ❌ `"nombre": "Operar Escotilla"` (field name translated - WRONG)

Only translate **values**, not **keys**.

## Current Scripts

- `tools/translate_comprehensive.py` - Supports both Google and DeepL
- `tools/translate_fast.py` - Google Translate only, with progress tracking
- `tools/translate_batch.py` - Attempts batch translation (experimental)

## Recommended Workflow

1. **Small files first**: Translate `mission_actions.json`, `universal_actions.json` first (few minutes each)
2. **Large files**: Use DeepL API or manual translation for `teams.json`
3. **Validate**: Always run `validate_translation.py` after translation
4. **Review**: Check for Games Workshop terminology consistency

## Estimated Translation Times (Google Translate)

| File | Strings | Estimated Time |
|------|---------|----------------|
| mission_actions.json | ~20 | 5-10 minutes |
| universal_actions.json | ~50 | 10-15 minutes |
| universal_equipment.json | ~100 | 20-30 minutes |
| weapon_rules.json | ~200 | 40-60 minutes |
| ops_2025.json | ~300 | 60-90 minutes |
| teams.json | ~5000+ | **3-5+ hours** |

**Total**: ~6-8 hours for all files

For `teams.json`, **strongly recommend using DeepL API** or manual translation.

