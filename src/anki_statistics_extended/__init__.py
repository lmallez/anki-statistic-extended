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
    "Relearning",
    "Young",
    "Mature",
]

COLOR_MAP = {
    "New": "#5CADDE",
    "Learning": "#F58C2E",
    "Relearning": "#EF5A3C",
    "Young": "#66C667",
    "Mature": "#059849",
}


def card_status(card) -> str | None:
    if card.type == 0:
        return "New"
    if card.type == 1:
        if card.queue in (0, 1):
            return "Learning"
        elif card.queue == 3:
            return "Relearning"
    if card.type == 2:
        return "Young" if card.ivl < 21 else "Mature"
    return None


def build_tag_counts() -> Dict[str, Dict[str, int]]:
    counts = defaultdict(lambda: {k: 0 for k in STATUS_ORDER})
    for cid in mw.col.find_cards("deck:current"):
        card = mw.col.get_card(cid)
        status = card_status(card)
        if status:
            for tag in card.note().tags or ["(untagged)"]:
                counts[tag][status] += 1
    return counts


def create_plotly_chart_config(data: dict) -> str:
    mw.addonManager.setWebExports(__name__, r"web/.*(js|css)")
    addon_pkg = mw.addonManager.addonFromModule(__name__)
    plotly_url = f"/_addons/{addon_pkg}/web/plotly.min.js"

    if not data:
        return ""

    payload = json.dumps(data).replace("\\", "\\\\").replace("'", "\\'")
    stack_order = list(reversed(STATUS_ORDER))
    colors_json = json.dumps(COLOR_MAP).replace("'", "\\'")

    return f"""(function() {{
  const rows = JSON.parse('{payload}');
  const TAGS = Object.keys(rows).sort();
  const COLORS = JSON.parse('{colors_json}');
  const STACK_ORDER = {stack_order};
  
  const traces = Object.fromEntries(
    STACK_ORDER.map(k => [k, {{
      type: 'bar',
      x: TAGS,
      y: [],
      name: k,
      marker: {{color: COLORS[k]}}
    }}])
  );
  
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


def inject_chart(web):
    js = create_plotly_chart_config(build_tag_counts())
    if js:
        web.eval(js)


def inject_with_retry(dlg, attempt=0):
    if attempt > 30:
        return
    web = getattr(dlg, "web", None) or getattr(dlg.form, "web", None)
    if web:
        inject_chart(web)
    else:
        QTimer.singleShot(200, lambda: inject_with_retry(dlg, attempt + 1))


def on_stats_dialog(dlg):
    QTimer.singleShot(200, lambda: inject_with_retry(dlg))


stats_dialog_will_show.append(on_stats_dialog)
