"""Royal Kingdom (gg.com.dreamgames.royalkingdom) 플러그인.

레벨이 **FlatBuffers 바이너리**로 들어 있다 — 이름이 `1`~`4500` 인 TextAsset.
`.fbs` 스키마가 없어서 필드 이름은 슬롯 번호(`f0`·`f1`…)로 나온다. 아래 매핑은
값의 성질과 내부 정합성으로 확인한 것이다:

    f0  레벨 이름 문자열      "0001v01_E" … "4500v01_E" (번호와 1:1로 맞음)
    f1  이동 수               22~31 구간에 몰림 — 매치3 이동 수로 자연스러움
    f2  보드 테이블
          f0  셀 타입 int32 벡터   길이가 항상 f2×f3 과 정확히 일치 (4,500개 전수)
          f1  **셀 위에 덮인 것** 벡터  같은 길이. 커버형 기믹이 전부 여기 있다
              (담쟁이·얼음·사슬·테두리·모자이크). 처음엔 "대부분 빈 테이블"로
              넘겼는데 4,500개 전 레벨에 있고 합계 130,785칸이었다.
              검증: 7스테이지 화면의 목표가 "담쟁이 72"인데 Lv7 의 f2.f1
              비어있지 않은 칸이 정확히 72개이고 값이 전부 Ivy1(34)이다.
          f2  가로               8~9
          f3  세로               7~67
    f3  {f0, f1, f2} 테이블 벡터 — 구조는 확정, **의미는 미확정**

f3 에 대해 확인된 사실만 적는다:

    · 4,500개 중 447개(10%)에만 값이 있고 나머지는 빈 벡터다
    · f0 ∈ 1~8, f1 ∈ 10~111, f2 = 정수 벡터(대개 길이 1)
    · (f0, f1) 이 격자를 이룬다 (447개 중 281개는 빈칸 없는 완전격자)
    · f2 값은 보드 셀 타입과 **같은 ID 공간**을 쓴다 (26·36·90·24 등이 양쪽에 나온다)

의미를 좁히려 한 검사와 그 결과(둘 다 결론을 못 냈다):

    · f2 값이 그 레벨 보드 타입의 부분집합인가 → 211개는 예, 236개는 아니오
    · f3 유무가 난이도와 상관 있나 → 이동수 26.3 vs 26.7, 셀수 94.7 vs 95.1 로 차이 없음

목표(goal)라면 모든 레벨에 있어야 하는데 10%뿐이라 목표는 아니다. 그 이상은
게임을 직접 돌려 대조하기 전에는 단정할 수 없다.

가로×세로 = 셀 수가 4,500개 전부에서 맞으므로 f2 안쪽 매핑은 확실하다.
f1(이동 수)은 분포 근거이므로 **추정**으로 표시한다.
"""

#: 보드 슬롯 경로
_BOARD = "f2"

