"""Geometry for a flat interface between two fluids and a solid boundary."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .curves import CurveGeometry, PointArray


@dataclass(frozen=True, slots=True)
class Rectangle:
    """A rectangle represented by four ordered 2D vertices."""

    vertices: PointArray

    def __post_init__(self) -> None:
        vertices = np.array(self.vertices, dtype=float, copy=True)
        if vertices.shape != (4, 2) or not np.isfinite(vertices).all():
            raise ValueError("Rectangle vertices must be a finite 4x2 array")
        edges = np.roll(vertices, -1, axis=0) - vertices
        lengths = np.linalg.norm(edges, axis=1)
        if np.any(lengths == 0):
            raise ValueError("Rectangle edges must have positive length")
        if not np.allclose(lengths[0], lengths[2]) or not np.allclose(lengths[1], lengths[3]):
            raise ValueError("Opposite rectangle edges must have equal lengths")
        products = np.sum(edges * np.roll(edges, -1, axis=0), axis=1)
        scales = lengths * np.roll(lengths, -1)
        if not np.all(np.abs(products) <= 1e-10 * scales):
            raise ValueError("Adjacent rectangle edges must be perpendicular")
        vertices.setflags(write=False)
        object.__setattr__(self, "vertices", vertices)

    @classmethod
    def from_bounds(
        cls, x_min: float, y_min: float, x_max: float, y_max: float,
    ) -> Rectangle:
        """Create an axis-aligned rectangle from its coordinate bounds."""
        bounds = (x_min, y_min, x_max, y_max)
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) for value in bounds):
            raise ValueError("Rectangle bounds must be finite numbers")
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("Rectangle bounds must have positive width and height")
        return cls(np.array([
            [x_min, y_min], [x_max, y_min],
            [x_max, y_max], [x_min, y_max],
        ], dtype=float))

    @property
    def edges(self) -> PointArray:
        """Return the four edge endpoint pairs in vertex order."""
        return np.stack((self.vertices, np.roll(self.vertices, -1, axis=0)), axis=1)


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
    """Compute coordinates for a flat interface in a rectangular domain.

    The interface is represented by a cubic Bézier curve with 220 samples.
    """

    def calculate(self, theta: float) -> RectangleCoordinates:
        if isinstance(theta, bool) or not isinstance(theta, (int, float)):
            raise ValueError("theta must be a finite angle in degrees")
        if not math.isfinite(theta) or not 0 < theta < 90:
            raise ValueError("Flat-interface geometry requires 0 < theta < 90")

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
