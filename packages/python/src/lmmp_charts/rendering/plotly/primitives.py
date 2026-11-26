"""Low-level Plotly drawing helpers (no domain-specific assumptions)."""

from __future__ import annotations

import html
from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from lmmp_charts.geometry.curves import CurveGeometry


class PlotlyPrimitives:
    """Append filled polygons, polylines, labels and sectors to a figure."""

    @staticmethod
    def polygon(fig: go.Figure, points: np.ndarray | Sequence, fill: str) -> None:
        coords = np.asarray(points, dtype=float)
        coords = np.vstack((coords, coords[0]))
        fig.add_trace(go.Scatter(
            x=coords[:, 0], y=coords[:, 1], mode="lines", fill="toself",
            fillcolor=fill, line={"color": fill, "width": 0},
            hoverinfo="skip", showlegend=False,
        ))

    @staticmethod
    def line(
        fig: go.Figure,
        points: np.ndarray | Sequence,
        *,
        color: str = "#171717",
        width: float = 3,
        dash: str = "solid",
    ) -> None:
        coords = np.asarray(points, dtype=float)
        fig.add_trace(go.Scatter(
            x=coords[:, 0], y=coords[:, 1], mode="lines",
            line={"color": color, "width": width, "dash": dash},
            hoverinfo="skip", showlegend=False,
        ))

    @staticmethod
    def text(
        fig: go.Figure, x: float, y: float, label: str, *,
        color: str = "#171717", size: int = 20,
        bgcolor: str | None = None, bordercolor: str | None = None,
        borderwidth: float = 0, borderpad: float = 1,
    ) -> None:
        annotation_kwargs = {}
        if bgcolor is not None:
            annotation_kwargs["bgcolor"] = bgcolor
        if bordercolor is not None:
            annotation_kwargs["bordercolor"] = bordercolor
            annotation_kwargs["borderwidth"] = borderwidth
            annotation_kwargs["borderpad"] = borderpad
        fig.add_annotation(
            x=x, y=y, text=html.escape(str(label)), showarrow=False,
            xanchor="center", yanchor="middle", align="center",
            font={"family": "Arial, sans-serif", "size": size, "color": color},
            **annotation_kwargs,
        )

    @classmethod
    def sector(
        cls, fig: go.Figure, center: np.ndarray, radius: float,
        start_deg: float, end_deg: float, color: str,
    ) -> None:
        arc = CurveGeometry.circular_arc(center, radius, start_deg, end_deg)
        cls.polygon(fig, np.vstack([center, arc]), color)
        cls.line(fig, arc, width=1.4, color="rgba(65,65,65,0.56)")
