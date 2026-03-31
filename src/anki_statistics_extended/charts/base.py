from __future__ import annotations

import json
import textwrap
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..runtime import plotly_asset_url

DataT = TypeVar("DataT")


def to_js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def wrap_plotly_chart_script(*, container_id: str, render_js: str) -> str:
    render_block = textwrap.indent(render_js.strip(), "    ")
    plotly_src = plotly_asset_url()

    return f"""(function() {{
  const CONTAINER_ID = {to_js(container_id)};
  const existing = document.getElementById(CONTAINER_ID);
  if (existing) existing.remove();

  function draw() {{
{render_block}
  }}

  if (window.Plotly) {{
    draw();
  }} else {{
    const script = document.createElement('script');
    script.src = {to_js(plotly_src)};
    script.onload = draw;
    document.head.appendChild(script);
  }}
}})();"""


class StatsChart(ABC):
    key: str
    order = 100

    @abstractmethod
    def build_script(self) -> str:
        raise NotImplementedError


class PlotlyChart(StatsChart, Generic[DataT], ABC):
    container_id: str

    def build_script(self) -> str:
        data = self.build_data()
        if not data:
            return ""
        return wrap_plotly_chart_script(
            container_id=self.container_id,
            render_js=self.build_render_js(data),
        )

    @abstractmethod
    def build_data(self) -> DataT:
        raise NotImplementedError

    @abstractmethod
    def build_render_js(self, data: DataT) -> str:
        raise NotImplementedError
