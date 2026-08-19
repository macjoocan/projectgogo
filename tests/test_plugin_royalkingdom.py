"""royalkingdom 플러그인 — 보드 3층 구조.

게임 구조상 판은 바텀(타일형 기믹·미션) / 노멀(상자류) / 커버(맨 위, 아래를 다 덮음)
세 층이다. 셀 테이블 슬롯이 층을 가른다 — f3 얼음·f9 테두리·f11 모자이크가 바텀,
f5 담쟁이·f7 사슬이 커버, `f2.f0` 셀 벡터가 노멀이다.
"""
import unittest

from levelscope.plugins import royalkingdom as rk

ICE, IVY, CHAIN, BORDER, MOSAIC = 32, 34, 120, 139, 183
BOX2, SET1 = 22, 14


def doc(cells, per, w=2, h=2, moves=30):
    """플러그인이 받는 모양의 최소 레벨 문서."""
    return {"f0": "0001v01_E", "f1": moves,
            "f2": {"f0": {"of": "i32", "n": len(cells), "items": list(cells)},
                   "f1": {"of": "table", "n": len(per), "items": list(per)},
                   "f2": w, "f3": h}}


class Layers(unittest.TestCase):
    def test_slots_split_into_bottom_and_cover(self):
        d = doc([SET1] * 4, [{"f3": ICE}, {"f5": IVY}, {"f9": BORDER}, {"f7": CHAIN}])
        lay = rk.layer_cells(d)
        self.assertEqual(lay["bottom"], {0: [ICE], 2: [BORDER]})
        self.assertEqual(lay["cover"], {1: [IVY], 3: [CHAIN]})

    def test_multiple_gimmicks_on_one_cell_are_all_kept(self):
        """예전엔 칸마다 하나만 집고 나머지를 버렸다 (얼음+담쟁이 663칸)."""
        d = doc([SET1] * 4, [{"f3": ICE, "f5": IVY}, {}, {}, {}])
        lay = rk.layer_cells(d)
        self.assertEqual(lay["bottom"][0], [ICE])
        self.assertEqual(lay["cover"][0], [IVY])

    def test_unknown_slot_goes_to_cover_not_dropped(self):
        """모르는 슬롯도 보이게 올린다 — "없다"와 "못 읽었다"는 다르다."""
        d = doc([SET1] * 4, [{"f13": MOSAIC}, {}, {}, {}])
        self.assertEqual(rk.layer_cells(d)["cover"], {0: [MOSAIC]})

    def test_small_ints_are_parameters_not_gimmicks(self):
        """f0·f6 등에 든 1~5 는 색 파라미터라 기믹이 아니다."""
        d = doc([SET1] * 4, [{"f0": 1, "f6": 3}, {}, {}, {}])
        lay = rk.layer_cells(d)
        self.assertEqual((lay["bottom"], lay["cover"]), ({}, {}))

    def test_no_cell_table(self):
        d = {"f2": {"f0": {"items": [SET1]}, "f2": 1, "f3": 1}}
        self.assertEqual(rk.layer_cells(d), {"bottom": {}, "cover": {}})


class ViewerStack(unittest.TestCase):
    def layers_at(self, v, x, y):
        tl = v["tl"]
        return {tl[i]: tl[i + 3] for i in range(0, len(tl), 5)
                if tl[i + 1] == x and tl[i + 2] == y}

    def test_draw_order_is_bottom_normal_cover(self):
        d = doc([BOX2] * 4, [{"f3": ICE, "f5": IVY}, {}, {}, {}])
        got = self.layers_at(rk.viewer_level(d), 0, 0)
        self.assertEqual(got, {0: ICE, 1: BOX2, 2: IVY})

    def test_normal_sits_at_layer_zero_without_bottom(self):
        d = doc([BOX2] * 4, [{"f5": IVY}, {}, {}, {}])
        self.assertEqual(self.layers_at(rk.viewer_level(d), 0, 0), {0: BOX2, 1: IVY})

    def test_same_layer_collision_stacks_instead_of_dropping(self):
        """담쟁이와 사슬이 한 칸에 같이 오면(40칸) 층을 더 만든다."""
        d = doc([BOX2] * 4, [{"f5": IVY, "f7": CHAIN}, {}, {}, {}])
        got = self.layers_at(rk.viewer_level(d), 0, 0)
        self.assertEqual(sorted(got.values()), sorted([BOX2, IVY, CHAIN]))
        self.assertEqual(got[0], BOX2)

    def test_chip_groups_name_both_layers(self):
        d = doc([BOX2] * 4, [{"f3": ICE}, {"f5": IVY}, {}, {}])
        labels = [g[0] for g in rk.viewer_level(d)["sq"]]
        self.assertTrue(any(x.startswith("커버") for x in labels), labels)
        self.assertTrue(any(x.startswith("바텀") for x in labels), labels)


class Extras(unittest.TestCase):
    def test_bottom_and_cover_counted_separately(self):
        d = doc([BOX2] * 4, [{"f3": ICE, "f5": IVY}, {"f3": ICE}, {}, {}])
        e = rk.level_extras(d)
        self.assertEqual((e["bottom_cells"], e["bottom_kinds"]), (2, 1))
        self.assertEqual((e["cover_cells"], e["cover_kinds"]), (1, 1))
        self.assertEqual(e["bottoms"], "Ice2")
        self.assertEqual(e["covers"], "Ivy1")

    def test_gimmick_cells_counts_every_layer(self):
        """한 칸에 둘이면 둘 다 센다 — 예전엔 칸 수만 세어 하나를 놓쳤다."""
        d = doc([SET1] * 4, [{"f3": ICE, "f5": IVY}, {}, {}, {}])
        self.assertEqual(rk.level_extras(d)["gimmick_cells"], 2)

    def test_moves_and_size_pass_through(self):
        e = rk.level_extras(doc([SET1] * 4, [{}] * 4, moves=31))
        self.assertEqual((e["moves"], e["grid_w"], e["grid_h"]), (31, 2, 2))


if __name__ == "__main__":
    unittest.main()
