"""원 클릭 진입점 — APK 하나만 주면 알아서 끝까지 뽑는다.

팀원이 `analyze.bat` 에 apk/xapk 를 끌어다 놓으면 이게 돌아간다. 하는 일:

  1. 패키지명·앱 이름을 읽어 **어떤 게임인지 먼저 알려준다**
     (방치형이라고 생각한 파일이 매치3였던 일이 실제로 있었다)
  2. `configs/` 에 그 게임 설정이 이미 있으면 그걸 쓴다. 없으면 `fields: auto` 로
     임시 설정을 만들어 쓴다 — 장르를 몰라도 표가 나온다
  3. `survey` 로 규모를 먼저 보고(20초 남짓), **무거운 추출 전에 한 번 물어본다**
  4. 확인하면 **단계를 나눠** 추출 → `out_<게임>\\`

**왜 중간에 물어보나:** 큰 게임은 30분 넘게 돈다. 여유를 확인하고 사람이 한 번
승인하게 둔다. 여유가 모자라면 무엇을 닫아야 하는지 알려준다.

**왜 나눠 돌리나:** 레벨·스프라이트·에셋·계층을 한 프로세스에서 연달아 하면 앞
단계의 잔여와 다음 단계의 할당이 겹쳐 커밋 피크가 합쳐진다. 2026-08-22 에
PixelFlow 계층 단계에서 커밋이 100GB 를 넘겨 PC 가 응답을 멈춘 일이 있었다.
이제 단계마다 프로세스를 끊고 `tools/watchdog.py` 로 상한을 걸어, 넘으면 PC 가
아니라 그 단계만 죽는다. 앞 단계 산출물은 이미 디스크에 남아 있다.

직접 쓰려면:
    python tools/analyze.py <apk|xapk|폴더> [--out <폴더>] [--yes] [--dry-run]
                            [--cap <GB>] [--no-cap]
"""
import argparse
import io
import json
import os
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

#: 전체 추출에 필요한 커밋 여유(GB). 실측 피크가 4.3~4.5GB 라 안전분을 더한 값.
NEED_FREE_GB = 7.0

#: 단계별 커밋 상한(GB) 기본값. 넘으면 PC 가 아니라 그 단계 프로세스만 죽는다.
DEFAULT_CAP_GB = 6.0

#: 나눠 돌리는 단계 — (표시 이름, `run --only` 값).
#:
#: **한 프로세스에 몰지 않는 이유.** 앞 단계의 잔여 메모리와 다음 단계의 할당이 겹쳐
#: 커밋 피크가 합쳐진다(CookieRun 실측: 스프라이트 직후 3.63GB 가 남은 채 에셋을
#: 시작해 5.50GB). 단계마다 프로세스를 끊으면 피크가 '가장 무거운 단계 하나' 로
#: 내려가고, 한 단계가 폭주해도 나머지 산출물은 이미 디스크에 있다.
STAGES = (
    ("레벨 표·뷰어·JSON", "xlsx,html,zip"),
    ("스프라이트", "sprites"),
    ("사운드·머티리얼·폰트·Spine", "assets"),
    ("씬·프리팹 계층", "hierarchy"),
)


