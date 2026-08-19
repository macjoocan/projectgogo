"""ObjectIndex — PPtr 해석과 이름 추출, load_bytes 예외 전파."""
import unittest

from levelscope import unity

from .helpers import FakeEnv, FakeFile, FakeObj, pptr


class IsPPtr(unittest.TestCase):
    def test_recognizes_pptr_shape(self):
        self.assertTrue(unity.is_pptr({"m_FileID": 0, "m_PathID": 12}))

    def test_rejects_lookalikes(self):
        self.assertFalse(unity.is_pptr({"m_FileID": 0}))
        self.assertFalse(unity.is_pptr({"m_FileID": 0, "m_PathID": 1, "extra": 2}))
        self.assertFalse(unity.is_pptr({"x": 1.0, "y": 2.0}))
        self.assertFalse(unity.is_pptr(None))
        self.assertFalse(unity.is_pptr([0, 1]))


class Resolve(unittest.TestCase):
    def setUp(self):
        # level0 은 externals[0]="resources.assets" → m_FileID 1 이 그 파일을 가리킨다
        self.lv = FakeFile("level0", externals=["resources.assets", "unity default resources"])
        self.res = FakeFile("resources.assets")
        self.owner = FakeObj("MonoBehaviour", 5, self.lv)
        self.same = FakeObj("Sprite", 7, self.lv, attrs={"m_Name": "in_level0"})
        self.other = FakeObj("Sprite", 7, self.res, attrs={"m_Name": "in_resources"})
        self.index = unity.ObjectIndex(FakeEnv([self.owner, self.same, self.other]))

    def test_file_id_zero_is_same_file(self):
        self.assertIs(self.index.resolve(self.owner, pptr(7, 0)), self.same)

    def test_file_id_one_follows_externals(self):
        """같은 path_id 7 이 두 파일에 있다 — externals를 안 보면 엉뚱한 쪽이 잡힌다."""
        self.assertIs(self.index.resolve(self.owner, pptr(7, 1)), self.other)

    def test_external_outside_bundle_is_unresolved(self):
        self.assertIsNone(self.index.resolve(self.owner, pptr(7, 2)))

    def test_file_id_beyond_externals(self):
        self.assertIsNone(self.index.resolve(self.owner, pptr(7, 9)))

    def test_negative_file_id(self):
        """음수 m_FileID 가 실제로 나온다 — 파이썬 음수 인덱싱에 걸리면 안 된다."""
        for fid in (-1, -2, -99):
            with self.subTest(fid=fid):
                self.assertIsNone(self.index.resolve(self.owner, pptr(7, fid)))

    def test_null_and_garbage(self):
        self.assertIsNone(self.index.resolve(self.owner, pptr(0)))
        self.assertIsNone(self.index.resolve(self.owner, None))

    def test_describe(self):
        self.assertEqual(self.index.describe(self.owner, pptr(7, 0)),
                         {"name": "in_level0", "type": "Sprite"})


class Expand(unittest.TestCase):
    def setUp(self):
        self.f = FakeFile("resources.assets", externals=["unity default resources"])
        self.owner = FakeObj("MonoBehaviour", 1, self.f)
        self.sprite = FakeObj("Sprite", 42, self.f, attrs={"m_Name": "bg-title"})
        self.index = unity.ObjectIndex(FakeEnv([self.owner, self.sprite]))

    def test_resolved_ref_becomes_name(self):
        self.assertEqual(self.index.expand(self.owner, pptr(42)), "bg-title (Sprite)")

    def test_empty_ref_collapses_to_none(self):
        self.assertIsNone(self.index.expand(self.owner, pptr(0)))

    def test_unresolvable_ref_is_marked(self):
        self.assertEqual(self.index.expand(self.owner, pptr(42, 1)), "→ 미해석")

    def test_walks_tuples_not_just_lists(self):
        """UnityPy는 머티리얼 프로퍼티를 tuple로 준다 — list만 훑으면 통째로 안 풀린다."""
        tree = {"m_TexEnvs": [("_MainTex", {"m_Texture": pptr(42)})]}
        got = self.index.expand(self.owner, tree)
        self.assertEqual(got["m_TexEnvs"][0][1]["m_Texture"], "bg-title (Sprite)")

    def test_nested_dicts_and_scalars_survive(self):
        tree = {"m_Color": {"r": 1.0, "g": 0.5}, "m_Text": "안녕", "n": 3, "ok": True}
        self.assertEqual(self.index.expand(self.owner, tree), tree)

    def test_bytes_summarized(self):
        self.assertEqual(self.index.expand(self.owner, b"\x00" * 10), "<10 bytes>")

    def test_depth_capped(self):
        deep = cur = {}
        for _ in range(40):
            cur["next"] = {}
            cur = cur["next"]
        out = self.index.expand(self.owner, deep)
        flat = str(out)
        self.assertIn("…", flat)


class NameOf(unittest.TestCase):
    def test_plain_name(self):
        f = FakeFile("f")
        self.assertEqual(unity.name_of(FakeObj("Sprite", 1, f, attrs={"m_Name": "x"})), "x")

    def test_shader_falls_back_to_parsed_form(self):
        """Shader의 m_Name은 비어 있고 실이름은 m_ParsedForm 안에 있다."""
        f = FakeFile("f")
        o = FakeObj("Shader", 1, f, tree={"m_ParsedForm": {"m_Name": "Spine/Skeleton"}},
                    attrs={"m_Name": ""})
        self.assertEqual(unity.name_of(o), "Spine/Skeleton")

    def test_unreadable_object(self):
        class Boom(FakeObj):
            def read(self, check_read=True):
                raise RuntimeError("nope")

        self.assertIsNone(unity.name_of(Boom("Sprite", 1, FakeFile("f"))))


class FileName(unittest.TestCase):
    def test_reads_assets_file_name(self):
        self.assertEqual(unity.file_name(FakeObj("Sprite", 1, FakeFile("level0"))), "level0")

    def test_missing_is_question_mark(self):
        self.assertEqual(unity.file_name(object()), "?")


class LoadBytesErrors(unittest.TestCase):
    """with 블록 본문의 예외가 그대로 밖으로 나와야 한다.

    yield가 try 안에 있으면 본문 예외가 폴백 경로로 삼켜져
    `RuntimeError: generator didn't stop after throw()` 로 바꿔치기됐다.
    """

    def setUp(self):
        self._orig = unity._unitypy
        sentinel = object()
        self.sentinel = sentinel

        class FakeUnityPy:
            @staticmethod
            def load(_x):
                return sentinel

        unity._unitypy = lambda: FakeUnityPy

    def tearDown(self):
        unity._unitypy = self._orig

    def test_body_exception_propagates_unchanged(self):
        with self.assertRaises(ValueError) as cm:
            with unity.load_bytes(b"data"):
                raise ValueError("본문 오류")
        self.assertEqual(str(cm.exception), "본문 오류")

    def test_yields_loaded_env(self):
        with unity.load_bytes(b"data") as env:
            self.assertIs(env, self.sentinel)


if __name__ == "__main__":
    unittest.main()
