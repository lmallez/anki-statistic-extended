from __future__ import annotations

from collections import defaultdict

from ..collection import (
    STATUS_COLORS,
    STATUS_ORDER,
    card_status,
    compiled_tag_filter,
    iter_card_level_tags,
    sort_tags,
)
from .base import PlotlyChart, to_js


class CardStatusChart(PlotlyChart[dict[str, dict[str, int]]]):
    key = "card-status-by-tag"
    order = 20
    container_id = "anki-tag-status-plotly"

    def build_data(self) -> dict[str, dict[str, int]]:
        from aqt import mw

        counts = defaultdict(lambda: {status: 0 for status in STATUS_ORDER})
        tag_pattern = compiled_tag_filter()

        for card_id in mw.col.find_cards("deck:current"):
            card = mw.col.get_card(card_id)
            status = card_status(card)
            if not status:
                continue

            for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                counts[tag][status] += 1

        return dict(counts)

    def build_render_js(self, data: dict[str, dict[str, int]]) -> str:
        return f"""
const rows = {to_js(data)};
const tags = {to_js(sort_tags(data.keys()))};
const colors = {to_js(STATUS_COLORS)};
const stackOrder = {to_js(list(reversed(STATUS_ORDER)))};

const traces = Object.fromEntries(
  stackOrder.map((status) => [status, {{
    type: 'bar',
    x: tags,
    y: [],
    name: status,
    marker: {{ color: colors[status] }},
    visible: status === 'Suspended' ? 'legendonly' : true
  }}])
);

tags.forEach((tag) => {{
  const row = rows[tag];
  Object.keys(colors).forEach((status) => traces[status].y.push(row[status] || 0));
}});

const dataArr = stackOrder
  .map((status) => traces[status])
  .filter((trace) => trace.y.some((value) => value > 0));

if (!dataArr.length) return;

Plotly.newPlot(container, dataArr, {{
  barmode: 'stack',
  title: 'Card Status by Tag',
  height: 320,
  margin: {{ t: 50, l: 40, r: 20, b: 120 }},
  xaxis: {{ tickangle: -90 }},
}}, {{ displayModeBar: false }});

container.on('plotly_click', function(eventData) {{
  const point = eventData.points[0];
  const tag = point.x;
  const status = point.data.name.toLowerCase();
  window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" is:${{status}}`));
}});
"""


CHART = CardStatusChart()
