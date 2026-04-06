from __future__ import annotations

import traceback

from aqt.gui_hooks import stats_dialog_will_show
from aqt.qt import QTimer

from .charts import clear_chart_caches, get_charts

MAX_INJECT_ATTEMPTS = 30
RETRY_DELAY_MS = 200

_registered = False


def _log_chart_failure(chart_key: str, stage: str) -> None:
    print(f"[anki-statistics-extended] Failed to {stage} chart '{chart_key}'")
    print(traceback.format_exc())


def inject_charts(web) -> None:
    clear_chart_caches()
    for chart in get_charts():
        try:
            chart_js = chart.build_script()
        except Exception:
            _log_chart_failure(chart.key, "build")
            continue

        if not chart_js:
            continue

        try:
            web.eval(chart_js)
        except Exception:
            _log_chart_failure(chart.key, "inject")


def inject_with_retry(dlg, attempt: int = 0) -> None:
    if attempt > MAX_INJECT_ATTEMPTS:
        return

    form = getattr(dlg, "form", None)
    web = getattr(dlg, "web", None) or getattr(form, "web", None)
    if web:
        inject_charts(web)
        return

    QTimer.singleShot(RETRY_DELAY_MS, lambda: inject_with_retry(dlg, attempt + 1))


def on_stats_dialog(dlg) -> None:
    QTimer.singleShot(RETRY_DELAY_MS, lambda: inject_with_retry(dlg))


def register() -> None:
    global _registered

    if _registered:
        return

    stats_dialog_will_show.append(on_stats_dialog)
    _registered = True
