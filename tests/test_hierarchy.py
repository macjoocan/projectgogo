"""hierarchy — 좌표 정리, JSON 규격 보장, 씬/프리팹 분류, 트리 복원."""
import io
import json
import math
import unittest
import zipfile

from levelscope import hierarchy, typetree, unity

from .helpers import FakeEnv, FakeFile, FakeObj, go, pptr, rect


class Vectors(unittest.TestCase):
    def test_packs_named_axes(self):
        self.assertEqual(hierarchy._v({"x": 1.0, "y": 2.5}, "x", "y"), [1, 2.5])

    def test_missing_returns_none(self):
        self.assertIsNone(hierarchy._v({}, "x", "y"))
        self.assertIsNone(hierarchy._v(None, "x", "y"))

    def test_rounds_to_four_places(self):
        self.assertEqual(hierarchy._v({"x": 1.234567}, "x"), [1.2346])

    def test_nan_becomes_none_not_crash(self):
        """실제 RectTransform에 NaN이 들어 있다 — int(NaN)은 ValueError를 낸다."""
        self.assertEqual(hierarchy._v({"x": float("nan"), "y": 3.0}, "x", "y"), [None, 3])

    def test_inf(self):
        self.assertEqual(hierarchy._round(float("inf")), None)


class DumpValidJson(unittest.TestCase):
    def test_plain_document(self):
        self.assertEqual(json.loads(hierarchy._dump({"a": [1, "안녕"]})), {"a": [1, "안녕"]})

    def test_nan_is_sanitized_to_valid_json(self):
        """json 기본값은 NaN 리터럴을 뱉는데 그건 JSON이 아니라 뷰어가 파싱에 실패한다."""
        blob = hierarchy._dump({"v": float("nan"), "w": [float("inf"), 2.0]})
        self.assertNotIn(b"NaN", blob)
        self.assertEqual(json.loads(blob), {"v": None, "w": [None, 2]})

    def test_deeply_nested_survives(self):
        deep = cur = {}
        for _ in range(80):
            cur["n"] = {"v": float("nan")}
            cur = cur["n"]
        json.loads(hierarchy._dump(deep))          # 예외 없이 파싱되면 통과


class Classify(unittest.TestCase):
    def test_scene_detected_by_render_settings(self):
        f = FakeFile("level0")
        env = FakeEnv([FakeObj("RenderSettings", 1, f), rect(2, f, 3), go(3, f, "Root")])
        self.assertEqual(hierarchy._classify(unity.ObjectIndex(env)), {"level0": "scene"})

    def test_prefab_store_without_scene_markers(self):
        f = FakeFile("resources.assets")
        env = FakeEnv([rect(2, f, 3), go(3, f, "Panel")])
        self.assertEqual(hierarchy._classify(unity.ObjectIndex(env)),
                         {"resources.assets": "prefab"})

    def test_files_without_transforms_are_skipped(self):
        f = FakeFile("globalgamemanagers.assets")
        env = FakeEnv([FakeObj("MonoScript", 1, f), FakeObj("Material", 2, f)])
        self.assertEqual(hierarchy._classify(unity.ObjectIndex(env)), {})


def _panel_env():
    """Panel > (Icon, Label) 두 단계 트리 + Image/Text 컴포넌트."""
    f = FakeFile("resources.assets")
    img = FakeObj("MonoBehaviour", 10, f, tree={"m_Sprite": pptr(90), "m_Color": {"r": 1.0}},
                  attrs={"m_Name": ""})
    txt = FakeObj("MonoBehaviour", 11, f, tree={"m_Text": "확인"}, attrs={"m_Name": ""})
    sprite = FakeObj("Sprite", 90, f, attrs={"m_Name": "btn-bg"})
    objs = [
        go(1, f, "Panel", components=(2,)), rect(2, f, 1, children=(4, 6), size=(750.0, 1160.0)),
        go(3, f, "Icon", components=(4, 10)), rect(4, f, 3, father=2, size=(80.0, 80.0)),
        go(5, f, "Label", components=(6, 11)), rect(6, f, 5, father=2, size=(200.0, 40.0)),
        img, txt, sprite,
    ]
    return f, unity.ObjectIndex(FakeEnv(objs))


