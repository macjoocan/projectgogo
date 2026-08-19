"""SheepNSheep (com.game.keepsheep) 플러그인 — 3매칭 타일 스택 퍼즐.

한 TextAsset이 맵 여러 개를 담고, 맵 하나가 다시 스테이지 2~3개를 담는다.
그래서 `split_levels` 로 **레코드 1개 = 스테이지 1개** 로 펼친다 (id = "<mapId>-<스테이지>").

에셋 구조 2종
  최신형  {version, mapData:[{mapId, level:[스테이지...], blockTypeData:[스테이지별...]}]}
          스테이지 = {"레이어번호": [{col,row,layer,type,moldType}, ...]}
  구형    defaultMapData — {mapData:[{mapId, level1:{...}, level2:{...}}]}
          타일 키가 rolNum/rowNum/layerNum, blockTypeData 없음
  AdventureMap 은 mapData 대신 easy/hard/hellMapData 3종을 갖는다.

blockTypeData = {블록타입id: 개수}. **합 × 3 = 랜덤 타일 수** (3개 맞추기).
APK 수록분 전 스테이지에서 이 등식이 성립함을 확인했다(73/73).
`type` 0 = 랜덤 배정, 그 외 = 고정 블록. 서버에서 받는 일일 맵은 APK에 없다.
"""
import collections

#: 타일 하나가 차지하는 좌표 유닛 (col/row 간격이 12) — 절반 겹침이 흔하다
TILE_SPAN = 12
#: 스택 높이 팔레트 단계 수 (이상은 마지막 색)
MAX_STACK = 16

#: 맵 목록이 들어있는 키들 (AdventureMap은 난이도별로 나뉘어 있다)
_GROUP_KEYS = {"mapData": "", "easyMapData": "easy", "hardMapData": "hard",
               "hellMapData": "hell"}


def _tile(t):
    """구형/최신형 타일 키를 하나로 맞춘다."""
    return {"col": t.get("col", t.get("rolNum", 0)),
            "row": t.get("row", t.get("rowNum", 0)),
            "layer": t.get("layer", t.get("layerNum", 1)),
            "type": t.get("type", 0),
            "moldType": t.get("moldType", 1)}


def _stages(m):
    """맵 하나 → [(스테이지 타일들, blockTypeData)]"""
    bts = m.get("blockTypeData") or []
    if "level" in m:
        stages = m["level"]
    else:                                   # 구형: level1, level2, ...
        stages = [m[k] for k in sorted(k for k in m if k.startswith("level"))]
    out = []
    for i, st in enumerate(stages):
        tiles = [_tile(t) for layer in (st or {}).values() for t in layer]
        out.append((tiles, bts[i] if i < len(bts) else {}))
    return out


def split_levels(data, record):
    """에셋 하나 → 스테이지 단위 레벨들. [(세트명, "<mapId>-<스테이지>", 레벨 dict)]"""
    asset = str(record.level_id)
    out = []
    for key, suffix in _GROUP_KEYS.items():
        maps = data.get(key)
        if not isinstance(maps, list):
            continue
        set_name = f"{asset}_{suffix}" if suffix else asset
        for m in maps:
            if not isinstance(m, dict):
                continue
            mid = m.get("mapId", "?")
            for si, (tiles, bt) in enumerate(_stages(m), 1):
                if not tiles:
                    continue
                out.append((set_name, f"{mid}-{si}",
                            {"asset": asset, "mapId": mid, "stage": si,
                             "stage_count": len(_stages(m)),
                             "tiles": tiles, "blockTypeData": bt,
                             "version": data.get("version")}))
    return out