#: TiledId 열거형 (IL2CPP 메타데이터에서 복원). 셀 타입 번호 → 기믹 이름.
#: 4,500 레벨에서 실제로 쓰인 178종이 모두 이 표 안에 있다 (미상 0).
TILED_ID = {
    0: "None", 1: "Blue", 2: "Green", 3: "Red", 4: "Yellow", 5: "Pink", 6: "Match1",
    7: "Match2", 8: "Match3", 9: "Match4", 10: "Spinner", 11: "Fill", 12: "Defined",
    13: "Empty", 14: "Set1", 15: "Set2", 16: "Set3", 17: "Fill1", 18: "Fill2", 19: "Fill3",
    20: "VerticalRocket", 21: "Box1", 22: "Box2", 23: "Box3", 24: "Safe", 25: "Turtle",
    26: "Vase", 27: "Birdhouse", 28: "Curtain", 29: "Lyre", 30: "HorizontalRocket",
    31: "Ice1", 32: "Ice2", 33: "Jelly", 34: "Ivy1", 35: "Ivy2", 36: "Lantern", 37: "Gnome",
    38: "ClockTL", 39: "ClockTR", 40: "Dynamite", 41: "ChaliceBoxTL", 42: "ChaliceBoxTR",
    43: "ColumnCrusher", 44: "ColumnLeft", 45: "ColumnUp", 46: "ColumnDown",
    47: "ColumnRight", 48: "ClockBL", 49: "ClockBR", 50: "ElectroBall", 51: "ChaliceBoxBL",
    52: "ChaliceBoxBR", 53: "WallA", 54: "WallB", 55: "WallC", 56: "TargetA", 57: "TargetB",
    58: "TargetC", 59: "GemOn", 60: "GemOff", 61: "MagicOrbTL", 62: "MagicOrbTR",
    63: "MagicOrbCurtainTL", 64: "MagicOrbCurtainTR", 65: "SnowmanTL", 66: "SnowmanTR",
    67: "SteamBombTL", 68: "SteamBombTR", 69: "KnightTL", 70: "KnightTR",
    71: "ColorMagicOrbBL", 72: "MagicOrbBR", 73: "ColorMagicOrbBL2", 74: "MagicOrbCurtainBR",
    75: "SnowmanBL", 76: "SnowmanBR", 77: "SteamBombBL", 78: "SteamBombBR", 79: "KnightBL",
    80: "KnightBR", 81: "YellowMagicOrbBL", 82: "RedMagicOrbBL", 83: "GreenMagicOrbBL",
    84: "BlueMagicOrbBL", 85: "PinkMagicOrbBL", 86: "MetalCrate1", 87: "MetalCrate2",
    88: "MetalCrate3", 89: "FlowerPot", 90: "Log", 91: "DragonBoxTL", 92: "DragonBoxTR",
    93: "TurtleHouseTL", 94: "TurtleHouseTR", 95: "Magnet", 96: "Cannon",
    97: "CannonFlipped", 98: "Lily", 99: "Gnome3", 100: "Gnome2", 101: "DragonBoxBL",
    102: "DragonBoxBR", 103: "TurtleHouseBL", 104: "TurtleHouseBR",
    105: "MetalColumnCrusher", 106: "MetalColumnLeft", 107: "MetalColumnUp",
    108: "MetalColumnDown", 109: "MetalColumnRight", 110: "Volcano", 111: "DirectionUp",
    112: "DirectionDown", 113: "DirectionRight", 114: "DirectionLeft", 115: "LightbulbTL",
    116: "LightbulbTM", 117: "LightbulbTR", 118: "LightbulbBLBlue", 119: "LightbulbBLGreen",
    120: "Chain1", 121: "DirectionUpToRight", 122: "DirectionRightToDown",
    123: "DirectionDownToLeft", 124: "DirectionLeftToUp", 125: "LightbulbML",
    126: "LightbulbMM", 127: "LightbulbMR", 128: "LightbulbBLRed", 129: "LightbulbBLYellow",
    130: "Chain2", 131: "DirectionUpToLeft", 132: "DirectionLeftToDown",
    133: "DirectionDownToRight", 134: "DirectionRightToUp", 135: "LightbulbBLPink",
    136: "LightbulbBM", 137: "LightbulbBR", 138: "Mask", 139: "Border", 140: "GiftBox",
    141: "MagicCardsTL", 142: "MagicCardsTM", 143: "MagicCardsTR", 144: "MagicCardsBLS",
    145: "MagicCardsBLD", 146: "Starfish", 147: "TabletA", 148: "TabletB", 149: "TabletC",
    150: "Barrel", 151: "MagicCardsBL", 152: "MagicCardsBM", 153: "MagicCardsBR",
    154: "MagicCardsBLR", 155: "MagicCardsBLE", 156: "Puzzle", 157: "PuzzleBox",
    158: "ArmoryTL", 159: "ArmoryTM", 160: "ArmoryTR", 161: "JellyMakerTL",
    162: "JellyMakerTR", 163: "Flowers", 164: "Gong", 165: "TimberMachine",
    166: "SpaceshipTL", 167: "SpaceshipTR", 168: "ArmoryML", 169: "ArmoryMM",
    170: "ArmoryMR", 171: "JellyMakerBL", 172: "JellyMakerBR", 173: "MagicGlobe",
    174: "MultiBoard", 175: "Accordion", 176: "SpaceshipML", 177: "SpaceshipMR",
    178: "ArmoryBL", 179: "ArmoryBM", 180: "ArmoryBR", 181: "Tube", 182: "Penguin",
    183: "Mosaic", 186: "SpaceshipBL", 187: "SpaceshipBR", 188: "PowerCapsules",
    189: "MaceBoxTL", 190: "MaceBoxTR", 191: "MushroomsCloseTL", 192: "MushroomsCloseTM",
    193: "MushroomsCloseTR", 194: "MushroomsOpenTL", 195: "MushroomsOpenTM",
    196: "MushroomsOpenTR", 197: "ParrotT", 199: "MaceBoxBL", 200: "MaceBoxBR",
    201: "MushroomsCloseBL", 202: "MushroomsCloseBM", 203: "MushroomsCloseBR",
    204: "MushroomsOpenBL", 205: "MushroomsOpenBM", 206: "MushroomsOpenBR", 207: "ParrotB",
    10000: "DragonSmallBoxVerticalB", 10001: "DragonSmallBoxVerticalT",
    10002: "DragonSmallBoxHorizontalL", 10003: "DragonSmallBoxHorizontalR",
    10004: "DragonEgg", 10005: "ArsenalMissile", 10006: "Blinds", 10007: "IceCube",
    10008: "FireDragonEgg", 10009: "Sand", 10010: "Parchment", 10011: "TimberBody",
    10012: "ColumnBody", 10013: "MetalColumnBody", 10014: "MaceSmallBox"
}

