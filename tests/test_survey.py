"""survey — 계열 판정, 에셋형/파일형 선택, 설정 초안 생성."""
import base64
import gzip
import os
import tempfile
import unittest

from levelscope import survey

from .helpers import jbytes, level, write_zip


def fam(family, count, codec=("json",), type_name="TextAsset", source="s",
        median=100, head="7b22"):
    """_scan_source 가 만드는 계열 dict 한 개."""
    return {"source": source, "family": family, "count": count, "type": type_name,
            "codec": list(codec) if codec else None, "decodable": codec is not None,
            "median_bytes": median, "sample_name": family, "sample_head": head}


class NameFamilies(unittest.TestCase):
    def test_ranked_by_member_count(self):
        fams = [fam("ZenMasterConfigDataModel", 1), fam("Level_[0-9]+", 377)]
        self.assertEqual(survey.name_families(fams)[0], ("Level_[0-9]+", 377))

    def test_same_family_across_sources_is_merged(self):
        fams = [fam("[0-9]+", 3000, source="a"), fam("[0-9]+", 1500, source="b")]
        self.assertEqual(survey.name_families(fams), [("[0-9]+", 4500)])

    def test_norm_collapses_digits(self):
        self.assertEqual(survey._norm_name("Level_37"), "Level_[0-9]+")
        self.assertEqual(survey._norm_name("4500"), "[0-9]+")

    def test_name_hint_uses_decodable_only(self):
        """못 읽는 계열을 name_pattern 에 넣으면 설정이 바로 실패한다."""
        fams = [fam("[0-9]+", 4500, codec=None), fam("cfg_[0-9]+", 5)]
        self.assertEqual(survey._name_hint(fams), "cfg_[0-9]+")

    def test_name_hint_without_decodable(self):
        self.assertEqual(survey._name_hint([fam("[0-9]+", 10, codec=None)]), ".*")


class DecodableSplit(unittest.TestCase):
    def setUp(self):
        self.fams = [fam("a", 3), fam("b", 9, codec=None), fam("c", 1)]

    def test_split(self):
        self.assertEqual([f["family"] for f in survey.decodable(self.fams)], ["a", "c"])
        self.assertEqual([f["family"] for f in survey.undecodable(self.fams)], ["b"])


class DominantCodec(unittest.TestCase):
    def test_single_chain(self):
        got = survey._dominant_codec([fam("a", 5), fam("b", 3)], lambda *_: None)
        self.assertEqual(got, ["json"])

    def test_weighted_by_count_not_family_number(self):
        """4,500개짜리 계열이 1개짜리 계열 세 개에 밀리면 안 된다."""
        logs = []
        fams = [fam("big", 4500, codec=("json",)),
                fam("x", 1, codec=("strip_bom", "json")),
                fam("y", 1, codec=("strip_bom", "json"))]
        # 체인이 섞였으므로 auto 를 권하되, 로그에는 큰 쪽이 먼저 나와야 한다
        self.assertIsNone(survey._dominant_codec(fams, logs.append))
        self.assertTrue(any("json" in m and "4500" in m for m in logs))

    def test_mixed_chains_prefer_auto(self):
        logs = []
        fams = [fam("a", 7), fam("b", 1, codec=("strip_bom", "json"))]
        self.assertIsNone(survey._dominant_codec(fams, logs.append))
        self.assertTrue(any("auto 권장" in m for m in logs))

    def test_undecodable_ignored(self):
        self.assertIsNone(survey._dominant_codec([fam("a", 9, codec=None)], lambda *_: None))

    def test_empty(self):
        self.assertIsNone(survey._dominant_codec([], lambda *_: None))


