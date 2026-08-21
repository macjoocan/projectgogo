r"""tools/watchdog.py — 상한 감시가 실제로 값을 보고 있는지.

**왜 이 파일이 있나.** 2026-08-22 에 watchdog 이 `최고 커밋 0.00GB` 를 보고했다.
가상환경의 `.venv\Scripts\python.exe` 가 리다이렉터 스텁이라 실제 작업은 손자
프로세스가 하는데, 기본값이 '대상 프로세스 하나만' 이어서 스텁의 1MB 만 재고 있었다.
상한이 영원히 발동하지 않는, 있는 척만 하는 감시였다. 그 회귀를 막는다.
"""
import importlib.util
import inspect
import os
import subprocess
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if os.name == "nt":                       # 커밋 측정에 psapi/toolhelp 를 쓴다
    _spec = importlib.util.spec_from_file_location(
        "_test_watchdog", os.path.join(ROOT, "tools", "watchdog.py"))
    wd = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(wd)
else:
    wd = None


@unittest.skipUnless(os.name == "nt", "watchdog 은 Windows 전용")
class Defaults(unittest.TestCase):
    def test_run_measures_the_tree_by_default(self):
        """기본이 트리 합산이어야 한다 — 아니면 venv 에서 상한이 안 먹는다."""
        self.assertIs(inspect.signature(wd.run).parameters["tree"].default, True)

    def test_step_and_interval_are_fine_enough_to_catch_a_spike(self):
        self.assertLessEqual(wd.INTERVAL, 0.5)
        self.assertLessEqual(wd.STEP_GB, 1.0)


@unittest.skipUnless(os.name == "nt", "watchdog 은 Windows 전용")
class SeesRealAllocation(unittest.TestCase):
    """스텁이 한 겹 끼어 있어도 트리 합산은 실제 할당을 봐야 한다."""

    MB = 300

    def test_tree_commit_sees_the_allocation(self):
        # stdout 으로 동기화하지 않는다 — 스텁이 한 겹 끼면 파이프가 안 잡힌다.
        # 값이 올라오는 것 자체가 준비 신호이므로 폴링한다.
        code = "b=bytearray(%d*1024*1024)\nimport time\ntime.sleep(15)\n" % self.MB
        child = subprocess.Popen([sys.executable, "-c", code])
        try:
            want = (self.MB / 1024) * 0.8            # 여유 20%
            tree = single = 0.0
            for _ in range(100):                     # 최대 10초
                tree = wd.tree_commit(child.pid)
                single = wd._commit_of(child.pid)
                if tree > want:
                    break
                time.sleep(0.1)
            self.assertGreater(
                tree, want, f"트리 합산이 할당({self.MB}MB)을 못 봤다: {tree:.3f}GB")
            self.assertGreaterEqual(tree, single)    # 트리는 자기 자신을 포함한다
        finally:
            child.kill()
            child.wait()

    def test_missing_process_reads_zero_not_crash(self):
        self.assertEqual(wd._commit_of(0x7FFFFFF0), 0.0)
