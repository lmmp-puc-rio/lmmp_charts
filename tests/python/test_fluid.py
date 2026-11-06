"""Tests for fluid display configuration."""

import unittest

from lmmp_charts.models import Fluid


class FluidTests(unittest.TestCase):
    def test_valid_fluid_roundtrip(self):
        value = {"name": "Salmoura", "color": "#4472C4"}
        fluid = Fluid.from_dict(value)
        self.assertEqual(fluid.to_dict(), value)
        self.assertEqual(Fluid.from_dict(fluid.to_dict()), fluid)

    def test_fluid_does_not_include_wettability(self):
        self.assertEqual(set(Fluid("CO2", "red").to_dict()), {"name", "color"})

    def test_invalid_names(self):
        for bad in ("", "  ", None, 12):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Fluid(name=bad, color="#ff0000")

    def test_invalid_colors(self):
        for bad in ("", "  ", None, 12):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Fluid(name="CO2", color=bad)

    def test_arbitrary_color_strings_not_rejected_at_model_layer(self):
        # Plotly performs final color parsing; model checks type/non-emptiness.
        fluid = Fluid(name="CO2", color="rgba(255,0,0,0.5)")
        self.assertEqual(fluid.color, "rgba(255,0,0,0.5)")


if __name__ == "__main__":
    unittest.main()
