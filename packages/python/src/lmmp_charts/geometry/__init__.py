"""Backend-independent geometry building blocks."""
from .curves import CurveGeometry
from .interfacial import (
    CornerInterfaceCoordinates,
    FlatInterfaceCoordinates,
    InterfacialCoordinates,
    InterfacialGeometry,
)
from .rectangle import Rectangle
from .triangle import Triangle

__all__ = [
    "CurveGeometry",
    "CornerInterfaceCoordinates",
    "FlatInterfaceCoordinates",
    "InterfacialCoordinates",
    "InterfacialGeometry",
    "Rectangle",
    "Triangle",
]
