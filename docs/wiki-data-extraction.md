# Old World Wiki Data Extraction — Design Document

## Project Overview

A standalone data extraction pipeline that reads Old World's static game data from XML files and outputs structured JSON. The output serves as the data layer for wiki/encyclopedia client applications (iOS app, web app, etc.).

**Key constraints:**

- No game runtime required — the pipeline reads XML files directly from a local Old World installation
- Separate project from the OldWorldAPIEndpoint mod — no shared code or dependencies
- Clients consume the JSON output; the pipeline does not serve data or provide an API
- Single pipeline run per game version (no incremental diffing)

## Data Source

### Location

Old World stores all static game data as XML files within the installation directory:

```
<Old World Install>/Reference/XML/Infos/
```

Platform-specific installation paths:

| Platform | Typical Path |
|----------|-------------|
| macOS (Steam) | `~/Library/Application Support/Steam/steamapps/common/Old World/Reference/XML/Infos/` |
| Windows (Steam) | `C:\Program Files (x86)\Steam\steamapps\common\Old World\Reference\XML\Infos\` |
| Windows (Epic/GOG) | Varies by launcher |

The pipeline accepts the Old World installation path as a CLI argument.

### Scope

The directory contains **338 XML files** covering **160+ entity categories**. Every category of static game data — units, technologies, improvements, nations, laws, religions, traits, effects, terrain, and more — is represented.

### Game Version

The game version (e.g., `1.0.81366 (2026-01-07)`) is stored in a Unity asset bundle (`Resources/Version/Version.xml`) and is not trivially accessible from the filesystem. On macOS it is also in the app bundle's `Info.plist` under `CFBundleShortVersionString`, but this is platform-specific.

**Recommendation:** Accept the game version as an optional CLI argument and embed it in the JSON output metadata. If not provided, omit it.

## XML Structure Reference

### File Layout

Every XML data file follows the same pattern:

```xml
<?xml version="1.0"?>
<Root>
  <Entry>              <!-- Schema entry: all possible fields, empty -->
    <zType/>
    <Name/>
    <iStrength/>
    <!-- ... every field the entity type supports ... -->
  </Entry>
  <Entry>              <!-- First real data entry -->
    <zType>UNIT_WARRIOR</zType>
    <Name>TEXT_UNIT_WARRIOR</Name>
    <iStrength>40</iStrength>
    <!-- only populated fields are present -->
  </Entry>
  <Entry>              <!-- Second real data entry -->
    <zType>UNIT_ARCHER</zType>
    <!-- ... -->
  </Entry>
</Root>
```

**The first `<Entry>` in every file is a schema template** — it lists all possible fields with empty values. It must be skipped during data extraction. All subsequent entries are real data.

Only populated fields appear in data entries. Absent fields should be treated as their type's default (0 for integers, false for booleans, null for enum references).

### Field Naming Conventions

Field names encode their data type via Hungarian notation prefixes:

| Prefix | Type | Example |
|--------|------|---------|
| `z` | String | `<zType>UNIT_WARRIOR</zType>` |
| `i` | Integer | `<iStrength>40</iStrength>` |
| `f` | Float | `<fAttackDuration>2.0</fAttackDuration>` |
| `b` | Boolean (0/1) | `<bMelee>1</bMelee>` |
| `m` | Mixed/no prefix | `<Name>TEXT_UNIT_WARRIOR</Name>` |
| `e` | Enum reference | `<eTechPrereq>TECH_IRONWORKING</eTechPrereq>` |
| `ae` | List of enums | `<aeUpgradeUnit>` container |
| `ai` | Sparse int map (enum-indexed) | `<aiYieldCost>` container |
| `ab` | Sparse bool map (enum-indexed) | `<abTechPrereq>` container |
| `az` | Sparse string map (enum-indexed) | `<azGenderPortraitName>` container |
| `aai` | 2D sparse map | `<aaiTerrainYieldModifier>` container |

### Data Patterns

The XML uses 7 distinct structural patterns. Every field in every file uses one of these.

#### Pattern 1: Single Value

Primitive values or enum references stored as element text.

```xml
<!-- Integer -->
<iMovement>2</iMovement>

<!-- Float -->
<fAttackDuration>2.0</fAttackDuration>

<!-- Boolean (0 or 1, not true/false) -->
<bMelee>1</bMelee>

