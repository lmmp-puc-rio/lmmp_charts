"""Tests for the shared configuration model behavior."""

import json
import tempfile
import unittest
from abc import ABC
from collections import UserDict
from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

from lmmp_charts.models import ConfigModel, Fluid, Rock, Wettability


class ConfigModelTests(unittest.TestCase):
    def test_base_is_abstract(self):
        self.assertTrue(issubclass(ConfigModel, ABC))
        with self.assertRaises(TypeError):
            ConfigModel()

    def test_unimplemented_validation_remains_abstract(self):
        class Incomplete(ConfigModel):
            pass

        with self.assertRaises(TypeError):
            Incomplete()

    def test_subclasses_are_dataclasses_and_inherit_methods(self):
        self.assertTrue(is_dataclass(Fluid))
        self.assertTrue(is_dataclass(Rock))
        self.assertIs(Fluid.from_dict.__func__, ConfigModel.from_dict.__func__)
        self.assertIs(Rock.to_dict, ConfigModel.to_dict)

    def test_accepts_other_mapping_types_without_modification(self):
        source = UserDict({"name": "CO2", "color": "#ff0000"})
        obj = Fluid.from_dict(source)
        self.assertEqual(obj.name, "CO2")
        self.assertEqual(source.data, {"name": "CO2", "color": "#ff0000"})

    def test_rejects_non_mapping_input(self):
        for value in (None, 0, "text", []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Fluid.from_dict(value)

    def test_missing_field_rejected(self):
        with self.assertRaises(TypeError):
            Fluid.from_dict({"name": "CO2"})

    def test_instance_is_immutable(self):
        obj = Rock(name="Bentheimer")
        with self.assertRaises(FrozenInstanceError):
            obj.name = "Berea"

    def test_from_json_file_is_inherited(self):
        self.assertIs(Fluid.from_json_file.__func__, ConfigModel.from_json_file.__func__)
        self.assertIs(Wettability.from_json_file.__func__, ConfigModel.from_json_file.__func__)

    def test_from_json_file_accepts_path_object_and_string(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "fluid.json"
            file_path.write_text('{"name": "Salmoura", "color": "#4472C4"}', encoding="utf-8")
            for path in (file_path, str(file_path)):
                with self.subTest(path_type=type(path).__name__):
                    fluid = Fluid.from_json_file(path)
                    self.assertEqual(fluid, Fluid("Salmoura", "#4472C4"))

    def test_from_json_file_nested_wettability_and_aliases(self):
        config = {
            "rock": {"name": "Bentheimer"},
            "fluids": {
                "wetting": {"name": "Salmoura", "color": "#4472C4"},
                "non_wetting": {"name": "CO2", "color": "#FF0000"},
            },
            "angles": {"theta": 45, "theta_a": 75, "theta_r": 25},
        }
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "interface.json"
            file_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
            model = Wettability.from_json_file(file_path)
            self.assertEqual(model, Wettability.from_dict(config))
            self.assertEqual(model.theta_advancing, 75)
            self.assertEqual(model.theta_receding, 25)
            self.assertEqual(model.wetting_fluid.name, "Salmoura")

    def test_from_json_file_nonexistent_file(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaises(FileNotFoundError):
                Rock.from_json_file(missing)

    def test_from_json_file_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "broken.json"
            file_path.write_text('{"name": ', encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                Rock.from_json_file(file_path)

    def test_from_json_file_invalid_json_root_delegated_to_from_dict(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "array.json"
            file_path.write_text('["Bentheimer"]', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dictionary-like"):
                Rock.from_json_file(file_path)

    def test_from_json_file_triggers_model_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "invalid_fluid.json"
            file_path.write_text('{"name": "", "color": "#FF0000"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                Fluid.from_json_file(file_path)



if __name__ == "__main__":
    unittest.main()
