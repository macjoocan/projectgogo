"""Royal Match (com.dreamgames.royalmatch) 플러그인.

레벨은 FlatBuffers 바이너리 14,300개(TextAsset 이름 `1`~`14300`)다. Royal Kingdom과
같은 스튜디오(Dream Games)라 형식은 같지만 **열거형이 다르다** — Royal Kingdom의
TiledId를 그대로 쓰면 6번이 Match1(RK)이 아니라 Orange(RM)라서 전부 어긋난다.

이름은 전부 **앱에서 뽑은 확정값**이다:

  TiledId(429)·GoalType(105)  IL2CppDumper 로 뽑은 dump.cs 의 열거형
  필드 이름                   같은 덤프의 FlatBuffers 생성 클래스
                              (`FTiledLevel`·`FTiledGrid`·`FTiledCell`)
                              → tools/fbnames_from_dump.py 가 지도를 만든다

그래서 이 게임은 슬롯 번호가 아니라 `Name`·`Move`·`Grid.Cells[].Honey` 처럼
원래 이름으로 나온다. 14,300레벨 전부에서 셀 타입 100%가 이름이 붙었다(미상 0).
"""

#: 셀 타입 — 앱의 `Royal.Scenes.Game.Utils.LevelParser.TiledId` (429개)
TILED_ID = {
    0: "None", 1: "Blue", 2: "Green", 3: "Red", 4: "Yellow", 5: "Pink", 6: "Orange", 7:
    "Fill1", 8: "Fill2", 9: "Fill3", 10: "Propeller", 11: "Fill", 12: "Defined", 13:
    "Empty", 14: "Set1", 15: "Set2", 16: "Set3", 17: "Scroll", 19: "PurpleGrass", 20:
    "VerticalRocket", 21: "Box1", 22: "Box2", 23: "Box3", 24: "Box4", 25: "Vase", 26: "Egg",
    27: "OwlStatue1", 28: "OwlStatue2", 29: "OwlStatue3", 30: "HorizontalRocket", 31:
    "Grass1", 32: "Grass2", 33: "Honey1", 34: "MailBox", 35: "Bird", 36: "LogLeft", 37:
    "LogUp", 38: "LogDown", 39: "LogRight", 40: "Tnt", 41: "CupboardTL", 42: "CupboardTR",
    43: "PotionTL", 44: "PotionTR", 45: "BushTL", 46: "BushTR", 47: "SafeTL", 48: "SafeTR",
    49: "LogBase", 50: "Lightball", 51: "CupboardBL", 52: "CupboardBR", 53: "PotionBL", 54:
    "PotionBR", 55: "BushBL", 56: "BushBR", 57: "SafeBL", 58: "SafeBR", 59: "Piggy", 60:
    "Coin", 61: "BluePotionTL", 62: "BluePotionTR", 63: "GreenPotionTL", 64:
    "GreenPotionTR", 65: "RedPotionTL", 66: "RedPotionTR", 67: "YellowPotionTL", 68:
    "YellowPotionTR", 69: "PinkPotionTL", 70: "PinkPotionTR", 71: "BluePotionBL", 72:
    "BluePotionBR", 73: "GreenPotionBL", 74: "GreenPotionBR", 75: "RedPotionBL", 76:
    "RedPotionBR", 77: "YellowPotionBL", 78: "YellowPotionBR", 79: "PinkPotionBL", 80:
    "PinkPotionBR", 81: "BlueBox1", 82: "GreenBox1", 83: "RedBox1", 84: "YellowBox1", 85:
    "PinkBox1", 86: "Oyster", 87: "Hat", 88: "FlowerPot", 89: "GiantBirdTL", 90:
    "GiantBirdTR", 91: "BlueBox2", 92: "GreenBox2", 93: "RedBox2", 94: "YellowBox2", 95:
    "PinkBox2", 96: "DynamiteBoxTL", 97: "DynamiteBoxTR", 98: "Rock", 99: "GiantBirdBL",
    100: "GiantBirdBR", 101: "BlueBox3", 102: "GreenBox3", 103: "RedBox3", 104:
    "YellowBox3", 105: "PinkBox3", 106: "DynamiteBoxBL", 107: "DynamiteBoxBR", 108: "SoilA",
    109: "SoilB", 110: "SoilC", 111: "BlueCurtain", 112: "GreenCurtain", 113: "RedCurtain",
    114: "YellowCurtain", 115: "CupA", 116: "CupB", 117: "CupC", 118: "LightBulbTL", 119:
    "LightBulbTM", 120: "LightBulbTR", 121: "BirdBoxTL", 122: "BirdBoxTR", 123: "DrillUp",
    124: "DrillDown", 125: "Frog", 126: "LightBulbBLBlue", 127: "LightBulbBLGreen", 128:
    "LightBulbML", 129: "LightBulbMM", 130: "LightBulbMR", 131: "BirdBoxBL", 132:
    "BirdBoxBR", 133: "DrillRight", 134: "DrillLeft", 135: "CookieJar", 136:
    "LightBulbBLRed", 137: "LightBulbBLYellow", 138: "LightBulbBLPink", 139: "LightBulbBM",
    140: "LightBulbBR", 141: "MetalCrusherBase", 142: "MetalCrusherLeft", 143:
    "MetalCrusherUp", 144: "MetalCrusherDown", 145: "MetalCrusherRight", 146: "BowTieOn",
    147: "BowTieOff", 148: "CaldronItem", 149: "Chain1", 150: "Chain2", 151: "Pouch", 152:
    "Lantern", 153: "Roof", 154: "SeedBox", 155: "Ufo", 156: "Jelly", 157: "Soap", 158:
    "TreasureMap", 159: "MapScrollCollect", 160: "HoneyJar", 161: "BowlingTL", 162:
    "BowlingTR", 163: "GummyMakerTL", 164: "GummyMakerTR", 165: "WhackAMoleTL", 166:
    "WhackAMoleTR", 167: "Piggy2", 168: "Piggy3", 169: "IceCubeTL", 170: "IceCubeTR", 171:
    "BowlingBL", 172: "BowlingBR", 173: "GummyMakerBL", 174: "GummyMakerBR", 175:
    "WhackAMoleBL", 176: "WhackAMoleBR", 177: "PinkCurtain", 179: "IceCubeBL", 180:
    "IceCubeBR", 181: "DuckShootingTL", 182: "DuckShootingTM", 183: "DuckShootingTR", 184:
    "SlotMachineTL", 185: "SlotMachineTM", 186: "SlotMachineTR", 187: "Ceramic1", 188:
    "Ceramic2", 189: "MagnetHitEnd", 190: "MagnetNoHitEnd", 191: "DuckShootingML", 192:
    "DuckShootingMM", 193: "DuckShootingMR", 194: "SlotMachineBL", 195: "SlotMachineBM",
    196: "SlotMachineBR", 197: "DirectionUp", 198: "DirectionDown", 199: "DirectionRight",
    200: "DirectionLeft", 201: "DuckShootingBL", 202: "DuckShootingBM", 203:
    "DuckShootingBR", 204: "Fireworks", 205: "CandyCaneCenter", 206: "CandyCaneEnd", 207:
    "DirectionUpToRight", 208: "DirectionRightToDown", 209: "DirectionDownToLeft", 210:
    "DirectionLeftToUp", 211: "Match1", 212: "Match2", 213: "Match3", 214: "CoilTL", 215:
    "CoilTR", 216: "ConveyorBelt", 217: "DirectionUpToLeft", 218: "DirectionLeftToDown",
    219: "DirectionDownToRight", 220: "DirectionRightToUp", 221: "MushroomSoil", 223:
    "Mushroom", 224: "CoilML", 225: "CoilMR", 226: "CoilCollect", 227: "TabletA", 228:
    "TabletB", 229: "TabletC", 230: "IvyHead", 231: "GiantPiggyTL", 232: "GiantPiggyTR",
    233: "SeaMine", 234: "CoilBL", 235: "CoilBR", 236: "CrystalTL", 237: "CrystalTR", 238:
    "Water", 239: "WaterSoil", 240: "IvyEnd", 241: "GiantPiggyBL", 242: "GiantPiggyBR", 243:
    "BlindsA", 244: "BlindsB", 245: "BlindsC", 246: "CrystalBL", 247: "CrystalBR", 248:
    "ShifterStop", 249: "PorcelainMachine", 250: "PorcelainMachineFake", 251: "FurnaceTL",
    252: "FurnaceTR", 253: "DarkHoney", 254: "MagicGemBlueA", 255: "MagicGemBlueB", 256:
    "MagicGemBlueC", 257: "VendingOffTL", 258: "VendingOffTR", 259: "VendingOnTL", 260:
    "VendingOnTR", 261: "FurnaceBL", 262: "FurnaceBR", 263: "ToyBoxVerticalT", 264:
    "MagicGemGreenA", 265: "MagicGemGreenB", 266: "MagicGemGreenC", 267: "VendingOffML",
    268: "VendingOffMR", 269: "VendingOnML", 270: "VendingOnMR", 271: "ToyBoxHorizontalL",
    272: "ToyBoxHorizontalR", 273: "ToyBoxVerticalB", 274: "MagicGemRedA", 275:
    "MagicGemRedB", 276: "MagicGemRedC", 277: "VendingOffBL", 278: "VendingOffBR", 279:
    "VendingOnBL", 280: "VendingOnBR", 281: "AncientVaultBL", 282: "MagicCube", 283: "Pin",
    284: "MagicGemYellowA", 285: "MagicGemYellowB", 286: "MagicGemYellowC", 287:
    "ForceFieldA", 288: "ForceFieldB", 289: "ForceFieldC", 290: "ShuttleT", 291: "IglooTL",
    292: "IglooTR", 293: "DrillLogCollect", 294: "MagicGemPinkA", 295: "MagicGemPinkB", 296:
    "MagicGemPinkC", 297: "ForceFieldACenter", 298: "ForceFieldBCenter", 299:
    "ForceFieldCCenter", 300: "ShuttleB", 301: "IglooBL", 302: "IglooBR", 303: "DrillLogUp",
    304: "DrillLogDown", 305: "DrillLogRight", 306: "DrillLogLeft", 307: "Cryptex", 308:
    "Laser", 309: "IceBorder", 310: "SapphireBL", 311: "PowerCubeA", 312: "PowerCubeB", 313:
    "PowerCubeC", 314: "PotionTubeBlue", 315: "PotionTubeGreen", 316: "PotionTubeRed", 317:
    "PotionTubeYellow", 318: "PotionTubePink", 319: "PotionTubeFake", 320: "Portal", 321:
    "CuckooA", 322: "CuckooB", 323: "CuckooC", 324: "CuckooOffA", 325: "CuckooOffB", 326:
    "CuckooOffC", 327: "RoyalCapsuleVerticalB", 328: "ChocoMaker", 329: "BowlingRack", 330:
    "RoyalBot", 331: "GrassBombTL", 332: "GrassBombTM", 333: "GrassBombTR", 334:
    "PortalDoorTL", 335: "PortalDoorTM", 336: "PortalDoorTR", 337: "PropellerMachineTL",
    338: "PropellerMachineTR", 339: "SwordT", 340: "BoomerangBox", 341: "GrassBombML", 342:
    "GrassBombMM", 343: "GrassBombMR", 344: "PortalDoorML", 345: "PortalDoorMM", 346:
    "PortalDoorMR", 347: "PropellerMachineBL", 348: "PropellerMachineBR", 349: "SwordB",
    350: "MagicLanternB", 351: "GrassBombBL", 352: "GrassBombBM", 353: "GrassBombBR", 354:
    "PortalDoorBL", 355: "PortalDoorBM", 356: "PortalDoorBR", 357: "RadarTL", 358:
    "RadarTR", 359: "ClockTowerTL", 360: "ClockTowerTR", 361: "JellyBombTL", 362:
    "JellyBombTR", 363: "SquirrelVerticalT", 364: "SquirrelHorizontalL", 365:
    "SquirrelHorizontalR", 366: "RoofMachineUp", 367: "RadarBL", 368: "RadarBR", 369:
    "ClockTowerML", 370: "ClockTowerMR", 371: "JellyBombBL", 372: "JellyBombBR", 373:
    "SquirrelVerticalB", 374: "PairFirst", 375: "PairSecond", 376: "RoofMachineDown", 377:
    "RoofMachineLeft", 378: "RoofMachineRight", 379: "ClockTowerBL", 380: "ClockTowerBR",
    381: "BoxingGloveUp", 382: "BoxingGloveLeft", 383: "Lava", 384: "MetalPlateA", 385:
    "MetalPlateB", 386: "MetalPlateC", 387: "Turtle", 388: "ToyBoatTL", 389: "ToyBoatTR",
    391: "BoxingGloveDown", 392: "BoxingGloveRight", 393: "ColorMixerBL", 394:
    "PaintBucket", 395: "OtterOpen", 396: "OtterClosed", 398: "ToyBoatBL", 399: "ToyBoatBR",
    32734: "ColorMixerTL", 32735: "ColorMixerTR", 32736: "ColorMixerBR", 32737:
    "MagicLanternT", 32738: "PairTL", 32739: "PairML", 32740: "PairBL", 32741: "PairMM",
    32742: "PairBM", 32743: "PairBR", 32744: "Choco", 32745: "RoyalCapsuleHorizontalL",
    32746: "RoyalCapsuleVerticalT", 32747: "RoyalCapsuleHorizontalR", 32748: "SapphireTL",
    32749: "SapphireTM", 32750: "SapphireTR", 32751: "SapphireML", 32752: "SapphireMM",
    32753: "SapphireMR", 32754: "SapphireBM", 32755: "SapphireBR", 32756: "Capsule", 32757:
    "DrillLogFake", 32758: "Penguin", 32759: "AncientVaultTL", 32760: "AncientVaultTR",
    32761: "AncientVaultBR", 32762: "GummyBarHorizontalL", 32763: "GummyBarHorizontalR",
    32764: "GummyBarVerticalB", 32765: "GummyBarVerticalT", 32766: "Gummy", 32767: "Pumpkin"
}

