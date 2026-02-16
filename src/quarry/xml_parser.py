"""Generic XML parser for Old World game data files.

Parses any XML file from Reference/XML/Infos/ by inspecting
Hungarian notation prefixes to determine field types.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


# Regex: one or more lowercase letters at the start, followed by an uppercase letter.
# The matched group is the Hungarian prefix.
_PREFIX_RE = re.compile(r"^([a-z]+)(?=[A-Z])")

# Known prefixes mapped to parse strategies, checked longest-first.
_PREFIX_TO_STRATEGY: list[tuple[str, str]] = [
    ("aai", "sparse_2d_map"),
    ("aae", "sparse_enum_list_map"),
    ("ae", "string_list"),
    ("ai", "sparse_int_map"),
    ("ab", "sparse_bool_map"),
    ("az", "sparse_string_map"),
    ("i", "int"),
    ("f", "float"),
    ("b", "bool"),
    ("z", "string"),
    ("e", "string"),
]


def detect_field_type(tag: str) -> str:
    """Determine the parse strategy for a field based on its XML tag name.

    Returns one of: 'int', 'float', 'bool', 'string', 'string_list',
    'sparse_int_map', 'sparse_bool_map', 'sparse_string_map',
    'sparse_enum_list_map', 'sparse_2d_map'.
    """
    match = _PREFIX_RE.match(tag)
    if not match:
        return "string"

    prefix = match.group(1)
    for known_prefix, strategy in _PREFIX_TO_STRATEGY:
        if prefix == known_prefix:
            return strategy

    return "string"


def _get_text(element: ET.Element) -> str | None:
    """Get the text content of an element, returning None if empty."""
    text = element.text
    if text is None or text.strip() == "":
        return None
    return text.strip()


def parse_field(element: ET.Element, field_type: str) -> Any:
    """Parse an XML element according to its detected field type."""
    match field_type:
        case "int":
            text = _get_text(element)
            if text is None:
                return None
            try:
                value = int(text)
            except ValueError:
                # Some i-prefixed fields contain strings (e.g. iTriggerSubject)
                return text if text != "NONE" else None
            return None if value == -1 else value

        case "float":
            text = _get_text(element)
            if text is None:
                return None
            return float(text)

        case "bool":
            text = _get_text(element)
            if text is None:
                return None
            return text == "1"

        case "string":
            text = _get_text(element)
            if text is None or text == "NONE":
                return None
            return text

        case "string_list":
            # Some ae-prefixed fields use <Pair> structure instead of <zValue>.
            # Detect and delegate to sparse_string_map if so.
            if element.find("Pair") is not None:
                return parse_field(element, "sparse_string_map")
            return [
                child.text.strip()
                for child in element
                if child.text and child.text.strip()
            ]

        case "sparse_int_map":
            result: dict[str, int] = {}
            for pair in element.findall("Pair"):
                index_el = pair.find("zIndex")
                value_el = pair.find("iValue")
                if index_el is not None and value_el is not None:
                    key = _get_text(index_el)
                    val = _get_text(value_el)
                    if key and val:
                        result[key] = int(val)
            return result if result else None

        case "sparse_bool_map":
            keys: list[str] = []
            for pair in element.findall("Pair"):
                index_el = pair.find("zIndex")
                value_el = pair.find("bValue")
                if index_el is not None and value_el is not None:
                    key = _get_text(index_el)
                    val = _get_text(value_el)
                    if key and val == "1":
                        keys.append(key)
            return keys if keys else None

        case "sparse_string_map":
            result_s: dict[str, str] = {}
            for pair in element.findall("Pair"):
                index_el = pair.find("zIndex")
                value_el = pair.find("zValue")
                if index_el is not None and value_el is not None:
                    key = _get_text(index_el)
                    val = _get_text(value_el)
                    if key and val:
                        result_s[key] = val
            return result_s if result_s else None

        case "sparse_enum_list_map":
            result_ael: dict[str, list[str]] = {}
            for pair in element.findall("Pair"):
                index_el = pair.find("zIndex")
                if index_el is None:
                    continue
                key = _get_text(index_el)
                if not key:
                    continue
                values = [
                    child.text.strip()
                    for child in pair.findall("zValue")
                    if child.text and child.text.strip()
                ]
                if values:
                    result_ael[key] = values
            return result_ael if result_ael else None

        case "sparse_2d_map":
            result_2d: dict[str, dict[str, int]] = {}
            for pair in element.findall("Pair"):
                index_el = pair.find("zIndex")
                if index_el is None:
                    continue
                key = _get_text(index_el)
                if not key:
                    continue
                sub_map: dict[str, int] = {}
                for sub_pair in pair.findall("SubPair"):
                    sub_index = sub_pair.find("zSubIndex")
                    sub_value = sub_pair.find("iValue")
                    if sub_index is not None and sub_value is not None:
                        sub_key = _get_text(sub_index)
                        sub_val = _get_text(sub_value)
                        if sub_key and sub_val:
                            sub_map[sub_key] = int(sub_val)
                if sub_map:
                    result_2d[key] = sub_map
            return result_2d if result_2d else None

        case _:
            return _get_text(element)


def parse_entry(entry_element: ET.Element) -> dict[str, Any]:
    """Parse a single <Entry> element into a dict.

    Detects field types from tag names, parses accordingly.
    Omits fields whose parsed value is None. Keeps False booleans
    so that filters can distinguish "explicitly false" from "not set".
    """
    result: dict[str, Any] = {}
    for child in entry_element:
        tag = child.tag
        field_type = detect_field_type(tag)
        value = parse_field(child, field_type)

        if value is None:
            continue

        result[tag] = value

    return result


def _is_schema_entry(entry: ET.Element) -> bool:
    """Check if an Entry is a schema template (empty zType)."""
    z_type = entry.find("zType")
    if z_type is None:
        return True
    return z_type.text is None or z_type.text.strip() == ""


def parse_xml_file(path: Path) -> list[dict[str, Any]]:
    """Parse an entire XML data file, returning all data entries.

    Skips schema template entries (detected by empty zType).
    Base game files have a schema entry as their first Entry;
    expansion files do not.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    entries = root.findall("Entry")

    return [
        parse_entry(entry)
        for entry in entries
        if not _is_schema_entry(entry)
    ]
