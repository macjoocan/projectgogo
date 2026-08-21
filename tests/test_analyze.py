"""원 클릭 진입점(tools/analyze.py) — 단계 분할 계획과 watchdog 연결.

`tools/` 는 패키지가 아니므로 경로로 직접 읽는다.
"""
import importlib.util
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


analyze = _load("_test_analyze", "tools/analyze.py")


def has_yaml():
    return importlib.util.find_spec("yaml") is not None


class Stages(unittest.TestCase):
    """단계 목록 자체 — 여기가 곧 '무엇을 나눠 돌리는가' 다."""

    def test_every_stage_maps_to_known_outputs(self):
        from levelscope import cli
        for _label, only in analyze.STAGES:
            for name in only.split(","):
                with self.subTest(only=name):
                    self.assertIn(name, cli._ALL_OUTPUTS)

    def test_stages_cover_all_outputs_exactly_once(self):
        """빠진 산출물도, 두 단계에 걸친 산출물도 없어야 한다."""
        from levelscope import cli
        seen = [o for _l, only in analyze.STAGES for o in only.split(",")]
        self.assertEqual(sorted(seen), sorted(cli._ALL_OUTPUTS))
        self.assertEqual(len(seen), len(set(seen)))

    def test_heavy_stages_are_separate(self):
        """무거운 셋(sprites/assets/hierarchy)이 한 단계에 몰려 있지 않아야 한다."""
        for _label, only in analyze.STAGES:
            names = set(only.split(","))
            with self.subTest(only=only):
                self.assertLessEqual(len(names & {"sprites", "assets", "hierarchy"}), 1)


class PlanStages(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def write_cfg(self, body):
        path = os.path.join(self.tmp, "g.yaml")
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        return path

    @unittest.skipUnless(has_yaml(), "PyYAML 미설치")
    def test_reads_outputs(self):
        path = self.write_cfg("game: G\noutputs: [xlsx, sprites]\n")
        self.assertEqual(analyze.config_outputs(path), ["xlsx", "sprites"])

    @unittest.skipUnless(has_yaml(), "PyYAML 미설치")
    def test_defaults_when_outputs_absent(self):
        path = self.write_cfg("game: G\n")
        self.assertEqual(analyze.config_outputs(path), ["xlsx", "html"])

    @unittest.skipUnless(has_yaml(), "PyYAML 미설치")
    def test_plan_drops_stages_the_config_cannot_make(self):
        path = self.write_cfg("game: G\noutputs: [xlsx, sprites]\n")
        msgs = []
        stages = analyze.plan_stages(path, log=msgs.append)
        self.assertEqual([only for _l, only in stages], ["xlsx,html,zip", "sprites"])
        # 빠진 단계를 조용히 넘기지 않는다
        self.assertIn("제외", "\n".join(msgs))
        self.assertIn("계층", "\n".join(msgs))

    @unittest.skipUnless(has_yaml(), "PyYAML 미설치")
    def test_plan_is_quiet_when_nothing_dropped(self):
        path = self.write_cfg(
            "game: G\noutputs: [xlsx, html, zip, sprites, assets, hierarchy]\n")
        msgs = []
        stages = analyze.plan_stages(path, log=msgs.append)
        self.assertEqual(len(stages), len(analyze.STAGES))
        self.assertEqual(msgs, [])

    def test_unreadable_config_tries_every_stage(self):
        """설정을 못 읽으면 단계를 임의로 줄이지 않는다 — 줄이면 조용히 덜 뽑힌다."""
        msgs = []
        stages = analyze.plan_stages(os.path.join(self.tmp, "nope.yaml"),
                                     log=msgs.append)
        self.assertEqual(stages, list(analyze.STAGES))
        self.assertIn("모든 단계", "\n".join(msgs))


class Watchdog(unittest.TestCase):
    def test_loads_by_path_with_run(self):
        mod = analyze.load_watchdog()
        if os.name != "nt":
            self.assertIsNone(mod, "Windows 전용이라 다른 OS 에서는 None")
            return
        self.assertIsNotNone(mod, "tools/watchdog.py 를 못 읽었다")
        self.assertTrue(callable(mod.run))
        # PyPI 의 동명 패키지가 아니라 우리 파일을 읽었는지
        self.assertTrue(mod.__file__.endswith(os.path.join("tools", "watchdog.py")))

    def test_does_not_pollute_sys_modules_name(self):
        analyze.load_watchdog()
        self.assertNotIn("watchdog", sys.modules)


class Utf8Output(unittest.TestCase):
    def test_survives_being_called(self):
        analyze.force_utf8_output()          # 예외 없이 끝나야 한다
        print("em dash — ok", file=io.StringIO())


class Defaults(unittest.TestCase):
    def test_cap_is_above_measured_peak(self):
        """실측 피크 4.3~4.5GB 위에 있어야 정상 실행을 안 죽인다."""
        self.assertGreater(analyze.DEFAULT_CAP_GB, 4.5)
