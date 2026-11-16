"""Rectangular geometric primitive."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .curves import PointArray


@dataclass(frozen=True, slots=True)
class Rectangle:
    """A rectangle represented by four ordered two-dimensional vertices."""

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

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Rectangle) and bool(
            np.array_equal(self.vertices, other.vertices)
        )

    def __hash__(self) -> int:
        return hash(tuple(tuple(point) for point in self.vertices.tolist()))

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
