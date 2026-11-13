"""Flat rock/fluid-interface geometry preserved from the approved v5 chart."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .curves import CurveGeometry, PointArray


@dataclass(frozen=True, slots=True)
class RectangleCoordinates:
    """Calculated drawing coordinates; no Plotly or presentation attributes."""

    non_wetting_polygon: PointArray
    wetting_polygon: PointArray
    interface_curve: PointArray
    contact_point: PointArray
    tangent_direction: PointArray
    rock_segment: PointArray


class RectangleGeometry:
    """Compute the flat-interface coordinates used by the v5 diagram.

    Default values reproduce the approved geometry exactly. In particular,
    the interface is the same cubic Bézier with 220 samples.
    """

    def calculate(self, theta: float) -> RectangleCoordinates:
        if isinstance(theta, bool) or not isinstance(theta, (int, float)):
            raise ValueError("theta must be a finite angle in degrees")
        if not math.isfinite(theta) or not 0 < theta < 90:
            raise ValueError("The approved flat diagram requires 0 < theta < 90")

        x0, x1, y0, y1 = 1.20, 10.80, 11.00, 15.30
        contact = np.array([6.15, y0])
        top = np.array([8.45, y1])
        tangent = CurveGeometry.direction(theta)

        curve = CurveGeometry.cubic_bezier(
            contact,
            contact + 2.10 * tangent,
            [7.45, 14.45],
            top,
        )
        nonwet_polygon = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        wet_polygon = np.vstack((curve, [x1, y1], [x1, y0]))
        rock_segment = np.array([(x0, y0), (x1, y0)])
        return RectangleCoordinates(
            non_wetting_polygon=nonwet_polygon,
            wetting_polygon=wet_polygon,
            interface_curve=curve,
            contact_point=contact,
            tangent_direction=tangent,
            rock_segment=rock_segment,
        )
