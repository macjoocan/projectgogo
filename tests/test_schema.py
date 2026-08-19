"""점 경로 매핑 · 보드 추출."""
import unittest

from levelscope import schema


class GetPath(unittest.TestCase):
    def test_nested_dict(self):
        self.assertEqual(schema.get_path({"a": {"b": {"c": 7}}}, "a.b.c"), 7)

    def test_list_index(self):
        self.assertEqual(schema.get_path({"a": [10, 20]}, "a.1"), 20)

    def test_star_unique_list(self):
        self.assertEqual(schema.get_path({"Shooters": {"Shooters": [1, 2]}}, "Shooters.*"), [1, 2])

    def test_star_on_list_passes_through(self):
        self.assertEqual(schema.get_path({"a": [1, 2]}, "a.*"), [1, 2])

    def test_missing_returns_default(self):
        self.assertIsNone(schema.get_path({"a": 1}, "a.b.c"))
        self.assertEqual(schema.get_path({}, "x", default=0), 0)

    def test_out_of_range_index(self):
        self.assertIsNone(schema.get_path({"a": [1]}, "a.5"))


class ExtractRow(unittest.TestCase):
    def test_scalars_and_counts(self):
        data = {"difficulty": "Hard", "walls": {"Walls": [1, 2, 3]}, "empty": None}
        row = schema.extract_row(data, {"scalars": {"Difficulty": "difficulty"},
                                        "counts": {"walls": "walls.*", "gates": "gates.*"}})
        self.assertEqual(row, {"Difficulty": "Hard", "walls": 3, "gates": 0})


class ExtractBoard(unittest.TestCase):
    CFG = {"width": "width", "height": "height", "pixels": "pixels",
           "pixel": {"x": "x", "y": "y", "material": "material"}}

    def test_basic(self):
        data = {"width": 2, "height": 2,
                "pixels": [{"x": 0, "y": 0, "material": 3}, {"x": 1, "y": 1, "material": 4}]}
        b = schema.extract_board(data, self.CFG)
        self.assertEqual((b["w"], b["h"], b["pixel_count"]), (2, 2, 2))
        self.assertEqual(sorted(b["cells"]), [(0, 0, 3), (1, 1, 4)])

    def test_area_expands_cells(self):
        cfg = dict(self.CFG, pixel={"x": "x", "y": "y", "material": "material",
                                    "area_x": "areaX", "area_y": "areaY"})
        data = {"width": 4, "height": 4,
                "pixels": [{"x": 0, "y": 0, "material": 1, "areaX": 2, "areaY": 2}]}
        b = schema.extract_board(data, cfg)
        self.assertEqual(len(b["cells"]), 4)
        self.assertEqual(b["pixel_count"], 1)

    def test_overlays(self):
        cfg = dict(self.CFG, overlays={"walls": {"path": "walls", "points": "GridPoints",
                                                 "style": "wall"}})
        data = {"width": 2, "height": 2, "pixels": [],
                "walls": [{"GridPoints": [{"X": 0, "Y": 1}, {"x": 1, "y": 0}]}]}
        b = schema.extract_board(data, cfg)
        self.assertEqual(b["overlays"]["walls"]["points"], [(0, 1), (1, 0)])
        self.assertEqual(b["overlays"]["walls"]["style"], "wall")

    def test_no_config_or_no_size(self):
        self.assertIsNone(schema.extract_board({"width": 1}, None))
        self.assertIsNone(schema.extract_board({"width": 0, "height": 0}, self.CFG))


if __name__ == "__main__":
    unittest.main()
