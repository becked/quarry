# Adding Wiki Categories

How to add a new wiki category to the quarry extraction pipeline.

## Quick Version

1. Open the source XML file and read the first `<Entry>` (schema template) to see all fields
2. Add a `CategoryDef` to the `CATEGORIES` dict in `src/quarry/categories.py`
3. Run the pipeline and inspect the JSON output

That's it. The generic parser handles all XML files — no parsing code needed.

## Step by Step

### 1. Examine the XML Source

Every XML file in `Reference/XML/Infos/` has the same structure. The first `<Entry>` is a schema template listing every possible field with empty values. Open the source file and read this entry to understand the field landscape.

Quick way to dump the schema and a sample entry:

```bash
uv run python -c "
from quarry.xml_parser import parse_xml_file
from pathlib import Path
import json

entries = parse_xml_file(Path('Reference/XML/Infos/YOUR_FILE.xml'))
print(f'{len(entries)} entries')
print(json.dumps(entries[0], indent=2))
"
```

This shows the first *real* entry (the schema template is already skipped). Fields with default/empty values are omitted, so this shows you what a populated entry looks like.

### 2. Identify Text Fields

Look for fields whose values start with `TEXT_`, `GENDERED_TEXT_`, or similar localization key prefixes. Common text fields:

| XML Field | Typical Output Name | Notes |
|-----------|-------------------|-------|
| `Name` | `name` | Display name |
| `GenderedName` | `name` | Gendered variant (same purpose) |
| `Description` | `description` | |
| `Advice` | `advice` | In-game guidance |
| `History` | `history` | Flavor text |
| `Help` | `help` | Tooltip text |
| `Encyclopedia` | `encyclopedia` | Encyclopedia body |

These need `TextField` entries so the pipeline resolves the key to a display string instead of outputting the raw `TEXT_...` key.

### 3. Determine the Filter

Check `docs/wiki-categories.txt` for the filter logic. The filter receives a raw parsed entry (dict with original XML field names, *not* normalized names) and returns `True` to include.

The `m` prefix in wiki-categories.txt is C# member naming — drop it for the XML field name:
- `mbEncyclopedia` → `bEncyclopedia` in XML (parsed as `True`/`False`)
- `mbWonder` → `bWonder`
- `meFirstRuler` → `FirstRuler` (no prefix in XML, parsed as string)
- `miSubjectWeight` → `iSubjectWeight` (parsed as int)

The parser keeps `False` booleans in the parsed dict (so filters can distinguish "explicitly false" from "not set") but omits them from JSON output. `None` values are omitted everywhere.

**Important:** Some boolean fields have a default of `true` in the game's C# code (e.g., `bEncyclopedia` for improvements, traits, occurrences). These fields are often absent from the XML, meaning entries rely on the game default. For default-true fields, use:

```python
entry.get("bEncyclopedia") is not False  # includes absent (default true) and explicit true
```

For default-false fields (e.g., `bEncyclopedia` on missions), use:

```python
entry.get("bEncyclopedia") is True  # requires explicit true
```

Checking for an explicitly-false boolean:

```python
entry.get("bWonder") is not True  # excludes only explicit true
```

### 4. Check for Expansion Files

Look for variant files with suffixes (`-wog`, `-btt`, `-sap`, `-wd`):

```bash
ls Reference/XML/Infos/ | grep "^yourfile"
```

If expansion files exist (e.g., `council-btt.xml`), list them in `expansion_files`. They're parsed and merged into the base entries automatically.

### 5. Write the CategoryDef

Add an entry to the `CATEGORIES` dict in `src/quarry/categories.py`.

**Simple category** (no filter, no expansion files):

```python
"yields": CategoryDef(
    name="yields",
    display_name="Yields",
    xml_file="yield.xml",
    text_fields=[
        TextField("Name", "name"),
        TextField("Help", "help"),
        TextField("Encyclopedia", "encyclopedia"),
    ],
),
```

**Filtered category:**

```python
"projects": CategoryDef(
    name="projects",
    display_name="Projects",
    xml_file="project.xml",
    filter_fn=lambda e: e.get("bEncyclopedia") is True and "bHidden" not in e,
    text_fields=[
        TextField("Name", "name"),
        TextField("Description", "description"),
    ],
),
```

**Category with expansion files:**

```python
"councils": CategoryDef(
    name="councils",
    display_name="Councils",
    xml_file="council.xml",
    expansion_files=["council-btt.xml"],
    text_fields=[
        TextField("Name", "name"),
    ],
),
```

**Split category** (multiple categories from one XML file):

```python
"wonders": CategoryDef(
    name="wonders",
    display_name="Wonders",
    xml_file="improvement.xml",
    filter_fn=lambda e: e.get("bEncyclopedia") is True and e.get("bWonder") is True,
    text_fields=[
        TextField("Name", "name"),
        TextField("Description", "description"),
    ],
),
```

