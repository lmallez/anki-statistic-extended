from __future__ import annotations

import json
import textwrap
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..runtime import plotly_asset_url

DataT = TypeVar("DataT")


def to_js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def wrap_plotly_chart_script(
    *, container_id: str, panel_order: int, render_js: str
) -> str:
    render_block = textwrap.indent(render_js.strip(), "    ")
    plotly_src = plotly_asset_url()

    return f"""(function() {{
  const CONTAINER_ID = {to_js(container_id)};
  const PANEL_ID = `${{CONTAINER_ID}}-panel`;
  const PANEL_ORDER = {panel_order};
  const ROOT_ID = 'anki-stats-extended-root';
  const GRID_ID = 'anki-stats-extended-grid';
  const STYLE_ID = 'anki-stats-extended-grid-style';
  const PLOTLY_SCRIPT_ATTR = 'data-anki-stats-extended-plotly';
  const existingPanel = document.getElementById(PANEL_ID);
  if (existingPanel) existingPanel.remove();

  function ensureLayout() {{
    if (!document.getElementById(STYLE_ID)) {{
      const style = document.createElement('style');
      style.id = STYLE_ID;
      style.textContent = `
        #${{ROOT_ID}} {{
          max-width: 1320px;
          margin: 1rem auto 2rem auto;
          padding: 0 8px;
          box-sizing: border-box;
        }}
        #${{GRID_ID}} {{
          display: grid;
          grid-template-columns: repeat(2, minmax(340px, 1fr));
          gap: 14px;
          align-items: start;
        }}
        #${{ROOT_ID}} .anki-stats-extended-panel {{
          border: 1px solid rgba(127, 127, 127, 0.14);
          border-radius: 16px;
          padding: 14px 14px 6px 14px;
          box-sizing: border-box;
          background: rgba(255, 255, 255, 0.96);
          min-height: 310px;
          overflow: hidden;
          order: 0;
        }}
        #${{ROOT_ID}} .anki-stats-extended-panel:hover {{
          border-color: rgba(127, 127, 127, 0.28);
        }}
        #${{ROOT_ID}} .anki-stats-extended-chart {{
          width: 100%;
          height: 290px;
        }}
        @media (max-width: 980px) {{
          #${{GRID_ID}} {{
            grid-template-columns: minmax(280px, 1fr);
          }}
        }}
      `;
      document.head.appendChild(style);
    }}

    let root = document.getElementById(ROOT_ID);
    if (!root) {{
      root = document.createElement('section');
      root.id = ROOT_ID;
      const grid = document.createElement('div');
      grid.id = GRID_ID;
      root.appendChild(grid);
      document.body.prepend(root);
    }}

    return {{
      root,
      grid: document.getElementById(GRID_ID),
    }};
  }}

  function ensurePanel() {{
    const layout = ensureLayout();
    let panel = document.getElementById(PANEL_ID);
    if (!panel) {{
      panel = document.createElement('section');
      panel.id = PANEL_ID;
      panel.className = 'anki-stats-extended-panel';
      panel.style.order = String(PANEL_ORDER);

      const container = document.createElement('div');
      container.id = CONTAINER_ID;
      container.className = 'anki-stats-extended-chart';
      panel.appendChild(container);
      layout.grid.appendChild(panel);
    }}
    return document.getElementById(CONTAINER_ID);
  }}

  const container = ensurePanel();

  function draw() {{
{render_block}
  }}

  function queueDrawUntilPlotlyLoads() {{
    window.__ankiStatsExtendedPlotlyQueue = window.__ankiStatsExtendedPlotlyQueue || [];
    window.__ankiStatsExtendedPlotlyQueue.push(draw);

    if (window.__ankiStatsExtendedPlotlyLoading) {{
      return;
    }}

    window.__ankiStatsExtendedPlotlyLoading = true;

    const flushQueue = () => {{
      const queue = window.__ankiStatsExtendedPlotlyQueue || [];
      window.__ankiStatsExtendedPlotlyQueue = [];
      window.__ankiStatsExtendedPlotlyLoading = false;
      queue.forEach((callback) => callback());
    }};

    const existingScript = document.querySelector(`script[${{PLOTLY_SCRIPT_ATTR}}="1"]`);
    if (existingScript) {{
      existingScript.addEventListener('load', flushQueue, {{ once: true }});
      existingScript.addEventListener('error', () => {{
        window.__ankiStatsExtendedPlotlyLoading = false;
      }}, {{ once: true }});
      return;
    }}

    const script = document.createElement('script');
    script.setAttribute(PLOTLY_SCRIPT_ATTR, '1');
    script.src = {to_js(plotly_src)};
    script.onload = flushQueue;
    script.onerror = () => {{
      window.__ankiStatsExtendedPlotlyLoading = false;
      console.error('Failed to load Plotly for Anki Statistics Extended');
    }};
    document.head.appendChild(script);
  }}

  if (window.Plotly) {{
    draw();
  }} else {{
    queueDrawUntilPlotlyLoads();
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
            panel_order=self.order,
            render_js=self.build_render_js(data),
        )

    @abstractmethod
    def build_data(self) -> DataT:
        raise NotImplementedError

    @abstractmethod
    def build_render_js(self, data: DataT) -> str:
        raise NotImplementedError
