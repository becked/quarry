"""Text dictionary builder and resolver for Old World localization.

Parses language.xml to determine the correct column name for a language code,
then parses all text-*.xml files to build a text_key -> display_string dictionary.
"""

import xml.etree.ElementTree as ET
from pathlib import Path


class TextResolver:
    """Loads and resolves Old World localized text strings."""

    def __init__(self, infos_dir: Path, language: str = "en-US") -> None:
        field_name = self._validate_language(infos_dir, language)
        self._dict = self._build_dictionary(infos_dir, field_name)

    def _validate_language(self, infos_dir: Path, language: str) -> str:
        """Validate language code against language.xml.

        Returns the XML element name used in text files for this language.
        Raises ValueError if the language code is not found.
        """
        tree = ET.parse(infos_dir / "language.xml")
        for entry in tree.getroot().findall("Entry"):
            field_name_el = entry.find("zFieldName")
            if field_name_el is not None and field_name_el.text == language:
                return language
        valid = []
        for entry in tree.getroot().findall("Entry"):
            field_name_el = entry.find("zFieldName")
            if field_name_el is not None and field_name_el.text:
                valid.append(field_name_el.text)
        raise ValueError(
            f"Unknown language '{language}'. Valid options: {', '.join(valid)}"
        )

    def _build_dictionary(self, infos_dir: Path, field_name: str) -> dict[str, str]:
        """Parse all text-*.xml files and build the lookup dictionary.

        For each entry, extracts the zType and the text from the language column,
        taking the first tilde-separated form as the display string.
        """
        result: dict[str, str] = {}
        for text_file in sorted(infos_dir.glob("text-*.xml")):
            tree = ET.parse(text_file)
            entries = tree.getroot().findall("Entry")
            for entry in entries:
                z_type_el = entry.find("zType")
                if z_type_el is None or not z_type_el.text:
                    continue

                lang_el = entry.find(field_name)
                if lang_el is None or not lang_el.text:
                    continue

                text_key = z_type_el.text.strip()
                raw_text = lang_el.text.strip()

                # Take the first tilde-separated form (base/singular)
                display_text = raw_text.split("~")[0]
                result[text_key] = display_text

        return result

    def resolve(self, text_key: str) -> str | None:
        """Look up a text key and return the localized display string."""
        return self._dict.get(text_key)

    def __len__(self) -> int:
        """Number of text entries loaded."""
        return len(self._dict)
