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


def extract_row(data, fields_cfg):
    row = {}
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
