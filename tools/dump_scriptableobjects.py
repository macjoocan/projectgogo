"""독립 ScriptableObject 를 JSON 으로 뽑는다 — 파이프라인이 못 덮는 구멍을 메운다.

**왜 필요한가.** `hierarchy` 는 `_classify` 가 Transform 이 있는 파일만 분류한다.
그래서 MonoBehaviour 만 들어 있는 번들(= 데이터용 ScriptableObject 모음)은 통째로
건너뛴다. `assets` 의 종류에도 ScriptableObject 는 없다. 즉 **게임 데이터가 SO 에만
있는 게임은 현재 어떤 산출물로도 안 나온다.**

SANABI(Steam, Unity 2019.4 IL2CPP)가 그렇다 — TextAsset 이 2개뿐이고 밸런스가 전부
SO 다(`MainDifficultySo`·`DLCDifficultySo`·`PlayerHpState`·`EnemyRespawnerSO`·
`BattleGateSO`·`NewTilePalette`…). 모바일 게임도 `type: MonoBehaviour` 로 받는
`input.unity` 가 있지만 그건 **JSON 문자열을 품은** SO 용이라(`unity.payload_bytes` 가
가장 긴 문자열을 꺼낸다) 구조화된 필드에는 맞지 않는다.

**독립 SO 와 컴포넌트를 가르는 기준은 `m_GameObject` 다.** PPtr 의 path_id 가 0 이면
어디에도 붙어 있지 않은 에셋이고, 0 이 아니면 GameObject 에 붙은 컴포넌트다
(후자는 `hierarchy` 가 이미 낸다). 기본은 에셋만 낸다 — `--components` 로 둘 다.

    py tools/dump_scriptableobjects.py --input <게임 폴더|apk> --config configs/sanabi.yaml
    py tools/dump_scriptableobjects.py --input <입력> --source "*dataso*,*eventso*"

산출물: `<out>/<game>_scriptableobjects.zip`
    so/<클래스>/<이름>.json      필드 복원 결과
    manifest.json                클래스별 개수 · 실패 목록 · 소스 목록

**필드를 못 읽은 것을 조용히 빼지 않는다.** 복원 실패는 manifest 의 `failures` 에
클래스와 이유를 남긴다("없다"와 "못 읽었다"는 다르다).
"""
import argparse
import collections
import io
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def force_utf8_output():
    """한국어 Windows 콘솔(cp949)에서 '—' 같은 문자로 죽는 것을 막는다."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def _safe(name, fallback):
    """zip 안에서 쓸 수 있는 파일명. 빈 이름·경로 문자를 정리한다."""
    name = (name or "").strip() or fallback
    for ch in '\\/:*?"<>|\r\n\t':
        name = name.replace(ch, "_")
    return name[:120]


def main():
    force_utf8_output()
    ap = argparse.ArgumentParser(
        description="독립 ScriptableObject 를 JSON 으로 뽑는다 (hierarchy 가 못 덮는 구멍)")
    ap.add_argument("--input", required=True, help="게임 폴더 / apk / xapk")
    ap.add_argument("--config", default=None,
                    help="게임 yaml — typetree 절(il2cpp 경로 등)을 쓴다. "
                         "윈도우 IL2CPP 빌드는 이게 없으면 필드가 전부 빈다")
    ap.add_argument("--source", default="auto",
                    help="Unity 소스 이름 패턴 쉼표 구분 (기본 auto = 전체 자동 발견)")
    ap.add_argument("--out", default="out")
    ap.add_argument("--game", default=None, help="출력 파일명 접두어 (기본: 설정의 game)")
    ap.add_argument("--unity-version", default=None,
                    help="번들 헤더에 버전이 없을 때 쓸 값")
    ap.add_argument("--components", action="store_true",
                    help="GameObject 에 붙은 컴포넌트도 포함 (기본은 독립 에셋만 — "
                         "컴포넌트는 hierarchy 가 이미 낸다)")
    ap.add_argument("--max", type=int, default=100000, help="상한 (넘으면 중단하고 알린다)")
    a = ap.parse_args()

    from levelscope import discover, hierarchy, typetree, unity

    cfg = {}
    if a.config:
        from levelscope import cli
        cfg = cli._load_config(a.config)
    game = a.game or cfg.get("game") or "game"

    sources, src_objs = discover.resolve_detailed(
        a.input, None if a.source == "auto" else [s.strip() for s in a.source.split(",")],
        log=print)
    if not sources:
        sys.exit("Unity 소스를 찾지 못했습니다")
    print(f"[so] 소스 {len(sources)}개")

    os.makedirs(a.out, exist_ok=True)
    zpath = os.path.join(a.out, f"{game}_scriptableobjects.zip")
    counts, failures, used, seen = collections.Counter(), [], [], collections.Counter()
    n_assets = n_components = 0
    truncated = False
    reader = None       # 소스마다 만들지 않는다 — IL2CPP 재료를 백엔드마다 다시 읽는다

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        # 번들 경계를 넘는 MonoScript 참조를 푼다 (없으면 복원률이 크게 떨어진다)
        registry = hierarchy._script_registry(a.input, src_objs, cfg.get("hierarchy") or {},
                                              print)
        for label, data in hierarchy._iter_sources(a.input, sources):
            if truncated:
                break
            try:
                with unity.load_bytes(data, os.path.splitext(label)[1] or ".bundle",
                                      path=None) as env:
                    # 연 김에 이 번들의 MonoScript 를 색인에 넣는다 — 스크립트가
                    # 콘텐츠 번들에 흩어진 게임에서 참조가 그만큼 더 풀린다.
                    # alias: 다른 번들은 이 파일을 **소스 이름**으로 부른다
                    # (내부 이름은 다르다 — ScriptRegistry.add_env 주석 참고).
                    if registry is not None:
                        base = os.path.basename(str(label).replace("!", "/"))
                        registry.add_env(env, base, alias=base)
                    objs = [o for o in env.objects if o.type.name == "MonoBehaviour"]
                    if not objs:
                        continue
                    if reader is None:
                        ver = a.unity_version or typetree.detect_unity_version(env)
                        reader = typetree.open_reader(a.input, cfg.get("typetree"), ver,
                                                      log=print, registry=registry)
                    used.append(label)
                    for o in objs:
                        cls, tree = reader.read(o)
                        if tree is None:
                            failures.append({"source": label,
                                             "class": cls or "(알 수 없음)",
                                             "why": "필드 복원 실패"})
                            continue
                        go = (tree.get("m_GameObject") or {}).get("m_PathID", 0)
                        if go:
                            n_components += 1
                            if not a.components:
                                continue
                        else:
                            n_assets += 1
                        cls = cls or "UnknownScript"
                        base = _safe(tree.get("m_Name"), f"{cls}_{o.path_id}")
                        seen[(cls, base)] += 1
                        k = seen[(cls, base)]
                        fn = f"so/{_safe(cls, 'Unknown')}/{base}{'' if k == 1 else f'_{k}'}.json"
                        zf.writestr(fn, json.dumps(tree, ensure_ascii=False, indent=1,
                                                   default=str))
                        counts[cls] += 1
                        if sum(counts.values()) >= a.max:
                            truncated = True
                            print(f"[so] 상한 {a.max} 도달로 중단 — 남은 소스는 처리하지 "
                                  f"않았습니다(--max 를 올리세요)")
                            break
            except Exception as e:  # noqa: BLE001
                failures.append({"source": label, "why": f"번들 열기 실패: {e!r}"})

        manifest = {
            "game": game,
            "input": os.path.abspath(a.input),
            "sources_used": used,
            "counts_by_class": dict(counts.most_common()),
            "total": sum(counts.values()),
            "standalone_assets": n_assets,
            "components_seen": n_components,
            "components_included": bool(a.components),
            "truncated": truncated,
            "typetree": reader.summary() if reader else "MonoBehaviour 가 있는 소스 없음",
            "failures": failures[:500],
            "failure_total": len(failures),
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=1))

    print(f"[so] {sum(counts.values())}개 저장 (독립 에셋 {n_assets} · 컴포넌트 "
          f"{n_components}{'(포함)' if a.components else '(제외)'}) → {zpath} "
          f"({os.path.getsize(zpath) / 1e6:.1f}MB)")
    if failures:
        print(f"[so] 실패 {len(failures)}건 — manifest.json 의 failures 참고")
    for cls, n in counts.most_common(15):
        print(f"      {n:>5}x  {cls}")
    if reader is not None:
        print(reader.summary())


if __name__ == "__main__":
    main()