#: 목표 종류 — 앱의 `GoalType` (105개)
GOAL_TYPE = {
    0: "None", 1: "Blue", 2: "Green", 3: "Orange", 4: "Red", 5: "Pink", 6: "Yellow", 7:
    "Rocket", 8: "Propeller", 9: "Tnt", 10: "Lightball", 11: "Box", 12: "Vase", 13: "Grass",
    14: "Honey", 15: "Cupboard", 16: "Egg", 17: "OwlStatue", 18: "Mail", 19: "Potion", 20:
    "Safe", 21: "Coin", 22: "Bush", 23: "Bird", 24: "GiantBird", 25: "ColorBox", 26:
    "IceCrusher", 27: "Piggy", 28: "Oyster", 29: "FlowerPot", 30: "PurpleGrass", 31:
    "DynamiteBox", 32: "Cup", 33: "BirdNest", 34: "Rock", 35: "Soil", 36: "LightBulb", 37:
    "Frog", 38: "MetalCrusher", 39: "Cookie", 40: "BowTie", 41: "Pumpkin", 42: "Chain", 43:
    "Pouch", 44: "Lantern", 45: "Bowling", 46: "Roof", 47: "Gummy", 48: "Ufo", 49: "Jelly",
    50: "Soap", 51: "WhackAMole", 52: "MapScrollCollect", 53: "TreasureMap", 54: "HoneyJar",
    55: "Bear", 56: "Ceramic", 58: "DuckShooting", 59: "SlotMachine", 60: "Magnet", 61:
    "CandyCane", 62: "ConveyorBelt", 63: "Fireworks", 64: "Coil", 65: "CoilCollect", 66:
    "MushroomSoil", 67: "Tablet", 68: "Crystal", 69: "Ivy", 70: "Blinds", 71: "SeaMine", 72:
    "VendingMachineCan", 73: "MagicGem", 74: "Furnace", 75: "ToyBoxHorizontal", 76:
    "ToyBoxVertical", 77: "AncientVault", 78: "Penguin", 79: "Log", 80: "LogCollect", 81:
    "Pin", 82: "Monkey", 83: "Laser", 84: "IceBorder", 85: "PowerCube", 86: "PotionTube",
    87: "Cuckoo", 88: "Sapphire", 89: "Choco", 90: "BowlingRack", 91: "Bot", 92:
    "PropellerMachine", 93: "Sword", 94: "BoomerangBox", 95: "Squirrel", 96: "Radar", 97:
    "ClockTower", 98: "MagicLantern", 99: "Pair", 100: "BoxingGlove", 101: "Lava", 102:
    "Turtle", 103: "ColorMixer", 104: "PaintBucket", 105: "OtterBall"
}

