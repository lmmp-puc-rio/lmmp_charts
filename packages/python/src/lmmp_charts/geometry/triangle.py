"""Triangular geometric primitive."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .curves import PointArray


@dataclass(frozen=True, slots=True)
class Triangle:
    """A nondegenerate triangle represented by three ordered 2D vertices."""

    vertices: PointArray

    def __post_init__(self) -> None:
        vertices = np.array(self.vertices, dtype=float, copy=True)
        if vertices.shape != (3, 2) or not np.isfinite(vertices).all():
            raise ValueError("Triangle vertices must be a finite 3x2 array")
        first, second = vertices[1] - vertices[0], vertices[2] - vertices[0]
        area_twice = first[0] * second[1] - first[1] * second[0]
        if area_twice == 0:
            raise ValueError("Triangle vertices must not be collinear")
        vertices.setflags(write=False)
        object.__setattr__(self, "vertices", vertices)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Triangle) and bool(
            np.array_equal(self.vertices, other.vertices)
        )

    def __hash__(self) -> int:
        return hash(tuple(tuple(point) for point in self.vertices.tolist()))

    @property
    def edges(self) -> PointArray:
        """Return the three edge endpoint pairs in vertex order."""
        return np.stack((self.vertices, np.roll(self.vertices, -1, axis=0)), axis=1)
