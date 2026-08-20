"""split — 소스마다 별 프로세스로 돌리는 드라이버.

실제 프로세스를 띄우지 않는다. 검사 대상은 우리 쪽 로직이다 —
소스 목록·Unity 버전 헤더 파싱, 산출물 꼬리표, 자식에게 넘기는 인자.
"""
import types
import unittest
from unittest import mock

from levelscope import split


def _proc(stdout="", returncode=0, stderr=""):
    return types.SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)


class TagOf(unittest.TestCase):
    def test_strips_known_extensions(self):
        self.assertEqual(split.tag_of("assets/aa/Android/theme_assets_all.bundle"),
                         "theme_assets_all")
        self.assertEqual(split.tag_of("assets/bin/Data/data.unity3d"), "data")
        self.assertEqual(split.tag_of("area01.ab"), "area01")

    def test_keeps_extensionless_names(self):
        """확장자 없는 번들이 실제로 있다 (Play Asset Delivery 팩)."""
        self.assertEqual(split.tag_of("assets/ContentArchives/66697af186f695d5"),
                         "66697af186f695d5")

    def test_sanitizes_and_truncates(self):
        got = split.tag_of("a b/c(d)e" + "x" * 80 + ".bundle")
        self.assertLessEqual(len(got), 48)
        self.assertTrue(all(c.isalnum() or c in "-_" for c in got))

    def test_empty_name_still_gives_a_tag(self):
        self.assertTrue(split.tag_of(""))


class ListSources(unittest.TestCase):
    def test_parses_names_and_version_header(self):
        out = "#unity=6000.3.11f1\nassets/a.bundle\nassets/b.unity3d\n"
        with mock.patch("subprocess.run", return_value=_proc(out)):
            names, ver = split.list_sources("in.apk", log=lambda *_: None)
        self.assertEqual(names, ["assets/a.bundle", "assets/b.unity3d"])
        self.assertEqual(ver, "6000.3.11f1")

    def test_missing_version_header_is_fine(self):
        with mock.patch("subprocess.run", return_value=_proc("assets/a.bundle\n")):
            names, ver = split.list_sources("in.apk", log=lambda *_: None)
        self.assertEqual(names, ["assets/a.bundle"])
        self.assertIsNone(ver)

    def test_other_comment_lines_are_not_sources(self):
        with mock.patch("subprocess.run", return_value=_proc("# 메모\nassets/a.bundle\n")):
            names, _ver = split.list_sources("in.apk", log=lambda *_: None)
        self.assertEqual(names, ["assets/a.bundle"])

    def test_child_failure_reports_and_returns_empty(self):
        logs = []
        with mock.patch("subprocess.run", return_value=_proc("", 1, "boom\n")):
            names, ver = split.list_sources("in.apk", log=logs.append)
        self.assertEqual((names, ver), ([], None))
        self.assertTrue(any("실패" in m for m in logs))

    def test_oserror_does_not_escape(self):
        with mock.patch("subprocess.run", side_effect=OSError("no python")):
            self.assertEqual(split.list_sources("in.apk", log=lambda *_: None), ([], None))


class RunPerSource(unittest.TestCase):
    def _run(self, names, version, extra=(), rc=0):
        calls = []

        def fake_call(cmd, **_kw):
            calls.append(cmd)
            return rc

        with mock.patch.object(split, "list_sources", return_value=(names, version)), \
             mock.patch("subprocess.call", side_effect=fake_call):
            failed = split.run_per_source("sprites", "in.apk", "out", "G",
                                          extra=extra, log=lambda *_: None)
        return failed, calls

    def test_one_child_per_source_with_its_own_game_name(self):
        failed, calls = self._run(["a/x.bundle", "a/y.bundle"], None)
        self.assertEqual(failed, 0)
        self.assertEqual(len(calls), 2)
        self.assertIn("--source", calls[0])
        self.assertEqual(calls[0][calls[0].index("--source") + 1], "a/x.bundle")
        self.assertEqual(calls[0][calls[0].index("--game") + 1], "G__x")
        self.assertEqual(calls[1][calls[1].index("--game") + 1], "G__y")

    def test_version_is_passed_down(self):
        """소스를 하나만 받는 자식은 버전을 배울 데가 없다."""
        _failed, calls = self._run(["a/x.bundle"], "6000.3.11f1")
        self.assertEqual(calls[0][calls[0].index("--unity-version") + 1], "6000.3.11f1")

    def test_explicit_version_in_extra_is_not_overridden(self):
        _failed, calls = self._run(["a/x.bundle"], "6000.3.11f1",
                                   extra=["--unity-version", "2021.3.1f1"])
        self.assertEqual(calls[0].count("--unity-version"), 1)
        self.assertEqual(calls[0][calls[0].index("--unity-version") + 1], "2021.3.1f1")

    def test_duplicate_tags_get_distinct_output_names(self):
        """같은 이름의 번들이 여러 컨테이너에 있을 수 있다 — 산출물이 덮이면 안 된다."""
        _failed, calls = self._run(["a/data.unity3d", "b/data.unity3d"], None)
        got = [c[c.index("--game") + 1] for c in calls]
        self.assertEqual(len(set(got)), 2, got)

    def test_child_failures_are_counted(self):
        failed, _calls = self._run(["a/x.bundle", "a/y.bundle"], None, rc=1)
        self.assertEqual(failed, 2)

    def test_no_sources_is_reported_as_failure(self):
        logs = []
        with mock.patch.object(split, "list_sources", return_value=([], None)):
            failed = split.run_per_source("sprites", "in.apk", "out", "G", log=logs.append)
        self.assertEqual(failed, 1)
        self.assertTrue(any("소스가 없습니다" in m for m in logs))