def level_extras(data):
    tiles = data["tiles"]
    bt = data.get("blockTypeData") or {}
    layers = collections.Counter(t["layer"] for t in tiles)
    stacks = collections.Counter((t["col"], t["row"]) for t in tiles)
    random_tiles = sum(1 for t in tiles if t["type"] == 0)
    pool = sum(bt.values())
    return {
        "asset": data["asset"],
        "mapId": data["mapId"],
        "stage": data["stage"],
        "stage_count": data["stage_count"],
        "tile_count": len(tiles),
        "layer_count": len(layers),
        "max_stack": max(stacks.values(), default=0),
        "cells_used": len(stacks),
        "random_tiles": random_tiles,
        "fixed_tiles": len(tiles) - random_tiles,
        "block_kinds": len(bt),
        "match_sets": pool,                       # 3개씩 맞출 세트 수
        # 합×3 == 랜덤 타일 수 검증. blockTypeData가 없는 구형 에셋은 '-'
        "pool_ok": "-" if not pool else ("OK" if pool * 3 == random_tiles else "불일치"),
        "mold_kinds": len({t["moldType"] for t in tiles}),
        "version": data.get("version") if data.get("version") is not None else "",
    }


def _bounds(tiles):
    cs = [t["col"] for t in tiles]
    rs = [t["row"] for t in tiles]
    return min(cs), min(rs), max(cs), max(rs)


def board(data):
    """셀 색 = 그 좌표에 겹쳐 쌓인 타일 수. 타일 1개가 TILE_SPAN² 영역을 차지한다."""
    tiles = data["tiles"]
    if not tiles:
        return None
    c0, r0, c1, r1 = _bounds(tiles)
    w, h = c1 - c0 + TILE_SPAN, r1 - r0 + TILE_SPAN
    stacks = collections.Counter()
    for t in tiles:
        x0, y0 = t["col"] - c0, t["row"] - r0
        for dy in range(TILE_SPAN):
            for dx in range(TILE_SPAN):
                stacks[(x0 + dx, y0 + dy)] += 1
    marks = [(t["col"] - c0, t["row"] - r0) for t in tiles if t["type"] != 0]
    cells = [(x, y, min(n, MAX_STACK) - 1) for (x, y), n in stacks.items()]
    return {"w": w, "h": h, "cells": cells, "pixel_count": len(tiles),
            "overlays": {"fixed": {"points": marks, "style": "outline"}}}


def viewer_level(data):
    """뷰어 tiles 모드용 — 실제 배치를 그대로 넘긴다.

    tl = [레이어(0기준), x, y, type, flags]*  좌표는 1/TILE_SPAN 타일 단위, 0기준 정규화
    type -1 = 런타임 랜덤 배정(얼굴 이미지 없음), 그 외 = 고정 블록 → cardN 이미지
    tw/th = 보드 크기(유닛), lc = 레이어 수
    """
    tiles = data["tiles"]
    if not tiles:
        return {"ma": [], "sq": [], "tl": [], "lc": 0, "tw": 0, "th": 0}
    c0, r0, c1, r1 = _bounds(tiles)
    tl = []
    for t in sorted(tiles, key=lambda t: t["layer"]):
        tp = t["type"] if t["type"] != 0 else -1        # 0 = 랜덤 → 얼굴 없음
        tl.extend((max(0, t["layer"] - 1), t["col"] - c0, t["row"] - r0, tp, 0))
    stacks = collections.Counter((t["col"], t["row"]) for t in tiles)
    dist = collections.Counter(min(n, MAX_STACK) - 1 for n in stacks.values())
    bt = data.get("blockTypeData") or {}
    # 모달 칩: 이 스테이지에 등장하는 블록타입과 타일 수(세트×3)
    chips = [[int(k) if str(k).isdigit() else k, v * 3, -1]
             for k, v in sorted(bt.items(), key=lambda kv: (-kv[1], int(kv[0])))]
    sq = [[f"블록 풀 ({len(bt)}종 · ×3)", chips]] if chips else []
    return {"ma": [[k, v] for k, v in sorted(dist.items())], "sq": sq,
            "tl": tl, "lc": max(t["layer"] for t in tiles),
            "tw": c1 - c0 + TILE_SPAN, "th": r1 - r0 + TILE_SPAN}
