"""Portable expression interpreter tests (Python side)."""
from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from lmmp_charts.parametric.expressions import ExpressionError, evaluate, references

FIXTURES = Path(__file__).resolve().parents[1] / "integration" / "fixtures"


def c(v): return {"const": v}
def v(name): return {"var": name}
def op(name, *args): return {"op": name, "args": list(args)}


class ExpressionTests(unittest.TestCase):
    def test_shared_language_fixture(self):
        cases = json.loads((FIXTURES / "expressions.json").read_text(encoding="utf8"))["numbers"]
        for case in cases["cases"]:
            with self.subTest(case=case["name"]):
                actual = evaluate(case["expression"], cases["variables"])
                expected = case["expected"]
                if type(expected) is float:
                    self.assertTrue(math.isclose(actual, expected, abs_tol=1e-11, rel_tol=1e-11))
                else:
                    self.assertEqual(actual, expected)

    def test_references(self):
        self.assertEqual(references(op("mul", v("theta"), v("wetting.size"))),
                         {"theta", "wetting.size"})

    def test_unknown_operation(self):
        with self.assertRaises(ExpressionError):
            evaluate(op("import", c("os")), {})

    def test_unknown_extra_property(self):
        with self.assertRaises(ExpressionError):
            evaluate({"const": 1, "evil": True}, {})

    def test_unknown_parameter(self):
        with self.assertRaises(ExpressionError):
            evaluate(v("unknown"), {})

    def test_forbidden_parameter_name(self):
        with self.assertRaises(ExpressionError):
            evaluate(v("__proto__"), {"__proto__": 5})

    def test_rejects_string_as_number(self):
        with self.assertRaises(ExpressionError):
            evaluate(op("cos", c("theta")), {})

    def test_division_by_zero(self):
        with self.assertRaises(ExpressionError):
            evaluate(op("div", c(1), c(0)), {})

    def test_invalid_sqrt(self):
        with self.assertRaises(ExpressionError):
            evaluate(op("sqrt", c(-4)), {})

    def test_nonfinite_input(self):
        with self.assertRaises(ExpressionError):
            evaluate(c(float("nan")), {})

    def test_nonfinite_result(self):
        with self.assertRaises(ExpressionError):
            evaluate(op("pow", c(10.0), c(1000)), {})

    def test_bad_argument_count(self):
        with self.assertRaises(ExpressionError):
            evaluate(op("add", c(1)), {})

    def test_if_is_lazy(self):
        expression = op("if", c(False), op("div", c(1), c(0)), c(4))
        self.assertEqual(evaluate(expression, {}), 4)

    def test_tree_complexity_limit(self):
        expr = c(1)
        for _ in range(42):
            expr = op("neg", expr)
        with self.assertRaises(ExpressionError):
            evaluate(expr, {})

    def test_svg_path_arc_flags(self):
        expr = {"op": "path", "commands": [{"cmd": "A", "values": [c(4), c(4), c(0), c(2), c(1), c(5), c(5)]}]}
        with self.assertRaises(ExpressionError):
            evaluate(expr, {})

    def test_svg_path_command_restriction(self):
        expr = {"op": "path", "commands": [{"cmd": "javascript", "values": []}]}
        with self.assertRaises(ExpressionError):
            evaluate(expr, {})


if __name__ == "__main__":
    unittest.main()
