"""Tests of the consumer-facing InterfacialChart facade."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import plotly.graph_objects as go

from lmmp_charts import InterfacialChart, Wettability
from lmmp_charts.rendering.plotly import InterfacialBuilder

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "fixtures" / "interfacial_chart_config.json").read_text(encoding="utf-8"))


class InterfacialChartTests(unittest.TestCase):
    def setUp(self):
        self.input = copy.deepcopy(CONFIG)
        self.model = Wettability.from_dict(self.input)
        self.chart = InterfacialChart(self.model)

    def test_constructor_requires_model(self):
        for invalid in (self.input, None, "wrong", 42):
            with self.subTest(invalid=type(invalid).__name__), self.assertRaises(TypeError):
                InterfacialChart(invalid)

    def test_model_property_is_original(self):
        self.assertIs(self.chart.model, self.model)

    def test_generate_default_returns_plotly_payload(self):
        payload = self.chart.generate()
        self.assertIsInstance(payload, dict)
        self.assertEqual(set(payload), {"data", "layout", "config"})
        self.assertEqual(payload["config"], {"responsive": True, "displayModeBar": False})
        self.assertEqual(len(payload["data"]), 17)
        self.assertEqual(len(payload["layout"]["annotations"]), 10)

    def test_generate_matches_builder(self):
        self.assertEqual(self.chart.generate(), InterfacialBuilder().to_payload(self.model))

    def test_json_round_trip_includes_render_options(self):
        result = self.chart.to_json()
        self.assertIsInstance(result, str)
        self.assertEqual(json.loads(result), self.chart.generate())
        self.assertIn("θₐ = 75°", result)

    def test_figure_matches_payload_data_and_layout(self):
        figure = self.chart.to_figure()
        self.assertIsInstance(figure, go.Figure)
        expected = self.chart.generate()
        encoded = json.loads(figure.to_json())
        self.assertEqual(encoded["data"], expected["data"])
        self.assertEqual(encoded["layout"], expected["layout"])

    def test_show_delegates_to_plotly_figure(self):
        with patch.object(go.Figure, "show", autospec=True) as display:
            self.assertIsNone(self.chart.show())
            display.assert_called_once()
            self.assertIsInstance(display.call_args.args[0], go.Figure)

    def test_save_image_delegates_to_plotly_export(self):
        with patch.object(go.Figure, "write_image", autospec=True) as export:
            self.assertIsNone(self.chart.save_image(Path("figure.png"), scale=2))
            export.assert_called_once()
            self.assertEqual(export.call_args.args[1], "figure.png")
            self.assertEqual(export.call_args.kwargs["scale"], 2.0)

    def test_save_image_bad_arguments(self):
        for bad_path in (None, "", 42):
            with self.subTest(path=bad_path), self.assertRaises(ValueError):
                self.chart.save_image(bad_path)
        for bad_scale in (0, -1, True, float("nan"), float("inf"), "2"):
            with self.subTest(scale=bad_scale), self.assertRaises(ValueError):
                self.chart.save_image("image.png", scale=bad_scale)

    def test_no_changes_to_model_or_input(self):
        before = copy.deepcopy(self.input)
        self.chart.generate()
        self.chart.to_json()
        self.chart.to_figure()
        self.assertEqual(self.input, before)
        self.assertEqual(self.model.to_dict(), before)

    def test_chart_specific_angles_still_enforced(self):
        high_angle = copy.deepcopy(self.input)
        high_angle["angles"] = {"theta": 90, "theta_advancing": 120, "theta_receding": 20}
        model = Wettability.from_dict(high_angle)
        with self.assertRaises(ValueError):
            InterfacialChart(model).generate()


if __name__ == "__main__":
    unittest.main()
