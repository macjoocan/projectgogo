"""소스를 **별 프로세스로 하나씩** 돌려 메모리 수위를 낮춘다.

한 프로세스에서 소스를 차례로 처리하면, 앞 번들에서 해제한 메모리가 OS 로 즉시
반납되지 않는다. 커밋 수위가 그대로 남은 채 다음 번들 할당이 얹혀서, 실제로 살아
있는 양보다 훨씬 높은 피크가 찍힌다.

실측(CookieRun: Crumble, Unity 소스 7개 · 오브젝트 597,791개):

    통짜 실행 스프라이트                     최고 커밋 4.26GB
    번들 하나(272MB · 오브젝트 579,681개)     1.83GB

프로세스를 갈면 각 실행이 자기 몫만 쓰고 끝나므로 피크가 "가장 무거운 소스 하나"로
내려간다. 대가는 두 가지다 — 산출물이 소스마다 따로 나오고(zip 여러 개), 컨테이너를
소스마다 다시 여니 총 시간이 늘어난다.

부모는 **무거운 일을 하지 않는다.** 소스 목록조차 자식(`levelscope sources`)에게
물어본다. 부모가 직접 발견하면 그 1.8GB 가 부모에 남아 자식 피크와 겹친다.
"""
import os
import subprocess
import sys


def _child_env():
    """자식이 이 패키지를 찾을 수 있게 PYTHONPATH 를 넣어 준다."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = dict(os.environ)
    prev = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root + (os.pathsep + prev if prev else "")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def list_sources(input_path, log=print):
    """자식에게 (소스 이름 목록, Unity 버전) 을 받아 온다. 실패하면 ([], None)."""
    cmd = [sys.executable, "-m", "levelscope", "sources", "--input", input_path]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=_child_env())
    except OSError as e:
        log(f"[split] 소스 목록 조회 실패: {e}")
        return [], None
    if p.returncode != 0:
        log(f"[split] 소스 목록 조회 실패 (종료코드 {p.returncode})")
        for line in (p.stderr or "").strip().splitlines()[-3:]:
            log(f"  ! {line}")
        return [], None
    names, version = [], None
    for ln in (p.stdout or "").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("#unity="):
            version = ln[len("#unity="):].strip() or None
        elif not ln.startswith("#"):
            names.append(ln)
    return names, version


def tag_of(name):
    """소스 경로 → 산출물 이름에 붙일 짧은 꼬리표."""
    base = os.path.basename(name.replace("\\", "/")) or "src"
    for ext in (".bundle", ".unity3d", ".assets", ".ab"):
        if base.lower().endswith(ext):
            base = base[: -len(ext)]
            break
    safe = "".join(c if (c.isalnum() or c in "-_") else "_" for c in base)
    return safe[:48] or "src"


def run_per_source(stage, input_path, out_dir, game, extra=(), log=print):
    """`stage` 를 소스마다 따로 실행한다. 실패한 소스 수를 반환.

    stage: "sprites" | "assets" | "hierarchy"
    extra: 자식에게 그대로 넘길 추가 플래그 (`--source` 는 여기서 넣으므로 제외)
    """
    names, version = list_sources(input_path, log=log)
    if not names:
        log("[split] 처리할 Unity 소스가 없습니다 — 통짜 실행으로 돌려 보세요")
        return 1
    log(f"[split] Unity 소스 {len(names)}개를 각각 따로 실행합니다 "
        f"(산출물이 소스마다 나뉩니다)"
        + (f" · Unity {version}" if version else ""))
    extra = list(extra)
    if version and "--unity-version" not in extra:
        # 소스를 하나만 받는 자식은 버전을 배울 데가 없다 — 부모가 알려 준다
        extra += ["--unity-version", version]
    seen, failed = {}, 0
    for i, name in enumerate(names, 1):
        tag = tag_of(name)
        seen[tag] = seen.get(tag, 0) + 1
        if seen[tag] > 1:                      # 같은 이름이 여러 컨테이너에 있을 수 있다
            tag = f"{tag}_{seen[tag]}"
        cmd = [sys.executable, "-m", "levelscope", stage,
               "--input", input_path, "--out", out_dir,
               "--game", f"{game}__{tag}", "--source", name, *extra]
        log(f"[split] ({i}/{len(names)}) {name}")
        rc = subprocess.call(cmd, env=_child_env())
        if rc != 0:
            failed += 1
            log(f"[split] ! 실패 (종료코드 {rc}): {name}")
    log(f"[split] 완료 — 소스 {len(names)}개 중 실패 {failed}개")
    return failed
