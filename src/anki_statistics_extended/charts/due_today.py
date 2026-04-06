from __future__ import annotations

from collections import defaultdict

from aqt import mw

from ..collection import (
    compiled_tag_filter,
    current_deck_card_ids,
    iter_card_level_tags,
    iter_current_deck_cards,
    sort_tags,
)
from .base import PlotlyChart, to_js


class DueTodayChart(PlotlyChart[dict[str, dict[str, int]]]):
    key = "due-today-by-tag"
    order = 10
    container_id = "anki-tag-due-plotly"

    def build_data(self) -> dict[str, dict[str, int]]:
        counts = defaultdict(
            lambda: {"CompletedToday": 0, "ReviewRemaining": 0, "NewQueue": 0}
        )
        tag_pattern = compiled_tag_filter()

        new_queue_cards = list(
            iter_current_deck_cards("deck:current is:new -is:suspended -is:buried")
        )
        new_queue_ids = {card.id for card in new_queue_cards}

        for card in new_queue_cards:
            for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                counts[tag]["NewQueue"] += 1

        review_remaining_cards = list(
            iter_current_deck_cards("deck:current is:due -is:new")
        )
        review_remaining_ids = {card.id for card in review_remaining_cards}

        for card in review_remaining_cards:
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
            completed_card_ids = (
                reviewed_card_ids - review_remaining_ids - new_queue_ids
            )

            for card_id in completed_card_ids:
                card = mw.col.get_card(card_id)
                for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                    counts[tag]["CompletedToday"] += 1
        except Exception:
            pass

        return dict(counts)

    def build_render_js(self, data: dict[str, dict[str, int]]) -> str:
        return f"""
const rows = {to_js(data)};
const tags = {to_js(sort_tags(tag for tag, row in data.items() if (row.get("NewQueue", 0) + row.get("ReviewRemaining", 0) + row.get("CompletedToday", 0)) > 0))};

if (!tags.length) return;

const completedY = tags.map((tag) => rows[tag].CompletedToday || 0);
const remainingY = tags.map((tag) => rows[tag].ReviewRemaining || 0);
const newQueueY = tags.map((tag) => rows[tag].NewQueue || 0);

const dataArr = [
  {{ type: 'bar', x: tags, y: completedY, name: 'Completed Today', marker: {{ color: '#2ca02c' }} }},
  {{ type: 'bar', x: tags, y: remainingY, name: 'Review Remaining', marker: {{ color: '#1f3b87' }} }},
  {{ type: 'bar', x: tags, y: newQueueY, name: 'New Queue', marker: {{ color: '#1f77b4' }} }},
];

Plotly.newPlot(container, dataArr, {{
  barmode: 'stack',
  title: 'Activity by Tag',
  height: 320,
  margin: {{ t: 50, l: 40, r: 20, b: 120 }},
  xaxis: {{ tickangle: -90 }},
}}, {{ displayModeBar: false }});

container.on('plotly_click', function(eventData) {{
  const point = eventData.points[0];
  const tag = point.x;
  const series = point.data && point.data.name ? point.data.name : '';

  if (series === 'New Queue') {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" is:new -is:suspended -is:buried`));
  }} else if (series === 'Review Remaining') {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" is:due -is:new`));
  }} else if (series === 'Completed Today') {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" rated:1 -is:due -is:new`));
  }} else {{
    window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{tag}}" (rated:1 -is:due -is:new OR is:due -is:new OR is:new -is:suspended -is:buried)`));
  }}
}});
"""


CHART = DueTodayChart()