#: 판 구성 마커라서 기믹으로 세지 않는 것들. 색(Blue~Orange)은 그냥 조각이고
#: Fill 계열은 화면에 아무것도 안 그려지는 빈 통로, Set/Match/Defined/Empty 는
#: 판 모양 마커다 (Royal Kingdom 에서 확인한 것과 같은 규칙).
_NON_GIMMICK = frozenset((
    "None", "Empty", "Defined", "Blue", "Green", "Red", "Yellow", "Pink", "Orange",
    "Set1", "Set2", "Set3", "Match1", "Match2", "Match3", "Match4", "Match5",
    "Fill", "Fill1", "Fill2", "Fill3",
))

#: 화면에 아무것도 안 그리는 빈 통로
_PASSAGE = frozenset(("Fill", "Fill1", "Fill2", "Fill3"))


def tile_name(t):
    return TILED_ID.get(t, f"Unknown{t}")


def goal_name(g):
    return GOAL_TYPE.get(g, f"Goal{g}")


def is_gimmick(t):
    return tile_name(t) not in _NON_GIMMICK


def is_passage(t):
    return tile_name(t) in _PASSAGE


#: 칸별 기믹 필드 — 이름은 앱의 `FTiledCell` 에서 온 확정값이다.
#: `FillType`·`IsPredefined` 는 기믹이 아니라 파라미터라 뺀다.
#:
#: **추정**: 층 배정. Royal Kingdom 은 바텀(타일형·미션) / 노멀(상자류) / 커버(맨 위)
#: 세 층인데, 같은 스튜디오라 Royal Match 도 같은 구조로 본다. 다만 어느 필드가
#: 어느 층인지는 실제 화면으로 아직 대조하지 못했다. 바닥에 깔리는 성격
#: (잔디·꿀·젤리·버섯흙·물흙·얼음테두리·도자기)을 바텀, 위에서 덮는 성격
#: (사슬·커튼·지붕·블라인드·역장·암호상자·철판·보물지도)을 커버로 두었다.
_BOTTOM_FIELDS = ("Grass", "Honey", "Jelly", "MushroomSoil", "WaterSoil",
                  "IceBorder", "Ceramic")
