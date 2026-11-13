"""Backend-independent geometry building blocks."""
from .curves import CurveGeometry
from .rectangle import RectangleCoordinates, RectangleGeometry
from .triangle import TriangleCoordinates, TriangleGeometry

__all__ = ["CurveGeometry", "RectangleCoordinates", "RectangleGeometry", "TriangleCoordinates", "TriangleGeometry"]
