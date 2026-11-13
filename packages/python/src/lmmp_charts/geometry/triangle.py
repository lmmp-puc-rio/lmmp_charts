"""Wetting film in the lower-left corner of a triangular throat (v5)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .curves import CurveGeometry, PointArray


@dataclass(frozen=True, slots=True)
class TriangleCoordinates:
    """Calculated geometry, including angles expressed as unit directions."""

    corner: PointArray
    inclined_contact: PointArray
    lower_contact: PointArray
    meniscus: PointArray  # Ordered from lower contact Q to inclined contact P.
    wetting_polygon: PointArray
    non_wetting_polygon: PointArray
    inclined_rock_segment: PointArray
    lower_rock_segment: PointArray
    tangent_direction: PointArray
    advancing_direction: PointArray
    receding_direction: PointArray


class TriangleGeometry:
    """Calculate the approved circular film with contact-angle hysteresis.

    θ controls the meniscus and its tangent at the lower contact.
    θa and θr supply absolute reference rays at that *same* contact;
    neither is used to reposition either endpoint of the meniscus.
    """

    def calculate(
        self, theta: float, theta_advancing: float, theta_receding: float
    ) -> TriangleCoordinates:
        values = (theta, theta_advancing, theta_receding)
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) for value in values):
            raise ValueError("Contact angles must be finite numeric values")
        if not 0 <= theta_receding < theta < theta_advancing < 90:
            raise ValueError("Expected 0 <= theta_receding < theta < theta_advancing < 90")

        corner = np.array([1.30, 0.94])
        length = 9.40
        opening_deg = 60.0
        opening = math.radians(opening_deg)
        apex = corner + length * CurveGeometry.direction(opening_deg)
        right = corner + np.array([length, 0.0])

        q = 0.62 * length
        Q = corner + np.array([q, 0.0])
        P = corner + q * CurveGeometry.direction(opening_deg)
        radians = math.radians(theta)
        denominator = math.cos(radians + opening / 2)

        # A curvature-free limit exists precisely at θ + φ/2 = 90°.
        if abs(denominator) < 1e-9:
            meniscus = np.linspace(Q, P, 220)
        else:
            signed_radius = q * math.sin(opening / 2) / denominator
            center = Q + signed_radius * np.array([math.sin(radians), math.cos(radians)])
            radius = abs(signed_radius)
            a0 = math.atan2(Q[1] - center[1], Q[0] - center[0])
            a1 = math.atan2(P[1] - center[1], P[0] - center[0])
            delta = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            azimuth = a0 + np.linspace(0, delta, 220)
            meniscus = center + radius * np.column_stack((np.cos(azimuth), np.sin(azimuth)))
            meniscus[0] = Q
            meniscus[-1] = P

        return TriangleCoordinates(
            corner=corner,
            inclined_contact=P,
            lower_contact=Q,
            meniscus=meniscus,
            wetting_polygon=np.vstack((corner, P, meniscus[::-1], Q)),
            non_wetting_polygon=np.vstack((corner, apex, right)),
            inclined_rock_segment=np.vstack((corner, apex)),
            lower_rock_segment=np.vstack((corner, right)),
            tangent_direction=CurveGeometry.direction(180 - theta),
            advancing_direction=CurveGeometry.direction(180 - theta_advancing),
            receding_direction=CurveGeometry.direction(180 - theta_receding),
        )