<!-- String / enum reference -->
<TechPrereq>TECH_IRONWORKING</TechPrereq>

<!-- Localization key -->
<Name>TEXT_UNIT_WARRIOR</Name>
```

#### Pattern 2: Simple List

An ordered collection of enum values.

```xml
<aeUpgradeUnit>
  <zValue>UNIT_AXEMAN</zValue>
  <zValue>UNIT_SPEARMAN</zValue>
</aeUpgradeUnit>

<aeUnitTrait>
  <zValue>UNITTRAIT_MELEE</zValue>
  <zValue>UNITTRAIT_INFANTRY</zValue>
</aeUnitTrait>
```

**Output:** JSON array of strings.

#### Pattern 3: Sparse Integer Map (Enum-Indexed)

Maps enum keys to integer values. Only non-default entries are present.

```xml
<aiYieldCost>
  <Pair>
    <zIndex>YIELD_IRON</zIndex>
    <iValue>50</iValue>
  </Pair>
  <Pair>
    <zIndex>YIELD_FOOD</zIndex>
    <iValue>100</iValue>
  </Pair>
</aiYieldCost>
```

**Output:** JSON object with string keys and integer values.

#### Pattern 4: Sparse Boolean Map

Maps enum keys to boolean flags. Only true entries are present (absence = false).

```xml
<abTechPrereq>
  <Pair>
    <zIndex>TECH_IRONWORKING</zIndex>
    <bValue>1</bValue>
  </Pair>
  <Pair>
    <zIndex>TECH_STONECUTTING</zIndex>
    <bValue>1</bValue>
  </Pair>
</abTechPrereq>
```

**Output:** JSON array of the key strings (since all values are true, the keys are sufficient).

#### Pattern 5: Sparse String/Enum Map

Maps enum keys to string or enum values.

```xml
<azGenderPortraitName>
  <Pair>
    <zIndex>GENDER_MALE</zIndex>
    <zValue>UNIT_WARRIOR</zValue>
  </Pair>
  <Pair>
    <zIndex>GENDER_FEMALE</zIndex>
    <zValue>UNIT_FEMALE_WARRIOR</zValue>
  </Pair>
</azGenderPortraitName>
```

**Output:** JSON object with string keys and string values.

#### Pattern 6: 2D Sparse Map

Maps two enum dimensions to a value. Used for relationships like terrain + yield = modifier.

```xml
<aaiTerrainYieldModifier>
  <Pair>
    <zIndex>TERRAIN_LUSH</zIndex>
    <SubPair>
      <zSubIndex>YIELD_FOOD</zSubIndex>
      <iValue>40</iValue>
    </SubPair>
  </Pair>
  <Pair>
    <zIndex>TERRAIN_ARID</zIndex>
    <SubPair>
      <zSubIndex>YIELD_FOOD</zSubIndex>
      <iValue>-40</iValue>
    </SubPair>
  </Pair>
</aaiTerrainYieldModifier>
```

**Output:** Nested JSON object — `{ "TERRAIN_LUSH": { "YIELD_FOOD": 40 }, ... }`.

#### Pattern 7: Relationship Map

Maps enum keys to enum values, representing entity-to-entity relationships.

```xml
<aeRelationships>
  <Pair>
    <zIndex>CHARACTER_ESARHADDON</zIndex>
    <zValue>RELATIONSHIP_MENTOR_OF</zValue>
  </Pair>
