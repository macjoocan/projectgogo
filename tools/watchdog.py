"""메모리 상한을 걸고 levelscope 명령을 돌린다 — PC 가 멈추는 대신 프로세스만 죽는다.

이 도구가 있는 이유. 2026-08-14 에 추출 작업이 커밋 54~81GB 까지 올라가 이 PC 가 세 번
멈췄다. 원인(번들 bytes 누적)은 v1.21.0 에서 고쳤고 지금 실측 피크는 4~4.5GB 지만,
**도구 자체에는 상한이 없다.** 처음 보는 게임이 지금까지 본 것보다 훨씬 크면 다시 같은
일이 날 수 있다. 그때 PC 를 멈추는 대신 프로세스만 죽게 하는 것이 이 스크립트다.

    py tools\\watchdog.py --cap 6 -- survey --input <apk>
    py tools\\watchdog.py --cap 6 -- run --config configs/zenmatch.yaml --input <apk> --out out
    py tools\\watchdog.py --cap 8 --tree -- sprites --input <apk> --out out --split

`--` 뒤는 `python -m levelscope` 에 그대로 넘어간다. 상한을 넘으면 즉시 죽이고, 어디까지
갔는지·무엇을 하던 중이었는지 남긴다. 안 넘으면 최고 커밋만 찍고 조용히 끝난다.

**`--tree` 는 `--split` 처럼 자식 프로세스를 띄우는 경우에 쓴다.** 기본은 대상 프로세스
하나만 본다(자식 합산이 필요 없고 더 싸다).

재는 값은 **커밋(private commit, `PagefileUsage`)** 이다. 작업 관리자의 "커밋 크기" 와
같은 값이고, 이 PC 가 멈춘 기준도 이것이었다(물리 메모리가 아니라 커밋 한도).

측정만 하고 싶을 때는 `--cap` 을 넉넉히(예: 100) 주면 감시 없이 피크만 재는 셈이 된다.

참고: 오늘의 측정 결론(어디서 메모리가 드는지, 무엇이 효과 없었는지)은 `CLAUDE.md` 의
"메모리 피크는 가장 큰 번들 하나를 여는 값이다" 항목과 `CHANGELOG.md` v1.21.0~v1.26.1 에
수치와 함께 남겨 두었다. 일회성 진단 스크립트는 결론만 남기고 정리했다.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: 샘플 간격(초). 0.3 이면 4GB 급 작업에서 수백 표본이라 피크를 놓치지 않는다.
INTERVAL = 0.3
#: 이 폭만큼 늘 때마다 한 줄 찍는다(GB)
STEP_GB = 0.5


class _PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD)] + [
        (n, ctypes.c_size_t) for n in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]


class _PE(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", ctypes.c_char * 260)]


_K32 = ctypes.WinDLL("kernel32", use_last_error=True)
_PSAPI = ctypes.WinDLL("psapi")
_PROCESS_QUERY = 0x1000 | 0x0010          # QUERY_INFORMATION | VM_READ
_SNAP_PROCESS = 0x00000002


def _commit_of(pid):
    """한 프로세스의 커밋(GB). 못 읽으면 0.0 (이미 죽은 프로세스 등)."""
    h = _K32.OpenProcess(_PROCESS_QUERY, False, pid)
    if not h:
        return 0.0
    try:
        m = _PMC()
        m.cb = ctypes.sizeof(_PMC)
        if not _PSAPI.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb):
            return 0.0
        return m.PagefileUsage / 2**30
    finally:
        _K32.CloseHandle(h)


def _children_map():
    """{부모 pid: [자식 pid…]} — 스냅샷 한 번."""
    snap = _K32.CreateToolhelp32Snapshot(_SNAP_PROCESS, 0)
    if snap in (0, -1):
        return {}
    out = {}
    try:
        pe = _PE()
        pe.dwSize = ctypes.sizeof(_PE)
        if _K32.Process32First(snap, ctypes.byref(pe)):
            while True:
                out.setdefault(pe.th32ParentProcessID, []).append(pe.th32ProcessID)
                if not _K32.Process32Next(snap, ctypes.byref(pe)):
                    break
    finally:
        _K32.CloseHandle(snap)
    return out


def tree_commit(root_pid):
    """root_pid 와 그 자손 전체의 커밋 합계(GB)."""
    kids = _children_map()
    seen, stack, total = set(), [root_pid], 0.0
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        stack.extend(kids.get(pid, ()))
        total += _commit_of(pid)
    return total


def _kill_tree(pid):
    """대상과 자손을 죽인다. taskkill 이 가장 확실하다."""
    subprocess.call(["taskkill", "/PID", str(pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(cap_gb, argv, tree=False, log=print):
    """`python -m levelscope <argv>` 를 상한 아래에서 돌린다. (종료코드, 최고커밋)."""
    cmd = [sys.executable, "-m", "levelscope", *argv]
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    log(f"[watchdog] 상한 {cap_gb:.1f}GB · {'프로세스 트리' if tree else '단일 프로세스'} 감시")
    log(f"[watchdog] > levelscope {' '.join(argv)}")
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env)

    peak = [0.0]
    killed = [False]
    t0 = time.time()

    def watch():
        last = 0.0
        while proc.poll() is None:
            cur = tree_commit(proc.pid) if tree else _commit_of(proc.pid)
            if cur > peak[0]:
                peak[0] = cur
            if cur - last >= STEP_GB:
                last = cur
                log(f"[watchdog] +{time.time() - t0:5.0f}s  커밋 {cur:5.2f}GB")
            if cur > cap_gb:
                killed[0] = True
                log(f"\n[watchdog] !! 커밋 {cur:.2f}GB > 상한 {cap_gb:.1f}GB — 중단합니다")
                log("[watchdog]    PC 가 멈추는 것을 막기 위해 프로세스를 죽였습니다.")
                log("[watchdog]    상한을 올리려면 --cap, 작업을 쪼개려면 --source 나 --split.")
                _kill_tree(proc.pid)
                return
            time.sleep(INTERVAL)

    th = threading.Thread(target=watch, daemon=True)
    th.start()
    rc = proc.wait()
    th.join(timeout=2)

    log(f"\n[watchdog] 최고 커밋 {peak[0]:.2f}GB · 경과 {time.time() - t0:.0f}s"
        + (" · 상한 초과로 중단됨" if killed[0] else ""))
    return (9 if killed[0] else rc), peak[0]


def main():
    if os.name != "nt":
        sys.exit("이 스크립트는 Windows 전용입니다 (커밋 측정에 psapi/toolhelp 를 씁니다).")
    ap = argparse.ArgumentParser(
        description="메모리 상한을 걸고 levelscope 명령을 실행한다",
        epilog="예: py tools/watchdog.py --cap 6 -- run --config configs/zenmatch.yaml "
               "--input game.xapk --out out")
    ap.add_argument("--cap", type=float, default=6.0,
                    help="커밋 상한(GB). 넘으면 즉시 중단. 기본 6 "
                         "(실측 피크가 4~4.5GB 라 그 위 여유값)")
    ap.add_argument("--tree", action="store_true",
                    help="자식 프로세스까지 합산해서 본다 (--split 을 쓸 때)")
    ap.add_argument("rest", nargs=argparse.REMAINDER,
                    help="-- 뒤에 levelscope 명령을 그대로 적는다")
    a = ap.parse_args()

    argv = a.rest[1:] if a.rest and a.rest[0] == "--" else a.rest
    if not argv:
        ap.error("실행할 levelscope 명령이 없습니다. 예: --cap 6 -- survey --input game.xapk")

    rc, _peak = run(a.cap, argv, tree=a.tree)
    sys.exit(rc)


if __name__ == "__main__":
    main()
