"""assets — 갈래 분류, 스트리밍 리소스 조회, 파일명 처리."""
import os
import tempfile
import unittest

from levelscope import assets

from .helpers import make_zip_bytes, write_zip


class SpineClassify(unittest.TestCase):
    def test_atlas_and_skel_by_extension(self):
        self.assertTrue(assets._is_spine("skeleton.atlas", b"skeleton.png\nsize:1,1"))
        self.assertTrue(assets._is_spine("Baba2.skel", b"\xff\x00binary"))
        self.assertTrue(assets._is_spine("UI_fat.skel.atlas", b"x"))

    def test_json_needs_skeleton_key(self):
        self.assertTrue(assets._is_spine("hero.json", b'{"skeleton":{"spine":"4.1"},"bones":[]}'))
        self.assertFalse(assets._is_spine("newMap3.json", b'{"mapData":[{"mapId":1}]}'))

    def test_plain_localization_is_not_spine(self):
        self.assertFalse(assets._is_spine("English", b"email:Mail\nday:D\n"))


class LooksText(unittest.TestCase):
    def test_text(self):
        self.assertTrue(assets._looks_text("안녕하세요 hello".encode("utf-8")))

    def test_binary(self):
        self.assertFalse(assets._looks_text(bytes(range(0, 32)) * 20))

    def test_empty_counts_as_text(self):
        self.assertTrue(assets._looks_text(b""))


class SafeAndUnique(unittest.TestCase):
    def test_strips_path_characters(self):
        self.assertEqual(assets._safe('a/b\\c:d*e?f"g<h>i|j'), "a_b_c_d_e_f_g_h_i_j")

    def test_blank_falls_back(self):
        self.assertEqual(assets._safe("   "), "unnamed")
        self.assertEqual(assets._safe(None, "clip"), "clip")

    def test_unique_suffixes_collisions(self):
        seen = set()
        self.assertEqual(assets._unique("audio/x", ".wav", seen), "audio/x.wav")
        self.assertEqual(assets._unique("audio/x", ".wav", seen), "audio/x_2.wav")
        self.assertEqual(assets._unique("audio/x", ".wav", seen), "audio/x_3.wav")


class ResourceStoreTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.apk = write_zip(os.path.join(self._td.name, "g.apk"), {
            "assets/bin/Data/resources.resource": b"AUDIOBYTES" * 10,
            "assets/bin/Data/data.unity3d": b"not-a-real-bundle",
        })
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def store(self):
        return assets.ResourceStore(self.apk, log=self.logs.append)

    def test_finds_by_basename(self):
        self.assertEqual(self.store().get("resources.resource"), b"AUDIOBYTES" * 10)

    def test_strips_archive_prefix(self):
        """m_Source는 'archive:/CAB-x/resources.resource' 처럼 오기도 한다."""
        s = self.store()
        self.assertEqual(s.get("archive:/CAB-abc/resources.resource"), b"AUDIOBYTES" * 10)

    def test_caches_single_lookup(self):
        s = self.store()
        s.get("resources.resource")
        s.get("resources.resource")
        found = [m for m in self.logs if "확보" in m]
        self.assertEqual(len(found), 1)

    def test_unique_candidate_substituted_but_announced(self):
        """이름이 안 맞아도 후보가 하나뿐이면 대체한다 — 단, 조용히 하지 않는다."""
        s = self.store()
        self.assertEqual(s.get("renamed.resource"), b"AUDIOBYTES" * 10)
        self.assertTrue(any("대체" in m for m in self.logs))

    def test_ambiguous_candidates_are_refused(self):
        """여러 후보 중 하나를 찍으면 엉뚱한 오프셋으로 잘라 소리가 쓰레기가 된다."""
        apk = write_zip(os.path.join(self._td.name, "two.apk"), {
            "assets/bin/Data/resources.resource": b"A" * 50,
            "assets/bin/Data/sharedassets0.resource": b"B" * 50,
        })
        s = assets.ResourceStore(apk, log=self.logs.append)
        self.assertIsNone(s.get("nope.resource"))
        self.assertTrue(any("찾지 못했" in m for m in self.logs))

    def test_missing_warns_once_then_stays_quiet(self):
        apk = write_zip(os.path.join(self._td.name, "none.apk"),
                        {"assets/bin/Data/data.unity3d": b"x"})
        s = assets.ResourceStore(apk, log=self.logs.append)
        self.assertIsNone(s.get("nope.resource"))
        self.assertIsNone(s.get("nope.resource"))
        self.assertEqual(len([m for m in self.logs if "찾지 못했" in m]), 1)

    def test_empty_source(self):
        self.assertIsNone(self.store().get(None))
        self.assertIsNone(self.store().get(""))