</aeRelationships>
```

**Output:** JSON object with string keys and string values (same structure as Pattern 5, but semantically a relationship).

### Special Values

| Value | Meaning |
|-------|---------|
| `NONE` | Null/unset enum reference |
| `-1` | Unset integer (sentinel) |
| `0` / `1` | Boolean false / true |
| Empty tag (`<Field/>`) | Unset — use type default |
| Absent field | Same as empty tag — use type default |

### Expansion Content

Expansion packs add variant XML files with suffixes:

| Suffix | Expansion |
|--------|-----------|
| `-wog.xml` | Wonders of the Ancient World |
| `-btt.xml` | Behind the Throne |
| `-sap.xml` | Sacred and Profane |

These files add new entries to existing categories (e.g., `unit-wog.xml` adds expansion units). The pipeline should merge expansion entries into the base category during parsing. Entries use the same XML structure as base game files.

## Localization System

### Text Files

Localized strings are stored in `text-*.xml` files (150+ files). Each entry maps a text key to translations in all supported languages:

```xml
<Entry>
  <zType>TEXT_UNIT_WARRIOR</zType>
  <en-US>Warrior~a Warrior~Warriors</en-US>
  <fr>Guerrier~un Guerrier~Guerriers</fr>
  <de>Krieger~Kriegers~Krieger~Krieger</de>
  <es>Guerrero~un Guerrero~Guerreros</es>
  <ja>戦士~戦士~戦士</ja>
  <zh-TW>戰士~戰士~戰士</zh-TW>
  <ru>Воин~воина~воины~воинов</ru>
  <zh-CN>战士~战士~战士</zh-CN>
  <pt-BR>Guerreiro~um Guerreiro~Guerreiros</pt-BR>
  <ko>전사~전사~전사</ko>
</Entry>
```

### Plural Forms

The tilde (`~`) separates plural forms within a language string. The number of forms varies by language based on its grammatical rules (English has 3 forms, Russian has 4, etc.).

For wiki purposes, **use the first form** (before the first tilde) as the display name. This is the base/singular form in all languages.

### Language Configuration

`language.xml` defines metadata for each supported language:

```xml
<Entry>
  <zType>LANGUAGE_ENGLISH</zType>
  <zFieldName>en-US</zFieldName>
  <zISOCode>en-US</zISOCode>
  <zSingularExpression>x==1</zSingularExpression>
  <zThousandsSeparator>,</zThousandsSeparator>
  <zDecimalSeparator>.</zDecimalSeparator>
