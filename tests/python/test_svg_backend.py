"""Regression tests for the parametric Python SVG interfacial builder."""

from __future__ import annotations

import copy
import json
import math
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from lmmp_charts.geometry.triangle import TriangleGeometry
from lmmp_charts.models import Wettability
from lmmp_charts.parametric.svg import ParametricSvgDocument
from lmmp_charts.rendering.svg import InterfacialBuilder

HERE = Path(__file__).resolve().parent
CONFIG = json.loads(
    (HERE / "fixtures" / "interfacial_chart_config.json").read_text(encoding="utf-8")
)
SVG_NS = "{http://www.w3.org/2000/svg}"


class InterfacialSvgBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = copy.deepcopy(CONFIG)
        self.model = Wettability.from_dict(self.config)
        self.builder = InterfacialBuilder()
        self.document = self.builder.build(self.model)
        self.root = ET.fromstring(self.document.svg)
        self.elements = {
            element.attrib["id"]: element
            for element in self.root.iter()
            if "id" in element.attrib
        }

    def _patches(self, **overrides):
        return {
            (patch["target"], patch["attribute"]): patch["value"]
            for patch in self.document.evaluate_bindings(overrides)
        }

    def test_builds_complete_validated_contract_document(self):
        self.assertIsInstance(self.document, ParametricSvgDocument)
        self.assertEqual(self.document.to_dict()["format"], "lmmp-parametric-svg")
        self.assertEqual(self.document.to_dict()["version"], "1.0.0")
        self.assertEqual(self.root.attrib["width"], "850")
        self.assertEqual(self.root.attrib["height"], "1150")
        self.assertEqual(len(self.document.bindings), 25)
        self.assertIn("drawing", self.elements)
        self.assertIn("title-label", self.elements)

    def test_every_binding_targets_an_existing_matching_initial_attribute(self):
        ids = [
            element.attrib["id"]
            for element in self.root.iter()
            if "id" in element.attrib
        ]
        self.assertEqual(len(ids), len(set(ids)))
        for patch in self.document.evaluate_bindings():
            with self.subTest(target=patch["target"], attribute=patch["attribute"]):
                element = self.elements[patch["target"]]
                if patch["attribute"] == "textContent":
                    self.assertEqual(element.text, patch["value"])
                else:
                    self.assertEqual(element.attrib[patch["attribute"]], patch["value"])

    def test_angles_colors_and_labels_update_through_contract_bindings(self):
        patches = self._patches(
            theta=50,
            theta_advancing=80,
            theta_receding=20,
            **{
                "wetting.name": "Brine",
                "wetting.color": "#123456",
                "non_wetting.name": "Gas",
                "non_wetting.color": "#654321",
                "rock.name": "Sandstone",
            },
        )
        self.assertEqual(patches[("theta-label", "textContent")], "θ = 50°")
        self.assertEqual(patches[("receding-label", "textContent")], "θᵣ = 20°")
        self.assertEqual(patches[("advancing-label", "textContent")], "θₐ = 80°")
        self.assertEqual(patches[("rectangle-wetting-label", "textContent")], "Brine")
        self.assertEqual(patches[("triangle-non-wetting-label", "textContent")], "Gas")
        self.assertEqual(patches[("triangle-rock-label", "textContent")], "Sandstone")
        self.assertEqual(patches[("rectangle-wetting-region", "fill")], "#123456")
        self.assertEqual(patches[("triangle-non-wetting-region", "fill")], "#654321")
        self.assertNotEqual(patches[("triangle-meniscus", "d")],
                            self._patches()[("triangle-meniscus", "d")])

    def test_meniscus_svg_arc_matches_shared_geometry_across_curvature_limit(self):
        path_pattern = re.compile(
            r"^M (-?[\d.]+) (-?[\d.]+) A ([\d.]+) ([\d.]+) 0 0 ([01]) "
            r"(-?[\d.]+) (-?[\d.]+)$"
        )
        for theta in (15, 45, 59.9, 60, 60.1, 75, 89):
            advancing = min(theta + 5, 89.9)
            receding = max(theta - 5, 0)
            path = self._patches(
                theta=theta,
                theta_advancing=advancing,
                theta_receding=receding,
            )[("triangle-meniscus", "d")]
            geometry = TriangleGeometry().calculate(theta, advancing, receding)
            if math.isclose(theta, 60, abs_tol=1e-8):
                match = re.fullmatch(
                    r"M (-?[\d.]+) (-?[\d.]+) L (-?[\d.]+) (-?[\d.]+)", path
                )
                self.assertIsNotNone(match)
                assert match is not None
                coords = [float(value) for value in match.groups()]
                self.assertAlmostEqual(coords[0], geometry.lower_contact[0], places=6)
                self.assertAlmostEqual(coords[1], geometry.lower_contact[1], places=6)
                self.assertAlmostEqual(coords[2], geometry.inclined_contact[0], places=6)
                self.assertAlmostEqual(coords[3], geometry.inclined_contact[1], places=6)
                continue

            match = path_pattern.fullmatch(path)
            self.assertIsNotNone(match, path)
            assert match is not None
            start_x, start_y, radius_x, radius_y, sweep, end_x, end_y = (
                float(value) for value in match.groups()
            )
            self.assertAlmostEqual(start_x, geometry.lower_contact[0], places=6)
            self.assertAlmostEqual(start_y, geometry.lower_contact[1], places=6)
            self.assertAlmostEqual(end_x, geometry.inclined_contact[0], places=6)
            self.assertAlmostEqual(end_y, geometry.inclined_contact[1], places=6)
            self.assertAlmostEqual(radius_x, radius_y, places=6)
            expected_radius = (
                0.62 * 9.40 * math.sin(math.radians(30))
                / abs(math.cos(math.radians(theta + 30)))
            )
            self.assertAlmostEqual(radius_x, expected_radius, places=5)
            self.assertEqual(int(sweep), 0 if theta < 60 else 1)

    def test_flat_interface_uses_shared_geometry_and_dynamic_tangent(self):
        patches = self._patches(theta=30)
        match = re.fullmatch(
            r"M (-?[\d.]+) (-?[\d.]+) C (-?[\d.]+) (-?[\d.]+) "
            r"(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)",
            patches[("rectangle-interface", "d")],
        )
        self.assertIsNotNone(match)
        assert match is not None
        coords = [float(value) for value in match.groups()]
        expected = (6.15, 11.0)
        self.assertAlmostEqual(coords[0], expected[0], places=6)
        self.assertAlmostEqual(coords[1], expected[1], places=6)
        self.assertAlmostEqual(coords[2], expected[0] + 2.10 * math.cos(math.radians(30)), places=6)
        self.assertAlmostEqual(coords[3], expected[1] + 2.10 * math.sin(math.radians(30)), places=6)
        tangent = patches[("rectangle-tangent", "d")]
        self.assertIn("L 8.488269 12.35", tangent)

    def test_invalid_angle_overrides_are_rejected_atomically(self):
        for overrides in (
            {"theta": 0},
            {"theta": 80},
            {"theta_receding": 50},
            {"theta_advancing": 45},
            {"theta_advancing": 90},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.document.evaluate_bindings(overrides)

    def test_chart_specific_angle_limit_is_enforced(self):
        config = copy.deepcopy(self.config)
        config["angles"]["theta_advancing"] = 90
        model = Wettability.from_dict(config)
        with self.assertRaises(ValueError):
            self.builder.build(model)

    def test_build_does_not_mutate_configuration_or_model(self):
        before = copy.deepcopy(self.config)
        self.builder.build(self.model)
        self.assertEqual(self.config, before)
        self.assertEqual(self.model.to_dict(), before)

    def test_user_text_and_color_attributes_are_xml_escaped(self):
        config = copy.deepcopy(self.config)
        config["rock"]["name"] = "Rock <script>&"
        config["fluids"]["wetting"]["name"] = 'Brine "wet"'
        config["fluids"]["wetting"]["color"] = '#123456" onload="bad'
        document = self.builder.build(Wettability.from_dict(config))
        root = ET.fromstring(document.svg)
        elements = {item.attrib.get("id"): item for item in root.iter()}
        self.assertEqual(elements["rectangle-rock-label"].text, "Rock <script>&")
        self.assertEqual(elements["rectangle-wetting-label"].text, 'Brine "wet"')
        self.assertEqual(elements["rectangle-wetting-region"].attrib["fill"],
                         '#123456" onload="bad')
        self.assertNotIn('" onload="bad"', document.svg)

    def test_wrong_input_type_rejected(self):
        with self.assertRaises(TypeError):
            self.builder.build(self.config)


if __name__ == "__main__":
    unittest.main()
