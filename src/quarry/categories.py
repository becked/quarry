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


def encyclopedia_default_true(entry: dict[str, Any]) -> bool:
    """Include entries where bEncyclopedia defaults to true (most types).

    Excludes only entries that explicitly set bEncyclopedia=0.
    """
    return entry.get("bEncyclopedia") is not False


def encyclopedia_default_false(entry: dict[str, Any]) -> bool:
    """Include entries where bEncyclopedia defaults to false (missions).

    Requires bEncyclopedia to be explicitly set to 1.
    """
    return entry.get("bEncyclopedia") is True


def projects_filter(entry: dict[str, Any]) -> bool:
    """Encyclopedia-visible, non-hidden projects."""
    return entry.get("bEncyclopedia") is not False and entry.get("bHidden") is not True


def improvements_filter(entry: dict[str, Any]) -> bool:
    """Buildable, non-wonder, non-religious improvements."""
    return (
        entry.get("bEncyclopedia") is not False
        and entry.get("bBuild") is True
        and entry.get("bWonder") is not True
        and entry.get("ReligionPrereq") is None
    )


def wonders_filter(entry: dict[str, Any]) -> bool:
    """Encyclopedia-visible wonders."""
    return entry.get("bEncyclopedia") is not False and entry.get("bWonder") is True


def religious_improvements_filter(entry: dict[str, Any]) -> bool:
    """Encyclopedia-visible religious improvements (non-wonder)."""
    return (
        entry.get("bEncyclopedia") is not False
        and entry.get("bWonder") is not True
        and entry.get("ReligionPrereq") is not None
    )


def special_improvements_filter(entry: dict[str, Any]) -> bool:
    """Encyclopedia-visible, non-buildable, non-wonder, non-religious."""
    return (
        entry.get("bEncyclopedia") is not False
        and entry.get("bBuild") is not True
        and entry.get("bWonder") is not True
        and entry.get("ReligionPrereq") is None
    )


def dynasties_filter(entry: dict[str, Any]) -> bool:
    """Only dynasties with a first ruler defined."""
    return entry.get("FirstRuler") is not None


def characters_filter(entry: dict[str, Any]) -> bool:
    """Only characters with a first name defined."""
    return entry.get("FirstName") is not None


def archetypes_filter(entry: dict[str, Any]) -> bool:
    """Archetype traits visible in encyclopedia."""
    return entry.get("bArchetype") is True and entry.get("bEncyclopedia") is not False


def traits_filter(entry: dict[str, Any]) -> bool:
    """Non-archetype, non-strength/weakness, non-item encyclopedia traits."""
    return (
        entry.get("bEncyclopedia") is not False
        and entry.get("bArchetype") is not True
        and entry.get("bWeakness") is not True
        and entry.get("bStrength") is not True
        and entry.get("bItem") is not True
    )


def strengths_weaknesses_filter(entry: dict[str, Any]) -> bool:
    """Strengths and weaknesses (non-archetype, non-item)."""
    return (
        entry.get("bEncyclopedia") is not False
        and entry.get("bArchetype") is not True
        and (entry.get("bWeakness") is True or entry.get("bStrength") is True)
        and entry.get("bItem") is not True
    )


def items_filter(entry: dict[str, Any]) -> bool:
    """Item traits."""
    return entry.get("bItem") is True


def national_ambitions_filter(entry: dict[str, Any]) -> bool:
    """Victory-eligible goals with positive subject weight."""
    return (
        entry.get("bVictoryEligible") is True
        and (entry.get("iSubjectWeight") or 0) > 0
    )


