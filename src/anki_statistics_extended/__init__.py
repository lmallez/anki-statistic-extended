from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from aqt.gui_hooks import stats_dialog_will_show
from aqt.qt import QTimer
from aqt import mw

STATUS_ORDER: List[str] = [
    "New",
    "Learning",
    "Relearning",
    "Young",
    "Mature",
]

COLOR_MAP = {
    "New": "#5CADDE",         # Light Blue
    "Learning": "#F58C2E",    # Orange
    "Relearning": "#EF5A3C",  # Red-Orange
    "Young": "#66C667",       # Light Green
    "Mature": "#059849",      # Dark Green
}

def card_status(card) -> str | None:
    if card.type == 0:  # New card
        return "New"
    if card.type == 1:  # Learning
        if card.queue in (0, 1):
            return "Learning"
        elif card.queue == 3:
            return "Relearning"
    if card.type == 2:  # Review
        if card.ivl < 21:
            return "Young"
        else:
            return "Mature"
    return None


def build_tag_counts() -> Dict[str, Dict[str, int]]:
    counts = defaultdict(lambda: {k: 0 for k in STATUS_ORDER})
    for cid in mw.col.find_cards("deck:current"):
        card = mw.col.get_card(cid)
        status = card_status(card)
        if not status:
            continue
        for tag in card.note().tags or ["(untagged)"]:
            counts[tag][status] += 1
    return counts


def _build_js_payload() -> str:
    mw.addonManager.setWebExports(__name__, r"web/.*(js|css)")
    addon_pkg = mw.addonManager.addonFromModule(__name__)
    plotly_url = f"/_addons/{addon_pkg}/web/plotly.min.js"

    data = build_tag_counts()
    if not data:
        return ""

    payload = (
        json.dumps(data)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
    )

    return f"""(function() {{
  const rows = JSON.parse('{payload}');
  const TAGS = Object.keys(rows).sort();
  const COLORS = {{
    New: '{COLOR_MAP["New"]}',
    Learning: '{COLOR_MAP["Learning"]}',
    Relearning: '{COLOR_MAP["Relearning"]}',
    Young: '{COLOR_MAP["Young"]}',
    Mature: '{COLOR_MAP["Mature"]}',
  }};
  const STACK_ORDER = ["Mature", "Young", "Relearning", "Learning", "New"];
  const traces = Object.fromEntries(STACK_ORDER.map(k => [k, {{type:'bar', x:TAGS, y:[], name:k, marker:{{color:COLORS[k]}}}}]));
  TAGS.forEach(t => {{
    const rec = rows[t];
    Object.keys(COLORS).forEach(k => traces[k].y.push(rec[k] || 0));
  }});
  const dataArr = STACK_ORDER.map(k => traces[k]).filter(t => t.y.some(v => v));
  if (!dataArr.length) return;

  function draw() {{
    const container = document.createElement('div');
    container.style.maxWidth = '900px';
    container.style.margin = '2rem auto';
    document.body.prepend(container);
    Plotly.newPlot(container, dataArr, {{
      barmode: 'stack',
      title: 'Card Status by Tag (stacked)'
    }});
    container.on('plotly_click', function(eventData) {{
      const pt = eventData.points[0];
      const tag = pt.x;
      const status = pt.data.name.toLowerCase();
      window.pycmd('browser?search=' + encodeURIComponent(`tag:${{tag}} is:${{status}}`));
    }});
  }}

  if (window.Plotly) {{
    draw();
  }} else {{
    const s = document.createElement('script');
    s.src = '{plotly_url}';
    s.onload = draw;
    document.head.appendChild(s);
  }}
}})();"""


def _inject_into_webview(web):
    js = _build_js_payload()
    if js:
        web.eval(js)


def _on_stats_dialog(dlg):
    def try_inject(attempt=0):
        if attempt > 30:
            return
        web = getattr(dlg, "web", None)
        if web is None and hasattr(dlg, "form"):
            web = getattr(dlg.form, "web", None)
        if web:
            _inject_into_webview(web)
        else:
            QTimer.singleShot(200, lambda: try_inject(attempt + 1))
    QTimer.singleShot(200, try_inject)


stats_dialog_will_show.append(_on_stats_dialog)