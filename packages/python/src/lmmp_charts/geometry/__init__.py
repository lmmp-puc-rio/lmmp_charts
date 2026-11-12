"""Backend-independent geometry building blocks."""
from .curves import CurveGeometry
from .rectangle import Rectangle, RectangleCoordinates, RectangleGeometry
from .triangle import Triangle, TriangleCoordinates, TriangleGeometry

__all__ = [
    "CurveGeometry",
    "Rectangle",
    "RectangleCoordinates",
    "RectangleGeometry",
    "Triangle",
    "TriangleCoordinates",
    "TriangleGeometry",
]