### 6. Run and Verify

```bash
# Extract just your new category
uv run python -m quarry --game-path . --language en-US --output-dir ./output --categories your_category

# Check the output
python -c "
import json
with open('output/your_category.json') as f:
    data = json.load(f)
print(f'{len(data[\"entries\"])} entries')
# Print first entry
first_key = next(iter(data['entries']))
print(json.dumps(data['entries'][first_key], indent=2))
"
```

Things to check:
- Entry count is reasonable
- Text fields show display strings, not `TEXT_...` keys
- Field names are camelCase (Hungarian prefixes stripped)
- No `null` values or `"NONE"` strings
- Boolean fields are `true` only (false values are omitted)

## CategoryDef Reference

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `name` | `str` | required | JSON filename slug and meta.category value |
| `display_name` | `str` | required | Human-readable category name |
| `xml_file` | `str` | required | Source filename in `Reference/XML/Infos/` |
| `expansion_files` | `list[str]` | `[]` | Expansion variant filenames to merge |
| `filter_fn` | `EntryFilter` | `no_filter` | Predicate receiving raw parsed entry dict |
| `text_fields` | `list[TextField]` | `[]` | Fields to resolve via text dictionary |
| `exclude_fields` | `set[str]` | `set()` | XML field names to omit from output |

`TextField` has three fields: `xml_field` (source), `output_field` (JSON key), and optional `text_key_prefix` (prepended before text lookup, e.g. `"TEXT_"` for character FirstName fields).

Built-in filters:
- `no_filter` — accept all entries
- `encyclopedia_default_true` — exclude entries that explicitly set `bEncyclopedia=0` (for types where it defaults to true)
- `encyclopedia_default_false` — include only entries that explicitly set `bEncyclopedia=1` (for types where it defaults to false)

## How Field Names are Normalized

The pipeline strips Hungarian prefixes and produces camelCase:

| XML | JSON | Rule |
|-----|------|------|
| `iCost` | `cost` | prefix `i` stripped |
| `bMelee` | `melee` | prefix `b` stripped |
| `zIconName` | `iconName` | prefix `z` stripped |
| `aeNationValid` | `nationValid` | prefix `ae` stripped |
| `abTechPrereq` | `techPrereq` | prefix `ab` stripped |
| `aiYieldCost` | `yieldCost` | prefix `ai` stripped |
| `aaiTerrainYieldModifier` | `terrainYieldModifier` | prefix `aai` stripped |
| `Name` | (resolved) | text field, not normalized |
| `EffectPlayer` | `effectPlayer` | no prefix, first char lowered |
| `TechPrereq` | `techPrereq` | no prefix, first char lowered |
| `zType` | (used as dict key) | never appears as a field |

## How Data Types are Parsed

The parser detects types from the Hungarian prefix on the XML tag:

| Prefix | Parsed As | JSON Type | Notes |
|--------|-----------|-----------|-------|
| `i` | int | `number` | `-1` sentinel → omitted |
| `f` | float | `number` | |
| `b` | bool | `true` | `false` kept in parsed dict, omitted from JSON |
| `z`, `e` | string | `"string"` | `"NONE"` → omitted |
| no prefix | string | `"string"` | `Name`, `EffectPlayer`, etc. |
| `ae` | list | `["A", "B"]` | or string map if `<Pair>` children |
| `ai` | int map | `{"K": 1}` | |
| `ab` | bool map | `["K1", "K2"]` | keys only (values always true) |
| `az` | string map | `{"K": "V"}` | |
| `aae` | enum list map | `{"K": ["V1"]}` | |
| `aai` | 2D int map | `{"K": {"SK": 1}}` | |

## Common Patterns

**Reusable filter for encyclopedia-visible entries:**

Many categories use `bEncyclopedia` as a visibility flag. Rather than repeating lambdas, add a named filter in `categories.py`:

```python
def encyclopedia_filter(entry: dict[str, Any]) -> bool:
    """Include only entries marked for the encyclopedia."""
    return entry.get("bEncyclopedia") is True
```

**Combining filters:**

```python
def improvements_filter(entry: dict[str, Any]) -> bool:
    return (
        entry.get("bEncyclopedia") is True
        and entry.get("bBuild") is True
        and "bWonder" not in entry
        and entry.get("ReligionPrereq") is None
    )
```

**Excluding internal fields:**

Some files have fields that are only relevant to the game engine (audio, animation, asset references). Use `exclude_fields` to keep them out of the JSON:

```python
exclude_fields={"zAudioLoopWhenBuilding", "zAudioSwitchName", "AssetVariation"},
```
