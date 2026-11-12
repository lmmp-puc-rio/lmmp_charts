"""Plotly renderer for an interface in a solid corner."""

from __future__ import annotations

import plotly.graph_objects as go

from lmmp_charts.geometry.curves import CurveGeometry
from lmmp_charts.geometry.interfacial import CornerInterfaceCoordinates
from lmmp_charts.models.wettability import Wettability

from .primitives import PlotlyPrimitives as Draw


class CornerInterfacePlotlyRenderer:
    """Render a corner meniscus, tangent and absolute hysteresis rays."""

    def draw(self, fig: go.Figure, geom: CornerInterfaceCoordinates, model: Wettability) -> None:
        Q = geom.lower_contact
        Draw.polygon(fig, geom.non_wetting_region, model.non_wetting_fluid.color)
        Draw.polygon(fig, geom.wetting_region, model.wetting_fluid.color)
        Draw.line(fig, geom.meniscus, color="rgba(255,255,255,0.8)", width=1.4)

        alpha_r = 180 - model.theta_receding
        alpha_a = 180 - model.theta_advancing
        Draw.line(fig, CurveGeometry.circular_arc(Q, 0.88, 180, alpha_r),
                  color="rgba(20,20,20,0.9)", width=2.1)
        Draw.line(fig, CurveGeometry.circular_arc(Q, 1.27, 180, alpha_a),
                  color="rgba(20,20,20,0.9)", width=2.1)

        Draw.line(fig, [Q, Q + 2.05 * geom.receding_direction],
                  color="white", width=4.2, dash="dash")
        Draw.line(fig, [Q, Q + 2.35 * geom.advancing_direction],
                  color="white", width=4.2, dash="dash")
        Draw.line(fig, [Q, Q + 2.0 * geom.tangent_direction],
                  color="#151515", width=4.0, dash="dash")

        Draw.text(fig, 4.08, 3.17, f"θᵣ = {model.theta_receding:g}°", color="white", size=15)
        Draw.text(fig, 8.15, 3.15, f"θₐ = {model.theta_advancing:g}°", color="white", size=15)
        Draw.text(fig, 3.10, 1.81, model.wetting_fluid.name, color="white", size=16)
        Draw.text(fig, 6.65, 6.24, model.non_wetting_fluid.name, color="white", size=17)

        Draw.line(fig, geom.inclined_solid_boundary, width=6)
        Draw.line(fig, geom.lower_solid_boundary, width=6)
        Draw.text(fig, 6.0, 0.46, model.rock.name, size=19)
