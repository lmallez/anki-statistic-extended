from __future__ import annotations

from .base import StatsChart
from .counts import CHART as CARD_STATUS_CHART
from .due_today import CHART as DUE_TODAY_CHART
from .units import (
    UNIT_MASTERY_SCORE_CHART,
    UNIT_WEAKNESS_CHART,
)

REGISTERED_CHARTS: tuple[StatsChart, ...] = tuple(
    sorted(
        (
            DUE_TODAY_CHART,
            UNIT_MASTERY_SCORE_CHART,
            UNIT_WEAKNESS_CHART,
            CARD_STATUS_CHART,
        ),
        key=lambda chart: chart.order,
    )
)


def get_charts() -> tuple[StatsChart, ...]:
    return REGISTERED_CHARTS
