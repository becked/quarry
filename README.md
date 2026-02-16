# Quarry

Data extraction pipeline for [Old World](https://store.steampowered.com/app/597180/Old_World/). Reads the game's static XML data files and outputs structured JSON for wiki and encyclopedia applications.

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

Point `--game-path` at your Old World game installation directory:

```bash
# Extract all categories
uv run python -m quarry --game-path "/path/to/Old World" --output-dir ./output

# Extract specific categories
uv run python -m quarry --game-path "/path/to/Old World" --categories technologies units wonders

# Include game version in output metadata
uv run python -m quarry --game-path "/path/to/Old World" --version "1.0.81366"
```

Output is one JSON file per category in the output directory. Each file contains metadata and a dictionary of entries keyed by their game identifier:

```json
{
  "meta": {
    "category": "technologies",
    "language": "en-US",
    "extractedAt": "2026-02-16T..."
  },
  "entries": {
    "TECH_IRONWORKING": {
      "name": "Ironworking",
      "cost": 80,
      "column": 0,
      "row": 2
    }
  }
}
```

## Categories

37 categories extracted across all base game and expansion content:

| Group | Categories |
|-------|-----------|
| Core | technologies, units, specialists, projects, laws, resources |
| Improvements | improvements, wonders, religiousImprovements, specialImprovements |
| Traits | archetypes, traits, traitsAdjectives (strengths/weaknesses), traitsItems |
| People | nations, familyClasses, dynasties, characters, councils |
| Religion | religions, theologies |
| Map | terrain, vegetation, heights, yields |
| Military | promotions, unitEffects, missions |
| Reference | concepts, tutorials, ratings, difficultyLevels, victoryTypes, occurrences, nationalAmbitions, tribes, cognomen |

## How It Works

The pipeline is generic — a single XML parser handles all game data files by detecting field types from [Hungarian notation](https://en.wikipedia.org/wiki/Hungarian_notation) prefixes on XML tag names (`iCost` → integer, `bMelee` → boolean, `zName` → string, `aiYieldCost` → sparse int map, etc.).

Adding a new category requires only a declarative config entry in `src/quarry/categories.py`. No per-category parsing code. See [docs/adding-categories.md](docs/adding-categories.md) for the full guide.

## Supported Languages

Any language included in the game's localization files. Pass the language code to `--language`:

`en-US`, `fr-FR`, `de-DE`, `es-ES`, `it-IT`, `pt-BR`, `ru-RU`, `zh-Hans`, `zh-Hant`, `ja-JP`, `ko-KR`, `pl-PL`, `tr-TR`, `cs-CZ`

## Web Interface

A static encyclopedia site for browsing the extracted data. See [web/README.md](web/README.md) for setup and development.
