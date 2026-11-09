"""Regression tests: this backend must preserve the approved v5 figure."""

from __future__ import annotations

import base64
import copy
import json
import unittest
from pathlib import Path

import numpy as np
import plotly.graph_objects as go

from lmmp_charts.rendering.plotly import InterfacialBuilder
from lmmp_charts.rendering.plotly.primitives import PlotlyPrimitives
from lmmp_charts.models import Wettability

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE.parent.parent / 'examples/interface_config.json').read_text(encoding='utf-8'))
GOLDEN = json.loads((HERE / 'fixtures/v5_plotly_reference.json').read_text(encoding='utf-8'))


def assert_v5_figure(testcase, actual: dict, expected: dict) -> None:
    """Compare every visual setting exactly and coordinates to numerical precision.

    Base64 typed arrays may differ by 1-2 ULPs with different NumPy/Python
    environments, without changing the displayed geometry.
    """
    testcase.assertEqual(actual["layout"], expected["layout"])
    testcase.assertEqual(len(actual["data"]), len(expected["data"]))
    for i, (trace, reference) in enumerate(zip(actual["data"], expected["data"])):
        testcase.assertEqual(set(trace), set(reference), f"trace {i} fields")
        for key in trace:
            if key in ("x", "y") and isinstance(trace[key], dict) and "bdata" in trace[key]:
                testcase.assertEqual(trace[key]["dtype"], reference[key]["dtype"])
                testcase.assertEqual(set(trace[key]), set(reference[key]))
                dtype = np.dtype(trace[key]["dtype"])
                actual_values = np.frombuffer(base64.b64decode(trace[key]["bdata"]), dtype=dtype)
                reference_values = np.frombuffer(base64.b64decode(reference[key]["bdata"]), dtype=dtype)
                np.testing.assert_allclose(actual_values, reference_values, rtol=0, atol=2e-15)
            else:
                testcase.assertEqual(trace[key], reference[key], f"trace {i} field {key}")


class PlotlyBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = copy.deepcopy(CONFIG)
        self.builder = InterfacialBuilder()
        self.model = Wettability.from_dict(self.config)

    def test_native_figure_matches_approved_v5_with_numerical_tolerance(self):
        figure = self.builder.build(self.model)
        self.assertIsInstance(figure, go.Figure)
        assert_v5_figure(self, json.loads(figure.to_json()), GOLDEN)

    def test_payload_is_js_consumable_native_plotly_spec(self):
        payload = self.builder.to_payload(self.model)
        self.assertEqual(set(payload), {"data", "layout", "config"})
        assert_v5_figure(self, payload, GOLDEN)
        self.assertEqual(payload["config"], {"displayModeBar": False, "responsive": True})
        self.assertEqual(json.loads(json.dumps(payload)), payload)

    def test_trace_count_and_annotation_labels(self):
        figure = self.builder.build(self.model)
        self.assertEqual(len(figure.data), 17)
        self.assertEqual(len(figure.layout.annotations), 10)
        texts = {ann.text for ann in figure.layout.annotations}
        self.assertTrue({"Salmoura", "CO2", "Bentheimer", "Interfaces",
                         "θ = 45°", "θₐ = 75°", "θᵣ = 25°"} <= texts)

    def test_preserves_approved_label_styles(self):
        figure = self.builder.build(self.model)
        labels = {ann.text: ann for ann in figure.layout.annotations}
        advancing = labels["θₐ = 75°"]
        receding = labels["θᵣ = 25°"]
        self.assertEqual((advancing.x, advancing.y, advancing.font.size,
                          advancing.font.color), (8.15, 3.15, 15, "white"))
        self.assertEqual((receding.x, receding.y, receding.font.size,
                          receding.font.color), (4.08, 3.17, 15, "white"))

    def test_tangent_and_hysteresis_rays_are_separate_colors(self):
        figure = self.builder.build(self.model)
        # Plotly curves are created in the exact v5 trace order.
        # Final three long rays in the triangular segment: white/white/black.
        rays = [trace for trace in figure.data if trace.line.dash == "dash"]
        self.assertEqual([r.line.color for r in rays], ["#151515", "white", "white", "#151515"])
        self.assertEqual([r.line.width for r in rays], [4.0, 4.2, 4.2, 4.0])

    def test_aliases_preserve_plot(self):
        self.config["angles"] = {"theta": 45, "theta_a": 75, "theta_r": 25}
        model = Wettability.from_dict(self.config)
        assert_v5_figure(self, json.loads(self.builder.build(model).to_json()), GOLDEN)

    def test_other_angles_change_geometry_without_moving_reference_labels(self):
        config = copy.deepcopy(self.config)
        config["angles"] = {"theta": 30, "theta_advancing": 70, "theta_receding": 10}
        result = self.builder.to_payload(Wettability.from_dict(config))
        self.assertEqual(result["layout"]["width"], 850)
        self.assertEqual(result["layout"]["height"], 1150)
        self.assertEqual(len(result["data"]), 17)
        texts = [ann["text"] for ann in result["layout"]["annotations"]]
        self.assertIn("θₐ = 70°", texts)
        self.assertIn("θᵣ = 10°", texts)

    def test_model_limits_are_stricter_in_chart(self):
        config = copy.deepcopy(self.config)
        config["angles"] = {"theta": 90, "theta_advancing": 120, "theta_receding": 20}
        model = Wettability.from_dict(config)
        with self.assertRaises(ValueError):
            self.builder.build(model)

    def test_wrong_input_type_rejected(self):
        with self.assertRaises(TypeError):
            self.builder.build(self.config)

    def test_escaping_of_user_controlled_text(self):
        self.config["rock"]["name"] = "Rock <script>"
        self.config["fluids"]["wetting"]["name"] = "H<sub>2</sub>O"
        fig = self.builder.build(Wettability.from_dict(self.config))
        texts = [ann.text for ann in fig.layout.annotations]
        self.assertIn("Rock &lt;script&gt;", texts)
        self.assertIn("H&lt;sub&gt;2&lt;/sub&gt;O", texts)
        self.assertNotIn("Rock <script>", texts)

    def test_no_mutation_of_config_or_model(self):
        before = copy.deepcopy(self.config)
        self.builder.to_payload(self.model)
        self.assertEqual(self.config, before)
        self.assertEqual(self.model.to_dict(), before)


class PlotlyPrimitiveTests(unittest.TestCase):
    def test_polygon_auto_closes_and_fillcolor(self):
        fig = go.Figure()
        PlotlyPrimitives.polygon(fig, [[0, 0], [1, 0], [1, 1]], "#AA00FF")
        trace = fig.data[0]
        np.testing.assert_array_equal(trace.x, [0, 1, 1, 0])
        np.testing.assert_array_equal(trace.y, [0, 0, 1, 0])
        self.assertEqual(trace.fillcolor, "#AA00FF")

    def test_line_has_correct_stroke(self):
        fig = go.Figure()
        PlotlyPrimitives.line(fig, [[0, 0], [1, 1]], color="white", width=3, dash="dash")
        self.assertEqual(fig.data[0].line.to_plotly_json(), {"color": "white", "dash": "dash", "width": 3})

    def test_sector_adds_polygon_and_arc(self):
        fig = go.Figure()
        PlotlyPrimitives.sector(fig, np.array([0., 0.]), 1.0, 0, 45, "#DDDDDD")
        self.assertEqual(len(fig.data), 2)
        self.assertEqual(fig.data[0].fillcolor, "#DDDDDD")


if __name__ == '__main__':
    unittest.main()