#: 전투 보드 전용 열거형 (AttackTiledId). 끝자리가 5·0 인 레벨(5의 배수)은
#: 일반 매치3가 아니라 **전투 퍼즐**이고, 보드 타일이 이 다른 ID 공간을 쓴다.
#: 성(Tower)·문(Gate)·골렘·문어·두더지 같은 전투 요소가 들어 있다.
ATTACK_TILED_ID = {
    0: "None", 1: "Wave", 11: "Gate0", 12: "Gate1", 13: "Gate2", 14: "TowerTL",
    15: "TowerTR", 19: "SwitcherClosedTL", 20: "SwitcherClosedTR", 21: "Castle6",
    22: "Castle7", 23: "Castle8", 24: "TowerBL", 25: "TowerBR", 29: "SwitcherClosedBL",
    30: "SwitcherClosedBR", 31: "Castle3", 32: "Castle4", 33: "Castle5", 34: "Shield",
    36: "ArsenalTL", 37: "ArsenalTM", 38: "ArsenalTR", 39: "SwitcherOpenTL",
    40: "SwitcherOpenTR", 41: "Castle0", 42: "Castle1", 43: "Castle2", 44: "MaceHead",
    46: "ArsenalML", 47: "ArsenalMM", 48: "ArsenalMR", 49: "SwitcherOpenBL",
    50: "SwitcherOpenBR", 51: "MetalTowerTL", 52: "MetalTowerTR", 53: "WaterTowerTL",
    54: "WaterTowerTR", 56: "ArsenalBL", 57: "ArsenalBM", 58: "ArsenalBR", 59: "MagicWallA",
    60: "MagicWallB", 61: "MetalTowerBL", 62: "MetalTowerBR", 63: "WaterTowerBL",
    64: "WaterTowerBR", 65: "WaterAT", 66: "WaterBT", 67: "BossScarecrowTL",
    68: "BossScarecrowTM", 69: "BossScarecrowTR", 70: "BossScarecrowGround1", 71: "MoleTL",
    72: "MoleTR", 73: "WaterTowerIgnoreBL", 74: "WaterTowerIgnoreBR", 75: "WaterAM",
    76: "WaterBM", 77: "BossScarecrowML", 78: "BossScarecrowMM", 79: "BossScarecrowMR",
    80: "BossScarecrowGround2", 81: "MoleBL", 82: "MoleBR", 83: "MoleSoil1", 84: "MoleSoil2",
    85: "WaterAB", 86: "WaterBB", 87: "BossScarecrowBL", 88: "BossScarecrowBM",
    89: "BossScarecrowBR", 90: "IceBlockHead", 91: "GoldGolemTL", 92: "GoldGolemTM",
    93: "GoldGolemTR", 94: "SilverGolemTL", 95: "SilverGolemTR", 96: "BossGuardTL",
    97: "BossGuardTM", 98: "BossGuardTR", 99: "TurtleTL", 100: "TurtleTR",
    101: "GoldGolemML", 102: "GoldGolemMM", 103: "GoldGolemMR", 104: "SilverGolemBL",
    105: "SilverGolemBR", 106: "BossGuardML", 107: "BossGuardMM", 108: "BossGuardMR",
    109: "TurtleBL", 110: "TurtleBR", 111: "GoldGolemBL", 112: "GoldGolemBM",
    113: "GoldGolemBR", 114: "BronzeGolem", 115: "Chest", 116: "BossGuardBL",
    117: "BossGuardBM", 118: "BossGuardBR", 119: "BomberTL", 120: "BomberTR",
    121: "SilverGolemGround", 122: "GoldGolemGround", 123: "MagnetHead", 124: "DirectionUp",
    125: "DirectionDown", 126: "DirectionRight", 127: "DirectionLeft", 128: "SnakeHead",
    129: "BomberBL", 130: "BomberBR", 131: "GiantMoleTL", 132: "GiantMoleTM",
    133: "GiantMoleTR", 134: "DirectionUpToRight", 135: "DirectionRightToDown",
    136: "DirectionDownToLeft", 137: "DirectionLeftToUp", 138: "ProtectorTowerTL",
    139: "ProtectorTowerTR", 140: "Octopus", 141: "GiantMoleML", 142: "GiantMoleMM",
    143: "GiantMoleMR", 144: "DirectionUpToLeft", 145: "DirectionLeftToDown",
    146: "DirectionDownToRight", 147: "DirectionRightToUp", 148: "ProtectorTowerBL",
    149: "ProtectorTowerBR", 150: "Seed", 151: "GiantMoleBL", 152: "GiantMoleBM",
    153: "GiantMoleBR", 154: "TeslaCollected15", 155: "PharaohTL", 156: "PharaohTM",
    157: "PharaohTR", 158: "Mummy", 159: "CannonTL", 160: "CannonTR", 161: "TeslaTL",
    162: "TeslaTR", 163: "TeslaCollected5", 164: "TeslaCollected20", 165: "PharaohML",
    166: "PharaohMM", 167: "PharaohMR", 168: "Cactus", 169: "CannonBL", 170: "CannonBR",
    171: "TeslaBL", 172: "TeslaBR", 173: "TeslaCollected10", 174: "TeslaCollected25",
    175: "PharaohBL", 176: "PharaohBM", 177: "PharaohBR", 178: "Raccoon",
    179: "CannonBallHeadA", 180: "CannonBallHeadB", 181: "BlacksmithTL", 182: "BlacksmithTM",
    183: "BlacksmithTR", 184: "PandaTL", 185: "PandaTR", 186: "TrojanHorseTL",
    187: "TrojanHorseTM", 188: "TrojanHorseTR", 189: "GenieTL", 190: "GenieTR",
    191: "BlacksmithML", 192: "BlacksmithMM", 193: "BlacksmithMR", 194: "PandaBL",
    195: "PandaBR", 196: "TrojanHorseML", 197: "TrojanHorseMM", 198: "TrojanHorseMR",
    199: "GenieBL", 200: "GenieBR", 201: "BlacksmithBL", 202: "BlacksmithBM",
    203: "BlacksmithBR", 204: "FireGateLeft", 205: "FireGateRight", 206: "TrojanHorseBL",
    207: "TrojanHorseBM", 208: "TrojanHorseBR", 209: "Ghost", 211: "GiantOctopus6",
    212: "GiantOctopus7", 213: "GiantOctopus8", 214: "GiantOctopusWater",
    221: "GiantOctopus3", 222: "GiantOctopus4", 223: "GiantOctopus5", 224: "GiantOctopusArm",
    231: "GiantOctopus0", 232: "GiantOctopus1", 233: "GiantOctopus2", 234: "Cloud",
    10000: "Pumpkin", 10001: "MagnetBody", 10002: "Mushroom", 10010: "BossPumpkinBL",
    10011: "BossPumpkinTL", 10012: "BossPumpkinBR", 10013: "BossPumpkinTR",
    10050: "SnakeBody", 10051: "IceBlockBody", 10052: "IcePenguin", 10053: "MaceBody",
    10055: "CannonBallBody", 10056: "TrojanWarrior", 10057: "FireGateBody",
    20000: "Playable", 20001: "PlayableFake"
}

