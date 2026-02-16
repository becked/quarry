# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Quarry is a Python data extraction pipeline for the Old World strategy game. It reads static XML game data from a local install and outputs structured JSON for wiki/encyclopedia applications. Pure Python 3.13+, zero dependencies.

## Running the Pipeline

```bash
# Full extraction (all 37 categories)
uv run python -m quarry --game-path "$(pwd)" --language en-US --output-dir ./output

# Single category
uv run python -m quarry --game-path "$(pwd)" --categories technologies

# Quick inspection of parsed XML (no pipeline needed)
uv run python -c "
from quarry.xml_parser import parse_xml_file
from pathlib import Path
import json
entries = parse_xml_file(Path('Reference/XML/Infos/tech.xml'))
print(json.dumps(entries[0], indent=2))
"
```

Game data lives at `Reference/` (a symlink to the local game install's XML/Source directories). This symlink is gitignored.

## Architecture

Five-stage pipeline in `src/quarry/pipeline.py`:

1. **Parse** (`xml_parser.py`) — Generic XML parser auto-detects field types from Hungarian notation prefixes (`iCost`→int, `bMelee`→bool, `zName`→string, `aiYieldCost`→sparse int map, etc.). Prefix list checked longest-first: `aai` > `aae` > `ae` > `ai` > `ab` > `az` > `i` > `f` > `b` > `z` > `e`.

2. **Filter** (`categories.py`) — Entry-level predicates on the raw parsed dict (original XML field names, not normalized). Filters receive booleans including explicit `False` values.

3. **Resolve text** (`text_resolver.py`) — Maps `TEXT_*` keys to display strings via `text-*.xml`. GenderedName fields use two-step resolution: `GENDERED_TEXT_*` → masculine `TEXT_*` via `genderedText*.xml` → display string.

4. **Normalize** (`pipeline.py`) — Strips Hungarian prefixes, lowercases first char: `iCost`→`cost`, `EffectPlayer`→`effectPlayer`. Omits `False` booleans from JSON output.

5. **Emit** — One JSON file per category, keyed by `zType`.

## Boolean Default Handling

The parser **keeps `False` booleans** in the parsed dict so filters can distinguish "explicitly false" from "not set". The game's C# code has per-type defaults (e.g., `bEncyclopedia` defaults to `true` for improvements but `false` for missions).

- Default-true fields: `entry.get("bEncyclopedia") is not False`
- Default-false fields: `entry.get("bEncyclopedia") is True`

`False` values are stripped during JSON output in `pipeline.py`, not in the parser.

## Adding Categories

See `docs/adding-categories.md` for the full guide. In short: add a `CategoryDef` to the `CATEGORIES` dict in `categories.py`. The generic parser handles all XML files — no per-category parsing code.

Split categories (multiple outputs from one XML file) use different `filter_fn` values on the same `xml_file` (e.g., `improvement.xml` → 4 categories, `trait.xml` → 4 categories).

## Key Conventions

- `Reference/XML/Infos/` contains all game XML data files
- Schema entries (first `<Entry>` in base files with empty `zType`) are auto-skipped
- Expansion files (`-wog`, `-btt`, `-sap`, `-wd` suffixes) are listed in `expansion_files` on the CategoryDef
- Sentinel values (`-1` ints, `NONE` strings, empty tags) are parsed as `None` and omitted
- Text markup (`link(...)`, `{0}`, `{lowercase:...}`) is passed through as-is
