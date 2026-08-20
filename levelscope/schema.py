"""설정 기반 필드 매핑.

경로 문법 (점 구분):
  a.b.c        중첩 dict 접근
  a.*          dict이면 내부의 '유일한 리스트' (게임들이 {"Shooters":[...]} 식 래퍼를 쓰는 경우)
  a.0          리스트 인덱스

scalars: 컬럼명 -> 경로 (값 그대로)
counts:  컬럼명 -> 경로 (리스트 길이; 경로가 없거나 리스트가 아니면 0)
"""


def get_path(data, path, default=None):
    cur = data
    for part in str(path).split("."):
        if cur is None:
            return default
        if part == "*":
            if isinstance(cur, dict):
                lists = [v for v in cur.values() if isinstance(v, list)]
                cur = lists[0] if len(lists) == 1 else (lists if lists else None)
            # 리스트면 그대로 통과
        elif isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        else:
            return default
    return default if cur is None else cur


#: 자동 컬럼의 기본 상한 — 표를 사람이 읽을 수 있는 크기로 유지한다
AUTO_MAX_COLS = 60
#: dict 을 점 경로로 펼치는 깊이 상한
AUTO_MAX_DEPTH = 4


def _walk(data, prefix, depth, kinds, max_depth):
    """dict 하나를 점 경로로 펼쳐 경로별 **값 종류**를 센다.

    종류를 따로 세는 이유: 같은 경로가 레코드마다 다른 종류일 수 있다. FlatBuffers
    게임이 대표적이다 — 같은 슬롯이 어떤 레벨에서는 정수, 다른 레벨에서는
    `{"of": "empty", "n": 0, "items": []}`(빈 벡터) 로 나온다. 종류가 갈리는 경로를
    컬럼으로 잡으면 dict 이 셀에 들어가 **xlsx 생성이 통째로 실패**한다(실측).
    """
    if depth > max_depth or not isinstance(data, dict):
        return
    for k, v in data.items():
        if not isinstance(k, str):
            continue
        path = f"{prefix}{k}"
        if isinstance(v, bool) or isinstance(v, (int, float, str)):
            # 너무 긴 문자열은 컬럼에 넣어도 못 읽는다 (원본 JSON 은 zip 에 있다)
            kinds[(path, "skip" if isinstance(v, str) and len(v) > 200 else "scalar")] += 1
        elif isinstance(v, list):
            # 리스트 **안쪽**은 펼치지 않는다. 레벨마다 길이가 달라 컬럼이 폭발한다.
            kinds[(path, "list")] += 1
        elif isinstance(v, dict):
            kinds[(path, "dict")] += 1
            _walk(v, path + ".", depth + 1, kinds, max_depth)
        else:
            kinds[(path, "skip")] += 1


def infer_fields(samples, max_cols=AUTO_MAX_COLS, max_depth=AUTO_MAX_DEPTH):
    """표본 JSON들에서 컬럼 지도를 자동으로 만든다.

    `fields: auto` 가 쓴다. 장르가 바뀔 때마다 필드 경로를 손으로 적는 게 병목이었다 —
    퍼즐이면 board/기믹, RPG면 스탯/스킬, 방치형이면 생산·비용처럼 이름이 전부 다르다.

    규칙은 기존 수동 설정과 같게 맞춘다. 스칼라(bool·수·짧은 문자열)는 값 그대로,
    리스트는 **길이**로 잡는다(`counts`). dict 은 점 경로로 펼치고, 리스트 안쪽은
    펼치지 않는다 — 레벨마다 원소 수가 달라 컬럼이 폭발한다.

    반환: (fields_cfg, dropped, conflicts)
      dropped   상한에 걸려 빠진 경로
      conflicts 표본 안에서 값 종류가 갈려 뺀 경로 (dict 이 섞이면 xlsx 가 깨진다)
    둘 다 호출자가 로그로 남긴다. 조용히 빼면 "그 필드는 없었다"로 읽힌다.
    """
    import collections
    kinds = collections.Counter()
    for d in samples:
        _walk(d, "", 1, kinds, max_depth)

    # 경로별로 어떤 종류가 몇 번 나왔나 모은다
    by_path = collections.defaultdict(dict)
    for (path, kind), n in kinds.items():
        by_path[path][kind] = n

    usable, conflicts = [], []
    for path, ks in by_path.items():
        real = {k: n for k, n in ks.items() if k != "skip"}
        if not real:
            continue
        if len(real) > 1:
            # 스칼라와 리스트/dict 가 섞인 경로 — 컬럼으로 쓰면 셀 타입이 흔들린다
            conflicts.append(path)
            continue
        kind, n = next(iter(real.items()))
        if kind == "dict":
            continue          # 중간 노드다. 펼친 자식들이 컬럼이 된다
        usable.append((path, kind, n))

    # 표본에 많이 나온 경로가 먼저다. 같은 빈도면 경로 순으로 안정 정렬한다.
    usable.sort(key=lambda t: (-t[2], t[0]))
    keep, dropped = usable[:max_cols], [p for p, _k, _n in usable[max_cols:]]
    out = {"scalars": {}, "counts": {}}
    for path, kind, _n in keep:
        out["scalars" if kind == "scalar" else "counts"][path] = path
    return out, dropped, sorted(conflicts)


def is_auto(fields_cfg):
    """`fields: auto` 또는 `fields: {auto: true}` 인지."""
    if isinstance(fields_cfg, str):
        return fields_cfg.strip().lower() == "auto"
    return bool(isinstance(fields_cfg, dict) and fields_cfg.get("auto"))


def extract_row(data, fields_cfg):
    row = {}
    if not isinstance(fields_cfg, dict):
        return row          # 'auto' 가 아직 실제 지도로 바뀌지 않은 경우
    for col, path in (fields_cfg.get("scalars") or {}).items():
        row[col] = get_path(data, path)
    for col, path in (fields_cfg.get("counts") or {}).items():
        v = get_path(data, path)
        row[col] = len(v) if isinstance(v, list) else 0
    return row


def extract_board(data, board_cfg):
    """보드(그리드) 데이터 추출 → dict(w,h,cells[(x,y,material)], overlays{name:[(x,y)]})"""
    if not board_cfg:
        return None
    w = get_path(data, board_cfg["width"])
    h = get_path(data, board_cfg["height"])
    if not w or not h:
        return None
    pk = board_cfg.get("pixel", {})
    kx, ky_, km = pk.get("x", "x"), pk.get("y", "y"), pk.get("material", "material")
    kax, kay = pk.get("area_x"), pk.get("area_y")
    cells = []
    pixels = get_path(data, board_cfg["pixels"]) or []
    for p in pixels:
        ax = (p.get(kax) or 1) if kax else 1
        ay = (p.get(kay) or 1) if kay else 1
        for dy in range(ay):
            for dx in range(ax):
                cells.append((p[kx] + dx, p[ky_] + dy, p[km]))
    overlays = {}
    for name, ov in (board_cfg.get("overlays") or {}).items():
        items = get_path(data, ov["path"]) or []
        pts = []
        pkey = ov.get("points")
        for it in items:
            gps = it.get(pkey, []) if (pkey and isinstance(it, dict)) else [it]
            for gp in gps:
                pts.append((gp.get("X", gp.get("x")), gp.get("Y", gp.get("y"))))
        overlays[name] = {"points": pts, "style": ov.get("style", "wall")}
    return {"w": w, "h": h, "cells": cells, "pixel_count": len(pixels), "overlays": overlays}
