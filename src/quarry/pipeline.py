"""Pipeline orchestrator: parse -> resolve -> filter -> normalize -> emit."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from quarry.categories import CATEGORIES, CategoryDef
from quarry.text_resolver import TextResolver
from quarry.xml_parser import parse_xml_file

# Matches one or more lowercase letters at start, followed by an uppercase letter.
_PREFIX_RE = re.compile(r"^[a-z]+(?=[A-Z])")


def normalize_field_name(xml_name: str) -> str:
    """Strip Hungarian prefix and produce camelCase JSON field name.

    Examples:
        iCost -> cost
        bHide -> hide
        zIconName -> iconName
        aeNationValid -> nationValid
        Name -> name
        EffectPlayer -> effectPlayer
    """
    match = _PREFIX_RE.match(xml_name)
    if match:
        remainder = xml_name[match.end() :]
        return remainder[0].lower() + remainder[1:]
    else:
        return xml_name[0].lower() + xml_name[1:]


def process_category(
    category: CategoryDef,
    infos_dir: Path,
    text_resolver: TextResolver,
) -> dict[str, dict[str, Any]]:
    """Process a single category: parse, filter, resolve text, normalize."""
    # Parse base XML file
    raw_entries = parse_xml_file(infos_dir / category.xml_file)

    # Parse and merge expansion files
    for exp_file in category.expansion_files:
        exp_path = infos_dir / exp_file
        if exp_path.exists():
            raw_entries.extend(parse_xml_file(exp_path))

    # Filter entries
    filtered = [e for e in raw_entries if category.filter_fn(e)]

    # Build text field lookup for fast matching
    text_field_map = {tf.xml_field: tf for tf in category.text_fields}

    # Transform each entry
    result: dict[str, dict[str, Any]] = {}
    for raw in filtered:
        z_type = raw.get("zType")
        if z_type is None:
            continue

        output_entry: dict[str, Any] = {}
        for xml_field, value in raw.items():
            if xml_field == "zType":
                continue
            if xml_field in category.exclude_fields:
                continue

            # Resolve text fields
            tf = text_field_map.get(xml_field)
            if tf is not None:
                resolved = text_resolver.resolve(str(value))
                if resolved is not None:
                    output_entry[tf.output_field] = resolved
                continue

            # Normalize field name and include
            output_entry[normalize_field_name(xml_field)] = value

        result[z_type] = output_entry

    return result


def run_pipeline(
    game_path: Path,
    language: str,
    output_dir: Path,
    game_version: str | None = None,
    categories: list[str] | None = None,
) -> None:
    """Run the full extraction pipeline."""
    infos_dir = game_path / "Reference" / "XML" / "Infos"
    if not infos_dir.is_dir():
        raise FileNotFoundError(f"Infos directory not found: {infos_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading text dictionary for '{language}'...")
    text_resolver = TextResolver(infos_dir, language)
    print(f"  {len(text_resolver)} text entries loaded")

    # Determine which categories to process
    category_names = categories if categories else list(CATEGORIES.keys())

    for name in category_names:
        cat_def = CATEGORIES.get(name)
        if cat_def is None:
            print(f"  Warning: unknown category '{name}', skipping")
            continue

        print(f"Processing '{cat_def.display_name}'...")
        entries = process_category(cat_def, infos_dir, text_resolver)

        meta: dict[str, str] = {
            "category": cat_def.name,
            "language": language,
            "extractedAt": datetime.now(timezone.utc).isoformat(),
        }
        if game_version:
            meta["gameVersion"] = game_version

        output = {"meta": meta, "entries": entries}

        out_path = output_dir / f"{cat_def.name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"  {len(entries)} entries -> {out_path}")