_COVER_FIELDS = ("Curtain", "Chain", "Roof", "Blinds", "ForceField", "Cryptex",
                 "MetalPlates", "Treasuremap")

#: 이 값 미만은 색(1~6)이라 기믹이 아니다 — 커튼·보물지도처럼 색을 담는 필드가 있다.
_GIMMICK_MIN = 7


def _grid(data):
    g = data.get("Grid")
    return g if isinstance(g, dict) else {}


def _cells(data):
    v = _grid(data).get("Items")
    return v.get("items", []) if isinstance(v, dict) else []


def _cell_tables(data):
    v = _grid(data).get("Cells")
    return v.get("items", []) if isinstance(v, dict) else []


def layer_cells(data):
    """칸별 기믹 → {"bottom": {셀: [(필드, 타입)…]}, "cover": {…}}.

    한 칸에 기믹이 여럿 올 수 있으므로 목록으로 돌려준다. 모르는 필드는 커버로
    올린다 — 안 보이게 묻어두는 것보다 낫다.
    """
    bottom, cover = {}, {}
    for i, cell in enumerate(_cell_tables(data)):
        if not isinstance(cell, dict):
            continue
        for field in sorted(cell):
            v = cell[field]
            if field in ("FillType", "IsPredefined"):
                continue
            if not (isinstance(v, int) and v >= _GIMMICK_MIN and v in TILED_ID):
                continue
            side = bottom if field in _BOTTOM_FIELDS else cover
            side.setdefault(i, []).append((field, v))
    return {"bottom": bottom, "cover": cover}


