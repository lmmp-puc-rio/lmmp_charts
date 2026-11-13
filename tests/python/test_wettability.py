"""Tests of wettability and the fluid-rock-fluid configuration contract."""

from __future__ import annotations

import json
import math
import unittest
from dataclasses import FrozenInstanceError

from lmmp_charts.models import ConfigModel, Fluid, Rock, Wettability


class WettabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "rock": {"name": "Bentheimer"},
            "fluids": {
                "wetting": {"name": "Salmoura", "color": "#4472C4"},
                "non_wetting": {"name": "CO2", "color": "#FF0000"},
            },
            "angles": {
                "theta": 45,
                "theta_advancing": 75,
                "theta_receding": 25,
            },
        }

    def test_inherits_shared_from_dict(self) -> None:
        self.assertIs(Wettability.from_dict.__func__, ConfigModel.from_dict.__func__)

    def test_nested_json_round_trip(self) -> None:
        model = Wettability.from_dict(self.config)
        self.assertIsInstance(model.rock, Rock)
        self.assertIsInstance(model.wetting_fluid, Fluid)
        self.assertIsInstance(model.non_wetting_fluid, Fluid)
        self.assertEqual(model.to_dict(), self.config)
        self.assertEqual(Wettability.from_dict(model.to_dict()), model)
        self.assertEqual(json.loads(json.dumps(model.to_dict())), self.config)

    def test_direct_constructor(self) -> None:
        obj = Wettability(
            rock=Rock("Bentheimer"),
            wetting_fluid=Fluid("Salmoura", "#4472C4"),
            non_wetting_fluid=Fluid("CO2", "#FF0000"),
            theta=45,
            theta_advancing=75,
            theta_receding=25,
        )
        self.assertEqual(obj.to_dict(), self.config)

    def test_constructor_shaped_dict(self) -> None:
        flat = {
            "rock": {"name": "Bentheimer"},
            "wetting_fluid": {"name": "Salmoura", "color": "#4472C4"},
            "non_wetting_fluid": {"name": "CO2", "color": "#FF0000"},
            **self.config["angles"],
        }
        self.assertEqual(Wettability.from_dict(flat).to_dict(), self.config)

    def test_accepts_typed_objects_in_constructor_shaped_mapping(self) -> None:
        obj = Wettability.from_dict({
            "rock": Rock("Bentheimer"),
            "wetting_fluid": Fluid("Salmoura", "#4472C4"),
            "non_wetting_fluid": Fluid("CO2", "#FF0000"),
            "theta": 45,
            "theta_a": 75,
            "theta_r": 25,
        })
        self.assertEqual(obj.to_dict(), self.config)

    def test_aliases_nested_and_flat(self) -> None:
        self.config["angles"] = {"theta": 45, "theta_a": 75, "theta_r": 25}
        self.assertEqual(Wettability.from_dict(self.config).to_dict()["angles"], {
            "theta": 45, "theta_advancing": 75, "theta_receding": 25
        })

    def test_duplicated_equivalent_aliases(self) -> None:
        self.config["angles"].update({"theta_a": 75, "theta_r": 25})
        obj = Wettability.from_dict(self.config)
        self.assertEqual(len(obj.to_dict()["angles"]), 3)
        self.assertIn("theta_a", self.config["angles"])

    def test_conflicting_aliases(self) -> None:
        for alias, value in (("theta_a", 70), ("theta_r", 20)):
            with self.subTest(alias=alias):
                self.config["angles"][alias] = value
                with self.assertRaisesRegex(ValueError, "Conflicting angle"):
                    Wettability.from_dict(self.config)
                del self.config["angles"][alias]

    def test_from_dict_never_mutates_input(self) -> None:
        self.config["angles"] = {"theta": 45, "theta_a": 75, "theta_r": 25}
        before = json.dumps(self.config, sort_keys=True)
        Wettability.from_dict(self.config)
        self.assertEqual(json.dumps(self.config, sort_keys=True), before)

    def test_wrong_nested_shape(self) -> None:
        cases = (
            {"rock": {}, "fluids": {}, "angles": self.config["angles"]},
            {"rock": {}, "fluids": self.config["fluids"], "angles": []},
            {"rock": self.config["rock"], "fluids": self.config["fluids"]},
            dict(self.config, extra=True),
        )
        for item in cases:
            with self.subTest(item=item), self.assertRaises((ValueError, TypeError)):
                Wettability.from_dict(item)

    def test_wrong_types_for_nested_models(self) -> None:
        for key, value in (("rock", None), ("wetting_fluid", 42), ("non_wetting_fluid", [])):
            with self.subTest(key=key):
                flat = {
                    "rock": Rock("Bentheimer"),
                    "wetting_fluid": Fluid("Salmoura", "blue"),
                    "non_wetting_fluid": Fluid("CO2", "red"),
                    **self.config["angles"],
                }
                flat[key] = value
                with self.assertRaises(ValueError):
                    Wettability.from_dict(flat)

    def test_invalid_fluid_nested_data(self) -> None:
        self.config["fluids"]["wetting"]["name"] = " "
        with self.assertRaises(ValueError):
            Wettability.from_dict(self.config)

    def test_invalid_numeric_values(self) -> None:
        for bad in (True, False, None, "45", float("nan"), math.inf, -math.inf):
            for field in self.config["angles"]:
                with self.subTest(field=field, value=bad):
                    self.config["angles"][field] = bad
                    with self.assertRaises(ValueError):
                        Wettability.from_dict(self.config)
                    self.config["angles"][field] = {"theta":45,"theta_advancing":75,"theta_receding":25}[field]

    def test_invalid_angle_order(self) -> None:
        for values in ((45, 45, 25), (45, 75, 45), (45, 25, 10), (0, 75, 0), (45, 181, 25)):
            with self.subTest(values=values):
                self.config["angles"] = dict(zip(("theta", "theta_advancing", "theta_receding"), values))
                with self.assertRaises(ValueError):
                    Wettability.from_dict(self.config)

    def test_lower_receding_zero_is_allowed(self) -> None:
        self.config["angles"]["theta_receding"] = 0
        self.assertEqual(Wettability.from_dict(self.config).theta_receding, 0)

    def test_generic_model_allows_angles_above_90(self) -> None:
        self.config["angles"] = {"theta": 100, "theta_advancing": 180, "theta_receding": 40}
        self.assertEqual(Wettability.from_dict(self.config).theta_advancing, 180)

    def test_missing_angle_rejected(self) -> None:
        del self.config["angles"]["theta_receding"]
        with self.assertRaises(TypeError):
            Wettability.from_dict(self.config)

    def test_immutable_instance_and_nested_models(self) -> None:
        instance = Wettability.from_dict(self.config)
        with self.assertRaises(FrozenInstanceError):
            instance.theta = 40
        with self.assertRaises(FrozenInstanceError):
            instance.rock.name = "Berea"
        with self.assertRaises(FrozenInstanceError):
            instance.wetting_fluid.name = "Water"

    def test_to_dict_returns_independent_structure(self) -> None:
        instance = Wettability.from_dict(self.config)
        output = instance.to_dict()
        output["rock"]["name"] = "Berea"
        output["angles"]["theta"] = 40
        self.assertEqual(instance.rock.name, "Bentheimer")
        self.assertEqual(instance.theta, 45)


if __name__ == "__main__":
    unittest.main()
