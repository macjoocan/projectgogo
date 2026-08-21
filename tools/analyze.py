"""원 클릭 진입점 — APK 하나만 주면 알아서 끝까지 뽑는다.

팀원이 `analyze.bat` 에 apk/xapk 를 끌어다 놓으면 이게 돌아간다. 하는 일:

  1. 패키지명·앱 이름을 읽어 **어떤 게임인지 먼저 알려준다**
     (방치형이라고 생각한 파일이 매치3였던 일이 실제로 있었다)
  2. `configs/` 에 그 게임 설정이 이미 있으면 그걸 쓴다. 없으면 `fields: auto` 로
     임시 설정을 만들어 쓴다 — 장르를 몰라도 표가 나온다
  3. `survey` 로 규모를 먼저 보고(20초 남짓), **무거운 추출 전에 한 번 물어본다**
  4. 확인하면 전체 추출 → `out_<게임>\\`

**왜 중간에 물어보나:** 전체 추출은 메모리를 4~5GB 쓰고 큰 게임은 30분 넘게 돈다.
이 PC 에서 과거에 메모리 폭주로 작업이 멈춘 이력이 있어서, 여유를 확인하고 사람이
한 번 승인하게 둔다. 여유가 모자라면 무엇을 닫아야 하는지 알려준다.

직접 쓰려면:
    python tools/analyze.py <apk|xapk|폴더> [--out <폴더>] [--yes] [--dry-run]
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
    ap = argparse.ArgumentParser(description="APK 하나로 끝까지 뽑는다")
    ap.add_argument("input", help="apk / xapk / obb / 압축 푼 폴더")
    ap.add_argument("--out", default=None, help="기본: <입력 폴더>\\out_<게임>")
    ap.add_argument("--yes", action="store_true", help="확인 없이 전체 추출까지 진행")
    ap.add_argument("--dry-run", action="store_true", help="무엇을 할지만 보여주고 끝낸다")
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

    if a.dry_run:
        print("\n--dry-run 이라 여기서 끝냅니다.")
        return

    os.makedirs(out, exist_ok=True)
    if not cfg:
        cfg = temp_config(out, game)
        print(f"임시 설정 생성: {cfg}")

    print("\n[1/2] survey — 규모·구조 먼저 봅니다 (20초 남짓, 메모리 1GB 안팎)")
    if run_cli(["survey", "--input", src, "--configs", os.path.join(ROOT, "configs")]) != 0:
        print("\n!! survey 가 실패했습니다. 위 로그를 확인하세요.")
        sys.exit(1)

    if not a.yes:
        print("\n" + "-" * 66)
        print("[2/2] 전체 추출은 게임 크기에 따라 몇 분~30분, 메모리 4~5GB 를 씁니다.")
        try:
            if input("계속할까요? (y/N) ").strip().lower() not in ("y", "yes"):
                print("여기서 멈췄습니다. survey 결과만 보셔도 규모는 파악됩니다.")
                return
        except EOFError:
            print("입력을 받을 수 없어 멈췄습니다. 전체 추출은 --yes 로 실행하세요.")
            return

    rc = run_cli(["run", "--config", cfg, "--input", src, "--out", out])
    print("\n" + "=" * 66)
    if rc == 0:
        print(f"완료: {out}")
    else:
        print(f"일부 산출물이 실패했습니다(종료코드 {rc}). 위 로그와 "
              f"{os.path.join(out, '*_errors.txt')} 를 보세요.")
    print("=" * 66)
    sys.exit(rc)


if __name__ == "__main__":
    main()
