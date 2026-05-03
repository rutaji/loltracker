from __future__ import annotations

import logging
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHAMPION_IMAGE_DIR = PROJECT_ROOT / "app" / "static" / "img" / "champions"
logger = logging.getLogger(__name__)


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


def resolve_champion_image_path(champion_id: str) -> str | None:
    logger.debug(f"resolve_champion_image_path: {champion_id}")
    if not champion_id:
        return None

    if not _IMAGE_INDEX:
        # Handles cases where images were unavailable during module import.
        _IMAGE_INDEX.update(_build_image_index())

    filename = _IMAGE_INDEX.get(_normalize_key(champion_id))
    if filename is None:
        logger.warning("No champion image resolved for '%s'", champion_id)
        return None

    return f"/static/img/champions/{filename}"
