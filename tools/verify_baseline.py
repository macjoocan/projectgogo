"""실제 APK로 기준치를 대조하는 회귀 검증.

tests/ 는 합성 데이터만 쓰므로 추가 설치 없이 돌아간다. 이 스크립트는 반대로
**실제 게임 파일**이 있어야 하며, pandas/PyYAML 없이 extract+decode 경로만 검증한다.
(xlsx/뷰어까지 보려면 `python -m levelscope run` 을 쓴다.)

    python tools/verify_baseline.py --zenmatch D:\\99.기타\\AAA.xapk \\
                                   --pixelflow D:\\99.기타\\xapk_unpacked

기준치는 인수인계 문서 7장 + v1.4 실측값이다. 크게 다르면 게임 업데이트로 구조가
바뀐 것 — `detect` / `inspect` 부터 다시 본다.
"""
import argparse
import collections
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from levelscope import cli, decode, extract, palette as pal_mod   # noqa: E402

FAILURES = []


def check(label, got, want):
    ok = got == want
    print(f"  {'OK  ' if ok else 'FAIL'} {label}: {got}" + ("" if ok else f"   (기준 {want})"))
    if not ok:
        FAILURES.append(f"{label}: {got} != {want}")


def decode_all(records, log):
    auto = decode.AutoCodec(log)
    ok, errors, datas = 0, [], []
    for r in records:
        try:
            data, _steps, _plain = auto.decode_capture(r.raw)
            ok += 1
            datas.append(data)
        except Exception as e:  # noqa: BLE001
            errors.append((r.source, repr(e)))
    return ok, errors, datas


def zenmatch(path):
    """기준: TextAsset 4,502 (main 4,493 + variant 9), 실패 0, board(v2) 6.

    포맷 분포(main 기준 layered 3,705 / random 782)는 이름 중복 레벨 쌍의 순서가
    UnityPy 버전·플랫폼에 따라 갈려 ±1 흔들릴 수 있다 — 합계로 판정한다.
    """
    from levelscope.plugins import zenmatch as plug
    print(f"\n=== Zen Match — {path} ===")
    t = time.time()
    res = extract.collect_levels(path, {"unity": {
        "data_file": "assets/bin/Data/data.unity3d",
        "name_pattern": r"Level_(\d+)", "set_name": "main"}})
    print(f"  수집 {len(res.records)}개 · {time.time() - t:.1f}s · {res.source}")
    check("TextAsset 총계", len(res.records), 4502)
    sets = collections.Counter(r.set_name for r in res.records)
    check("main", sets["main"], 4493)
    check("variant 합", sum(v for k, v in sets.items() if k != "main"), 9)

    ok, errors, datas = decode_all(res.records, lambda m: print(f"    {m}"))
    check("디코딩 실패", len(errors), 0)
    for s, e in errors[:3]:
        print(f"    ! {s}: {e}")

    fmt = collections.Counter(plug.level_extras(d)["format"] for d in datas)
    check("포맷 합계", sum(fmt.values()), 4502)
    check("board(v2)", fmt["board(v2)"], 6)
    print(f"  포맷 분포: {dict(fmt)}")
    res.container.close()


def pixelflow(path):
    """기준: 레벨 2,384 / 8세트 / 메인 2,100 / isValid 2,100 / 실패 0 / 팔레트 34색."""
    print(f"\n=== PixelFlow — {path} ===")
    t = time.time()
    res = extract.collect_levels(path, {"levels_glob": "assets/Levels/*/*.json"})
    print(f"  수집 {len(res.records)}개 · {time.time() - t:.1f}s · {res.source}")
    check("레벨 파일", len(res.records), 2384)
    sets = collections.Counter(r.set_name for r in res.records)
    check("세트 수", len(sets), 8)
    check("메인 세트 크기", max(sets.values()), 2100)

    ok, errors, datas = decode_all(res.records, lambda m: print(f"    {m}"))
    check("디코딩 성공", ok, 2384)
    check("디코딩 실패", len(errors), 0)
    for s, e in errors[:3]:
        print(f"    ! {s}: {e}")
    check("isValid=true", sum(1 for d in datas if d.get("isValid")), 2100)

    colors, _names = pal_mod.resolve_palette(
        {"source": "unity", "unity": {
            "data_file": "assets/bin/Data/data.unity3d",
            "list_class": "MaterialDataListSo",
            "list_name": "Main Pixel Unity Materials",
            "color_props": ["_BaseColor", "_Color"]}},
        extract.make_reader(res, path), log=lambda m: print(f"    {m}"))
    check("팔레트 색 수", len(colors), 34)
    res.container.close()


def main():
    cli.force_utf8_output()
    ap = argparse.ArgumentParser(description="실제 APK로 기준치 대조")
    ap.add_argument("--zenmatch", help="Zen Match xapk 경로")
    ap.add_argument("--pixelflow", action="append", default=[],
                    help="PixelFlow xapk 또는 해제 폴더 (여러 번 지정 가능)")
    args = ap.parse_args()
    if not args.zenmatch and not args.pixelflow:
        ap.error("--zenmatch 또는 --pixelflow 중 하나는 필요합니다")
    if args.zenmatch:
        zenmatch(args.zenmatch)
    for p in args.pixelflow:
        pixelflow(p)
    print("\n" + "=" * 60)
    if FAILURES:
        print(f"불일치 {len(FAILURES)}건:\n  " + "\n  ".join(FAILURES))
        return 1
    print("모든 기준치 일치")
    return 0


if __name__ == "__main__":
    sys.exit(main())
