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


class InferFields(unittest.TestCase):
    """fields: auto — 장르마다 필드 경로를 손으로 적지 않게 표본에서 컬럼을 뽑는다."""

    def test_scalars_and_list_counts(self):
        f, dropped, conflicts = schema.infer_fields([{"hp": 100, "name": "A", "alive": True,
                                           "skills": ["a", "b"]}])
        self.assertEqual(set(f["scalars"]), {"hp", "name", "alive"})
        self.assertEqual(set(f["counts"]), {"skills"})
        self.assertEqual(dropped, [])

    def test_nested_dict_becomes_dotted_path(self):
        f, _d, _c = schema.infer_fields([{"growth": {"atk": 3.5, "inner": {"deep": 1}}}])
        self.assertIn("growth.atk", f["scalars"])
        self.assertIn("growth.inner.deep", f["scalars"])

    def test_list_interior_is_not_expanded(self):
        """레벨마다 원소 수가 달라 컬럼이 폭발한다 — 길이만 잡는다."""
        f, _d, _c = schema.infer_fields([{"cells": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}])
        self.assertEqual(f["counts"], {"cells": "cells"})
        self.assertEqual(f["scalars"], {})

    def test_long_strings_are_skipped(self):
        f, _d, _c = schema.infer_fields([{"blob": "x" * 500, "short": "ok"}])
        self.assertEqual(set(f["scalars"]), {"short"})

    def test_depth_limit(self):
        deep = {"a": {"b": {"c": {"d": {"e": 1}}}}}
        f, _d, _c = schema.infer_fields([deep], max_depth=2)
        self.assertEqual(f["scalars"], {})

    def test_cap_reports_what_it_dropped(self):
        """상한에 걸린 걸 조용히 빼면 "그 필드는 없었다"로 읽힌다."""
        f, dropped, conflicts = schema.infer_fields([{f"k{i}": i for i in range(10)}], max_cols=4)
        self.assertEqual(len(f["scalars"]) + len(f["counts"]), 4)
        self.assertEqual(len(dropped), 6)

    def test_more_common_paths_come_first(self):
        samples = [{"always": 1}, {"always": 2}, {"always": 3, "rare": 9}]
        f, dropped, conflicts = schema.infer_fields(samples, max_cols=1)
        self.assertEqual(list(f["scalars"]), ["always"])
        self.assertEqual(dropped, ["rare"])

    def test_no_dict_samples_yield_nothing(self):
        f, _d, _c = schema.infer_fields([[1, 2, 3], "text", 5])
        self.assertEqual(f, {"scalars": {}, "counts": {}})

    def test_type_conflicting_path_is_excluded(self):
        """같은 경로가 어떤 레코드에선 스칼라, 다른 레코드에선 dict 인 경우.

        FlatBuffers 게임에서 실제로 나온다(빈 벡터가 dict 으로 온다). 컬럼으로 잡으면
        dict 이 셀에 들어가 xlsx 생성이 통째로 실패한다.
        """
        samples = [{"slot": 7}, {"slot": {"of": "empty", "n": 0, "items": []}}]
        f, _dropped, conflicts = schema.infer_fields(samples)
        self.assertNotIn("slot", f["scalars"])
        self.assertNotIn("slot", f["counts"])
        self.assertEqual(conflicts, ["slot"])

    def test_scalar_and_list_mix_is_excluded(self):
        f, _dropped, conflicts = schema.infer_fields([{"x": 1}, {"x": [1, 2]}])
        self.assertEqual(f, {"scalars": {}, "counts": {}})
        self.assertEqual(conflicts, ["x"])

    def test_intermediate_dict_is_not_a_column(self):
        """중간 노드는 컬럼이 아니다 — 펼친 자식이 컬럼이 된다."""
        f, _dropped, conflicts = schema.infer_fields([{"growth": {"atk": 1}}])
        self.assertEqual(list(f["scalars"]), ["growth.atk"])
        self.assertEqual(conflicts, [])

    def test_is_auto_forms(self):
        self.assertTrue(schema.is_auto("auto"))
        self.assertTrue(schema.is_auto(" AUTO "))
        self.assertTrue(schema.is_auto({"auto": True}))
        self.assertFalse(schema.is_auto({"scalars": {"a": "a"}}))
        self.assertFalse(schema.is_auto(None))

    def test_extract_row_survives_unresolved_auto(self):
        """'auto' 가 지도로 바뀌기 전에 불려도 죽지 않는다."""
        self.assertEqual(schema.extract_row({"a": 1}, "auto"), {})
