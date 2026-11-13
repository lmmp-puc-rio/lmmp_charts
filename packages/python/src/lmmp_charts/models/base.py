"""Shared interface for immutable chart configuration models."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, Self


class ConfigModel(ABC):
    """Base class for dataclass-based, serializable configuration models.

    Concrete subclasses must be dataclasses and implement ``validate()``.
    ``_normalize_dict`` is an optional hook for aliases or input adaptation.
    """

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Construct and validate the model from a mapping."""
        if not isinstance(data, Mapping):
            raise ValueError("Configuration must be a dictionary-like object.")

        normalized = cls._normalize_dict(dict(data))
        return cls(**normalized)

    @classmethod
    def from_json_file(cls, path: str | Path) -> Self:
        """Load UTF-8 JSON from a file, then normalize and validate via from_dict()."""
        with Path(path).open(encoding="utf-8") as file:
            data = json.load(file)

        return cls.from_dict(data)

    @classmethod
    def _normalize_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Return normalized constructor arguments (default: unchanged)."""
        return data

    def to_dict(self) -> dict[str, Any]:
        """Return the configuration as a serializable dictionary."""
        return asdict(self)

    def __post_init__(self) -> None:
        """Validate after the generated dataclass constructor completes."""
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """Validate fields for a concrete configuration model."""
        ...
