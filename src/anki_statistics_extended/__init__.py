from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from aqt import mw
from aqt.gui_hooks import stats_dialog_will_show
from aqt.qt import QTimer

STATUS_ORDER: List[str] = [
    "New",
    "Learning",
    "Consolidating",
    "Mature",
    "Trouble",
]


def card_status(card) -> str | None:
    if card.ivl == 0:
        return "New"
    if card.lapses >= 3:
        return "Trouble"
    if card.ivl <= 7:
        return "Learning"
    if 8 <= card.ivl <= 30:
        return "Consolidating"
    return "Mature"


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
    """Return a self-executing JS snippet that draws the stacked bar with Plotly."""
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
    Mature:'#4bc0c0',
    Young:'#9966ff',
    Relearning:'#ffce56',
    Learning:'#36a2eb',
    New:'#ff6384',
    Buried:'#c9cbcf',
    Suspended:'#ff9f40'
  }};
  const traces = Object.fromEntries(Object.keys(COLORS).map(k => [k, {{type:'bar', x:TAGS, y:[], name:k, marker:{{color:COLORS[k]}}}}]));
  TAGS.forEach(t => {{
    const rec = rows[t];
    Object.keys(COLORS).forEach(k => traces[k].y.push(rec[k] || 0));
  }});
  const dataArr = Object.values(traces).filter(t => t.y.some(v => v));
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
    s.src = 'https://cdn.plot.ly/plotly-2.27.0.min.js';
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