from __future__ import annotations

import logging
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHAMPION_IMAGE_DIR = PROJECT_ROOT / "tools" / "champion_imgs"
logger = logging.getLogger(__name__)


_CHAMPION_ALIASES = {
    "wukong": "MonkeyKing",
    "nunu and willump": "Nunu",
    "nunu & willump": "Nunu",
    "dr mundo": "DrMundo",
}


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _build_image_index() -> dict[str, str]:
    if not CHAMPION_IMAGE_DIR.exists():
        return {}

    mapping: dict[str, str] = {}
    for image_file in CHAMPION_IMAGE_DIR.glob("*.png"):
        mapping[_normalize_key(image_file.stem)] = image_file.name
    return mapping


_IMAGE_INDEX = _build_image_index()


def resolve_champion_image_path(champion_name: str) -> str | None:
    if not champion_name:
        return None

    if not _IMAGE_INDEX:
        # Handles cases where images were unavailable during module import.
        _IMAGE_INDEX.update(_build_image_index())

    alias = _CHAMPION_ALIASES.get(champion_name.lower(), champion_name)
    filename = _IMAGE_INDEX.get(_normalize_key(alias))
    if filename is None:
        logger.debug("No champion image resolved for '%s' (alias '%s')", champion_name, alias)
        return None

    return f"/champion-images/{filename}"