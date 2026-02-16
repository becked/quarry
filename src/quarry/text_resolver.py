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
        self._gendered_dict = self._build_gendered_dictionary(infos_dir)

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

    def _build_gendered_dictionary(self, infos_dir: Path) -> dict[str, str]:
        """Parse all genderedText*.xml files to map GENDERED_TEXT_* keys to masculine TEXT_* keys."""
        result: dict[str, str] = {}
        for gendered_path in sorted(infos_dir.glob("genderedText*.xml")):
            tree = ET.parse(gendered_path)
            for entry in tree.getroot().findall("Entry"):
                z_type_el = entry.find("zType")
                if z_type_el is None or not z_type_el.text:
                    continue

                texts_el = entry.find("Texts")
                if texts_el is None:
                    continue

                gendered_key = z_type_el.text.strip()
                for pair in texts_el.findall("Pair"):
                    index_el = pair.find("zIndex")
                    value_el = pair.find("zValue")
                    if (index_el is not None and value_el is not None
                            and index_el.text == "GRAMMATICAL_GENDER_MASCULINE"
                            and value_el.text):
                        result[gendered_key] = value_el.text.strip()
                        break

        return result

    def resolve(self, text_key: str) -> str | None:
        """Look up a text key and return the localized display string.

        Handles GENDERED_TEXT_* keys by resolving through genderedText.xml
        to the masculine TEXT_* key first, then looking up the display string.
        """
        if text_key.startswith("GENDERED_TEXT_"):
            text_key = self._gendered_dict.get(text_key, text_key)
        return self._dict.get(text_key)

    def __len__(self) -> int:
        """Number of text entries loaded."""
        return len(self._dict)
