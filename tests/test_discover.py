"""discover — Unity 소스 자동 발견의 후보 판정·내장 구분·sources 해석."""
import os
import tempfile
import unittest

from levelscope import discover

from .helpers import write_zip


class Candidate(unittest.TestCase):
    def test_asset_extensions_pass(self):
        for n in ("a/data.unity3d", "a/x.bundle", "a/y.assets", "a/z.ab"):
            with self.subTest(n=n):
                self.assertTrue(discover.is_candidate(n, 5000))

    def test_known_non_unity_rejected(self):
        for n in ("classes.dex", "lib/x/libil2cpp.so", "res/a.png", "a/b.json",
                  "a/AndroidManifest.xml", "a/font.ttf", "a/s.mp3", "a/x.dll"):
            with self.subTest(n=n):
                self.assertFalse(discover.is_candidate(n, 5000))

    def test_streaming_payloads_rejected(self):
        """.resource/.resS 는 에셋 파일이 아니라 텍스처·오디오 원본 덩어리다."""
        self.assertFalse(discover.is_candidate("assets/bin/Data/resources.resource", 9999))
        self.assertFalse(discover.is_candidate("assets/bin/Data/level0.resS", 9999))

    def test_unknown_extension_not_touched(self):
        self.assertFalse(discover.is_candidate("a/b.weird", 5000))

    def test_extensionless_only_under_unity_paths(self):
        """`unity default resources` 처럼 확장자 없는 SerializedFile을 놓치면 안 된다."""
        self.assertTrue(discover.is_candidate("assets/bin/Data/unity default resources", 99999))
        self.assertFalse(discover.is_candidate("META-INF/CERT", 99999))

    def test_tiny_files_skipped(self):
        self.assertFalse(discover.is_candidate("assets/bin/Data/data.unity3d", 8))


class Builtin(unittest.TestCase):
    def _src(self, name):
        return discover.UnitySource("c", name, "bundle", 100, 5, {})

    def test_builtin_detected(self):
        for n in ("assets/bin/Data/unity default resources",
                  "x/Resources/unity_builtin_extra",
                  "assets/aa/Android/abc_unitybuiltinshaders_def.bundle"):
            with self.subTest(n=n):
                self.assertTrue(self._src(n).builtin)

    def test_game_asset_not_builtin(self):
        self.assertFalse(self._src("assets/bin/Data/data.unity3d").builtin)
        self.assertFalse(self._src("assets/aa/Android/room10__abc.bundle").builtin)


class SourceFields(unittest.TestCase):
    def test_label_and_basename(self):
        s = discover.UnitySource("g.apk", "assets/bin/Data/data.unity3d", "bundle", 5, 3, {})
        self.assertEqual(s.label, "g.apk!assets/bin/Data/data.unity3d")
        self.assertEqual(s.basename, "data.unity3d")

    def test_top_types_sorted(self):
        s = discover.UnitySource("c", "n", "bundle", 1, 6, {"A": 1, "B": 5, "C": 3})
        self.assertEqual(s.top_types(2), [("B", 5), ("C", 3)])

    def test_to_dict_includes_builtin_flag(self):
        s = discover.UnitySource("c", "unity default resources", "serialized", 1, 1, {})
        self.assertTrue(s.to_dict()["builtin"])


class InnerFiles(unittest.TestCase):
    """부수 정보가 판정을 무효로 만들면 안 된다 (실제로 그 버그가 있었다)."""

    def test_int_keys_do_not_raise(self):
        import types
        inner = types.SimpleNamespace(files={1: object(), 2: object()})
        env = types.SimpleNamespace(files={"cab": inner})
        self.assertEqual(discover._inner_files(env), [])

    def test_string_keys_returned_without_streaming(self):
        import types
        inner = types.SimpleNamespace(files={"level0": 1, "level0.resS": 2,
                                            "resources.assets": 3})
        env = types.SimpleNamespace(files={"cab": inner})
        self.assertEqual(sorted(discover._inner_files(env)), ["level0", "resources.assets"])

    def test_broken_env_returns_empty(self):
        class Boom:
            @property
            def files(self):
                raise RuntimeError("nope")

        self.assertEqual(discover._inner_files(Boom()), [])


class ProbeNonUnity(unittest.TestCase):
    """UnityPy.load 는 아무 파일에나 성공한다 — objects>0 으로 걸러야 한다."""

    def setUp(self):
        self._orig = None

    def test_zero_objects_serialized_is_rejected(self):
        from levelscope import unity
        self._orig = unity._unitypy
        import types as _t

        class FakeUP:
            @staticmethod
            def load(_x):
                return _t.SimpleNamespace(objects=[], files={})

        unity._unitypy = lambda: FakeUP
        try:
            kind, n, counts, files = discover.probe(b'{"json": true}' * 20)
            self.assertIsNone(kind)
            self.assertEqual(n, 0)
        finally:
            unity._unitypy = self._orig

    def test_zero_objects_but_bundle_magic_is_kept(self):
        """번들 매직이 확실하면 내용이 비어도 Unity 파일로 본다."""
        from levelscope import unity
        self._orig = unity._unitypy
        import types as _t

        class FakeUP:
            @staticmethod
            def load(_x):
                return _t.SimpleNamespace(objects=[], files={})

        unity._unitypy = lambda: FakeUP
        try:
            kind, n, _c, _f = discover.probe(b"UnityFS\x00" + b"\x00" * 64)
            self.assertEqual(kind, "bundle")
            self.assertEqual(n, 0)
        finally:
            unity._unitypy = self._orig


class ResolveSources(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.apk = write_zip(os.path.join(self._td.name, "g.apk"), {"a.txt": b"x"})
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def test_explicit_list_passes_through_untouched(self):
        got = discover.resolve_sources(self.apk, ["a/b.unity3d", "c/*.bundle"],
                                       log=self.logs.append)
        self.assertEqual(got, ["a/b.unity3d", "c/*.bundle"])
        self.assertEqual(self.logs, [])          # 자동 발견을 돌리지 않았다

    def test_auto_with_nothing_found_falls_back(self):
        got = discover.resolve_sources(self.apk, "auto", log=self.logs.append)
        self.assertEqual(got, ["assets/bin/Data/data.unity3d"])
        self.assertTrue(any("자동 발견 실패" in m for m in self.logs))

    def test_none_behaves_like_auto(self):
        got = discover.resolve_sources(self.apk, None, log=self.logs.append,
                                       default=["x/y.unity3d"])
        self.assertEqual(got, ["x/y.unity3d"])

    def test_single_string_source(self):
        self.assertEqual(discover.resolve_sources(self.apk, "only/one.unity3d",
                                                  log=self.logs.append),
                         ["only/one.unity3d"])


class MatchAny(unittest.TestCase):
    def test_matches_tail(self):
        self.assertTrue(discover._match_any("base/assets/x.bundle", ["assets/x.bundle"]))

    def test_glob(self):
        self.assertTrue(discover._match_any("a/b/c.bundle", ["a/**/*.bundle"]))
        self.assertFalse(discover._match_any("a/b/c.unity3d", ["*.bundle"]))


if __name__ == "__main__":
    unittest.main()
