"""Zen Match (com.exoticmatch.game) 플러그인.

레벨 포맷 3종:
  fv1     {format_version:1, layer_data:[[{cordinates{x,y}, type, tile_modes, ice?, box?}]]}
          type -1 = 랜덤 타일, 그 외 = 고정 타일 id. 레이어 다수(최대 70+).
  fv2     {format_version:2, board:[{boardElementType, coordinates{x,y(0.25단위)}, configurations}]}
  random  {backgroundId, uniqueItems:{타일id: 개수}, seed} — 보드 없음 (시드 랜덤 생성)

보드 렌더: 셀 색 = 그 좌표에 쌓인 타일 수(스택 높이, 팔레트 16단계).
ice/box 타일은 outline 오버레이로 표시.
"""
import collections

MAX_STACK = 16  # 팔레트 단계 수 (이상은 마지막 색)


def _fmt(data):
    fv = data.get("format_version")
    if fv == 1:
        return "layered(v1)"
    if fv == 2:
        return "board(v2)"
    if "uniqueItems" in data:
        return "random"
    return f"v{fv}"


def _tiles_v1(data):
    for li, layer in enumerate(data.get("layer_data") or []):
        for t in layer:
            c = t.get("cordinates") or {}
            yield li, c.get("x", 0), c.get("y", 0), t


def _tiles_v2(data):
    for el in data.get("board") or []:
        if el.get("boardElementType") != 1:
            continue
        c = el.get("coordinates") or {}
        layer = 0
        for cf in el.get("configurations") or []:
            if cf.get("name") == "Layer":
                layer = cf.get("layer", 0)
        yield layer, c.get("x", 0.0), c.get("y", 0.0), el


def level_extras(data):
    fmt = _fmt(data)
    row = {"format": fmt, "layer_count": 0, "tile_count": 0, "random_tiles": 0,
           "fixed_tiles": 0, "fixed_kinds": 0, "max_stack": 0, "ice": 0, "box": 0,
           "unique_kinds": 0, "seed": data.get("seed", ""),
           "backgroundId": data.get("backgroundId", "")}
    if fmt == "random":
        items = data.get("uniqueItems") or {}
        row["unique_kinds"] = len(items)
        row["tile_count"] = sum(items.values())
        return row
    tiles = list(_tiles_v1(data)) if fmt == "layered(v1)" else list(_tiles_v2(data))
    stacks = collections.Counter((x, y) for _, x, y, _ in tiles)
    kinds = set()
    for _, _, _, t in tiles:
        tp = t.get("type", -1)
        if tp == -1:
            row["random_tiles"] += 1
        else:
            row["fixed_tiles"] += 1
            kinds.add(tp)
        row["ice"] += 1 if t.get("ice") else 0
        row["box"] += 1 if t.get("box") else 0
    row["tile_count"] = len(tiles)
    row["fixed_kinds"] = len(kinds)
    row["layer_count"] = (len(data.get("layer_data") or [])
                          if fmt == "layered(v1)"
                          else (max((l for l, *_ in tiles), default=-1) + 1))
    row["max_stack"] = max(stacks.values(), default=0)
    return row


def board(data):
    fmt = _fmt(data)
    if fmt == "random":
        return None
    tiles = list(_tiles_v1(data)) if fmt == "layered(v1)" else list(_tiles_v2(data))
    if not tiles:
        return None
    # fv2는 0.25 단위 좌표 → 4배 정수화
    scale = 1 if fmt == "layered(v1)" else 4
    xs = [round(x * scale) for _, x, y, _ in tiles]
    ys = [round(y * scale) for _, x, y, _ in tiles]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0 + 1, max(ys) - y0 + 1
    stacks = collections.Counter()
    marks = []
    for (_, x, y, t), gx, gy in zip(tiles, xs, ys):
        stacks[(gx - x0, gy - y0)] += 1
        if t.get("ice") or t.get("box"):
            marks.append((gx - x0, gy - y0))
    cells = [(x, y, min(n, MAX_STACK) - 1) for (x, y), n in stacks.items()]
    return {"w": w, "h": h, "cells": cells, "pixel_count": len(tiles),
            "overlays": {"marks": {"points": marks, "style": "outline"}}}


def viewer_level(data):
    """뷰어 tiles 모드용: tl=[layer,x,y,type,flags]*, tw/th=유닛 크기, lc=레이어 수"""
    fmt = _fmt(data)
    if fmt == "random":
        return {"ma": [], "sq": [], "tl": [], "lc": 0, "tw": 0, "th": 0}
    tiles = list(_tiles_v1(data)) if fmt == "layered(v1)" else list(_tiles_v2(data))
    if not tiles:
        return {"ma": [], "sq": [], "tl": [], "lc": 0, "tw": 0, "th": 0}
    scale = 1 if fmt == "layered(v1)" else 4
    pts = [(li, round(x * scale), round(y * scale), t) for li, x, y, t in tiles]
    x0 = min(p[1] for p in pts)
    y0 = min(p[2] for p in pts)
    tl = []
    stacks = collections.Counter()
    for li, gx, gy, t in sorted(pts, key=lambda p: p[0]):
        flags = (1 if t.get("ice") else 0) | (2 if t.get("box") else 0)
        tl.extend((li, gx - x0, gy - y0, t.get("type", -1), flags))
        stacks[(gx, gy)] += 1
    lc = max(p[0] for p in pts) + 1
    tw = max(p[1] for p in pts) - x0 + 2  # 타일 폭 2유닛
    th = max(p[2] for p in pts) - y0 + 2
    dist = collections.Counter(min(n, MAX_STACK) - 1 for n in stacks.values())
    ma = [[k, v] for k, v in sorted(dist.items())]
    return {"ma": ma, "sq": [], "tl": tl, "lc": lc, "tw": tw, "th": th}
