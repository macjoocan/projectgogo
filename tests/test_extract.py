"""레벨 수집 — glob 복수 패턴, 세트/id 규칙, 컨테이너 선택·병합."""
import os
import tempfile
import unittest

from levelscope import extract

from .helpers import apk_with_levels, jbytes, level, make_zip_bytes, write_tree, write_zip


class Tmp(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def p(self, *parts):
        return os.path.join(self.tmp, *parts)


class SetAndId(unittest.TestCase):
    def test_parent_dir_and_stem(self):
        s, lid = extract._set_and_id("assets/Levels/3db5/12.json", {})
        self.assertEqual((s, lid), ("3db5", 12))

    def test_non_numeric_id_stays_string(self):
        _s, lid = extract._set_and_id("a/b/intro.json", {})
        self.assertEqual(lid, "intro")

    def test_regex_rules(self):
        cfg = {"set_from": r"Levels/([^/]+)/", "level_id_from": r"lv(\d+)"}
        s, lid = extract._set_and_id("assets/Levels/setA/lv007.json", cfg)
        self.assertEqual((s, lid), ("setA", 7))

    def test_regex_miss_falls_back(self):
        cfg = {"set_from": r"nope/([^/]+)/", "level_id_from": r"nope(\d+)"}
        s, lid = extract._set_and_id("a/b/9.json", cfg)
        self.assertEqual((s, lid), ("", 9))


class CollectFiles(Tmp):
    def test_folder_single_pattern(self):
        write_tree(self.tmp, {"assets/Levels/s1/1.json": jbytes(level(1)),
                              "assets/Levels/s1/2.json": jbytes(level(2)),
                              "assets/Levels/s2/3.json": jbytes(level(3))})
        res = extract.collect_levels(self.tmp, {"levels_glob": "assets/Levels/*/*.json"})
        self.assertEqual(len(res.records), 3)
        self.assertEqual({r.set_name for r in res.records}, {"s1", "s2"})

    def test_multiple_patterns(self):
        write_tree(self.tmp, {"levels/a/1.json": b"{}", "extra/b/2.dat": b"{}"})
        res = extract.collect_levels(self.tmp,
                                     {"levels_glob": ["levels/*/*.json", "extra/*/*.dat"]})
        self.assertEqual(len(res.records), 2)

    def test_picks_container_with_most_levels(self):
        xapk = write_zip(self.p("app.xapk"), {"base.apk": apk_with_levels([1, 2]),
                                             "config.apk": apk_with_levels([1, 2, 3, 4, 5])})
        res = extract.collect_levels(xapk, {"levels_glob": "assets/Levels/*/*.json"})
        self.assertEqual(len(res.records), 5)
        self.assertIn("config.apk", res.source)

    def test_merge_containers(self):
        xapk = write_zip(self.p("app.xapk"),
                         {"base.apk": apk_with_levels([1, 2], set_dir="s1"),
                          "config.apk": apk_with_levels([3, 4, 5], set_dir="s2")})
        cfg = {"levels_glob": "assets/Levels/*/*.json", "merge_containers": True}
        res = extract.collect_levels(xapk, cfg)
        self.assertEqual(len(res.records), 5)
        self.assertEqual({r.set_name for r in res.records}, {"s1", "s2"})

    def test_levels_in_obb(self):
        xapk = write_zip(self.p("app.xapk"),
                         {"base.apk": make_zip_bytes({"classes.dex": b"x"}),
                          "Android/obb/main.obb": apk_with_levels([1, 2, 3])})
        res = extract.collect_levels(xapk, {"levels_glob": "assets/Levels/*/*.json"})
        self.assertEqual(len(res.records), 3)
        self.assertIn("main.obb", res.source)

    def test_raw_bytes_are_readable_after_collect(self):
        """컨테이너를 닫아도 이미 읽은 원본은 남아 있어야 한다."""
        xapk = write_zip(self.p("app.xapk"), {"base.apk": apk_with_levels([1])})
        res = extract.collect_levels(xapk, {"levels_glob": "assets/Levels/*/*.json"})
        res.container.close()
        self.assertIn(b'"id"', res.records[0].raw)

    def test_missing_glob_raises_with_hint(self):
        write_tree(self.tmp, {"a.txt": b"x"})
        with self.assertRaises(FileNotFoundError) as cm:
            extract.collect_levels(self.tmp, {"levels_glob": "assets/Levels/*/*.json"})
        self.assertIn("levelscope ls", str(cm.exception))

    def test_no_config_raises(self):
        with self.assertRaises(extract.ConfigError):
            extract.collect_levels(self.tmp, {})


class TupleCompat(Tmp):
    def test_record_and_result_unpack(self):
        write_tree(self.tmp, {"L/s/1.json": jbytes(level(1))})
        res = extract.collect_levels(self.tmp, {"levels_glob": "L/*/*.json"})
        recs, cont, src = res                       # 구버전 3튜플 언팩
        self.assertEqual(len(recs), 1)
        self.assertIsNotNone(cont)
        self.assertTrue(src)
        s, lid, raw, source = recs[0]               # 구버전 4튜플 언팩
        self.assertEqual((s, lid), ("s", 1))
        self.assertIn(b"{", raw)
        self.assertTrue(source.endswith("1.json"))


class ReadFromContainer(Tmp):
    def test_container_and_glob(self):
        write_tree(self.tmp, {"assets/bin/Data/data.unity3d": b"UNITY", "L/s/1.json": b"{}"})
        res = extract.collect_levels(self.tmp, {"levels_glob": "L/*/*.json"})
        self.assertEqual(extract.read_from_container(res.container,
                                                    "assets/bin/Data/data.unity3d"), b"UNITY")
        self.assertEqual(extract.read_from_container(res.container,
                                                    "assets/bin/Data/*.unity3d"), b"UNITY")
        self.assertIsNone(extract.read_from_container(res.container, "nope"))
        self.assertIsNone(extract.read_from_container(None, "x"))

    def test_make_reader_falls_back_to_whole_input(self):
        """레벨은 obb, 팔레트는 base.apk 인 split 배포."""
        xapk = write_zip(self.p("app.xapk"),
                         {"base.apk": make_zip_bytes({"assets/bin/Data/data.unity3d": b"UNITY"}),
                          "Android/obb/main.obb": apk_with_levels([1, 2])})
        res = extract.collect_levels(xapk, {"levels_glob": "assets/Levels/*/*.json"})
        read = extract.make_reader(res, xapk)
        self.assertIsNone(extract.read_from_container(res.container, "assets/bin/Data/data.unity3d"))
        self.assertEqual(read("assets/bin/Data/data.unity3d"), b"UNITY")


class ListEntries(Tmp):
    def test_reports_counts(self):
        write_tree(self.tmp, {"a/1.json": b"{}", "a/2.json": b"{}", "b.txt": b"x"})
        out = extract.list_entries(self.tmp, ["a/*.json"])
        self.assertEqual(out[0][2], 2)


if __name__ == "__main__":
    unittest.main()