def goals(data):
    """[(목표 이름, 개수)] — 앱의 GoalType 이름이 붙는다."""
    g = data.get("Goals")
    if not isinstance(g, dict):
        return []
    out = []
    for x in g.get("items", []):
        if isinstance(x, dict) and isinstance(x.get("Goal"), int):
            out.append((goal_name(x["Goal"]), x.get("Count") or 0))
    return out


def _count(seq):
    out = {}
    for x in seq:
        out[x] = out.get(x, 0) + 1
    return out


def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return out


def level_extras(data):
    """xlsx 컬럼."""
    g = _grid(data)
    cells = _cells(data)
    kinds = _count(cells)
    lay = layer_cells(data)
    bot = _count([t for ts in lay["bottom"].values() for _f, t in ts])
    cov = _count([t for ts in lay["cover"].values() for _f, t in ts])
    gl = goals(data)
    return {
        "name": data.get("Name") or "",
        "moves": data.get("Move") if isinstance(data.get("Move"), int) else 0,
        "grid_w": g.get("Width") if isinstance(g.get("Width"), int) else 0,
        "grid_h": g.get("Height") if isinstance(g.get("Height"), int) else 0,
        "cell_count": len(cells),
        "cell_kinds": len(kinds),
        "empty_cells": kinds.get(0, 0),
        "fill_cells": sum(1 for t in cells if isinstance(t, int) and is_passage(t)),
        "goal_kinds": len(gl),
        "goal_total": sum(n for _g, n in gl),
        "goals": ", ".join(f"{n} {name}" for name, n in gl[:5]),
        "gimmick_kinds": sum(1 for t in kinds if is_gimmick(t)) + len(bot) + len(cov),
        "gimmick_cells": (sum(n for t, n in kinds.items() if is_gimmick(t))
                          + sum(bot.values()) + sum(cov.values())),
        "gimmicks": ", ".join(
            tile_name(t) for _n, t in
            sorted(((n, t) for t, n in _merge(kinds, _merge(bot, cov)).items()
                    if is_gimmick(t)), reverse=True)[:6]),
        "bottom_cells": sum(bot.values()),
        "bottom_kinds": len(bot),
        "bottoms": ", ".join(tile_name(t) for _n, t in
                             sorted(((n, t) for t, n in bot.items()), reverse=True)[:4]),
        "cover_cells": sum(cov.values()),
        "cover_kinds": len(cov),
        "covers": ", ".join(tile_name(t) for _n, t in
                            sorted(((n, t) for t, n in cov.items()), reverse=True)[:4]),
        "chain_count": data.get("ChainCount") if isinstance(data.get("ChainCount"), int) else 0,
        "cage_count": data.get("CageCount") if isinstance(data.get("CageCount"), int) else 0,
        "scroll": "Y" if data.get("Scroll") else "",
        "has_hole": "Y" if data.get("HasHoleInGrid") else "",
    }


