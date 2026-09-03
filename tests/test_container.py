"""컨테이너 추상화 — 폴더/zip/apk/xapk/obb/중첩 apk."""
import os
import tempfile
import unittest

from levelscope import container

from .helpers import apk_with_levels, jbytes, level, make_zip_bytes, write_tree, write_zip


class Tmp(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def p(self, *parts):
        return os.path.join(self.tmp, *parts)


class AsList(unittest.TestCase):
    def test_normalizes(self):
        self.assertEqual(container.as_list(None), [])
        self.assertEqual(container.as_list("a"), ["a"])
        self.assertEqual(container.as_list(["a", "b"]), ["a", "b"])


class DirContainerTest(Tmp):
    def test_names_and_glob(self):
        write_tree(self.tmp, {"assets/Levels/s1/1.json": jbytes(level(1)),
                              "assets/Levels/s1/2.json": jbytes(level(2)),
                              "assets/other.txt": b"x"})
        c = container.DirContainer(self.tmp)
        self.assertIn("assets/Levels/s1/1.json", c.names())
        self.assertEqual(len(c.glob("assets/Levels/*/*.json")), 2)
        self.assertEqual(c.read("assets/other.txt"), b"x")

    def test_glob_accepts_list_and_dedupes(self):
        write_tree(self.tmp, {"a/1.json": b"{}", "b/2.json": b"{}"})
        c = container.DirContainer(self.tmp)
        hits = c.glob(["a/*.json", "b/*.json", "a/*.json"])
        self.assertEqual(hits, ["a/1.json", "b/2.json"])

    def test_glob_suffix_fallback(self):
        """apk 기준 경로를 해제본(접두어 한 단계 추가)에도 그대로 쓸 수 있다."""
        write_tree(self.tmp, {"base/assets/Levels/s1/1.json": b"{}"})
        c = container.DirContainer(self.tmp)
        self.assertEqual(c.glob("assets/Levels/*/*.json"), ["base/assets/Levels/s1/1.json"])
        self.assertEqual(c.glob("assets/Levels/s1/1.json"), ["base/assets/Levels/s1/1.json"])


class ZipContainerTest(Tmp):
    def test_zip_glob(self):
        z = write_zip(self.p("a.apk"), {"assets/Levels/s1/1.json": b"{}", "x": b"y"})
        with container.open_root(z) as c:
            self.assertIsInstance(c, container.ZipContainer)
            self.assertEqual(c.glob("assets/Levels/*/*.json"), ["assets/Levels/s1/1.json"])
            self.assertEqual(c.label, "a.apk")

    def test_directory_entries_excluded(self):
        import zipfile
        p = self.p("d.zip")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("dir/", b"")
            z.writestr("dir/f.json", b"{}")
        with container.open_root(p) as c:
            self.assertEqual(c.names(), ["dir/f.json"])


class OpenRoot(Tmp):
    def test_missing_path(self):
        with self.assertRaises(FileNotFoundError):
            container.open_root(self.p("nope.apk"))

    def test_not_an_archive(self):
        p = self.p("plain.bin")
        with open(p, "wb") as f:
            f.write(b"not a zip")
        with self.assertRaises(container.UnsupportedInput):
            container.open_root(p)


class NestedNames(unittest.TestCase):
    def test_base_apk_first_then_obb(self):
        names = ["Android/obb/main.obb", "config.arm64_v8a.apk", "base.apk", "icon.png"]
        self.assertEqual(container.nested_names(names),
                         ["base.apk", "config.arm64_v8a.apk", "Android/obb/main.obb"])

    def test_ignores_non_archives(self):
        self.assertEqual(container.nested_names(["a.png", "b.json"]), [])


class IterContainers(Tmp):
    def test_xapk_with_nested_apk(self):
        xapk = write_zip(self.p("app.xapk"), {"base.apk": apk_with_levels([1, 2, 3]),
                                             "manifest.json": b"{}"})
        labels, hits = [], []
        for c in container.iter_containers(xapk):
            with c:
                labels.append(c.label)
                hits.append(len(c.glob("assets/Levels/*/*.json")))
        self.assertEqual(labels, ["app.xapk", "app.xapk!base.apk"])
        self.assertEqual(hits, [0, 3])

    def test_obb_is_scanned(self):
        """구버전이 놓쳤던 경로 — 레벨이 obb 안에 있는 배포."""
        xapk = write_zip(self.p("app.xapk"),
                         {"base.apk": make_zip_bytes({"classes.dex": b"x"}),
                          "Android/obb/main.1.obb": apk_with_levels([1, 2, 3, 4])})
        found = {}
        for c in container.iter_containers(xapk):
            with c:
                n = len(c.glob("assets/Levels/*/*.json"))
                if n:
                    found[c.label] = n
        self.assertEqual(found, {"app.xapk!Android/obb/main.1.obb": 4})

    def test_unpacked_xapk_folder_finds_nested_obb(self):
        """XAPK 해제 폴더 — obb가 하위 폴더에 있어도 훑는다 (구버전은 최상위만 봤다)."""
        os.makedirs(self.p("Android", "obb"), exist_ok=True)
        write_zip(self.p("base.apk"), {"classes.dex": b"x"})
        write_zip(self.p("Android", "obb", "main.obb"), {"assets/Levels/s1/7.json": b"{}"})
        found = {}
        for c in container.iter_containers(self.tmp):
            with c:
                n = len(c.glob("assets/Levels/*/*.json"))
                if n:
                    found[os.path.basename(c.label)] = n
        self.assertEqual(found, {"main.obb": 1})

    def test_broken_nested_archive_skipped(self):
        xapk = write_zip(self.p("app.xapk"), {"base.apk": b"garbage not zip",
                                             "good.apk": apk_with_levels([1])})
        labels = []
        for c in container.iter_containers(xapk):
            with c:
                labels.append(c.label)
        self.assertNotIn("app.xapk!base.apk", labels)
        self.assertIn("app.xapk!good.apk", labels)

    def test_folder_root_yielded_first(self):
        write_tree(self.tmp, {"assets/Levels/s1/1.json": b"{}"})
        first = next(container.iter_containers(self.tmp))
        # 이어붙인 번들을 펼치는 ConcatView 로 감싸서 나온다 (`concat` 모듈 참고).
        self.assertIsInstance(first, container.ConcatView)
        self.assertIsInstance(first.inner, container.DirContainer)


class FindFirst(Tmp):
    def test_finds_in_nested_apk(self):
        xapk = write_zip(self.p("app.xapk"),
                         {"base.apk": make_zip_bytes({"assets/bin/Data/data.unity3d": b"UNITY"})})
        data, label = container.find_first(xapk, ["assets/bin/Data/data.unity3d"])
        self.assertEqual(data, b"UNITY")
        self.assertIn("base.apk", label)

    def test_missing_returns_none(self):
        xapk = write_zip(self.p("app.xapk"), {"base.apk": make_zip_bytes({"a": b"b"})})
        self.assertEqual(container.find_first(xapk, ["nope"]), (None, None))


if __name__ == "__main__":
    unittest.main()
