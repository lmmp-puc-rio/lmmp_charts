"""Fluid display configuration model."""

from __future__ import annotations

from dataclasses import dataclass

from .base import ConfigModel


@dataclass(frozen=True, slots=True)
class Fluid(ConfigModel):
    """Identification and display color of a fluid in a chart.

    Wetting/non-wetting status is assigned by the containing interface,
    not by a fluid in isolation.
    """

    name: str
    color: str

    def validate(self) -> None:
        """Require non-empty name and color strings."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Fluid name must be a non-empty string.")

        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError("Fluid color must be a non-empty string.")