#: 전투 타일 번호를 일반 타일과 섞이지 않게 띄우는 값 (뷰어 아이콘 파일명에 쓰인다)
BATTLE_ID_OFFSET = 100000


def battle_name(t):
    return ATTACK_TILED_ID.get(t, f"Unknown{t}")


#: 기믹이 아닌 것 — 판 구성 마커다. 장애물이 아니라 "이 칸은 이런 성격" 표시라서
#: 기믹 집계에서 뺀다. 뷰어에서도 전부 같은 빈 칸 타일로 그린다
#: (전용 아트가 없다 — 억지로 다른 이미지를 붙이면 없는 구분을 만들어내게 된다).
_NON_GIMMICK = frozenset((
    "None", "Empty", "Defined",
    "Set1", "Set2", "Set3",
    "Match1", "Match2", "Match3", "Match4",
    "Fill", "Fill1", "Fill2", "Fill3",
))

#: 화면에 아무것도 그려지지 않는 칸. 실제 게임 화면(Lv151)에서 Fill 줄과 None 줄이
#: 똑같은 "빈 틈"으로 보였다 — 칸은 있지만 타일이 없는 통로다. 장애물이 아니므로
#: 기믹으로 세지 않고, 뷰어에서도 타일을 그리지 않는다. 대신 fill_cells 로 센다.
_EMPTY_PASSAGE = frozenset(("Fill", "Fill1", "Fill2", "Fill3"))


