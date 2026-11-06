"""Tests for rock display configuration."""

import unittest

from lmmp_charts.models import Rock


class RockTests(unittest.TestCase):
    def test_valid_rock_roundtrip(self):
        data = {"name": "Bentheimer"}
        self.assertEqual(Rock.from_dict(data).to_dict(), data)
        self.assertEqual(Rock.from_dict(Rock("Bentheimer").to_dict()), Rock("Bentheimer"))

    def test_invalid_names(self):
        for bad in ("", " ", None, 3):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                Rock(name=bad)

    def test_rock_model_does_not_require_project_specific_fields(self):
        self.assertEqual(list(Rock("Berea").to_dict()), ["name"])


if __name__ == "__main__":
    unittest.main()
