from __future__ import annotations

import html
import json
import logging
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHAMPION_INFO_DIR = PROJECT_ROOT / "tools" / "champion_info"
CHAMPION_PASSIVE_DIR = PROJECT_ROOT / "tools" / "passive"
CHAMPION_SPELL_DIR = PROJECT_ROOT / "tools" / "spell"

logger = logging.getLogger(__name__)

_CHAMPION_ALIASES = {
    "wukong": "MonkeyKing",
    "nunu and willump": "Nunu",
    "nunu & willump": "Nunu",
    "dr mundo": "DrMundo",
}


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _build_file_index(directory: Path) -> dict[str, str]:
    if not directory.exists():
        return {}

    return {
        _normalize_key(file_path.stem): file_path.name
        for file_path in directory.iterdir()
        if file_path.is_file()
    }


_CHAMPION_INFO_INDEX = _build_file_index(CHAMPION_INFO_DIR)
_PASSIVE_IMAGE_INDEX = _build_file_index(CHAMPION_PASSIVE_DIR)
_SPELL_IMAGE_INDEX = _build_file_index(CHAMPION_SPELL_DIR)


def _resolve_alias(champion_name: str) -> str:
    return _CHAMPION_ALIASES.get(champion_name.lower(), champion_name)


def _resolve_file_name(index: dict[str, str], value: str | None) -> str | None:
    if not value:
        return None

    return index.get(_normalize_key(value), value)


def _resolve_asset_path(index: dict[str, str], prefix: str, file_name: str | None) -> str | None:
    resolved_name = _resolve_file_name(index, file_name)
    if resolved_name is None:
        return None

    return f"{prefix}/{resolved_name}"


def _clean_description(description: Any) -> str:
    if not description:
        return ""

    text = html.unescape(str(description))
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _load_champion_info(champion_name: str) -> dict[str, Any] | None:
    resolved_name = _resolve_alias(champion_name)
    file_name = _resolve_file_name(_CHAMPION_INFO_INDEX, resolved_name)
    if file_name is None:
        logger.debug("No champion kit JSON found for '%s'", champion_name)
        return None

    file_path = CHAMPION_INFO_DIR / file_name
    try:
        with file_path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)
    except OSError as error:
        logger.warning("Failed to read champion kit JSON '%s': %s", file_path, error)
        return None
    except json.JSONDecodeError as error:
        logger.warning("Failed to parse champion kit JSON '%s': %s", file_path, error)
        return None

    champion_entries = payload.get("data") or {}
    if not champion_entries:
        return None

    return next(iter(champion_entries.values()))


def resolve_champion_kit(champion_name: str) -> dict[str, Any] | None:
    if not champion_name:
        return None

    champion_info = _load_champion_info(champion_name)
    if champion_info is None:
        return None

    passive_info = champion_info.get("passive") or {}
    passive_image = passive_info.get("image") or {}
    spell_entries = champion_info.get("spells") or []

    passive = {
        "name": passive_info.get("name", "Passive"),
        "description": _clean_description(passive_info.get("description")),
        "icon": _resolve_asset_path(
            _PASSIVE_IMAGE_INDEX,
            "/champion-passives",
            passive_image.get("full"),
        ),
    }

    spells = []
    ability_slots = ["Q", "W", "E", "R"]
    for index, spell in enumerate(spell_entries):
        spell_image = spell.get("image") or {}
        slot = ability_slots[index] if index < len(ability_slots) else f"{index + 1}"
        spells.append(
            {
                "slot": slot,
                "name": spell.get("name", f"Spell {index + 1}"),
                "description": _clean_description(spell.get("description")),
                "icon": _resolve_asset_path(
                    _SPELL_IMAGE_INDEX,
                    "/champion-spells",
                    spell_image.get("full"),
                ),
            }
        )

    return {
        "championName": champion_info.get("name", champion_name),
        "title": champion_info.get("title", ""),
        "passive": passive if passive["name"] or passive["description"] or passive["icon"] else None,
        "spells": spells,
    }