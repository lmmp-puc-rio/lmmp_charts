"""Minimal backend-style example using the public lmmp_charts Python API.

Run from the repository root with:

    PYTHONPATH=packages/python/src python examples/example_backend.py

In VS Code, select ``Python: example_backend`` and press F5. Useful breakpoint
locations are the ``model``, ``chart`` and ``payload`` assignments in ``main``.
"""

from __future__ import annotations

from typing import Any

from lmmp_charts import InterfacialChart, Wettability


def example_configuration() -> dict[str, Any]:
    """Return input shaped like a JSON request received by a backend."""
    return {
        "rock": {"name": "Bentheimer"},
        "fluids": {
            "wetting": {"name": "Salmoura", "color": "#4472C4"},
            "non_wetting": {"name": "CO2", "color": "#C00000"},
        },
        "angles": {
            "theta": 45,
            "theta_advancing": 75,
            "theta_receding": 25,
        },
    }


def main() -> None:
    """Validate the request model and generate a Plotly.js payload."""
    configuration = example_configuration()

    model = Wettability.from_dict(configuration)
    chart = InterfacialChart(model)
    payload = chart.generate()

    print(f"Chart: {type(chart).__name__}")
    print(f"Model: {model.to_dict()}")
    print(f"Payload keys: {sorted(payload)}")
    print(f"Plotly traces: {len(payload['data'])}")
    print(f"Annotations: {len(payload['layout']['annotations'])}")
    print(f"Render config: {payload['config']}")


if __name__ == "__main__":
    main()
