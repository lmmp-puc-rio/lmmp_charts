"""Backend-independent geometry for fluid interfaces in solid domains."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from lmmp_charts.models.wettability import Wettability

from .curves import CurveGeometry, PointArray
from .rectangle import Rectangle
from .triangle import Triangle


@dataclass(frozen=True, slots=True)
class FlatInterfaceCoordinates:
    """Coordinates for a flat fluid interface and its rectangular domain."""

    domain: Rectangle
    non_wetting_region: PointArray
    wetting_region: PointArray
    interface_curve: PointArray
    contact_point: PointArray
    tangent_direction: PointArray
    solid_boundary: PointArray


@dataclass(frozen=True, slots=True)
class CornerInterfaceCoordinates:
    """Coordinates for a fluid meniscus and contact rays in a corner."""

    domain: Triangle
    corner: PointArray
    inclined_contact: PointArray
    lower_contact: PointArray
    meniscus: PointArray
    wetting_region: PointArray
    non_wetting_region: PointArray
    inclined_solid_boundary: PointArray
    lower_solid_boundary: PointArray
    tangent_direction: PointArray
    advancing_direction: PointArray
    receding_direction: PointArray


@dataclass(frozen=True, slots=True)
class InterfacialCoordinates:
    """Backend-neutral coordinates for the flat and corner interfaces."""

    flat_interface: FlatInterfaceCoordinates
    corner_interface: CornerInterfaceCoordinates


class InterfacialGeometry:
    """Calculate interfacial regions and meniscus geometry from wettability."""

    def calculate(self, model: Wettability) -> InterfacialCoordinates:
        """Return coordinates without assigning rendering-specific styles."""
        if not isinstance(model, Wettability):
            raise TypeError("InterfacialGeometry requires a Wettability instance")
        if not (0 <= model.theta_receding < model.theta < model.theta_advancing < 90):
            raise ValueError(
                "Expected 0 <= theta_receding < theta < theta_advancing < 90"
            )

        flat = self._flat_interface(model.theta)
        corner = self._corner_interface(
            model.theta, model.theta_advancing, model.theta_receding,
        )
        return InterfacialCoordinates(flat_interface=flat, corner_interface=corner)

    @staticmethod
    def _flat_interface(theta: float) -> FlatInterfaceCoordinates:
        x0, x1, y0, y1 = 1.20, 10.80, 11.00, 15.30
        domain = Rectangle.from_bounds(x0, y0, x1, y1)
        vertices = domain.vertices
        contact = np.array([6.15, y0])
        top = np.array([8.45, y1])
        tangent = CurveGeometry.direction(theta)
        curve = CurveGeometry.cubic_bezier(
            contact,
            contact + 2.10 * tangent,
            [7.45, 14.45],
            top,
        )
        wetting_region = np.vstack((curve, vertices[2], vertices[1]))
        solid_boundary = np.array([vertices[0], vertices[1]])
        return FlatInterfaceCoordinates(
            domain=domain,
            non_wetting_region=vertices,
            wetting_region=wetting_region,
            interface_curve=curve,
            contact_point=contact,
            tangent_direction=tangent,
            solid_boundary=solid_boundary,
        )

    @staticmethod
    def _corner_interface(
        theta: float, theta_advancing: float, theta_receding: float,
    ) -> CornerInterfaceCoordinates:
        corner = np.array([1.30, 0.94])
        length = 9.40
        opening_deg = 60.0
        opening = math.radians(opening_deg)
        apex = corner + length * CurveGeometry.direction(opening_deg)
        right = corner + np.array([length, 0.0])
        domain = Triangle(np.array([corner, apex, right]))

        q = 0.62 * length
        lower = corner + np.array([q, 0.0])
        inclined = corner + q * CurveGeometry.direction(opening_deg)
        radians = math.radians(theta)
        denominator = math.cos(radians + opening / 2)

        if abs(denominator) < 1e-9:
            meniscus = np.linspace(lower, inclined, 220)
        else:
            signed_radius = q * math.sin(opening / 2) / denominator
            center = lower + signed_radius * np.array(
                [math.sin(radians), math.cos(radians)]
            )
            radius = abs(signed_radius)
            start = math.atan2(lower[1] - center[1], lower[0] - center[0])
            end = math.atan2(inclined[1] - center[1], inclined[0] - center[0])
            sweep = (end - start + math.pi) % (2 * math.pi) - math.pi
            azimuth = start + np.linspace(0, sweep, 220)
            meniscus = center + radius * np.column_stack(
                (np.cos(azimuth), np.sin(azimuth))
            )
            meniscus[0] = lower
            meniscus[-1] = inclined

        return CornerInterfaceCoordinates(
            domain=domain,
            corner=corner,
            inclined_contact=inclined,
            lower_contact=lower,
            meniscus=meniscus,
            wetting_region=np.vstack((corner, inclined, meniscus[::-1], lower)),
            non_wetting_region=domain.vertices,
            inclined_solid_boundary=np.array([corner, apex]),
            lower_solid_boundary=np.array([corner, right]),
            tangent_direction=CurveGeometry.direction(180 - theta),
            advancing_direction=CurveGeometry.direction(180 - theta_advancing),
            receding_direction=CurveGeometry.direction(180 - theta_receding),
        )


__all__ = [
    "CornerInterfaceCoordinates",
    "FlatInterfaceCoordinates",
    "InterfacialCoordinates",
    "InterfacialGeometry",
]
