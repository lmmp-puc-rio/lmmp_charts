"""Public Python API for fluid–rock–fluid interfacial charts.

The facade owns the wettability configuration; the Plotly builder is a
reusable, stateless-with-respect-to-input rendering service.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go

from lmmp_charts.rendering.plotly import InterfacialBuilder
from lmmp_charts.models import Wettability


class InterfacialChart:
    """Generate a Plotly.js-compatible graph from one wettability model.

    The model is an immutable configuration object.  ``generate()`` returns
    a Python dictionary containing ``data``, ``layout`` and ``config``
    suitable for a Django REST Framework Response.

    No Django or JavaScript dependency is required by this facade.
    """

    def __init__(self, model: Wettability) -> None:
        if not isinstance(model, Wettability):
            raise TypeError("InterfacialChart requires a Wettability instance.")
        self._model = model
        self._builder = InterfacialBuilder()

    @property
    def model(self) -> Wettability:
        """The configuration used for this chart (read-only)."""
        return self._model

    def generate(self) -> dict[str, Any]:
        """Return a JSON-serializable Plotly.js figure specification."""
        return self._builder.to_payload(self._model)

    def to_json(self) -> str:
        """Return a JSON string including Plotly.js render options."""
        return json.dumps(self.generate(), ensure_ascii=False, allow_nan=False)

    def to_figure(self) -> go.Figure:
        """Create a Plotly.py figure for inspection or customization."""
        return self._builder.build(self._model)

    def show(self) -> None:
        """Open the chart using the configured Plotly.py renderer."""
        self.to_figure().show()

    def save_image(self, path: str | Path, *, scale: float = 1.0) -> None:
        """Save a static image using Plotly/Kaleido (optional dependency).

        Supported formats depend on the installed Plotly/Kaleido versions.
        A Chrome/Chromium installation may be required by Kaleido.
        """
        if not isinstance(path, (str, Path)) or not str(path):
            raise ValueError("path must be a non-empty string or pathlib.Path")
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not 0 < scale < float("inf"):
            raise ValueError("scale must be a positive finite number")
        self.to_figure().write_image(str(path), scale=float(scale))
