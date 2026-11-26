"""Plotly renderer for a flat fluid interface in a solid domain."""

from __future__ import annotations

import plotly.graph_objects as go

from lmmp_charts.geometry.interfacial import FlatInterfaceCoordinates
from lmmp_charts.models.wettability import Wettability

from .primitives import PlotlyPrimitives as Draw


class FlatInterfacePlotlyRenderer:
    """Render calculated coordinates for a flat fluid interface."""

    def draw(self, fig: go.Figure, geom: FlatInterfaceCoordinates, model: Wettability) -> None:
        Draw.polygon(fig, geom.non_wetting_region, model.non_wetting_fluid.color)
        Draw.polygon(fig, geom.wetting_region, model.wetting_fluid.color)
        Draw.line(fig, geom.interface_curve, color="rgba(255,255,255,0.65)", width=1.1)

        Draw.sector(fig, geom.contact_point, 1.20, 0, model.theta,
                    "rgba(238,238,238,0.84)")
        Draw.line(fig, [geom.contact_point, geom.contact_point + 2.7 * geom.tangent_direction],
                  color="#151515", width=4.0, dash="dash")
        Draw.line(fig, geom.solid_boundary, width=5.0)

        Draw.text(fig, 3.25, 13.05, model.non_wetting_fluid.name, color="white", size=18)
        Draw.text(fig, 9.30, 13.05, model.wetting_fluid.name, color="white", size=17)
        Draw.text(fig, 8.05, 11.67, f"θ = {model.theta:g}°", size=15)
        Draw.text(fig, 6.0, 10.50, model.rock.name, size=19)