def _fake_env(entries):
    """번들 내부 파일을 가진 env 대역. {이름: bytes}"""
    import types

    class Reader:
        def __init__(self, b):
            self.bytes = b

    inner = types.SimpleNamespace(files={k: Reader(v) for k, v in entries.items()})
    return types.SimpleNamespace(files={"cab": inner})


class FromEnv(unittest.TestCase):
    def test_reads_internal_resource(self):
        env = _fake_env({"CAB-abc.resource": b"FSB5DATA"})
        self.assertEqual(assets._from_env(env, "CAB-abc.resource"), b"FSB5DATA")

    def test_case_insensitive(self):
        env = _fake_env({"CAB-ABC.resource": b"X"})
        self.assertEqual(assets._from_env(env, "cab-abc.resource"), b"X")

    def test_missing_and_none(self):
        self.assertIsNone(assets._from_env(_fake_env({"a": b"1"}), "b"))
        self.assertIsNone(assets._from_env(None, "b"))

    def test_int_keys_do_not_crash(self):
        import types
        inner = types.SimpleNamespace(files={1: object()})
        self.assertIsNone(assets._from_env(types.SimpleNamespace(files={"c": inner}), "x"))


class BundleInternalResource(unittest.TestCase):
    """Addressables류 번들은 자기 오디오를 CAB-<hash>.resource 로 안에 품는다.

    Royal Kingdom에서 이걸 못 찾아 컨테이너의 다른 .resource 로 대체했고,
    오프셋이 원본 파일 기준이라 오디오 291개가 통째로 깨졌다.
    """

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.apk = write_zip(os.path.join(self._td.name, "g.apk"), {
            "assets/bin/Data/resources.resource": b"WRONGFILE" * 10,
        })
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def test_bundle_internal_wins_over_container(self):
        s = assets.ResourceStore(self.apk, log=self.logs.append)
        s.bind(_fake_env({"CAB-abc.resource": b"RIGHT"}))
        self.assertEqual(s.get("archive:/CAB-abc/CAB-abc.resource"), b"RIGHT")
        self.assertTrue(any("번들 내부" in m for m in self.logs))

    def test_cab_never_substituted_by_lone_candidate(self):
        """후보가 하나뿐이어도 CAB 이름은 대체하면 안 된다 — 소리가 깨진다."""
        s = assets.ResourceStore(self.apk, log=self.logs.append)
        s.bind(_fake_env({}))
        self.assertIsNone(s.get("CAB-notfound.resource"))
        self.assertTrue(any("소리가 깨지므로" in m for m in self.logs))
        self.assertFalse(any("대체합니다" in m for m in self.logs))

    def test_non_cab_still_substitutes(self):
        s = assets.ResourceStore(self.apk, log=self.logs.append)
        self.assertEqual(s.get("renamed.resource"), b"WRONGFILE" * 10)
        self.assertTrue(any("대체" in m for m in self.logs))

    def test_unbind_falls_back_to_container(self):
        s = assets.ResourceStore(self.apk, log=self.logs.append)
        s.bind(_fake_env({"resources.resource": b"INNER"}))
        self.assertEqual(s.get("resources.resource"), b"INNER")
        s2 = assets.ResourceStore(self.apk, log=self.logs.append)
        s2.unbind()
        self.assertEqual(s2.get("resources.resource"), b"WRONGFILE" * 10)


class KindSelection(unittest.TestCase):
    """설정 오류가 조용히 넘어가지 않아야 한다."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.out = self._td.name
        self.apk = write_zip(os.path.join(self._td.name, "g.apk"),
                             {"assets/bin/Data/data.unity3d": b"x"})
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def test_unknown_kind_is_reported(self):
        assets.extract_assets(self.apk, {"kinds": ["audio", "mesh"], "sources": ["nothing/*"]},
                              self.out, game="g", log=self.logs.append)
        self.assertTrue(any("모르는 kind" in m and "mesh" in m for m in self.logs))

    def test_all_kinds_unknown_stops_early(self):
        r = assets.extract_assets(self.apk, {"kinds": ["mesh"]}, self.out, game="g",
                                  log=self.logs.append)
        self.assertEqual(r.total, 0)
        self.assertTrue(any("추출할 갈래가 없" in m for m in self.logs))

    def test_missing_sources_warns(self):
        assets.extract_assets(self.apk, {"sources": ["no/such/path.unity3d"]}, self.out,
                              game="g", log=self.logs.append)
        self.assertTrue(any("찾지 못했" in m for m in self.logs))


class FontExtension(unittest.TestCase):
    def test_magic_table_covers_ttf_otf(self):
        self.assertEqual(assets._FONT_MAGIC[b"OTTO"], ".otf")
        self.assertEqual(assets._FONT_MAGIC[b"\x00\x01\x00\x00"], ".ttf")


if __name__ == "__main__":
    unittest.main()
