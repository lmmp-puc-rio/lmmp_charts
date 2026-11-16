"""Combine backend-agnostic interfacial geometry into a Plotly figure."""

from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go

from lmmp_charts.geometry.rectangle import RectangleGeometry
from lmmp_charts.geometry.triangle import TriangleGeometry
from lmmp_charts.models.wettability import Wettability

from .primitives import PlotlyPrimitives as Draw
from .rectangle import RectanglePlotlyRenderer
from .styles import FIGURE_LAYOUT, RENDER_CONFIG
from .triangle import TrianglePlotlyRenderer


class InterfacialBuilder:
    """Build the exact approved v5 figure from a typed wettability model.

    This backend is independent of Django and any JavaScript rendering library.
    It returns a Plotly Figure or a JSON-compatible mapping. An application-level
    facade in charts/interfacial_chart.py can expose it in the next phase.
    """

    def __init__(self) -> None:
        self._flat_geometry = RectangleGeometry()
        self._corner_geometry = TriangleGeometry()
        self._flat_renderer = RectanglePlotlyRenderer()
        self._corner_renderer = TrianglePlotlyRenderer()

    def build(self, model: Wettability) -> go.Figure:
        """Build a native Plotly figure, preserving v5 trace/annotation order."""
        if not isinstance(model, Wettability):
            raise TypeError("InterfacialBuilder requires a Wettability instance")
        if not (0 <= model.theta_receding < model.theta < model.theta_advancing < 90):
            raise ValueError("The approved interfacial figure requires angles < 90°")

        fig = go.Figure()
        self._flat_renderer.draw(fig, self._flat_geometry.calculate(model.theta), model)
        self._corner_renderer.draw(
            fig,
            self._corner_geometry.calculate(
                model.theta, model.theta_advancing, model.theta_receding,
            ),
            model,
        )
        Draw.text(fig, 6.0, 16.21, "Interfaces", size=31)
        fig.update_layout(**FIGURE_LAYOUT)
        return fig

    def to_payload(self, model: Wettability) -> dict[str, Any]:
        """Return a fully JSON-serializable Plotly.js figure specification.

        Plotly 6 may encode numeric trace arrays as base64 typed arrays. That is
        part of the native Plotly.js-compatible JSON representation. Consumers
        should use a compatible Plotly.js version when rendering this payload.
        """
        figure = self.build(model)
        payload: dict[str, Any] = json.loads(figure.to_json())
        payload["config"] = dict(RENDER_CONFIG)
        return payload


# Backwards-compatible class alias; no duplicate implementation.
InterfacialPlotlyBuilder = InterfacialBuilder
