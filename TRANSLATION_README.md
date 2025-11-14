# Translation Guide - Automated Translation Solutions

## Problem: Google Translate Rate Limits

The Google Translate free API has strict rate limits (approximately 1 request per 0.3-0.5 seconds). For large files or many individual team files with thousands of translatable strings, this means:
- **Estimated time**: 20-40 minutes per team file, 3-5+ hours for all teams
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

1. **Extract translatables**: `python tools/extract_translatables.py en/teams/IMP-AOD.json > translatables.txt`
2. **Translate manually** using Google Translate website or DeepL
3. **Validate**: `python tools/validate_translation.py en/teams/IMP-AOD.json es/teams/IMP-AOD.json`
4. **Check completeness**: `python tools/check_translation_completeness.py en/teams/IMP-AOD.json es/teams/IMP-AOD.json`

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

1. **Small files first**: Translate `actions.json`, `weapon_rules.json` first (few minutes each)
2. **Team files**: Use DeepL API or manual translation for individual team files in `teams/` folder
3. **Validate**: Always run `validate_translation.py` after translation
4. **Review**: Check for Games Workshop terminology consistency

**Note:** Team files are now split into individual files (e.g., `teams/IMP-AOD.json`) instead of a single monolithic `teams.json`. This makes translation more manageable as you can translate teams one at a time.

## Estimated Translation Times (Google Translate)

| File | Strings | Estimated Time |
|------|---------|----------------|
| actions.json | ~70 | 15-20 minutes |
| universal_equipment.json | ~100 | 20-30 minutes |
| weapon_rules.json | ~200 | 40-60 minutes |
| ops_2025.json | ~300 | 60-90 minutes |
| teams/*.json (per team) | ~100-200 | 20-40 minutes per team |
| All team files (42 teams) | ~5000+ | **3-5+ hours** total |

**Total**: ~6-8 hours for all files

**Note:** Since teams are now split into individual files, you can translate teams incrementally. For individual team files, **strongly recommend using DeepL API** or manual translation for better quality.

