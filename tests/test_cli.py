"""CLI 단계 분해 후의 동작 — 플러그인 로드, 디코딩 루프, run 전체 흐름.

xlsx만 pandas/openpyxl이 필요하므로 outputs=[html, zip] 으로 전체 경로를 돈다.
"""
import argparse
import base64
import gzip
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

from levelscope import cli

from .helpers import jbytes, level, make_zip_bytes, write_zip

PLUGIN_SRC = '''
ENTITY_SHEET = {"name": "Things", "headers": ["set", "level", "kind"]}

def level_extras(data):
    return {"extra": data.get("id", 0) * 10}

def entities(set_name, level, data):
    return [(set_name, level, "a"), (set_name, level, "b")]

def viewer_level(data):
    return {"ma": [[1, 2]], "sq": []}
'''


class Tmp(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def p(self, *parts):
        return os.path.join(self.tmp, *parts)


class LoadPlugin(Tmp):
    def test_packaged_plugin(self):
        cfg = {"plugin": "pixelflow", "_config_dir": self.tmp}
        mod = cli._load_plugin(cfg)
        self.assertTrue(hasattr(mod, "ENTITY_SHEET"))

    def test_none_when_unset(self):
        self.assertIsNone(cli._load_plugin({"_config_dir": self.tmp}))

    def test_external_plugin_dir(self):
        os.makedirs(self.p("plugins"), exist_ok=True)
        os.makedirs(self.p("configs"), exist_ok=True)
        with open(self.p("plugins", "mygame.py"), "w", encoding="utf-8") as f:
            f.write(PLUGIN_SRC)
        before = list(sys.path)
        mod = cli._load_plugin({"plugin": "mygame", "_config_dir": self.p("configs")})
        self.assertEqual(mod.level_extras({"id": 3}), {"extra": 30})
        self.assertEqual(sys.path, before, "sys.path 를 영구 오염시키면 안 된다")
        del sys.modules["mygame"]

    def test_missing_plugin_exits(self):
        with self.assertRaises(SystemExit):
            cli._load_plugin({"plugin": "does_not_exist_xyz", "_config_dir": self.tmp})


class ExtraImportPath(Tmp):
    def test_restores_on_exception(self):
        before = list(sys.path)
        with self.assertRaises(RuntimeError):
            with cli._extra_import_path(self.tmp):
                raise RuntimeError("boom")
        self.assertEqual(sys.path, before)

    def test_ignores_missing_dir(self):
        before = list(sys.path)
        with cli._extra_import_path(self.p("nope")):
            self.assertEqual(sys.path, before)


class FakeRecord:
    def __init__(self, set_name, level_id, raw):
        self.set_name, self.level_id, self.raw = set_name, level_id, raw
        self.source = f"{set_name}/{level_id}"


class DecodeAll(unittest.TestCase):
    CFG = {"codec": ["json"],
           "fields": {"scalars": {"Id": "id"}, "counts": {"pix": "pixels"}},
           "board": {"width": "width", "height": "height", "pixels": "pixels",
                     "pixel": {"x": "x", "y": "y", "material": "material"}}}

    def records(self, n=3):
        return [FakeRecord("s1", i, jbytes(level(i))) for i in range(n)]

    def test_rows_and_board(self):
        got = cli._decode_all(self.records(), self.CFG, None, lambda _m: None)
        self.assertEqual(len(got.rows), 3)
        self.assertEqual(got.errors, [])
        self.assertEqual(got.rows[0]["pix"], 2)
        self.assertEqual((got.rows[0]["grid_w"], got.rows[0]["grid_h"]), (3, 2))
        self.assertEqual(got.chains[("json",)], 3)
        self.assertIsNotNone(got.records[0]["board_enc"])

    def test_plugin_hooks(self):
        import types
        plug = types.ModuleType("p")
        exec(PLUGIN_SRC, plug.__dict__)
        got = cli._decode_all(self.records(2), self.CFG, plug, lambda _m: None)
        self.assertEqual(got.rows[1]["extra"], 10)
        self.assertEqual(len(got.entities_rows), 4)
        self.assertEqual(got.records[0]["extra_viewer"], {"ma": [[1, 2]], "sq": []})

    def test_on_plain_receives_plaintext(self):
        seen = []
        cli._decode_all(self.records(2), self.CFG, None, lambda _m: None,
                        on_plain=lambda s, lid, plain: seen.append((s, lid, plain)))
        self.assertEqual(len(seen), 2)
        self.assertEqual(json.loads(seen[0][2])["id"], 0)

    def test_auto_codec(self):
        recs = [FakeRecord("s", 1, gzip.compress(jbytes(level(1))))]
        got = cli._decode_all(recs, dict(self.CFG, codec="auto"), None, lambda _m: None)
        self.assertEqual(len(got.rows), 1)
        self.assertEqual(got.chains[("gunzip", "json")], 1)

    def test_failures_collected_and_suggested(self):
        logs = []
        recs = [FakeRecord("s", 1, gzip.compress(jbytes(level(1))))]   # 설정은 json인데 gzip
        got = cli._decode_all(recs, self.CFG, None, logs.append)
        self.assertEqual(len(got.rows), 0)
        self.assertEqual(len(got.errors), 1)
        self.assertTrue(any("자동 감지 제안" in m for m in logs), logs)

    def test_partial_failure_keeps_good_rows(self):
        recs = self.records(2) + [FakeRecord("s1", 9, b"\x00\x01 not json")]
        got = cli._decode_all(recs, self.CFG, None, lambda _m: None)
        self.assertEqual(len(got.rows), 2)
        self.assertEqual(len(got.errors), 1)


SPLIT_PLUGIN_SRC = '''
def split_levels(data, record):
    return [(f"set{m['g']}", f"{m['id']}-{s}", {"id": m["id"], "stage": s, "n": s * 10})
            for m in data["maps"] for s in (1, 2)]

def level_extras(data):
    return {"n": data["n"], "stage": data["stage"]}
'''


class SplitLevels(unittest.TestCase):
    """한 소스가 레벨 여러 개를 담는 게임 (SheepNSheep의 mapData 같은 구조)."""

    CFG = {"codec": ["json"]}

    def plugin(self, src=SPLIT_PLUGIN_SRC):
        import types
        mod = types.ModuleType("sp")
        exec(src, mod.__dict__)
        return mod

    def records(self):
        blob = jbytes({"maps": [{"id": 290, "g": "A"}, {"id": 291, "g": "B"}]})
        return [FakeRecord("src", "asset1", blob)]

    def test_expands_into_many_levels(self):
        got = cli._decode_all(self.records(), self.CFG, self.plugin(), lambda _m: None)
        self.assertEqual(len(got.rows), 4)                 # 맵 2개 × 스테이지 2개
        self.assertEqual([r["level"] for r in got.rows],
                         ["290-1", "290-2", "291-1", "291-2"])
        self.assertEqual([r["set"] for r in got.rows], ["setA", "setA", "setB", "setB"])
        self.assertEqual(got.rows[1]["n"], 20)
        self.assertEqual(len(got.records), 4)

    def test_plain_written_per_sublevel(self):
        seen = []
        cli._decode_all(self.records(), self.CFG, self.plugin(), lambda _m: None,
                        on_plain=lambda s, lid, p: seen.append((s, lid, json.loads(p))))
        self.assertEqual(len(seen), 4)
        self.assertEqual(seen[0][2], {"id": 290, "stage": 1, "n": 10})

    def test_split_failure_is_reported(self):
        bad = self.plugin("def split_levels(data, record):\n    raise ValueError('nope')\n")
        got = cli._decode_all(self.records(), self.CFG, bad, lambda _m: None)
        self.assertEqual(got.rows, [])
        self.assertEqual(len(got.errors), 1)
        self.assertIn("split_levels 실패", got.errors[0][1])

    def test_empty_split_is_reported(self):
        empty = self.plugin("def split_levels(data, record):\n    return []\n")
        got = cli._decode_all(self.records(), self.CFG, empty, lambda _m: None)
        self.assertIn("결과 없음", got.errors[0][1])


class SheepNSheepPlugin(unittest.TestCase):
    """플러그인이 최신형·구형 두 스키마를 다 받는지."""

    def setUp(self):
        from levelscope.plugins import sheepnsheep
        self.p = sheepnsheep

    def modern(self):
        return {"version": 54, "mapData": [{"mapId": 290, "blockTypeData": [{"1": 2, "2": 3}],
                "level": [{"1": [{"col": 16, "row": 16, "type": 0, "moldType": 1, "layer": 1}] * 15,
                           "2": [{"col": 28, "row": 16, "type": 3, "moldType": 1, "layer": 2}]}]}]}

    def legacy(self):
        return {"version": 0, "mapData": [{"mapId": 1,
                "level1": {"1": [{"rolNum": 16, "rowNum": 16, "layerNum": 1,
                                  "type": 0, "moldType": 1}]}}]}

    def test_modern_split_and_extras(self):
        rec = FakeRecord("s", "newMapLv3", b"")
        subs = self.p.split_levels(self.modern(), rec)
        self.assertEqual([(s, lid) for s, lid, _d in subs], [("newMapLv3", "290-1")])
        row = self.p.level_extras(subs[0][2])
        self.assertEqual(row["tile_count"], 16)
        self.assertEqual(row["random_tiles"], 15)
        self.assertEqual(row["fixed_tiles"], 1)
        self.assertEqual(row["match_sets"], 5)
        self.assertEqual(row["pool_ok"], "OK")     # 5 × 3 == 15

    def test_pool_ok_states(self):
        subs = self.p.split_levels(self.legacy(), FakeRecord("s", "defaultMapData", b""))
        self.assertEqual(self.p.level_extras(subs[0][2])["pool_ok"], "-")   # blockTypeData 없음
        data = self.modern()
        data["mapData"][0]["blockTypeData"] = [{"1": 99}]                   # 99×3 ≠ 15
        subs = self.p.split_levels(data, FakeRecord("s", "a", b""))
        self.assertEqual(self.p.level_extras(subs[0][2])["pool_ok"], "불일치")

    def test_legacy_keys_normalized(self):
        subs = self.p.split_levels(self.legacy(), FakeRecord("s", "defaultMapData", b""))
        self.assertEqual(subs[0][1], "1-1")
        self.assertEqual(subs[0][2]["tiles"][0], {"col": 16, "row": 16, "layer": 1,
                                                  "type": 0, "moldType": 1})

    def test_adventure_map_difficulty_groups(self):
        data = {"easyMapData": [{"mapId": 1, "level": [{"1": [{"col": 0, "row": 0}]}]}],
                "hellMapData": [{"mapId": 2, "level": [{"1": [{"col": 0, "row": 0}]}]}]}
        sets = {s for s, _l, _d in self.p.split_levels(data, FakeRecord("s", "AdventureMap", b""))}
        self.assertEqual(sets, {"AdventureMap_easy", "AdventureMap_hell"})

    def test_board_and_viewer(self):
        sub = self.p.split_levels(self.modern(), FakeRecord("s", "a", b""))[0][2]
        b = self.p.board(sub)
        self.assertEqual((b["w"], b["h"]), (12 + 12, 12))   # col 16~28 → span+타일폭
        self.assertEqual(b["pixel_count"], 16)
        self.assertEqual(len(b["overlays"]["fixed"]["points"]), 1)
        v = self.p.viewer_level(sub)
        self.assertTrue(v["ma"])
        self.assertTrue(v["sq"])

    def test_empty_stage_skipped(self):
        data = {"mapData": [{"mapId": 9, "level": [{}, {"1": [{"col": 0, "row": 0}]}]}]}
        subs = self.p.split_levels(data, FakeRecord("s", "a", b""))
        self.assertEqual([lid for _s, lid, _d in subs], ["9-2"])


class ErrorReport(Tmp):
    def test_writes_both_sections(self):
        p = cli._write_error_report(self.tmp, "G", [("src1", "err1")], ["warn1"], lambda _m: None)
        with open(p, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("src1", text)
        self.assertIn("warn1", text)

    def test_no_file_when_clean(self):
        self.assertIsNone(cli._write_error_report(self.tmp, "G", [], [], lambda _m: None))


class RunEndToEnd(Tmp):
    """run 전체 — 합성 apk → 뷰어 HTML + decoded zip (xlsx 제외: pandas 불필요)."""

    CFG = {
        "game": "TestGame",
        "input": {"levels_glob": "assets/Levels/*/*.json"},
        "codec": ["strip_bom", "prefix:gzip:", "base64", "gunzip", "json"],
        "fields": {"scalars": {"Id": "id"}, "counts": {"pix": "pixels"}},
        "board": {"width": "width", "height": "height", "pixels": "pixels",
                  "pixel": {"x": "x", "y": "y", "material": "material"}},
        "palette": {"source": "static", "static": ["#000000", "#FF0000", "#00FF00"]},
        "viewer": {"title": "t", "card_stats": ["pix"]},
        "outputs": ["html", "zip"],
    }

    def encoded_level(self, i):
        return b"gzip:" + base64.b64encode(gzip.compress(jbytes(level(i))))

    def make_apk(self):
        return write_zip(self.p("app.xapk"), {"base.apk": make_zip_bytes(
            {f"assets/Levels/set1/{i}.json": self.encoded_level(i) for i in (1, 2, 3)})})

    def run_pipeline(self, cfg=None, out_dir=None, **kw):
        cfg = dict(cfg or self.CFG)
        cfg["_config_dir"] = self.tmp
        orig = cli._load_config
        cli._load_config = lambda _p: cfg
        try:
            args = argparse.Namespace(config="x.yaml", input=self.make_apk(),
                                      out=out_dir or self.p("out"), limit=0, **kw)
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                cli.run(args)
            finally:
                sys.stdout = old
            return buf.getvalue()
        finally:
            cli._load_config = orig

    def test_produces_viewer_and_zip(self):
        out = self.run_pipeline()
        self.assertIn("[decode] 성공 3 / 실패 0", out)
        html = self.p("out", "TestGame_viewer.html")
        self.assertTrue(os.path.exists(html))
        self.assertGreater(os.path.getsize(html), 1000)

        zpath = self.p("out", "TestGame_levels_decoded.zip")
        with zipfile.ZipFile(zpath) as z:
            names = sorted(z.namelist())
            self.assertEqual(names, ["levels/set1/1.json", "levels/set1/2.json",
                                     "levels/set1/3.json", "palette.json"])
            self.assertEqual(json.loads(z.read("levels/set1/2.json"))["id"], 2)
            self.assertEqual(len(json.loads(z.read("palette.json"))), 3)

    def test_locked_output_does_not_kill_the_run(self):
        """산출물 하나가 잠겨 있어도(Excel로 열어둔 xlsx 등) 나머지는 나온다."""
        out = self.p("out3")
        os.makedirs(out, exist_ok=True)
        cfg = dict(self.CFG, outputs=["html", "zip"])
        cfg["_config_dir"] = self.tmp
        orig = cli._load_config
        cli._load_config = lambda _p: cfg
        held = open(os.path.join(out, "TestGame_viewer.html"), "w", encoding="utf-8")
        try:
            import levelscope.viewer as vmod
            real = vmod.build_viewer
            vmod.build_viewer = lambda *a, **k: (_ for _ in ()).throw(
                PermissionError("locked"))
            args = argparse.Namespace(config="x.yaml", input=self.make_apk(),
                                      out=out, limit=0)
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                with self.assertRaises(SystemExit):     # 실패가 있으면 종료코드 1
                    cli.run(args)
            finally:
                sys.stdout = old
                vmod.build_viewer = real
            text = buf.getvalue()
            self.assertIn("[html] 실패", text)
            self.assertIn("열려 있는지", text)           # PermissionError 안내
            self.assertIn("산출물 1종 실패", text)
            # html이 실패했어도 zip은 정상 생성돼야 한다
            zpath = os.path.join(out, "TestGame_levels_decoded.zip")
            with zipfile.ZipFile(zpath) as z:
                self.assertEqual(len([n for n in z.namelist() if n.startswith("levels/")]), 3)
        finally:
            held.close()
            cli._load_config = orig

    def test_no_error_report_when_clean(self):
        self.run_pipeline()
        self.assertFalse(os.path.exists(self.p("out", "TestGame_errors.txt")))

    def test_error_report_on_bad_codec(self):
        cfg = dict(self.CFG, codec=["json"])            # 실제는 prefix+base64+gzip
        with self.assertRaises(SystemExit):             # 전부 실패 → 중단
            self.run_pipeline(cfg)

    def test_limit_option(self):
        cfg = dict(self.CFG)
        cfg["_config_dir"] = self.tmp
        orig = cli._load_config
        cli._load_config = lambda _p: cfg
        try:
            args = argparse.Namespace(config="x.yaml", input=self.make_apk(),
                                      out=self.p("out2"), limit=2)
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                cli.run(args)
            finally:
                sys.stdout = old
            self.assertIn("[decode] 성공 2 / 실패 0", buf.getvalue())
        finally:
            cli._load_config = orig


class Parser(unittest.TestCase):
    def test_subcommands_present(self):
        ap = cli.build_parser()
        for cmd in ("run", "inspect", "detect", "ls", "survey", "sprites",
                    "assets", "hierarchy"):
            with self.subTest(cmd=cmd):
                args = ap.parse_args([cmd, "--input", "x"] +
                                     (["--config", "c"] if cmd in ("run", "inspect") else []))
                self.assertTrue(callable(args.func))

    def test_assets_kinds_parsed(self):
        args = cli.build_parser().parse_args(
            ["assets", "--input", "x", "--kinds", "audio, spine"])
        self.assertEqual(cli._sources_arg(args.kinds), ["audio", "spine"])

    def test_hierarchy_flags(self):
        args = cli.build_parser().parse_args(
            ["hierarchy", "--input", "x", "--scenes-only", "--no-fields", "--no-typetree"])
        self.assertTrue(args.scenes_only)
        self.assertTrue(args.no_fields)
        self.assertTrue(args.no_typetree)
        self.assertFalse(args.prefabs_only)

    def test_survey_flags(self):
        args = cli.build_parser().parse_args(
            ["survey", "--input", "x", "--configs", "configs", "--shallow",
             "--max-sources", "5"])
        self.assertEqual(args.configs, "configs")
        self.assertTrue(args.shallow)
        self.assertEqual(args.max_sources, 5)

    def test_survey_configs_optional(self):
        args = cli.build_parser().parse_args(["survey", "--input", "x"])
        self.assertIsNone(args.configs)
        self.assertFalse(args.shallow)

    def test_hierarchy_defaults_keep_everything(self):
        args = cli.build_parser().parse_args(["hierarchy", "--input", "x"])
        self.assertFalse(args.scenes_only or args.prefabs_only or args.no_fields)
        self.assertEqual(args.max_nodes, 200000)

    def test_detect_xor_flags(self):
        args = cli.build_parser().parse_args(
            ["detect", "--input", "x", "--xor-scan", "--max-keylen", "8"])
        self.assertTrue(args.xor_scan)
        self.assertEqual(args.max_keylen, 8)

    def test_run_limit_default_zero(self):
        args = cli.build_parser().parse_args(["run", "--config", "c", "--input", "i"])
        self.assertEqual(args.limit, 0)


if __name__ == "__main__":
    unittest.main()


class ResolveOutputs(unittest.TestCase):
    """`--only` — 설정의 outputs 를 좁힌다. 넓히지는 않는다."""

    CFG = {"outputs": ["xlsx", "html", "zip", "sprites"]}

    def pick(self, only, cfg=None):
        msgs = []
        # `{}` 도 넘길 수 있어야 하므로 `or` 가 아니라 None 검사를 쓴다
        got = cli._resolve_outputs(dict(self.CFG if cfg is None else cfg),
                                   only, msgs.append)
        return got, "\n".join(msgs)

    def test_none_returns_config_outputs(self):
        got, msgs = self.pick(None)
        self.assertEqual(got, ["xlsx", "html", "zip", "sprites"])
        self.assertEqual(msgs, "")                      # 조용하다

    def test_default_when_config_has_no_outputs(self):
        got, _ = self.pick(None, {})
        self.assertEqual(got, ["xlsx", "html"])

    def test_narrows_to_selection(self):
        got, _ = self.pick("zip")
        self.assertEqual(got, ["zip"])

    def test_keeps_config_order_not_argument_order(self):
        got, _ = self.pick("sprites,xlsx")
        self.assertEqual(got, ["xlsx", "sprites"])

    def test_tolerates_spaces_and_empty_items(self):
        got, _ = self.pick(" zip , , html ")
        self.assertEqual(got, ["html", "zip"])

    def test_cannot_enable_what_config_omitted(self):
        """설정에서 뺀 산출물은 --only 로도 살아나지 않고, 빠졌다고 로그에 남는다."""
        got, msgs = self.pick("zip,hierarchy")
        self.assertEqual(got, ["zip"])
        self.assertIn("hierarchy", msgs)
        self.assertIn("건너뜀", msgs)

    def test_unknown_name_exits(self):
        with self.assertRaises(SystemExit) as e:
            self.pick("zipp")
        self.assertIn("zipp", str(e.exception))

    def test_empty_intersection_exits(self):
        with self.assertRaises(SystemExit) as e:
            self.pick("hierarchy")
        self.assertIn("하나도 없습니다", str(e.exception))


class RunOnly(RunEndToEnd):
    """`--only` 로 단계를 나눠 돌린다 — 커밋 피크를 단계별로 낮추기 위한 것."""

    def test_only_zip_skips_viewer(self):
        out = self.run_pipeline(only="zip")
        self.assertIn("[decode] 성공 3 / 실패 0", out)
        self.assertTrue(os.path.exists(self.p("out", "TestGame_levels_decoded.zip")))
        self.assertFalse(os.path.exists(self.p("out", "TestGame_viewer.html")))

    def test_only_html_skips_zip(self):
        self.run_pipeline(only="html")
        self.assertTrue(os.path.exists(self.p("out", "TestGame_viewer.html")))
        self.assertFalse(os.path.exists(self.p("out", "TestGame_levels_decoded.zip")))

    def test_non_level_selection_skips_collection_entirely(self):
        """레벨을 쓰지 않는 산출물만 고르면 수집·디코딩을 아예 안 한다.

        단계를 나눠 돌릴 때 레벨을 단계마다 다시 푸는 낭비를 막는다.
        """
        cfg = dict(self.CFG, outputs=["html", "zip", "sprites"])
        out = self.run_pipeline(cfg, only="sprites")
        self.assertIn("레벨 단계 생략", out)
        self.assertNotIn("[input] 레벨 파일", out)
        self.assertNotIn("[decode]", out)
        self.assertFalse(os.path.exists(self.p("out", "TestGame_viewer.html")))
        self.assertFalse(os.path.exists(self.p("out", "TestGame_levels_decoded.zip")))

    def test_stages_split_produce_the_same_files_as_one_run(self):
        """나눠 돌린 결과가 통짜 실행과 같은 파일을 낸다."""
        whole = self.p("whole")
        self.run_pipeline(out_dir=whole)
        split = self.p("split")
        self.run_pipeline(only="zip", out_dir=split)
        self.run_pipeline(only="html", out_dir=split)

        for name in ("TestGame_viewer.html", "TestGame_levels_decoded.zip"):
            with self.subTest(name=name):
                self.assertTrue(os.path.exists(os.path.join(split, name)))
        with zipfile.ZipFile(os.path.join(whole, "TestGame_levels_decoded.zip")) as a, \
             zipfile.ZipFile(os.path.join(split, "TestGame_levels_decoded.zip")) as b:
            self.assertEqual(sorted(a.namelist()), sorted(b.namelist()))
            self.assertEqual(a.read("levels/set1/2.json"), b.read("levels/set1/2.json"))
