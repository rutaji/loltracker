from __future__ import annotations

from typing import Final


QUEUE_FILTER_ALL: Final = "all"
QUEUE_FILTER_RANKED_SOLO: Final = "ranked_solo"
QUEUE_FILTER_RANKED_FLEX: Final = "ranked_flex"
QUEUE_FILTER_ARAM: Final = "aram"
QUEUE_FILTER_OTHER: Final = "other"

QUEUE_FILTER_OPTIONS: Final[list[tuple[str, str]]] = [
    (QUEUE_FILTER_ALL, "All"),
    (QUEUE_FILTER_RANKED_SOLO, "Ranked Solo"),
    (QUEUE_FILTER_RANKED_FLEX, "Ranked Flex"),
    (QUEUE_FILTER_ARAM, "ARAM"),
    (QUEUE_FILTER_OTHER, "Other"),
]

FILTER_TO_QUEUE_ID: Final[dict[str, int]] = {
    QUEUE_FILTER_RANKED_SOLO: 420,
    QUEUE_FILTER_RANKED_FLEX: 440,
    QUEUE_FILTER_ARAM: 450,
}

PRIMARY_QUEUE_IDS: Final[tuple[int, ...]] = tuple(FILTER_TO_QUEUE_ID.values())
VALID_QUEUE_FILTERS: Final[set[str]] = {value for value, _label in QUEUE_FILTER_OPTIONS}


def normalize_queue_filter(queue_filter: str | None) -> str:
    if not queue_filter:
        return QUEUE_FILTER_ALL

    normalized = queue_filter.strip().lower()
    if normalized in VALID_QUEUE_FILTERS:
        return normalized
    return QUEUE_FILTER_ALL


def matches_queue_filter(queue_id: int | None, queue_filter: str | None) -> bool:
    normalized = normalize_queue_filter(queue_filter)

    if normalized == QUEUE_FILTER_ALL:
        return True

    if normalized == QUEUE_FILTER_OTHER:
        return queue_id is None or queue_id not in PRIMARY_QUEUE_IDS

    expected_queue_id = FILTER_TO_QUEUE_ID.get(normalized)
    return queue_id == expected_queue_id