</Entry>
```

The `zFieldName` value (e.g., `en-US`) corresponds to the XML element name used in text files. The pipeline uses this to select the correct language column.

### Pipeline Localization

The pipeline accepts a **language flag** at runtime (e.g., `--language en-US`). It:

1. Parses all `text-*.xml` files
2. Builds a lookup dictionary: text key → localized string (first plural form)
3. When emitting JSON, resolves all `Name`, `Description`, `Help`, `Encyclopedia`, etc. fields from text keys to display strings

## Output Design

### Structure: Normalized with Reverse Indexes

The output uses **normalized JSON** with string ID references. Each entity category is a top-level collection keyed by `mzType` identifiers. Cross-references between entities use these string IDs.

The pipeline pre-computes **reverse indexes** — relationships that are implicit in the raw data but not explicitly stored. This means clients don't need to scan all entities to answer questions like "what does this tech unlock?"

### Example

```json
{
  "meta": {
    "gameVersion": "1.0.81366",
    "language": "en-US",
    "extractedAt": "2026-02-15T12:00:00Z"
  },
  "units": {
    "UNIT_WARRIOR": {
      "name": "Warrior",
      "strength": 40,
      "hpMax": 20,
      "movement": 2,
      "melee": true,
      "techPrereq": "TECH_IRONWORKING",
      "productionType": "YIELD_TRAINING",
      "production": 60,
      "yieldCost": {
        "YIELD_IRON": 50
      },
      "yieldConsumption": {
        "YIELD_FOOD": 1,
        "YIELD_IRON": 1
      },
      "upgradesTo": ["UNIT_AXEMAN", "UNIT_SPEARMAN"],
      "upgradesFrom": ["UNIT_MILITIA"],
      "obsoleteTechs": ["TECH_STEEL", "TECH_PHALANX"],
      "unitTraits": ["UNITTRAIT_MELEE", "UNITTRAIT_INFANTRY"],
      "formations": ["FORMATION_WARRIOR", "FORMATION_DEFAULT_WATER"],
      "excludedByNations": ["NATION_EGYPT"]
    }
  },
  "techs": {
    "TECH_IRONWORKING": {
      "name": "Ironworking",
      "cost": 80,
      "column": 2,
      "row": 3,
      "techPrereqs": ["TECH_MINING"],
      "effectPlayer": "EFFECTPLAYER_TECH_IRONWORKING",
      "unlocksUnits": ["UNIT_WARRIOR", "UNIT_SPEARMAN"],
      "unlocksImprovements": ["IMPROVEMENT_MINE"],
      "requiredByTechs": ["TECH_STEEL", "TECH_LABOR_FORCE"],
      "obsoletesUnits": []
    }
  },
  "improvements": {
    "IMPROVEMENT_FARM": {
      "name": "Farm",
      "buildTurns": 3,
      "yieldOutput": {
        "YIELD_FOOD": 100
      },
      "terrainYieldModifier": {
        "TERRAIN_LUSH": { "YIELD_FOOD": 40 },
        "TERRAIN_ARID": { "YIELD_FOOD": -40 }
      },
      "adjacencyYieldRate": {
        "IMPROVEMENT_IRRIGATION": { "YIELD_FOOD": 50 }
      },
      "builtByUnits": ["UNIT_WORKER"]
    }
  }
}
```

### Forward vs. Reverse Relationships

The XML stores only forward references. The pipeline computes reverse indexes so clients have bidirectional navigation.

| Forward (stored in XML) | Reverse (computed by pipeline) |
|---|---|
| Unit.techPrereq → Tech | Tech.unlocksUnits → [Unit] |
| Unit.upgradesTo → [Unit] | Unit.upgradesFrom → [Unit] |
| Unit.obsoleteTechs → [Tech] | Tech.obsoletesUnits → [Unit] |
| Improvement.techPrereq → Tech | Tech.unlocksImprovements → [Improvement] |
| Tech.techPrereqs → [Tech] | Tech.requiredByTechs → [Tech] |
| Nation.unitNotValid → [Unit] | Unit.excludedByNations → [Nation] |
| Nation.startingTechs → [Tech] | Tech.startingForNations → [Nation] |
| Nation.dynasties → [Dynasty] | Dynasty.nations → [Nation] |
| Law.lawClass → LawClass | LawClass.laws → [Law] |
| Promotion.unitTraitPrereq → UnitTrait | UnitTrait.enablesPromotions → [Promotion] |
| EffectPlayer.techPrereq → Tech | Tech.grantsEffects → [EffectPlayer] |
| Character.traits → [Trait] | Trait.characters → [Character] |
| Character.nation → Nation | Nation.characters → [Character] |

This table is not exhaustive — each category will have its own set of relationships discovered during implementation. The dev team should catalog forward references as they parse each XML file and determine which reverse indexes are useful.

## Key Entity Categories

Not all 160+ categories are equally important for a wiki. The following are the primary content categories. All should be extracted, but these are the ones clients will build pages around.

### Primary (build wiki pages around these)

| Category | XML File | Complexity | Notes |
|----------|----------|------------|-------|
| Units | unit.xml | High (92 fields) | Combat stats, costs, upgrade paths, traits |
| Technologies | tech.xml | Medium | Tech tree position, prerequisites, unlocks |
| Improvements | improvement.xml | Very High (138 fields) | Yields, terrain modifiers, 2D maps |
| Nations | nation.xml | High | Starting units/techs, dynasties, restrictions |
| Laws | law.xml | Medium | Succession, effects, costs |
| Religions | religion.xml | Medium | Theology, bonuses |
| Families | family.xml | Medium | Bonuses, seat improvements |
| Traits | trait.xml | Medium | Character traits and effects |
| Characters | character.xml | High | Predefined historical characters |
| Promotions | promotion.xml | Medium | Unit upgrades and abilities |
| Projects | project.xml | Medium | City projects |
| Resources | resource.xml | Low-Medium | Map resources |
| Cultures | culture.xml | Low-Medium | Culture levels and bonuses |

### Supporting (provide context for primary categories)

| Category | XML File | Notes |
|----------|----------|-------|
| Yields | yield.xml | Food, production, science, etc. |
| Effects (Player) | effectPlayer.xml | Modifiers granted by techs, laws, etc. |
| Effects (City) | effectCity.xml | City-level modifiers |
| Effects (Unit) | effectUnit.xml | Unit-level modifiers |
| Terrain | terrain.xml | Map terrain types |
| Height | height.xml | Elevation types |
| Vegetation | vegetation.xml | Forest, jungle, etc. |
| Bonuses | bonus.xml | Resource/tile bonuses |
| Specialists | specialist.xml | City tile specialists |
| Councils | council.xml | Government council positions |
| Missions | mission.xml | Character missions |
| Goals | goal.xml | Victory conditions |
| Dynasties | dynasty.xml | Ruling dynasties per nation |
| Cognomens | cognomen.xml | Character titles/epithets |
| Relationships | relationship.xml | Character relationship types |

### Metadata (parse but may not need wiki pages)

Categories like `color.xml`, `asset.xml`, `font.xml`, `audio.xml`, `hotkey.xml` contain UI/rendering metadata. Parse them for completeness but they're unlikely to be displayed in a wiki.

## Pipeline Architecture

```
Input                        Processing                         Output
─────                        ──────────                         ──────
Old World install path  ──►  Parse XML data files          ──►  Structured JSON
Language flag (en-US)   ──►  Parse text-*.xml files        ──►  (format left to
Game version (optional) ──►  Resolve text keys to strings       dev team)
                             Compute reverse indexes
                             Merge expansion content
                             Emit JSON
