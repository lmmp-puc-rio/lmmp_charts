"""Reusable, backend-independent 2D geometry primitives.

Coordinates are NumPy arrays in an abstract Cartesian drawing space.
Angles are in degrees unless explicitly documented otherwise.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

PointArray = NDArray[np.float64]


class CurveGeometry:
    """Stateless mathematical helpers for 2D coordinate calculations."""

    @staticmethod
    def direction(degrees: float) -> PointArray:
        """Return the unit vector for an angle measured counterclockwise."""
        radians = math.radians(degrees)
        return np.array([math.cos(radians), math.sin(radians)], dtype=float)

    @staticmethod
    def cubic_bezier(
        p0: Sequence[float],
        p1: Sequence[float],
        p2: Sequence[float],
        p3: Sequence[float],
        *,
        n_points: int = 220,
    ) -> PointArray:
        """Sample a cubic Bézier curve, preserving its endpoint tangents."""
        if n_points < 2:
            raise ValueError("n_points must be at least 2")
        p0, p1, p2, p3 = (np.asarray(p, dtype=float) for p in (p0, p1, p2, p3))
        for point in (p0, p1, p2, p3):
            if point.shape != (2,) or not np.isfinite(point).all():
                raise ValueError("Control points must be finite 2D coordinates")
        t = np.linspace(0, 1, n_points)[:, None]
        return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1
                + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)

    @staticmethod
    def circular_arc(
        center: Sequence[float],
        radius: float,
        start_deg: float,
        end_deg: float,
        *,
        n_points: int = 100,
    ) -> PointArray:
        """Sample a circular arc from start_deg to end_deg (signed sweep)."""
        if n_points < 2:
            raise ValueError("n_points must be at least 2")
        center = np.asarray(center, dtype=float)
        if center.shape != (2,) or not np.isfinite(center).all():
            raise ValueError("center must be a finite 2D coordinate")
        if not math.isfinite(radius) or radius <= 0:
            raise ValueError("radius must be finite and positive")
        if not (math.isfinite(start_deg) and math.isfinite(end_deg)):
            raise ValueError("Arc angles must be finite")
        a = np.deg2rad(np.linspace(start_deg, end_deg, n_points))
        return center + radius * np.column_stack((np.cos(a), np.sin(a)))
