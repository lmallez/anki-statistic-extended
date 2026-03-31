from __future__ import annotations

from aqt import mw

ADDON_MODULE = __name__.split(".")[0]
WEB_EXPORT_PATTERN = r"web/.*(js|css)"


def addon_config() -> dict:
    return mw.addonManager.getConfig(ADDON_MODULE) or {}


def plotly_asset_url() -> str:
    mw.addonManager.setWebExports(ADDON_MODULE, WEB_EXPORT_PATTERN)
    addon_package = mw.addonManager.addonFromModule(ADDON_MODULE)
    return f"/_addons/{addon_package}/web/plotly.min.js"
