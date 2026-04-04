from __future__ import annotations

from collections import defaultdict

from aqt import mw

from ..collection import compiled_tag_filter, current_deck_card_ids, iter_card_level_tags, iter_current_deck_cards, sort_tags
from .base import PlotlyChart, to_js


class DueTodayChart(PlotlyChart[dict[str, dict[str, int]]]):
    key = "due-today-by-tag"
    order = 10
    container_id = "anki-tag-due-plotly"

    def build_data(self) -> dict[str, dict[str, int]]:
        counts = defaultdict(lambda: {"ReviewedToday": 0, "ReviewRemaining": 0, "New": 0})
        tag_pattern = compiled_tag_filter()

        try:
            remaining_new = int(mw.col.sched.counts()[0])
        except Exception:
            remaining_new = 10**9

        new_cards = list(iter_current_deck_cards("deck:current is:new"))
        new_cards.sort(key=lambda card: getattr(card, "due", 0) or 0)
        if remaining_new < len(new_cards):
            new_cards = new_cards[: max(0, remaining_new)]

        for card in new_cards:
            for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                counts[tag]["New"] += 1

        for card in iter_current_deck_cards("deck:current is:due -is:new"):
            for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                counts[tag]["ReviewRemaining"] += 1

        try:
            cutoff_s = int(getattr(mw.col.sched, "day_cutoff", 0) or 0)
            start_ms = (cutoff_s - 86400) * 1000
            cutoff_ms = cutoff_s * 1000

            reviewed_card_ids = {
                row[0]
                for row in mw.col.db.all(
                    "select distinct cid from revlog where id >= ? and id < ?",
                    start_ms,
                    cutoff_ms,
                )
            }
            reviewed_card_ids &= current_deck_card_ids()

            for card_id in reviewed_card_ids:
                card = mw.col.get_card(card_id)
                for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                    counts[tag]["ReviewedToday"] += 1
        except Exception:
            pass

        return dict(counts)

    def build_render_js(self, data: dict[str, dict[str, int]]) -> str:
        return f"""
const rows = {to_js(data)};
const tags = {to_js(sort_tags(tag for tag, row in data.items() if (row.get("New", 0) + row.get("ReviewRemaining", 0) + row.get("ReviewedToday", 0)) > 0))};

if (!tags.length) return;

const reviewedY = tags.map((tag) => rows[tag].ReviewedToday || 0);
const remainingY = tags.map((tag) => rows[tag].ReviewRemaining || 0);
const newY = tags.map((tag) => rows[tag].New || 0);

const dataArr = [
  {{ type: 'bar', x: tags, y: reviewedY, name: 'ReviewedToday', marker: {{ color: '#2ca02c' }} }},
  {{ type: 'bar', x: tags, y: remainingY, name: 'ReviewRemaining', marker: {{ color: '#1f3b87' }} }},
  {{ type: 'bar', x: tags, y: newY, name: 'New', marker: {{ color: '#1f77b4' }} }},
];

Plotly.newPlot(container, dataArr, {{
  barmode: 'stack',
  title: 'Today by Tag',
  height: 320,
  margin: {{ t: 50, l: 40, r: 20, b: 120 }},
  xaxis: {{ tickangle: -90 }},
}}, {{ displayModeBar: false }});

container.on('plotly_click', function(eventData) {{
  const point = eventData.points[0];
  const tag = point.x;
  const series = point.data && point.data.name ? point.data.name : '';

  if (series === 'New') {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" is:new`));
  }} else if (series === 'ReviewRemaining') {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" is:due -is:new`));
  }} else if (series === 'ReviewedToday') {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" rated:1`));
  }} else {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" (rated:1 OR is:due -is:new OR is:new)`));
  }}
}});
"""


CHART = DueTodayChart()
