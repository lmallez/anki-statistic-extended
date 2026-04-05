from __future__ import annotations

from collections.abc import Iterator

from aqt import mw

ADDON_MODULE = __name__.split(".")[0]
WEB_EXPORT_PATTERN = r"web/.*(js|css)"


def addon_config() -> dict:
    return mw.addonManager.getConfig(ADDON_MODULE) or {}


def current_deck_name() -> str | None:
    deck = mw.col.decks.current()
    if not deck:
        return None
    return deck.get("name")


def deck_name_candidates(deck_name: str | None) -> Iterator[str]:
    if not deck_name:
        return

    parts = deck_name.split("::")
    for size in range(len(parts), 0, -1):
        yield "::".join(parts[:size])


def plotly_asset_url() -> str:
    mw.addonManager.setWebExports(ADDON_MODULE, WEB_EXPORT_PATTERN)
    addon_package = mw.addonManager.addonFromModule(ADDON_MODULE)
    return f"/_addons/{addon_package}/web/plotly.min.js"