def force_utf8_output():
    """한국어 Windows 콘솔(cp949)에서 '—' 같은 문자로 죽는 것을 막는다.

    `levelscope.cli` 에 같은 함수가 있지만 여기서 다시 쓴다 — 이 스크립트는 진입점이라
    levelscope 임포트가 깨진 상황에서도 안내 문구를 찍어야 한다. 자식 프로세스는
    `run_cli` 가 `PYTHONIOENCODING` 으로 따로 처리한다.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def load_watchdog():
    """`tools/watchdog.py` 모듈. 쓸 수 없으면 None.

    **경로로 직접 읽는다.** `import watchdog` 은 PyPI 의 동명 패키지(파일시스템 감시)를
    잡을 수 있는데, 그쪽에는 `run(cap, argv)` 가 없어 조용히 엉뚱하게 동작한다.
    커밋 측정에 psapi/toolhelp 를 쓰므로 Windows 전용이다 — 아니면 상한 없이 돈다.
    """
    if os.name != "nt":
        return None
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watchdog.py")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_levelscope_watchdog", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod if hasattr(mod, "run") else None
    except Exception:  # noqa: BLE001 - 감시는 선택 사항이다. 없으면 그냥 돈다
        return None


def config_outputs(cfg_path):
    """설정의 `outputs` 목록. 못 읽으면 None.

    설정에 없는 단계를 헛돌리지 않기 위해 미리 본다 — `run --only hierarchy` 는
    설정에 hierarchy 가 없으면 오류로 끝나는데, 그건 실패가 아니라 '할 일이 없음' 이다.
    """
    try:
        from levelscope import cli      # ROOT 는 모듈 최상단에서 sys.path 에 넣었다
        return list(cli._load_config(cfg_path).get("outputs") or ["xlsx", "html"])
    except SystemExit:                     # 설정 형식 오류는 run 이 다시 보고한다
        raise
    except Exception:  # noqa: BLE001 - PyYAML 이 없거나 읽기 실패. 전 단계를 시도한다
        return None


def plan_stages(cfg_path, log=print):
    """이 설정으로 실제 만들 수 있는 단계만 골라 돌려준다."""
    outputs = config_outputs(cfg_path)
    if outputs is None:
        log("[i] 설정의 outputs 를 미리 읽지 못해 모든 단계를 시도합니다.")
        return list(STAGES)
    stages, skipped = [], []
    for label, only in STAGES:
        if any(o in outputs for o in only.split(",")):
            stages.append((label, only))
        else:
            skipped.append(label)
    if skipped:
        log(f"단계     : {len(stages)}개 실행 · 설정에 없어 제외 — {', '.join(skipped)}")
    return stages


def app_info(path):
    """(패키지 후보 목록, 앱 이름, 내부 apk 목록).

    패키지를 두 곳에서 모은다. `manifest.json`(XAPK)이 있으면 거기서, 없으면
    **내부 apk 파일 이름**에서 — APKS 래퍼는 manifest 가 없는 대신
    `assets/apks/com.dreamgames.royalkingdom.apk` 처럼 이름에 패키지가 들어 있다.
    """
    if os.path.isdir(path):
        return [], None, []
    pkgs, name, inner = [], None, []
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            inner = [n for n in names if n.lower().endswith(".apk")]
            if "manifest.json" in names:
                m = json.loads(z.read("manifest.json"))
                if m.get("package_name"):
                    pkgs.append(m["package_name"])
                name = m.get("name")
            for n in inner:
                stem = os.path.splitext(os.path.basename(n))[0]
                if stem.count(".") >= 2 and not stem.lower().startswith(("config", "split")):
                    pkgs.append(stem)
    except Exception:  # noqa: BLE001 - 못 읽어도 진행은 가능하다
        pass
    return pkgs, name, inner


def find_config(packages, app_name):
    """설정을 고른다. **패키지명 완전 일치만** 인정한다. 없으면 None.

    예전에는 이름을 느슨하게 부분일치시켰는데, 그러면 Zen Match("Zen Match")가
    `royalmatch.yaml` 에 걸렸다 — "match" 가 "royalmatch" 안에 있기 때문이다.
    엉뚱한 설정으로 뽑히면 산출물이 조용히 틀리므로, 근거가 확실한 패키지명만 쓴다.
    설정은 `package:` 로 자기 패키지를 밝힌다(문자열 또는 목록).
    """
    cfg_dir = os.path.join(ROOT, "configs")
    if not os.path.isdir(cfg_dir) or not packages:
        return None
    try:
        import yaml
    except ImportError:
        return None
    want = {p.lower() for p in packages if p}
    for fn in sorted(os.listdir(cfg_dir)):
        if not fn.endswith(".yaml") or fn.startswith(("_", "template")):
            continue
        path = os.path.join(cfg_dir, fn)
        try:
            cfg = yaml.safe_load(io.open(path, encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001 - 깨진 설정은 건너뛴다
            continue
        decl = cfg.get("package")
        decl = [decl] if isinstance(decl, str) else (decl or [])
        if any(str(d).lower() in want for d in decl):
            return path
    return None


def temp_config(out_dir, game):
    """설정이 없는 게임용 임시 설정 — 장르를 몰라도 되는 최소 구성."""
    path = os.path.join(out_dir, f"_auto_{game}.yaml")
    io.open(path, "w", encoding="utf-8", newline="\n").write(
        f"""# tools/analyze.py 가 자동 생성한 임시 설정입니다.
# 쓸 만하면 configs/{game}.yaml 로 옮기고 다듬어 주세요.
game: {game}

