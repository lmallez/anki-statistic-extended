from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Pattern

from aqt import mw

from .runtime import addon_config

STATUS_ORDER = (
    "Suspended",
    "New",
    "Learning",
    "Relearning",
    "Young",
    "Mature",
)

STATUS_COLORS = {
    "Suspended": "#808080",
    "New": "#5CADDE",
    "Learning": "#F58C2E",
    "Relearning": "#EF5A3C",
    "Young": "#66C667",
    "Mature": "#059849",
}


def compiled_tag_filter() -> Pattern[str] | None:
    pattern = addon_config().get("tag_filter_regex")
    return re.compile(pattern) if pattern else None


def is_level_tag(tag: str, *, tag_pattern: Pattern[str] | None = None) -> bool:
    pattern = compiled_tag_filter() if tag_pattern is None else tag_pattern
    if pattern is None:
        return True
    return bool(pattern.match(tag))


def tag_sort_key(tag: str) -> tuple[tuple[int, int | str], ...]:
    parts = re.findall(r"\d+|[^\d]+", tag.casefold())
    return tuple((0, int(part)) if part.isdigit() else (1, part) for part in parts)


def sort_tags(tags: Iterator[str] | list[str] | set[str]) -> list[str]:
    return sorted(tags, key=tag_sort_key)


def iter_card_level_tags(
    card, *, tag_pattern: Pattern[str] | None = None
) -> Iterator[str]:
    for tag in card.note().tags or []:
        if is_level_tag(tag, tag_pattern=tag_pattern):
            yield tag


def iter_current_deck_cards(search: str = "deck:current") -> Iterator:
    for card_id in mw.col.find_cards(search):
        yield mw.col.get_card(card_id)


def current_deck_card_ids() -> set[int]:
    return set(mw.col.find_cards("deck:current"))


def card_status(card) -> str | None:
    queue = getattr(card, "queue", None)
    card_type = getattr(card, "type", None)
    interval = getattr(card, "ivl", 0) or 0

    if queue == -1:
        return "Suspended"
    if card_type == 0 or queue == 0:
        return "New"
    if card_type == 3:
        return "Relearning"
    if card_type == 1 or queue in (1, 3):
        return "Learning"
    if card_type == 2:
        return "Mature" if interval >= 21 else "Young"
    return None