class _StubMono:
    """typetree 없이도 트리 로직만 보게 하는 리더 — MonoBehaviour를 그냥 읽는다."""

    def __init__(self, classes):
        self.classes = classes
        self.ok = self.failed = self.no_script = 0
        self.fail_classes = {}

    def read(self, obj):
        cls = self.classes.get(obj.path_id)
        if cls is None:
            self.failed += 1
            return None, None
        self.ok += 1
        return cls, obj.read_typetree()

    def summary(self):
        return "stub"


class BuildTree(unittest.TestCase):
    def setUp(self):
        self.f, self.index = _panel_env()
        self.mono = _StubMono({10: "Image", 11: "Text"})
        self.b = hierarchy._Builder(self.index, "resources.assets", self.mono)

    def test_finds_only_parentless_roots(self):
        self.assertEqual([n for n, _ in self.b.roots()], ["Panel"])

    def test_tree_shape_and_names(self):
        node = self.b.build(self.b.roots()[0][1])
        self.assertEqual(node["name"], "Panel")
        self.assertEqual([c["name"] for c in node["children"]], ["Icon", "Label"])

    def test_transform_geometry_captured(self):
        node = self.b.build(self.b.roots()[0][1])
        self.assertEqual(node["transform"]["kind"], "RectTransform")
        self.assertEqual(node["transform"]["sizeDelta"], [750, 1160])
        self.assertEqual(node["children"][0]["transform"]["sizeDelta"], [80, 80])

    def test_transform_not_duplicated_in_components(self):
        node = self.b.build(self.b.roots()[0][1])
        types_ = [c["type"] for c in node["children"][0].get("components", [])]
        self.assertNotIn("RectTransform", types_)

    def test_component_fields_resolve_pptr_to_name(self):
        node = self.b.build(self.b.roots()[0][1])
        icon = node["children"][0]
        image = next(c for c in icon["components"] if c.get("script") == "Image")
        self.assertEqual(image["fields"]["m_Sprite"], "btn-bg (Sprite)")

    def test_text_value_present(self):
        node = self.b.build(self.b.roots()[0][1])
        label = node["children"][1]
        text = next(c for c in label["components"] if c.get("script") == "Text")
        self.assertEqual(text["fields"]["m_Text"], "확인")

    def test_unreadable_component_marked_null_not_dropped(self):
        """못 읽은 컴포넌트를 빼버리면 '없다'와 '못 읽었다'가 구별되지 않는다."""
        b = hierarchy._Builder(self.index, "resources.assets", _StubMono({}))
        node = b.build(b.roots()[0][1])
        comps = node["children"][0]["components"]
        mb = next(c for c in comps if c["type"] == "MonoBehaviour")
        self.assertIsNone(mb["fields"])
        self.assertEqual(mb["script"], "(불명)")

    def test_fields_can_be_switched_off(self):
        b = hierarchy._Builder(self.index, "resources.assets", self.mono, want_fields=False)
        node = b.build(b.roots()[0][1])
        mb = next(c for c in node["children"][0]["components"] if c["type"] == "MonoBehaviour")
        self.assertNotIn("fields", mb)

    def test_max_nodes_truncates_and_flags(self):
        b = hierarchy._Builder(self.index, "resources.assets", self.mono, max_nodes=2)
        b.build(b.roots()[0][1])
        self.assertTrue(b.truncated)
        self.assertLessEqual(b.nodes, 2)

    def test_noise_fields_pruned(self):
        node = self.b.build(self.b.roots()[0][1])
        image = next(c for c in node["children"][0]["components"] if c.get("script") == "Image")
        self.assertNotIn("m_GameObject", image["fields"])
        self.assertNotIn("m_Script", image["fields"])

    def test_node_count_matches_transforms(self):
        b = hierarchy._Builder(self.index, "resources.assets", self.mono)
        b.build(b.roots()[0][1])
        self.assertEqual(b.nodes, 3)


class CycleGuard(unittest.TestCase):
    def test_self_referencing_children_do_not_hang(self):
        f = FakeFile("resources.assets")
        # 자기 자신을 자식으로 갖는 병든 트리 — 실제 손상 번들에서 나올 수 있다
        objs = [go(1, f, "Loop", components=(2,)), rect(2, f, 1, children=(2,))]
        index = unity.ObjectIndex(FakeEnv(objs))
        b = hierarchy._Builder(index, "resources.assets", _StubMono({}))
        b.build(b.roots()[0][1])
        self.assertTrue(any("순환" in m for m in b.failures))


