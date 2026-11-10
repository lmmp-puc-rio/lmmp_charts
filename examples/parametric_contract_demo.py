"""Demonstrate pure-Python evaluation of the shared SVG transport document.

Run from project root with:
  PYTHONPATH=packages/python/src python examples/parametric_contract_demo.py
"""
import json
from pathlib import Path

from lmmp_charts.parametric.svg import ParametricSvgDocument

root = Path(__file__).resolve().parents[1]
fixture = root / "tests/integration/fixtures/parametric_contract.json"
model = ParametricSvgDocument.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
print("Initial patches:")
print(json.dumps(model.evaluate_bindings(), ensure_ascii=False, indent=2))
print("Updated patches:")
print(json.dumps(model.evaluate_bindings({
    "theta": 35, "theta_receding": 20, "theta_advancing": 80,
}), ensure_ascii=False, indent=2))