input:
  levels_glob: "assets/**/*.json"     # 레벨이 어디 있는지 모를 때의 기본값
  set_from: parent_dir
  level_id_from: stem

codec: auto
fields: auto            # 표본에서 컬럼 자동 추론 — 장르를 몰라도 표가 나온다

sprites:
  sources: auto
  types: [Sprite, Texture2D]
  max_count: 40000
  categorize: true      # 이름 앞에 분류를 붙여 만 장도 훑을 수 있게

assets:
  sources: auto
  max_count: 40000

hierarchy:
  sources: auto
  fields: full
  max_nodes: 300000

# 보드형(퍼즐·매치3) 게임이면 board/palette 를 채우고 outputs 에 html 을 넣으세요.
outputs: [xlsx, zip, sprites, assets, hierarchy]
""")
    return path


def free_commit_gb():
    """커밋 여유(GB). 못 재면 None."""
    try:
        import ctypes
        import ctypes.wintypes as wt

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", wt.DWORD), ("dwMemoryLoad", wt.DWORD),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            return None
        return m.ullAvailPageFile / 2**30
    except Exception:  # noqa: BLE001 - 못 재면 경고 없이 진행
        return None


def hogs():
    """메모리를 많이 쓰는 프로세스 이름 — 무엇을 닫으라고 알려주기 위해."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Where-Object {$_.PagedMemorySize64 -gt 1GB} | "
             "Sort-Object PagedMemorySize64 -Descending | "
             "Select-Object -First 5 ProcessName,"
             "@{n='GB';e={[math]::Round($_.PagedMemorySize64/1GB,1)}} | "
             "ConvertTo-Json -Compress"],
            capture_output=True, text=True, encoding="utf-8", timeout=30)
        data = json.loads(out.stdout or "[]")
        if isinstance(data, dict):
            data = [data]
        return [(d.get("ProcessName"), d.get("GB")) for d in data]
    except Exception:  # noqa: BLE001
        return []


def run_cli(args, log=print):
    cmd = [sys.executable, "-m", "levelscope", *args]
    log("\n> " + " ".join(cmd[2:]) + "\n")
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.call(cmd, cwd=ROOT, env=env)


