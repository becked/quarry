"""Wiki category definitions for Old World data extraction.

Each category specifies its source XML file, display name,
and an optional filter predicate.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

EntryFilter = Callable[[dict[str, Any]], bool]


def no_filter(entry: dict[str, Any]) -> bool:
    """Accept all entries."""
    return True


def content_check(entry: dict[str, Any]) -> bool:
    """Exclude entries gated behind specific DLC content."""
    return entry.get("GameContentRequired") is None


@dataclass(frozen=True)
class TextField:
    """A field whose raw value is a text key that should be resolved to a display string."""

    xml_field: str
    output_field: str


@dataclass(frozen=True)
class CategoryDef:
    """Definition of a wiki data category."""

    name: str
    display_name: str
    xml_file: str
    expansion_files: list[str] = field(default_factory=list)
    filter_fn: EntryFilter = no_filter
    text_fields: list[TextField] = field(default_factory=list)
    exclude_fields: set[str] = field(default_factory=set)


CATEGORIES: dict[str, CategoryDef] = {
    "technologies": CategoryDef(
        name="technologies",
        display_name="Technologies",
        xml_file="tech.xml",
        filter_fn=content_check,
        text_fields=[
            TextField("Name", "name"),
            TextField("Advice", "advice"),
            TextField("History", "history"),
        ],
    ),
}
