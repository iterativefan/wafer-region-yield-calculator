import json
import unittest
from pathlib import Path

from wafer_region_calculator import calculate


class WaferRegionCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.input_data = json.loads(
            Path(__file__).with_name("example_input.json").read_text(encoding="utf-8")
        )

    def test_reference_geometry_and_regions(self):
        result = calculate(self.input_data)
        self.assertEqual(result["geometry"]["full_dies"], 141)
        self.assertEqual(result["geometry"]["partial_dies"], 9)
        self.assertEqual(
            {k: v["full_dies"] for k, v in result["regions"].items()},
            {"A": 12, "B": 28, "C": 37, "D": 41, "E": 23},
        )
        self.assertEqual(
            {k: v["partial_dies"] for k, v in result["regions"].items()},
            {"A": 0, "B": 0, "C": 0, "D": 0, "E": 9},
        )
        self.assertEqual(result["offset_optimization"]["offset_x_mm"], -12.4995)
        self.assertEqual(result["offset_optimization"]["offset_y_mm"], -15.0411)


if __name__ == "__main__":
    unittest.main()
