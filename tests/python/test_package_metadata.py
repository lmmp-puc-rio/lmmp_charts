"""Structural checks for the proposed Python package configuration."""
from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

PROPOSAL_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROPOSAL_ROOT / "packages" / "python" / "pyproject.toml"
SRC = PROPOSAL_ROOT / "packages" / "python" / "src" / "lmmp_charts"


class PackageMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    def test_name_and_version(self):
        self.assertEqual(self.data["project"]["name"], "lmmp-charts")
        self.assertEqual(self.data["project"]["version"], "0.4.0")

    def test_minimum_python(self):
        self.assertEqual(self.data["project"]["requires-python"], ">=3.11")

    def test_dependencies(self):
        deps = self.data["project"]["dependencies"]
        self.assertEqual(len(deps), 2)
        self.assertTrue(any(dep.startswith("numpy") for dep in deps))
        self.assertTrue(any(dep.startswith("plotly") for dep in deps))
        self.assertIn("image", self.data["project"]["optional-dependencies"])

    def test_build_backend(self):
        self.assertEqual(self.data["build-system"]["build-backend"], "uv_build")

    def test_typing_marker(self):
        self.assertTrue((SRC / "py.typed").is_file())


if __name__ == "__main__":
    unittest.main()