#: tiles 모드 좌표 단위 (설정의 viewer.tile_span 과 맞춰야 한다)
TILE_SPAN = 1


def viewer_level(data):
    """뷰어 tiles 모드용 — 바텀 → 노멀 → 커버 순으로 쌓는다.

    같은 층에 기믹이 여럿이면 층을 더 만든다. 하나만 그리고 나머지를 버리지 않는다.
    """
    g = _grid(data)
    w, h = g.get("Width"), g.get("Height")
    cells = _cells(data)
    if not (isinstance(w, int) and isinstance(h, int) and len(cells) == w * h):
        return {"tl": [], "lc": 0, "tw": 0, "th": 0, "sq": [], "ma": []}

    lay = layer_cells(data)
    tl = []

    def stack(side, first):
        depth = max((len(v) for v in side.values()), default=0)
        for i, ts in side.items():
            for k, (_f, t) in enumerate(ts):
                tl.extend((first + k, (i % w) * TILE_SPAN, (i // w) * TILE_SPAN, t, 0))
        return depth

    normal = stack(lay["bottom"], 0)
    for i, t in enumerate(cells):
        # 칸 없음(None)과 빈 통로(Fill 계열)는 아무것도 안 그린다 — 판 모양이 드러난다
        if not isinstance(t, int) or tile_name(t) == "None" or is_passage(t):
            continue
        tl.extend((normal, (i % w) * TILE_SPAN, (i // w) * TILE_SPAN, t, 0))
    layers = normal + 1 + stack(lay["cover"], normal + 1)

    counts = _count(cells)
    bot = _count([t for ts in lay["bottom"].values() for _f, t in ts])
    cov = _count([t for ts in lay["cover"].values() for _f, t in ts])
    gim = sorted(((n, t) for t, n in _merge(
        {t: n for t, n in counts.items() if is_gimmick(t)}, _merge(bot, cov)).items()),
        reverse=True)
    base = sorted(((n, t) for t, n in counts.items() if not is_gimmick(t)), reverse=True)
    sq = []
    gl = goals(data)
    if gim:
        sq.append([f"기믹 ({len(gim)}종)", [[t, n, -1] for n, t in gim[:24]]])
    for label, cnt, side in (("커버", cov, lay["cover"]), ("바텀", bot, lay["bottom"])):
        if cnt:
            sq.append([f"{label} ({len(cnt)}종 · {len(side)}칸)",
                       [[t, n, -1] for n, t in
                        sorted(((n, t) for t, n in cnt.items()), reverse=True)[:12]]])
    if base:
        sq.append(["판 구성", [[t, n, -1] for n, t in base[:8]]])
    ma = [f"{name} {n}" for name, n in gl[:6]]
    return {"tl": tl, "lc": layers, "tw": w * TILE_SPAN, "th": h * TILE_SPAN,
            "sq": sq, "ma": ma}


#: 팔레트 색인 상한 — 셀 타입 값이 이보다 크면 뭉쳐서 표시한다
_MAX_TYPE = 31


def board(data):
    """셀 타입 격자 → 뷰어 grid 모드 규격."""
    g = _grid(data)
    w, h = g.get("Width"), g.get("Height")
    cells = _cells(data)
    if not (isinstance(w, int) and isinstance(h, int) and 0 < w and 0 < h):
        return None
    if len(cells) != w * h:
        return None
    return {"w": w, "h": h,
            "cells": [(i % w, i // w, min(t, _MAX_TYPE))
                      for i, t in enumerate(cells) if isinstance(t, int)],
            "pixel_count": sum(1 for c in cells if c), "overlays": {}}
