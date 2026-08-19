"""팔레트 확보.

palette.source:
  static  — 설정의 static: ["#RRGGBB", ...] 사용
  unity   — 컨테이너 내 Unity 데이터 파일에서 추출 (UnityPy 필요)
            unity.data_file, unity.list_class(MonoBehaviour 스크립트 클래스명),
            unity.list_name(리스트 에셋 이름), unity.color_props(우선순위 색 프로퍼티)
실패 시 fallback: static → 자동 생성(HSV 균등 분할).
"""
import colorsys
import struct

from . import unity as unity_mod


def _auto_palette(n):
    out = []
    for i in range(n):
        h = (i * 0.61803398875) % 1.0
        s = 0.75 if i % 2 == 0 else 0.55
        v = 0.9 if i % 3 else 0.65
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        out.append("#%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255)))
    return out


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(c * 255)) for c in rgb[:3])


def _from_unity(data_bytes, ucfg, log=print):
    """MaterialDataListSo 류의 머티리얼 리스트에서 색을 순서대로 뽑는다.

    리스트 에셋은 typetree가 없어 raw 데이터에서 PPtr 배열을 직접 파싱한다
    (헤더 12 + m_Script 4 + GUID 12 → 이름 길이·이름 → 4바이트 정렬 → 개수 → PPtr[12]).
    """
    with unity_mod.load_bytes(data_bytes) as env:
        target = None
        for o in unity_mod.iter_objects(env, ["MonoBehaviour"]):
            if unity_mod.script_class(o) != ucfg["list_class"]:
                continue
            if unity_mod.name_of(o) == ucfg["list_name"]:
                target = o
                break
        if target is None:
            raise LookupError(f"{ucfg['list_class']} '{ucfg['list_name']}' 미발견")
        raw = target.get_raw_data()
        off = 12 + 4 + 12
        ln = struct.unpack_from("<i", raw, off)[0]
        off += 4 + ln
        off = (off + 3) & ~3
        cnt = struct.unpack_from("<i", raw, off)[0]
        off += 4
        ptrs = [struct.unpack_from("<iq", raw, off + 12 * i) for i in range(cnt)]
        matobjs = {o.path_id: o for o in unity_mod.iter_objects(env, ["Material"])}
        colors, names = [], []
        props = ucfg.get("color_props", ["_BaseColor", "_Color"])
        for _, pid in ptrs:
            m = matobjs[pid].read()
            cols = {}
            for k, v in m.m_SavedProperties.m_Colors:
                cols[str(k)] = (v.r, v.g, v.b, v.a) if hasattr(v, "r") else tuple(v)
            main = next((cols[p] for p in props if p in cols), next(iter(cols.values())))
            colors.append(_hex(main))
            names.append(m.m_Name)
        log(f"[palette] unity에서 {len(colors)}색 추출: {names[0]}..{names[-1]}")
        return colors, names


def resolve_palette(pal_cfg, container_reader, log=print):
    """(hex 리스트, 이름 리스트) 반환. container_reader(inner_path)->bytes|None"""
    pal_cfg = pal_cfg or {}
    names = pal_cfg.get("names") or []
    source = pal_cfg.get("source", "static")
    if source == "unity":
        try:
            data = container_reader(pal_cfg["unity"]["data_file"])
            if data is None:
                raise FileNotFoundError(pal_cfg["unity"]["data_file"])
            colors, unames = _from_unity(data, pal_cfg["unity"], log)
            return colors, (names or unames)
        except Exception as e:  # noqa: BLE001 - 팔레트는 없어도 파이프라인이 돌아야 한다
            log(f"[palette] unity 추출 실패({e}) → static/자동 팔레트로 대체")
    static = pal_cfg.get("static")
    if static:
        return list(static), (names or [f"Mat{i}" for i in range(len(static))])
    n = pal_cfg.get("auto_size", 36)
    return _auto_palette(n), (names or [f"Mat{i}" for i in range(n)])