def main():
    force_utf8_output()
    ap = argparse.ArgumentParser(description="APK 하나로 끝까지 뽑는다")
    ap.add_argument("input", help="apk / xapk / obb / 압축 푼 폴더")
    ap.add_argument("--out", default=None, help="기본: <입력 폴더>\\out_<게임>")
    ap.add_argument("--yes", action="store_true", help="확인 없이 전체 추출까지 진행")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 할지만 보여주고 끝낸다")
    ap.add_argument("--cap", type=float, default=DEFAULT_CAP_GB,
                    help=f"단계별 커밋 상한(GB, 기본 {DEFAULT_CAP_GB:g}). 넘으면 PC 가 "
                         "멈추는 대신 그 단계만 중단된다")
    ap.add_argument("--no-cap", action="store_true",
                    help="상한 없이 돌린다 (권장하지 않음 — 과거에 PC 가 멈춘 이력이 있다)")
    a = ap.parse_args()

    src = os.path.abspath(a.input)
    if not os.path.exists(src):
        sys.exit(f"입력을 찾을 수 없습니다: {src}")

    pkgs, name, inner = app_info(src)
    print("=" * 66)
    print(f"입력   : {src}")
    print(f"크기   : {os.path.getsize(src) / 2**20:.0f}MB" if os.path.isfile(src) else "크기   : (폴더)")
    print(f"앱     : {name or '(manifest 없음)'}"
          + (f"  ({', '.join(pkgs)})" if pkgs else ""))
    if inner:
        print(f"내부   : {', '.join(os.path.basename(x) for x in inner[:4])}")
    print("=" * 66)

    game = None
    cfg = find_config(pkgs, name)
    if cfg:
        print(f"설정   : {os.path.relpath(cfg, ROOT)} (기존 설정을 씁니다)")
    else:
        base = (name or (pkgs[0] if pkgs else None)
                or os.path.splitext(os.path.basename(src))[0])
        game = "".join(c for c in base if c.isalnum()) or "UnknownGame"
        print(f"설정   : 없음 → fields: auto 임시 설정을 만들어 씁니다 (게임명 {game})")

    out = a.out or os.path.join(os.path.dirname(src),
                                f"out_{(game or os.path.splitext(os.path.basename(cfg))[0]).lower()}")
    print(f"산출물 : {out}")

    free = free_commit_gb()
    if free is not None:
        print(f"메모리 : 커밋 여유 {free:.1f}GB (전체 추출에 {NEED_FREE_GB:.0f}GB 권장)")
        if free < NEED_FREE_GB:
            print("\n!! 여유가 모자랍니다. 아래를 닫고 다시 실행하세요:")
            for n, gb in hogs():
                print(f"     {n}  {gb}GB")
            print("   (Unity 에디터·ComfyUI·WSL 이 흔한 원인입니다. WSL 은 `wsl --shutdown`)")

    cap = None if a.no_cap else a.cap
    wd = load_watchdog() if cap else None
    if cap and wd is None:
        print("[i] 메모리 상한을 걸 수 없습니다(watchdog 사용 불가) — 상한 없이 돕니다.")
        cap = None
    print("상한   : " + (f"단계별 {cap:.1f}GB — 넘으면 PC 가 아니라 그 단계만 중단"
                         if cap else "없음 (--no-cap)"))

    if a.dry_run:
        # 무엇을 할지 보여주는 게 목적이니 단계 계획까지 보여준다. 설정이 없는
        # 게임은 임시 설정을 만들어야 알 수 있으므로 기본 단계 목록을 보여준다.
        stages = plan_stages(cfg) if cfg else list(STAGES)
        print(f"\n단계   : {len(stages)}개로 나눠 돕니다"
              + ("" if cfg else " (임시 설정 기준 예상)"))
        for i, (label, only) in enumerate(stages, 1):
            print(f"   [{i}/{len(stages)}] {label}   → run --only {only}")
        print("\n--dry-run 이라 여기서 끝냅니다.")
        return

    os.makedirs(out, exist_ok=True)
    if not cfg:
        cfg = temp_config(out, game)
        print(f"임시 설정 생성: {cfg}")

    stages = plan_stages(cfg)

    print("\n[survey] 규모·구조 먼저 봅니다 (20초 남짓, 메모리 1GB 안팎)")
    if run_cli(["survey", "--input", src, "--configs", os.path.join(ROOT, "configs")]) != 0:
        print("\n!! survey 가 실패했습니다. 위 로그를 확인하세요.")
        sys.exit(1)

    if not a.yes:
        print("\n" + "-" * 66)
        print(f"추출은 {len(stages)}단계로 나눠 돕니다. 게임 크기에 따라 몇 분~30분.")
        print("단계마다 프로세스를 끊으므로 한 단계가 실패해도 앞 산출물은 남습니다.")
        try:
            if input("계속할까요? (y/N) ").strip().lower() not in ("y", "yes"):
                print("여기서 멈췄습니다. survey 결과만 보셔도 규모는 파악됩니다.")
                return
        except EOFError:
            print("입력을 받을 수 없어 멈췄습니다. 전체 추출은 --yes 로 실행하세요.")
            return

    # 단계를 하나씩. 실패해도 다음 단계는 계속한다 — 단계끼리 서로 쓰지 않는다.
    results = []
    for i, (label, only) in enumerate(stages, 1):
        print("\n" + "-" * 66)
        print(f"[{i}/{len(stages)}] {label}")
        argv = ["run", "--config", cfg, "--input", src, "--out", out, "--only", only]
        if cap and wd:
            rc, peak = wd.run(cap, argv)
            print(f"[{label}] 최고 커밋 {peak:.2f}GB")
        else:
            rc = run_cli(argv)
        results.append((label, rc))
        if rc == 9:
            print(f"\n!! '{label}' 이 상한 {cap:.1f}GB 를 넘어 중단됐습니다. PC 는 안전합니다.")
            print("   --cap 을 올리거나, 이 단계를 `--source`/`--split` 으로 쪼개세요.")

    print("\n" + "=" * 66)
    bad = [(label, rc) for label, rc in results if rc != 0]
    if not bad:
        print(f"완료: {out}")
    else:
        print(f"단계 {len(results)}개 중 {len(bad)}개 실패:")
        for label, rc in bad:
            why = f"상한 초과로 중단(종료코드 {rc})" if rc == 9 else f"종료코드 {rc}"
            print(f"   - {label}: {why}")
        print(f"   나머지 산출물은 {out} 에 있습니다. "
              f"자세한 사유는 {os.path.join(out, '*_errors.txt')}.")
    print("=" * 66)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