```

### Processing Steps

1. **Discover XML files** — scan the `Reference/XML/Infos/` directory
2. **Parse language config** — read `language.xml` to get the field name for the selected language (e.g., `en-US`)
3. **Build text dictionary** — parse all `text-*.xml` files, extract the selected language column, store as `key → display string` (first plural form)
4. **Parse entity files** — for each category XML file:
   - Skip the first Entry (schema template)
   - Parse each subsequent Entry into a structured object
   - Resolve text key references (Name, Description, etc.) to display strings via the text dictionary
   - Handle all 7 data patterns (single values, lists, sparse maps, 2D maps, etc.)
5. **Merge expansion content** — parse `-wog.xml`, `-btt.xml`, `-sap.xml` variant files and merge entries into base categories
6. **Compute reverse indexes** — walk all parsed entities, build reverse relationship maps
7. **Emit JSON** — write the final structured output with metadata

### CLI Interface

```
wiki-extract --game-path "/path/to/Old World" --language en-US [--version "1.0.81366"]
```

## Implementation Notes

### Why Not Use Game Code Directly

The game's `TextManager` and `Infos` classes cannot be used in a standalone project without the game runtime:

- `Infos` is deeply coupled to the game's initialization sequence, mod system, and `Mohawk.SystemCore.dll`
- `TextManager` depends on `Infos` and uses Unity-specific calls (`Debug.Log`, `UnityProfileScope`)
- Porting these classes would require stubbing dozens of dependencies for what amounts to XML parsing and dictionary lookups

The XML files are the source of truth. Parsing them directly is simpler and more maintainable.

### Handling the Schema Entry

The first `<Entry>` in every XML file is a schema template with empty values. It exists so the game knows the full field set. The pipeline must detect and skip it. Detection approaches:

- Skip the first Entry unconditionally (simplest — this is consistent across all files)
- Check for empty `<zType/>` (schema entries have no type string)

### Field Name Normalization

XML field names use Hungarian notation (`iStrength`, `bMelee`, `zIconName`). The pipeline should strip prefixes and normalize to a consistent casing convention for JSON output. For example:

| XML Field | JSON Key |
|-----------|----------|
| `iStrength` | `strength` |
| `bMelee` | `melee` |
| `zType` | `id` (special case) |
| `TechPrereq` | `techPrereq` |
| `aiYieldCost` | `yieldCost` |

The dev team should define the exact normalization rules. The prefix stripping is straightforward — the first lowercase letter(s) before the first uppercase letter are the type prefix.

### NONE Values

Enum reference fields with the value `NONE` should be treated as null/absent in the JSON output. Do not include them.

### Generic XML Parser

Since all 338 files use the same 7 structural patterns and the type prefixes are consistent, a **single generic parser** can handle every file. The parser inspects the field name prefix to determine how to parse the content:

- `i` prefix → parse as integer
- `f` prefix → parse as float
- `b` prefix → parse as boolean
- `z` or `e` prefix → parse as string
- `ae` prefix → parse as list of strings
- `ai` prefix → look for `<Pair>` children, parse as sparse int map
- `ab` prefix → look for `<Pair>` children, parse as sparse bool map → list of keys
- `az` prefix → look for `<Pair>` children, parse as sparse string map
- `aai` prefix → look for `<Pair>/<SubPair>` children, parse as 2D map
- No recognized prefix → parse as string

Fields without a standard prefix (like `Name`, `TechPrereq`, `ProductionType`) are enum references or text keys — parse as strings.

This generic approach means adding new game categories requires zero code changes — the parser handles any XML file that follows the standard structure.
