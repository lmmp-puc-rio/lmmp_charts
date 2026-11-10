"""Tests for approved layout and public chart/builder imports."""
from __future__ import annotations
import unittest
from pathlib import Path

from lmmp_charts import InterfacialChart
from lmmp_charts.rendering.plotly import InterfacialBuilder, InterfacialPlotlyBuilder

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "packages" / "python" / "src" / "lmmp_charts"
TS_SRC = ROOT / "packages" / "typescript" / "src"

class ApprovedArchitectureTests(unittest.TestCase):
    def test_builder_compatibility_alias(self):
        self.assertIs(InterfacialBuilder, InterfacialPlotlyBuilder)

    def test_public_chart_available(self):
        self.assertTrue(callable(InterfacialChart))

    def test_approved_python_layout(self):
        self.assertTrue((SRC / "charts" / "interfacial_chart.py").is_file())
        self.assertTrue((SRC / "rendering" / "plotly" / "interfacial_builder.py").is_file())
        self.assertFalse((SRC / "scene").exists())
        self.assertFalse((SRC / "backends").exists())

    def test_parametric_modules_are_grouped_by_format(self):
        self.assertTrue((SRC / "parametric" / "expressions" / "evaluator.py").is_file())
        self.assertTrue((SRC / "parametric" / "svg" / "document.py").is_file())
        self.assertFalse((SRC / "expressions").exists())
        self.assertTrue((TS_SRC / "parametric" / "expressions" / "evaluator.ts").is_file())
        self.assertTrue((TS_SRC / "parametric" / "svg" / "document.ts").is_file())
        self.assertFalse((TS_SRC / "expressions").exists())

    def test_approved_repository_layout(self):
        self.assertTrue((ROOT / "packages" / "typescript" / "package.json").is_file())
        self.assertTrue((ROOT / "docs" / "specifications" / "parametric_svg.md").is_file())
        self.assertTrue((ROOT / "AGENTS.md").is_file())