@dataclass(frozen=True)
class TextField:
    """A field whose raw value is a text key that should be resolved to a display string."""

    xml_field: str
    output_field: str
    text_key_prefix: str = ""


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
    # ── Simple categories (no filter) ──────────────────────────────────
    "technologies": CategoryDef(
        name="technologies",
        display_name="Technologies",
        xml_file="tech.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("Advice", "advice"),
            TextField("History", "history"),
        ],
    ),
    "tutorials": CategoryDef(
        name="tutorials",
        display_name="Tutorials",
        xml_file="tutorial.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("zHelpText", "help"),
        ],
    ),
    "yields": CategoryDef(
        name="yields",
        display_name="Yields",
        xml_file="yield.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("Help", "help"),
        ],
    ),
    "specialists": CategoryDef(
        name="specialists",
        display_name="Specialists",
        xml_file="specialist.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "resources": CategoryDef(
        name="resources",
        display_name="Resources",
        xml_file="resource.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "vegetation": CategoryDef(
        name="vegetation",
        display_name="Vegetation",
        xml_file="vegetation.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("NameRemove", "nameRemove"),
        ],
    ),
    "heights": CategoryDef(
        name="heights",
        display_name="Heights",
        xml_file="height.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "ratings": CategoryDef(
        name="ratings",
        display_name="Attributes",
        xml_file="rating.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("Help", "help"),
        ],
    ),
    "terrain": CategoryDef(
        name="terrain",
        display_name="Terrain",
        xml_file="terrain.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "theologies": CategoryDef(
        name="theologies",
        display_name="Theologies",
        xml_file="theology.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "promotions": CategoryDef(
        name="promotions",
        display_name="Promotions",
        xml_file="promotion.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "difficultyLevels": CategoryDef(
        name="difficultyLevels",
        display_name="Difficulty Levels",
        xml_file="difficultyMode.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("Description", "description"),
        ],
    ),
    "victoryTypes": CategoryDef(
        name="victoryTypes",
        display_name="Victory Types",
        xml_file="victory.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("Help", "help"),
        ],
    ),
    # ── GenderedName categories ────────────────────────────────────────
    "concepts": CategoryDef(
        name="concepts",
        display_name="Concepts",
        xml_file="concept.xml",
        text_fields=[
            TextField("GenderedName", "name"),
            TextField("zHelpText", "help"),
        ],
    ),
    "tribes": CategoryDef(
        name="tribes",
        display_name="Tribes",
        xml_file="tribe.xml",
        text_fields=[
            TextField("GenderedName", "name"),
            TextField("Help", "help"),
        ],
    ),
    "cognomen": CategoryDef(
        name="cognomen",
        display_name="Cognomen",
        xml_file="cognomen.xml",
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    "councils": CategoryDef(
        name="councils",
        display_name="Councils",
        xml_file="council.xml",
        expansion_files=["council-btt.xml"],
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    # ── Filtered categories ────────────────────────────────────────────
    "units": CategoryDef(
        name="units",
        display_name="Units",
        xml_file="unit.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "projects": CategoryDef(
        name="projects",
        display_name="Projects",
        xml_file="project.xml",
        filter_fn=projects_filter,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "laws": CategoryDef(
        name="laws",
        display_name="Laws",
        xml_file="law.xml",
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "religions": CategoryDef(
        name="religions",
        display_name="Religions",
        xml_file="religion.xml",
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    "nations": CategoryDef(
        name="nations",
        display_name="Nations",
        xml_file="nation.xml",
        text_fields=[
            TextField("GenderedName", "name"),
            TextField("Story", "story"),
        ],
    ),
    "familyClasses": CategoryDef(
        name="familyClasses",
        display_name="Family Classes",
        xml_file="familyClass.xml",
        text_fields=[
            TextField("Name", "name"),
            TextField("AdviceFound", "adviceFound"),
        ],
    ),
    "dynasties": CategoryDef(
        name="dynasties",
        display_name="Dynasties",
        xml_file="dynasty.xml",
        filter_fn=dynasties_filter,
        text_fields=[
            TextField("Name", "name"),
            TextField("Description", "description"),
        ],
    ),
    "characters": CategoryDef(
        name="characters",
        display_name="Characters",
        xml_file="character.xml",
        filter_fn=characters_filter,
        text_fields=[
            TextField("FirstName", "name", text_key_prefix="TEXT_"),
        ],
    ),
    "missions": CategoryDef(
        name="missions",
        display_name="Missions",
        xml_file="mission.xml",
        filter_fn=encyclopedia_default_false,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "occurrences": CategoryDef(
        name="occurrences",
        display_name="Occurrences",
        xml_file="occurrence.xml",
        filter_fn=encyclopedia_default_true,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "nationalAmbitions": CategoryDef(
        name="nationalAmbitions",
        display_name="National Ambitions",
        xml_file="goal.xml",
        filter_fn=national_ambitions_filter,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "unitEffects": CategoryDef(
        name="unitEffects",
        display_name="Unit Effects",
        xml_file="effectUnit.xml",
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    # ── Split: improvement.xml × 4 ────────────────────────────────────
    "improvements": CategoryDef(
        name="improvements",
        display_name="Improvements",
        xml_file="improvement.xml",
        filter_fn=improvements_filter,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "wonders": CategoryDef(
        name="wonders",
        display_name="Wonders",
        xml_file="improvement.xml",
        filter_fn=wonders_filter,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "religiousImprovements": CategoryDef(
        name="religiousImprovements",
        display_name="Religious Improvements",
        xml_file="improvement.xml",
        filter_fn=religious_improvements_filter,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    "specialImprovements": CategoryDef(
        name="specialImprovements",
        display_name="Special Improvements",
        xml_file="improvement.xml",
        filter_fn=special_improvements_filter,
        text_fields=[
            TextField("Name", "name"),
        ],
    ),
    # ── Split: trait.xml × 4 ──────────────────────────────────────────
    "archetypes": CategoryDef(
        name="archetypes",
        display_name="Archetypes",
        xml_file="trait.xml",
        filter_fn=archetypes_filter,
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    "traits": CategoryDef(
        name="traits",
        display_name="Traits",
        xml_file="trait.xml",
        filter_fn=traits_filter,
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    "traitsAdjectives": CategoryDef(
        name="traitsAdjectives",
        display_name="Strengths & Weaknesses",
        xml_file="trait.xml",
        filter_fn=strengths_weaknesses_filter,
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
    "traitsItems": CategoryDef(
        name="traitsItems",
        display_name="Items",
        xml_file="trait.xml",
        filter_fn=items_filter,
        text_fields=[
            TextField("GenderedName", "name"),
        ],
    ),
}
