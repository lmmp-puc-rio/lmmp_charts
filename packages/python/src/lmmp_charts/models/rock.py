"""Rock display configuration model."""

from __future__ import annotations

from dataclasses import dataclass

from .base import ConfigModel


@dataclass(frozen=True, slots=True)
class Rock(ConfigModel):
    """Rock identification for diagram labels."""

    name: str

    def validate(self) -> None:
        """Require a non-empty rock name."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Rock name must be a non-empty string.")