class SafeName(unittest.TestCase):
    def test_path_separators_removed(self):
        self.assertEqual(hierarchy._safe("UI/Panel:1"), "UI_Panel_1")

    def test_blank(self):
        self.assertEqual(hierarchy._safe(""), "unnamed")


class UniquePath(unittest.TestCase):
    """프리팹 이름은 유일하지 않다 — 겹치면 zip에서 한쪽이 사라진다."""

    def test_first_use_unchanged(self):
        seen = set()
        self.assertEqual(hierarchy._unique("prefabs/r/Tooltip.json", seen),
                         "prefabs/r/Tooltip.json")

    def test_collisions_get_suffixes(self):
        seen = set()
        p = "prefabs/r/Tooltip.json"
        self.assertEqual(hierarchy._unique(p, seen), p)
        self.assertEqual(hierarchy._unique(p, seen), "prefabs/r/Tooltip_2.json")
        self.assertEqual(hierarchy._unique(p, seen), "prefabs/r/Tooltip_3.json")

    def test_suffix_does_not_collide_with_real_name(self):
        seen = set()
        hierarchy._unique("a/Tooltip.json", seen)
        hierarchy._unique("a/Tooltip_2.json", seen)          # 원래 이름이 _2 인 프리팹
        self.assertEqual(hierarchy._unique("a/Tooltip.json", seen), "a/Tooltip_3.json")


if __name__ == "__main__":
    unittest.main()


class SceneStreaming(unittest.TestCase):
    """씬 JSON을 루트 하나씩 흘려 써도 산출물이 예전(통째 조립)과 바이트 단위로 같다.

    통째 조립은 dict 과 JSON 문자열이 동시에 살아 있어 노드 11만 개짜리 씬에서
    피크의 큰 몫이었다. 줄이면서 산출물이 바뀌면 뷰어·후속 도구가 깨지므로
    여기서 바이트 일치를 못 박는다.
    """

    class _Builder:
        """`_write_scene` 이 기대하는 최소 인터페이스만 흉내낸다."""

        def __init__(self, docs):
            self._docs = docs
            self.nodes = sum(1 for d in docs if d is not None)

        def roots(self):
            return [(f"root{i}", i) for i in range(len(self._docs))]

        def build(self, tr):
            return self._docs[tr]

    def _old_way(self, fname, docs):
        """예전 코드 그대로 — 씬 전체를 조립해 한 번에 덤프."""
        doc = {"file": fname, "kind": "scene",
               "roots": [d for d in docs if d]}
        return hierarchy._dump(doc)

    def _new_way(self, fname, docs):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            b = self._Builder(docs)
            n = hierarchy._write_scene(zf, "scenes/x.json", fname, b, b.roots())
        with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as zf:
            return zf.read("scenes/x.json"), n

    def _same(self, fname, docs):
        old = self._old_way(fname, docs)
        new, n = self._new_way(fname, docs)
        self.assertEqual(new, old)
        json.loads(new)                      # 규격에 맞는 JSON 인지도 본다
        return n

    def test_single_root(self):
        self.assertEqual(self._same("level0", [{"name": "A", "components": []}]), 1)

    def test_multiple_roots(self):
        docs = [{"name": "A", "children": [{"name": "A1", "v": 1}]},
                {"name": "B", "components": [{"type": "Transform", "fields": None}]},
                {"name": "C", "v": [1, 2, 3]}]
        self.assertEqual(self._same("level1", docs), 3)

    def test_skipped_roots_are_not_written(self):
        """build() 가 None 을 준 루트는 빠진다 — 예전 동작과 같다."""
        docs = [None, {"name": "B"}, None, {"name": "D"}]
        self.assertEqual(self._same("level2", docs), 2)

    def test_no_roots_at_all(self):
        self.assertEqual(self._same("empty", [None]), 0)

    def test_non_ascii_and_quotes_in_file_name(self):
        self.assertEqual(self._same('레벨 "0"/x', [{"name": "가"}]), 1)

    def test_nan_still_becomes_valid_json(self):
        """RectTransform 에 NaN 이 실제로 들어 있다 — 뷰어의 JSON.parse 가 깨지면 안 된다."""
        docs = [{"name": "A", "fields": {"x": float("nan"), "y": float("inf")}}]
        new, n = self._new_way("level3", docs)
        self.assertEqual(n, 1)
        self.assertNotIn(b"NaN", new)
        self.assertEqual(new, self._old_way("level3", docs))
        json.loads(new)