class FileLevelCandidates(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def _apk(self, entries):
        return write_zip(os.path.join(self._td.name, f"g{len(self.logs)}.apk"), entries)

    def test_finds_level_folder_family(self):
        entries = {f"assets/Levels/setA/{i}.json": jbytes(level(i)) for i in range(6)}
        got = survey.file_level_candidates(self._apk(entries), log=self.logs.append)
        self.assertIn("assets/Levels/*/*.json", {p for p, _n, _c in got})

    def test_reports_detected_codec(self):
        payload = b"gzip:" + base64.b64encode(gzip.compress(jbytes(level(1))))
        entries = {f"assets/Levels/s/{i}.json": payload for i in range(5)}
        got = survey.file_level_candidates(self._apk(entries), log=self.logs.append)
        self.assertEqual(got[0][2], ["prefix:gzip:", "base64", "gunzip", "json"])

    def test_undecodable_files_are_not_candidates(self):
        entries = {f"assets/Levels/s/{i}.bin": bytes(range(64)) for i in range(6)}
        self.assertEqual(survey.file_level_candidates(self._apk(entries),
                                                     log=self.logs.append), [])

    def test_noise_paths_skipped(self):
        entries = {f"res/drawable/{i}.json": jbytes(level(i)) for i in range(8)}
        entries.update({f"lib/x/{i}.json": jbytes(level(i)) for i in range(8)})
        self.assertEqual(survey.file_level_candidates(self._apk(entries),
                                                     log=self.logs.append), [])

    def test_too_few_members_skipped(self):
        entries = {"assets/Levels/s/1.json": jbytes(level(1))}
        self.assertEqual(survey.file_level_candidates(self._apk(entries),
                                                     log=self.logs.append), [])

    def test_broader_pattern_wins_on_ties(self):
        entries = {f"assets/Q/Levels/{i}.json": jbytes(level(i)) for i in range(5)}
        got = survey.file_level_candidates(self._apk(entries), log=self.logs.append)
        self.assertEqual([g for g, _n, _c in got], ["assets/Q/*/*.json"])


class PrefersFileLevels(unittest.TestCase):
    def _rep(self, families=(), file_count=0):
        r = survey.Report()
        r.level_families = list(families)
        r.file_levels = [("assets/Levels/*/*.json", file_count, ["json"])] if file_count else []
        return r

    def test_no_file_candidates(self):
        self.assertFalse(survey.prefers_file_levels(self._rep([fam("Level_[0-9]+", 10)])))

    def test_no_asset_candidates_means_file(self):
        self.assertTrue(survey.prefers_file_levels(self._rep([], 12)))

    def test_pixelflow_shape_picks_file(self):
        """설정 TextAsset 몇 개 vs 레벨 파일 2384개 → 파일형."""
        self.assertTrue(survey.prefers_file_levels(
            self._rep([fam("IAPProductCatalog", 1), fam("default-config", 1)], 2384)))

    def test_zenmatch_shape_picks_asset(self):
        """에셋 레벨 377개 vs 미니게임 파일 7개 → 에셋형."""
        self.assertFalse(survey.prefers_file_levels(
            self._rep([fam("Level_[0-9]+", 377)], 7)))

    def test_small_file_family_does_not_win(self):
        self.assertFalse(survey.prefers_file_levels(
            self._rep([fam("newMap[0-9]+", 3)], 3)))

    def test_undecodable_assets_do_not_block_file_choice(self):
        """Royal Kingdom 형태 — 에셋 계열은 크지만 못 읽으면 파일 쪽을 본다."""
        self.assertTrue(survey.prefers_file_levels(
            self._rep([fam("[0-9]+", 4500, codec=None)], 10)))


class SuggestedConfig(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.out = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def _write(self, rep, codec=None):
        import yaml
        path = survey.write_suggested_config(rep, self.out, codec=codec, log=lambda *_: None)
        with open(path, encoding="utf-8") as f:
            return path, yaml.safe_load(f)

    def _asset_rep(self):
        from levelscope import discover
        rep = survey.Report(app_name="Zen Match", package="com.x",
                            unity_version="2022.3.62f2", backend="IL2CPP")
        rep.sources = [discover.UnitySource("g.apk", "assets/bin/Data/data.unity3d",
                                            "bundle", 1, 100, {})]
        rep.level_families = [fam("Level_[0-9]+", 20, source="assets/bin/Data/data.unity3d")]
        rep.type_totals = {"Sprite": 10, "AudioClip": 3, "Material": 4, "TextAsset": 20}
        return rep

    def test_asset_form_is_valid_yaml(self):
        _p, d = self._write(self._asset_rep(), codec=["json"])
        self.assertEqual(d["input"]["unity"]["name_pattern"], "Level_[0-9]+")
        self.assertEqual(d["codec"], ["json"])
        self.assertEqual(d["input"]["unity"]["data_file"], "assets/bin/Data/data.unity3d")

    def test_codec_none_becomes_auto(self):
        _p, d = self._write(self._asset_rep(), codec=None)
        self.assertEqual(d["codec"], "auto")

    def test_kinds_only_include_present_types(self):
        _p, d = self._write(self._asset_rep())
        self.assertEqual(d["assets"]["kinds"], ["audio", "material", "spine", "text"])
        self.assertNotIn("font", d["assets"]["kinds"])

    def test_file_form_uses_levels_glob(self):
        rep = survey.Report(app_name="Pixel Flow", backend="IL2CPP")
        rep.file_levels = [("assets/Levels/*/*.json", 2384, ["json"])]
        _p, d = self._write(rep, codec=["json"])
        self.assertEqual(d["input"]["levels_glob"], "assets/Levels/*/*.json")
        self.assertNotIn("unity", d["input"])

    def test_no_candidates_still_produces_parseable_draft(self):
        _p, d = self._write(survey.Report(app_name="Unknown", backend="불명"))
        self.assertIn("levels_glob", d["input"])

    def test_undecodable_family_does_not_reach_name_pattern(self):
        """못 읽는 계열이 name_pattern 에 들어가면 설정이 바로 실패한다."""
        rep = self._asset_rep()
        rep.level_families.append(fam("[0-9]+", 4500, codec=None))
        _p, d = self._write(rep, codec=["json"])
        self.assertEqual(d["input"]["unity"]["name_pattern"], "Level_[0-9]+")

    def test_sources_default_to_auto(self):
        _p, d = self._write(self._asset_rep())
        for sec in ("sprites", "assets", "hierarchy"):
            self.assertEqual(d[sec]["sources"], "auto")

    def test_filename_slugged_from_app_name(self):
        p, _d = self._write(self._asset_rep())
        self.assertTrue(os.path.basename(p).startswith("_suggested_zen_match"))


class Slug(unittest.TestCase):
    def test_normalizes(self):
        self.assertEqual(survey._slug("Zen Match"), "zen_match")
        self.assertEqual(survey._slug("A/B:C"), "a_b_c")

    def test_blank_falls_back(self):
        self.assertEqual(survey._slug("   "), "mygame")


class FormatReport(unittest.TestCase):
    def test_includes_key_lines(self):
        rep = survey.Report(input_path="x.apk", app_name="Game", package="com.g",
                            unity_version="2021.3.42f1", backend="IL2CPP")
        rep.type_totals = {"Sprite": 5}
        out = survey.format_report(rep)
        self.assertIn("Game", out)
        self.assertIn("IL2CPP", out)
        self.assertIn("Sprite 5", out)

    def test_undecodable_family_is_surfaced(self):
        """침묵하면 '레벨이 없다'로 읽힌다 — 못 읽는 계열도 보여야 한다."""
        rep = survey.Report()
        rep.level_families = [fam("[0-9]+", 4500, codec=None, head="2400000000001e00")]
        out = survey.format_report(rep)
        self.assertIn("디코딩 불가", out)
        self.assertIn("4500", out)
        self.assertIn("2400000000001e00", out)

    def test_empty_report_does_not_crash(self):
        self.assertIsInstance(survey.format_report(survey.Report()), str)


if __name__ == "__main__":
    unittest.main()