def is_passage(t):
    return tile_name(t) in _EMPTY_PASSAGE
#
# Fill 계열은 뺐다. 처음엔 판 구성으로 묶었는데 배치를 보니 아니다 —
# Set1 은 판 전체를 채우는 반면(Lv2801: 99칸 중 94칸), Fill 은 대칭 블록으로
# 놓인다(Lv2878: `###ggg###` 형태). 성격이 다르므로 기믹으로 센다.


def tile_name(t):
    return TILED_ID.get(t, f"Unknown{t}")


def is_gimmick(t):
    return tile_name(t) not in _NON_GIMMICK



def _board_table(data):
    b = data.get(_BOARD)
    return b if isinstance(b, dict) else {}


def _cells(data):
    v = _board_table(data).get("f0")
    return v.get("items", []) if isinstance(v, dict) else []


#: 팔레트 색인 상한 — 셀 타입 값이 이보다 크면 뭉쳐서 표시한다
_MAX_TYPE = 31


def board(data):
    """셀 타입 격자 → 뷰어 보드 규격 {w, h, cells[(x,y,material)], overlays}.

    셀 벡터는 행 우선이라고 보고 펼친다 (길이가 항상 w×h 와 맞는다).
    타입 값이 팔레트 범위를 넘으면 뭉쳐서 마지막 색으로 보낸다 — 실제 값은
    xlsx 의 cell_kinds 와 모달 상세에서 확인할 수 있다.
    """
    bt = _board_table(data)
    w, h = bt.get("f2"), bt.get("f3")
    cells = _cells(data)
    if not (isinstance(w, int) and isinstance(h, int) and 0 < w and 0 < h):
        return None
    if len(cells) != w * h:
        return None
    out = []
    for i, t in enumerate(cells):
        if not isinstance(t, int):
            continue
        out.append((i % w, i // w, min(t, _MAX_TYPE)))
    return {"w": w, "h": h, "cells": out,
            "pixel_count": sum(1 for c in cells if c), "overlays": {}}


def level_extras(data):
    """xlsx 컬럼."""
    bt = _board_table(data)
    cells = _cells(data)
    kinds = {}
    for c in cells:
        kinds[c] = kinds.get(c, 0) + 1
    lay = layer_cells(data)                  # 바텀(타일형·미션) / 커버(맨 위)
    bot_kinds = _count([t for ts in lay["bottom"].values() for t in ts])
    cov_kinds = _count([t for ts in lay["cover"].values() for t in ts])
    ov_kinds = _merge(bot_kinds, cov_kinds)
    n_over = sum(ov_kinds.values())
    tbl = _f3_stats(data)
    return {
        "name": data.get("f0") or "",
        "moves": data.get("f1") if isinstance(data.get("f1"), int) else 0,
        "grid_w": bt.get("f2") if isinstance(bt.get("f2"), int) else 0,
        "grid_h": bt.get("f3") if isinstance(bt.get("f3"), int) else 0,
        "cell_count": len(cells),
        "cell_kinds": len(kinds),
        "empty_cells": kinds.get(0, 0),
        # 기믹 — 이름은 TiledId 열거형에서 온 확정값이다
        "gimmick_kinds": (sum(1 for t in kinds if is_gimmick(t)) + len(ov_kinds)),
        "gimmick_cells": (sum(n for t, n in kinds.items() if is_gimmick(t)) + n_over),
        "gimmicks": ", ".join(
            tile_name(t) for _n, t in
            sorted(((n, t) for t, n in
                    _merge(kinds, ov_kinds).items() if is_gimmick(t)), reverse=True)[:6]),
        "fill_cells": sum(1 for t in cells if isinstance(t, int) and is_passage(t)),
        # 커버 = 맨 위(담쟁이·사슬), 바텀 = 맨 아래 타일형·미션(얼음·테두리·모자이크)
        "cover_cells": sum(cov_kinds.values()),
        "cover_kinds": len(cov_kinds),
        "covers": ", ".join(tile_name(t) for _n, t in
                            sorted(((n, t) for t, n in cov_kinds.items()), reverse=True)[:4]),
        "bottom_cells": sum(bot_kinds.values()),
        "bottom_kinds": len(bot_kinds),
        "bottoms": ", ".join(tile_name(t) for _n, t in
                             sorted(((n, t) for t, n in bot_kinds.items()), reverse=True)[:4]),
        # f3 — 이름을 못 붙였으므로 슬롯 이름 그대로 둔다
        "f3_entries": tbl["n"],
        "f3_f0_max": tbl["f0_max"],
        "f3_f1_span": tbl["f1_span"],
        **_battle_extras(data),
    }


def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return out


def _battle_extras(data):
    """전투 퍼즐 관련 컬럼. 일반 레벨이면 0/빈값으로 채운다."""
    boards = battle_boards(data)
    if not boards:
        return {"mode": "일반", "battle_waves": 0, "battle_grid": "",
                "battle_kinds": 0, "battle_units": ""}
    kinds = {}
    for _w, _h, cells in boards:
        for c in cells:
            if c and battle_name(c) != "None":
                kinds[c] = kinds.get(c, 0) + 1
    top = sorted(((n, t) for t, n in kinds.items()), reverse=True)[:5]
    return {
        "mode": "전투",
        "battle_waves": len(boards),
        "battle_grid": " / ".join(f"{w}×{h}" for w, h, _c in boards),
        "battle_kinds": len(kinds),
        "battle_units": ", ".join(battle_name(t) for _n, t in top),
    }


#: 오버레이 값이 이 번호 이상이면 기믹으로 본다.
#: 0~19 는 색(Blue~Pink)·판 구성 마커(Set·Match·Fill)라 덮개가 아니다.
_OVERLAY_MIN = 20


#: 보드는 **세 층**이다 (게임 구조).
#:
#:   바텀   타일형 기믹 · 미션이 깔리는 맨 아래 — 얼음 · 테두리 · 모자이크
#:   노멀   상자 같은 기믹이 놓이는 층 — `f2.f0` 셀 벡터가 이것이다
#:   커버   맨 위. 아래를 다 덮는다 — 담쟁이 · 사슬
#:
#: 슬롯마다 기믹 종류가 딱 갈린다(4,500레벨 실측): f3 얼음 17,377칸 · f5 담쟁이
#: 11,627 · f7 사슬 3,568 · f9 테두리 10,159 · f11 모자이크 3,967. 나머지 슬롯
#: (f0·f1·f2·f4·f6·f10·f12)은 1~5 같은 작은 정수라 타일 타입이 아니라 파라미터다.
#:
#: 층 배정 근거 — 9스테이지 실제 화면에서 아래 세 줄이 **나무 상자**로 보이는데
#: 그 칸들은 노멀 Box2 + 얼음이다. 상자가 보이므로 얼음이 아래(바텀)다. 반대로
#: 담쟁이는 7스테이지에서 칸을 통째로 가려 커버다. 얼음은 담쟁이(663칸)·사슬(397)·
#: 테두리(352)·모자이크(245)와 겹쳐 나오므로 이들과 다른 층이어야 맞다.
_BOTTOM_SLOTS = ("f3", "f9", "f11")
_COVER_SLOTS = ("f5", "f7")


def layer_cells(data):
    """`f2.f1` 셀 테이블 → {"bottom": {셀: [타입…]}, "cover": {셀: [타입…]}}.

    한 칸에 기믹이 여럿 올 수 있다(얼음+담쟁이 663칸, 얼음+사슬 397칸 …).
    예전엔 칸마다 **하나만** 집고 나머지를 버렸다. 목록으로 돌려준다.

    모르는 슬롯에 기믹 값이 들어 있으면 커버로 올린다 — 안 보이게 묻어두는 것보다
    낫다. "없다"와 "못 읽었다"는 다르다.
    """
    per = _board_table(data).get("f1")
    if not isinstance(per, dict):
        return {"bottom": {}, "cover": {}}
    bottom, cover = {}, {}
    for i, cell in enumerate(per.get("items", [])):
        if not isinstance(cell, dict):
            continue
        for slot in sorted(cell):
            v = cell[slot]
            if not (isinstance(v, int) and v >= _OVERLAY_MIN and v in TILED_ID):
                continue
            side = bottom if slot in _BOTTOM_SLOTS else cover
            side.setdefault(i, []).append(v)
    return {"bottom": bottom, "cover": cover}


def overlay_cells(data):
    """바텀·커버를 합친 평면 보기 → {셀 인덱스: TiledId}.

    칸마다 하나만 남으므로 개수 세는 용도로는 쓰지 말 것. `layer_cells` 를 쓴다.
    """
    lay = layer_cells(data)
    out = {}
    for side in ("bottom", "cover"):
        for i, ts in lay[side].items():
            out.setdefault(i, ts[0])
    return out


def battle_boards(data):
    """전투 퍼즐의 단계별 보드 → [(가로, 세로, 셀타입 리스트)].

    `f7` 이 있으면 전투 레벨이다. 실측으로 **f7 보유 900개 == 5의 배수 900개** 가
    완전히 일치했다 (레벨 번호 끝자리가 5 또는 0). 일반 레벨과 성격이 확연히 다르다:

        5의 배수   셀수 62.0 · 기믹종류 0.77
        나머지     셀수 103.3 · 기믹종류 8.35

    f7.f1 이 단계(웨이브) 벡터고 원소마다 자기 보드를 갖는다 — 1~3단계, 9×10 또는
    8×10. 셀수 = 가로×세로 정합성이 1,748개 보드 전부에서 맞는다.
    타일 번호는 일반 보드와 **다른 열거형**(AttackTiledId)을 쓴다.
    """
    f7 = data.get("f7")
    if not isinstance(f7, dict):
        return []
    waves = f7.get("f1")
    if not isinstance(waves, dict):
        return []
    out = []
    for ph in waves.get("items", []):
        if not isinstance(ph, dict):
            continue
        w, h, g = ph.get("f1"), ph.get("f2"), ph.get("f3")
        cells = g.get("items", []) if isinstance(g, dict) else []
        if isinstance(w, int) and isinstance(h, int) and len(cells) == w * h:
            out.append((w, h, cells))
    return out


def is_battle(data):
    return bool(battle_boards(data))


def _f3_stats(data):
    """f3 벡터의 형태만 수치로 낸다 (의미를 모르므로 해석하지 않는다)."""
    v = data.get("f3")
    items = v.get("items", []) if isinstance(v, dict) else []
    rows = [x for x in items if isinstance(x, dict)]
    if not rows:
        return {"n": 0, "f0_max": 0, "f1_span": 0}
    f0 = [x.get("f0", 1) for x in rows if isinstance(x.get("f0", 1), int)]
    f1 = [x["f1"] for x in rows if isinstance(x.get("f1"), int)]
    return {"n": len(rows),
            "f0_max": max(f0) if f0 else 0,
            "f1_span": (max(f1) - min(f1) + 1) if f1 else 0}


#: tiles 모드 좌표 단위 (설정의 viewer.tile_span 과 맞춰야 한다)
TILE_SPAN = 1


def viewer_level(data):
    """뷰어 tiles 모드용 — 셀을 원본 기믹 이미지로 그리게 한다.

    tl = [레이어, x, y, 타입, 플래그]*  — 로열 킹덤은 한 겹이라 레이어는 0 고정.
    빈칸(None)은 아예 넣지 않아 판 모양이 그대로 드러난다.
    sq = 모달 칩. 기믹만 추려 많은 순으로 — 이름은 TiledId 에서 온 확정값이다.
    """
    bt = _board_table(data)
    w, h = bt.get("f2"), bt.get("f3")
    cells = _cells(data)
    if not (isinstance(w, int) and isinstance(h, int) and len(cells) == w * h):
        return {"tl": [], "lc": 0, "tw": 0, "th": 0, "sq": [], "ma": []}

    # 아래에서 위로 바텀 → 노멀 → 커버 순으로 쌓는다. 한 칸에 같은 층 기믹이
    # 여럿이면 층을 더 만든다 — 하나만 그리고 나머지를 버리지 않기 위해서다.
    lay = layer_cells(data)
    tl = []

    def stack(side, first):
        """side 의 기믹을 first 층부터 쌓고, 쓴 층 수를 돌려준다."""
        depth = max((len(v) for v in side.values()), default=0)
        for i, ts in side.items():
            for k, t in enumerate(ts):
                tl.extend((first + k, (i % w) * TILE_SPAN, (i // w) * TILE_SPAN, t, 0))
        return depth

    nlayer = stack(lay["bottom"], 0)
    normal = nlayer
    for i, t in enumerate(cells):
        # None(칸 없음)과 Fill 계열(빈 통로)은 화면에 아무것도 안 그린다 —
        # 실제 게임에서 둘 다 빈 틈으로 보인다 (Lv151 3행 None / 7행 Fill).
        if not isinstance(t, int) or tile_name(t) == "None" or is_passage(t):
            continue
        tl.extend((normal, (i % w) * TILE_SPAN, (i // w) * TILE_SPAN, t, 0))
    base_layers = normal + 1 + stack(lay["cover"], normal + 1)

    bot_counts = _count([t for ts in lay["bottom"].values() for t in ts])
    cov_counts = _count([t for ts in lay["cover"].values() for t in ts])
    counts = _count(cells)
    gim = sorted(((n, t) for t, n in _merge(_merge(
        {t: n for t, n in counts.items() if is_gimmick(t)},
        bot_counts), cov_counts).items()), reverse=True)
    base = sorted(((n, t) for t, n in counts.items() if not is_gimmick(t)), reverse=True)
    sq = []
    if gim:
        sq.append([f"기믹 ({len(gim)}종)", [[t, n, -1] for n, t in gim[:24]]])
    for label, cnt, cells_ in (("커버", cov_counts, lay["cover"]),
                               ("바텀", bot_counts, lay["bottom"])):
        if cnt:
            sq.append([f"{label} ({len(cnt)}종 · {len(cells_)}칸)",
                       [[t, n, -1] for n, t in sorted(((n, t) for t, n in cnt.items()),
                                                      reverse=True)[:12]]])
    if base:
        sq.append(["판 구성", [[t, n, -1] for n, t in base[:8]]])

    # 전투 퍼즐이면 단계별 보드를 레이어로 얹는다 — 모달 슬라이더로 벗겨 볼 수 있다.
    # 타일 번호는 일반 보드와 ID 공간이 달라서 BATTLE_ID_OFFSET 만큼 띄운다
    # (안 띄우면 24가 일반 Safe 인지 전투 TowerBL 인지 구별이 안 된다).
    layers, tw, th = base_layers, w * TILE_SPAN, h * TILE_SPAN
    for bw, bh, bcells in battle_boards(data):
        for i, t in enumerate(bcells):
            if not isinstance(t, int) or battle_name(t) == "None":
                continue
            tl.extend((layers, (i % bw) * TILE_SPAN, (i // bw) * TILE_SPAN,
                       BATTLE_ID_OFFSET + t, 0))
        tw = max(tw, bw * TILE_SPAN)
        th = max(th, bh * TILE_SPAN)
        bc = _count(bcells)
        chips = sorted(((n, t) for t, n in bc.items() if t and battle_name(t) != "None"),
                       reverse=True)[:20]
        if chips:
            sq.append([f"전투 {layers}단계", [[BATTLE_ID_OFFSET + t, n, -1] for n, t in chips]])
        layers += 1

    return {"tl": tl, "lc": layers, "tw": tw, "th": th, "sq": sq, "ma": []}


def _count(seq):
    out = {}
    for x in seq:
        out[x] = out.get(x, 0) + 1
    return out
