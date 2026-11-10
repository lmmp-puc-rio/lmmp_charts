"""Contract validation and dynamic SVG binding tests."""
from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from lmmp_charts.parametric.expressions import ExpressionError
from lmmp_charts.parametric.svg import ParametricSvgDocument

FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"


class DocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((FIXTURES / "parametric_contract.json").read_text(encoding="utf8"))
        cls.expected = json.loads((FIXTURES / "expected_patches.json").read_text(encoding="utf8"))

    def test_roundtrip_document(self):
        model = ParametricSvgDocument.from_dict(self.raw)
        self.assertEqual(model.to_dict(), self.raw)

    def test_initial_bindings(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        self.assertEqual(doc.evaluate_bindings(), self.expected["initial"])

    def test_updated_bindings(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        actual = doc.evaluate_bindings({"theta": 35, "theta_receding": 20, "theta_advancing": 80})
        self.assertEqual(actual, self.expected["updated"])

    def test_strings_and_colors_override(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        updated = doc.evaluate_bindings({"wetting.color": "#00ff00", "wetting.name": "Água"})
        self.assertEqual(updated[3]["value"], "Água")
        self.assertEqual(updated[4]["value"], "#00ff00")

    def test_constraint_rejects_invalid_order(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        with self.assertRaisesRegex(ValueError, "Avanço"):
            doc.evaluate_bindings({"theta": 80})
        with self.assertRaisesRegex(ValueError, "Recuo"):
            doc.evaluate_bindings({"theta": 10})

    def test_bounds_enforced(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        with self.assertRaises(ValueError):
            doc.evaluate_bindings({"theta": 500})

    def test_unknown_override(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        with self.assertRaises(ValueError):
            doc.evaluate_bindings({"unexpected": 3})

    def test_unknown_json_version(self):
        raw = copy.deepcopy(self.raw)
        raw["version"] = "999.0.0"
        with self.assertRaises(ValueError):
            ParametricSvgDocument.from_dict(raw)

    def test_event_handler_binding_forbidden(self):
        raw = copy.deepcopy(self.raw)
        raw["bindings"][0]["attribute"] = "onload"
        with self.assertRaises(ValueError):
            ParametricSvgDocument.from_dict(raw)

    def test_unknown_expression_reference(self):
        raw = copy.deepcopy(self.raw)
        raw["bindings"][0]["expression"] = {"var": "unknown"}
        with self.assertRaises(ExpressionError):
            ParametricSvgDocument.from_dict(raw)

    def test_nonfinite_overrides(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        with self.assertRaises(ValueError):
            doc.evaluate_bindings({"theta": math.inf})

    def test_binding_type_consistency(self):
        raw = copy.deepcopy(self.raw)
        raw["bindings"][0]["expression"] = {"const": "not-a-number"}
        with self.assertRaises(ExpressionError):
            ParametricSvgDocument.from_dict(raw)

    def test_too_long_string(self):
        doc = ParametricSvgDocument.from_dict(self.raw)
        with self.assertRaises(ValueError):
            doc.evaluate_bindings({"wetting.name": "X" * 3000})


if __name__ == "__main__":
    unittest.main()
