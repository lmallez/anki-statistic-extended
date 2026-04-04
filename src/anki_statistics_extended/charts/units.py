from __future__ import annotations

from collections import defaultdict
from typing import Dict, Union

from aqt import mw

from ..collection import (
    STATUS_COLORS,
    card_status,
    compiled_tag_filter,
    current_deck_card_ids,
    iter_card_level_tags,
    iter_current_deck_cards,
    sort_tags,
)
from .base import PlotlyChart, to_js

RECENT_AGAIN_LOOKBACK_DAYS = 14
UnitMetricValue = Union[int, float]
UnitMetrics = Dict[str, Dict[str, UnitMetricValue]]


def _empty_unit_record() -> Dict[str, UnitMetricValue]:
    return {
        "Suspended": 0,
        "New": 0,
        "Learning": 0,
        "Relearning": 0,
        "Young": 0,
        "Mature": 0,
        "Total": 0,
        "Active": 0,
        "ReviewedToday": 0,
        "ReviewRemaining": 0,
        "NewToday": 0,
        "RecentAgain": 0,
        "Mastered": 0,
        "NotMastered": 0,
        "Unstable": 0,
        "MasteryPct": 0.0,
        "WeaknessPct": 0.0,
    }


def build_unit_metrics() -> UnitMetrics:
    metrics = defaultdict(_empty_unit_record)
    weak_card_ids_by_unit = defaultdict(set)
    tag_pattern = compiled_tag_filter()

    for card in iter_current_deck_cards():
        card_id = getattr(card, "id", None)
        status = card_status(card)
        for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
            record = metrics[tag]
            record["Total"] += 1
            if status:
                record[status] += 1
                if status != "Suspended":
                    record["Active"] += 1
                if status in {"Learning", "Relearning"} and card_id is not None:
                    weak_card_ids_by_unit[tag].add(card_id)

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
            metrics[tag]["NewToday"] += 1

    for card in iter_current_deck_cards("deck:current is:due -is:new"):
        for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
            metrics[tag]["ReviewRemaining"] += 1

    try:
        cutoff_s = int(getattr(mw.col.sched, "day_cutoff", 0) or 0)
        today_start_ms = (cutoff_s - 86400) * 1000
        cutoff_ms = cutoff_s * 1000
        lookback_start_ms = (cutoff_s - (RECENT_AGAIN_LOOKBACK_DAYS * 86400)) * 1000

        reviewed_today_ids = {
            row[0]
            for row in mw.col.db.all(
                "select distinct cid from revlog where id >= ? and id < ?",
                today_start_ms,
                cutoff_ms,
            )
        }
        reviewed_today_ids &= current_deck_card_ids()

        for card_id in reviewed_today_ids:
            card = mw.col.get_card(card_id)
            for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                metrics[tag]["ReviewedToday"] += 1

        again_ids = {
            row[0]
            for row in mw.col.db.all(
                "select distinct cid from revlog where id >= ? and id < ? and ease = 1",
                lookback_start_ms,
                cutoff_ms,
            )
        }
        again_ids &= current_deck_card_ids()

        for card_id in again_ids:
            card = mw.col.get_card(card_id)
            for tag in iter_card_level_tags(card, tag_pattern=tag_pattern):
                metrics[tag]["RecentAgain"] += 1
                weak_card_ids_by_unit[tag].add(card_id)
    except Exception:
        pass

    for tag, record in metrics.items():
        active = int(record["Active"])
        mature = int(record["Mature"])
        unstable = len(weak_card_ids_by_unit[tag])

        record["Mastered"] = mature
        record["NotMastered"] = max(active - mature, 0)
        record["Unstable"] = unstable
        record["MasteryPct"] = round((mature / active) * 100, 1) if active else 0.0
        record["WeaknessPct"] = round((unstable / active) * 100, 1) if active else 0.0

    return dict(metrics)


class UnitMasteryOverviewChart(PlotlyChart[UnitMetrics]):
    key = "unit-mastery-overview"
    order = 15
    container_id = "anki-unit-mastery-overview"

    def build_data(self) -> UnitMetrics:
        return build_unit_metrics()

    def build_render_js(self, data: UnitMetrics) -> str:
        tags = [
            tag
            for tag in sort_tags(data.keys())
            if sum(int(data[tag][status]) for status in ("New", "Learning", "Relearning", "Young", "Mature")) > 0
        ]

        return f"""
const rows = {to_js(data)};
const tags = {to_js(tags)};
const traces = [
  {{ key: 'Mastered', color: {to_js(STATUS_COLORS['Mature'])} }},
  {{ key: 'NotMastered', color: '#D9A441' }},
].map((series) => ({{
  type: 'bar',
  x: tags,
  y: tags.map((tag) => rows[tag][series.key] || 0),
  name: series.key === 'NotMastered' ? 'Not Mastered' : 'Mastered',
  marker: {{ color: series.color }},
}}));

const dataArr = traces.filter((trace) => trace.y.some((value) => value > 0));
if (!dataArr.length) return;

Plotly.newPlot(container, dataArr, {{
  barmode: 'stack',
  title: 'Unit Mastery Overview',
  height: 320,
  margin: {{ t: 50, l: 40, r: 20, b: 120 }},
  xaxis: {{ tickangle: -90 }},
}}, {{ displayModeBar: false }});

container.on('plotly_click', function(eventData) {{
  const point = eventData.points[0];
  window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{point.x}}"`));
}});
"""


