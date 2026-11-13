"""Fluid-rock-fluid wettability configuration model.

This module contains configuration data only. It has no dependency on
Django, Plotly, or any particular chart backend.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .base import ConfigModel
from .fluid import Fluid
from .rock import Rock


@dataclass(frozen=True, slots=True)
class Wettability(ConfigModel):
    """Wettability of a rock in contact with two fluid phases.

    All contact angles are absolute values in degrees, measured from the
    lower solid surface *through the wetting phase*. The reusable model
    accepts angles up to 180 degrees; individual charts may impose tighter
    restrictions (the PoreSIM v5 interfacial diagram requires advancing < 90).

    `from_dict()` reads the nested configuration agreed for the diagram::

        {
            "rock": {"name": "Bentheimer"},
            "fluids": {
                "wetting": {"name": "Salmoura", "color": "#4472C4"},
                "non_wetting": {"name": "CO2", "color": "#FF0000"}
            },
            "angles": {
                "theta": 45,
                "theta_advancing": 75,
                "theta_receding": 25
            }
        }

    Constructor-shaped mappings are also accepted for programmatic use.
    The legacy angle names `theta_a`/`theta_r` are supported in either form.
    """

    rock: Rock
    wetting_fluid: Fluid
    non_wetting_fluid: Fluid
    theta: float
    theta_advancing: float
    theta_receding: float

    @classmethod
    def _normalize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Convert nested input to typed constructor fields without mutation."""
        if "fluids" in data or "angles" in data:
            if set(data) != {"rock", "fluids", "angles"}:
                raise ValueError("Nested wettability requires rock, fluids, and angles only.")
            fluids = data["fluids"]
            angles = data["angles"]
            if not isinstance(fluids, Mapping) or set(fluids) != {"wetting", "non_wetting"}:
                raise ValueError("fluids must contain wetting and non_wetting objects.")
            if not isinstance(angles, Mapping):
                raise ValueError("angles must be a mapping of contact angles.")
            normalized = {
                "rock": data["rock"],
                "wetting_fluid": fluids["wetting"],
                "non_wetting_fluid": fluids["non_wetting"],
                **dict(angles),
            }
        else:
            normalized = data.copy()

        for alias, canonical in (
            ("theta_a", "theta_advancing"),
            ("theta_r", "theta_receding"),
        ):
            if alias in normalized:
                if canonical in normalized and normalized[canonical] != normalized[alias]:
                    raise ValueError(f"Conflicting angle values: {canonical} and {alias}.")
                normalized[canonical] = normalized.pop(alias)

        for key, model in (
            ("rock", Rock),
            ("wetting_fluid", Fluid),
            ("non_wetting_fluid", Fluid),
        ):
            value = normalized.get(key)
            if isinstance(value, Mapping):
                normalized[key] = model.from_dict(value)

        return normalized

    def validate(self) -> None:
        """Validate participating phases and absolute angle ordering."""
        if not isinstance(self.rock, Rock):
            raise ValueError("rock must be a Rock instance.")
        if not isinstance(self.wetting_fluid, Fluid):
            raise ValueError("wetting_fluid must be a Fluid instance.")
        if not isinstance(self.non_wetting_fluid, Fluid):
            raise ValueError("non_wetting_fluid must be a Fluid instance.")

        for name in ("theta", "theta_advancing", "theta_receding"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{name} must be a finite numeric angle in degrees.")

        if not (0 <= self.theta_receding < self.theta < self.theta_advancing <= 180):
            raise ValueError(
                "Contact angles must satisfy "
                "0 <= theta_receding < theta < theta_advancing <= 180."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the original nested, JSON-serializable configuration format."""
        return {
            "rock": self.rock.to_dict(),
            "fluids": {
                "wetting": self.wetting_fluid.to_dict(),
                "non_wetting": self.non_wetting_fluid.to_dict(),
            },
            "angles": {
                "theta": self.theta,
                "theta_advancing": self.theta_advancing,
                "theta_receding": self.theta_receding,
            },
        }