class UnitMasteryScoreChart(PlotlyChart[UnitMetrics]):
    key = "unit-mastery-score"
    order = 16
    container_id = "anki-unit-mastery-score"

    def build_data(self) -> UnitMetrics:
        return build_unit_metrics()

    def build_render_js(self, data: UnitMetrics) -> str:
        tags = [tag for tag in sort_tags(data.keys()) if int(data[tag]["Active"]) > 0]

        return f"""
const rows = {to_js(data)};
const tags = {to_js(tags)};
if (!tags.length) return;

const y = tags.map((tag) => rows[tag].MasteryPct || 0);
const text = tags.map((tag) => `${{rows[tag].MasteryPct || 0}}%`);
const customdata = tags.map((tag) => [rows[tag].Mature || 0, rows[tag].Active || 0]);

Plotly.newPlot(container, [{{
  type: 'bar',
  x: tags,
  y,
  text,
  textposition: 'outside',
  customdata,
  marker: {{
    color: y,
    colorscale: [
      [0.0, '#EF5A3C'],
      [0.5, '#F5C04A'],
      [1.0, '#059849']
    ],
    cmin: 0,
    cmax: 100
  }},
  hovertemplate: 'Unit %{{x}}<br>Mastery %{{y:.1f}}%<br>Mature %{{customdata[0]}} / Active %{{customdata[1]}}<extra></extra>',
}}], {{
  title: 'Unit Mastery Score',
  height: 320,
  margin: {{ t: 50, l: 50, r: 20, b: 120 }},
  xaxis: {{ tickangle: -90 }},
  yaxis: {{ range: [0, 100], ticksuffix: '%' }},
}}, {{ displayModeBar: false }});

container.on('plotly_click', function(eventData) {{
  const point = eventData.points[0];
  window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{point.x}}"`));
}});
"""


class UnitWeaknessChart(PlotlyChart[UnitMetrics]):
    key = "unit-weakness-score"
    order = 17
    container_id = "anki-unit-weakness-score"

    def build_data(self) -> UnitMetrics:
        return build_unit_metrics()

    def build_render_js(self, data: UnitMetrics) -> str:
        tags = [tag for tag in sort_tags(data.keys()) if int(data[tag]["Active"]) > 0]

        return f"""
const rows = {to_js(data)};
const tags = {to_js(tags)};
if (!tags.length) return;

const y = tags.map((tag) => rows[tag].WeaknessPct || 0);
const customdata = tags.map((tag) => [
  rows[tag].Unstable || 0,
  rows[tag].Learning || 0,
  rows[tag].Relearning || 0,
  rows[tag].RecentAgain || 0,
  rows[tag].Active || 0,
]);

Plotly.newPlot(container, [{{
  type: 'bar',
  x: tags,
  y,
  marker: {{ color: '#C94B4B' }},
  hovertemplate: 'Unit %{{x}}<br>Weakness %{{y:.1f}}%<br>Unstable Cards %{{customdata[0]}}<br>Learning %{{customdata[1]}}<br>Relearning %{{customdata[2]}}<br>Recent Again (14d) %{{customdata[3]}}<br>Active %{{customdata[4]}}<extra></extra>',
}}], {{
  title: 'Weak Units',
  height: 320,
  margin: {{ t: 50, l: 50, r: 20, b: 120 }},
  xaxis: {{ tickangle: -90 }},
  yaxis: {{ range: [0, 100], ticksuffix: '%' }},
}}, {{ displayModeBar: false }});

container.on('plotly_click', function(eventData) {{
  const point = eventData.points[0];
  window.pycmd('browser?search=' + encodeURIComponent(`deck:current tag:"${{point.x}}"`));
}});
"""


UNIT_MASTERY_OVERVIEW_CHART = UnitMasteryOverviewChart()
UNIT_MASTERY_SCORE_CHART = UnitMasteryScoreChart()
UNIT_WEAKNESS_CHART = UnitWeaknessChart()
