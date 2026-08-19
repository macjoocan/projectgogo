"""Royal Kingdom 다중칸 기믹 아이콘 생성.

한 기믹이 여러 칸을 차지할 때(2×2 성궤 상자, 2×2 마법 커튼 …) 열거형 이름 끝에
**칸 위치가 그대로 적혀 있다** — `ChaliceBoxTL`·`ChaliceBoxBR` 처럼 앞 글자가 행
(T/M/B), 뒷 글자가 열(L/M/R)이다.

예전 아이콘은 이걸 무시하고 **칸마다 원본 전체를 그렸다.** 2×2 기믹 하나가 화면에
4개로 보였다(44스테이지 실제 화면에는 성궤 상자가 5개인데 뷰어는 20개처럼 보임).
여기서는 원본을 행×열로 잘라 각 칸에 제 조각을 준다 — 나란히 놓이면 원래 그림이 된다.

원본 스프라이트는 **이름으로 확인한 것만** 쓴다. 못 찾은 기믹은 아이콘을 만들지
않는다(뷰어가 타입 번호를 그대로 보여주므로 "그림이 없다"가 드러난다). 이름 유사도로
아무거나 붙였다가 `Box` 에 남색 사각형이 붙은 적이 있다.

    python tools/build_icons_royalkingdom.py --sprites <RoyalKingdom_sprites.zip>
"""
import argparse
import io
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from levelscope.plugins.royalkingdom import TILED_ID  # noqa: E402

#: 기믹 이름 → 원본 스프라이트. 전부 스프라이트 이름으로 확인한 것이다.
#: 조각으로만 존재하거나(Lightbulb·SteamBomb) 이름이 안 맞는 기믹은 일부러 뺐다.
BASE = {
    "ChaliceBox": "ChaliceBox_big",
    "MagicOrb": "MagicOrb_big",
    "DragonBox": "dragon_goal_icon",
    "JellyMaker": "Jelly_box_cover",
    "MaceBox": "Mace_Goal_Icon",
    "MushroomsClose": "Mushrooms_goal_icon",
    "MushroomsOpen": "Mushrooms_goal_icon",
    "Snowman": "Snowman_big",
    "TurtleHouse": "Turtle_big",
    "MagicCards": "magic_cards_goal_icon",
    "Spaceship": "Space_Ship_goal_icon",
    "Armory": "armory_goal_icon_01",
}

#: `*MagicOrb*` 는 한 기믹인데 열거형 이름이 갈려 있다 — 커튼 세 칸은
#: `MagicOrbCurtainTL/TR/BR`, 남은 한 칸은 `<색>MagicOrbBL`. 44스테이지 실제 화면의
#: 목표 "무지개 구슬 16" 이 이 계열 셀 수 16(커튼 12 + 색 4)과 맞아 한 덩이가 맞다.
ORB = re.compile(r"(?i)^(?:[A-Z][a-z]+)?MagicOrb(?:Curtain)?(TL|TR|BL|BR)(\d*)$")

SUFFIX = re.compile(r"^(.*?)(?P<pos>[TMB][LMR])(\d*)$")
ROW = {"T": 0, "M": 1, "B": 2}
COL = {"L": 0, "M": 1, "R": 2}


def families():
    """{기믹 이름: {칸위치: [타입번호…]}}.

    한 위치에 타입이 여럿일 수 있다 — `<색>MagicOrbBL` 은 색깔별로 다른 번호를 쓰지만
    자리는 다 같은 왼쪽아래다. 목록으로 받지 않으면 색 변형이 조용히 빠진다.
    """
    out = {}
    for tid, name in TILED_ID.items():
        m = ORB.match(name)
        base, pos = ("MagicOrb", m.group(1).upper()) if m else (None, None)
        if base is None:
            m = SUFFIX.match(name)
            if not m or not m.group(1):
                continue
            base, pos = m.group(1), m.group("pos")
        out.setdefault(base, {}).setdefault(pos, []).append(tid)
    return out


def grid(positions):
    """칸 위치들에서 행·열 수를 정한다 — 있는 글자만 쓰므로 2×2도 3×3도 된다."""
    rows = sorted({ROW[p[0]] for p in positions})
    cols = sorted({COL[p[1]] for p in positions})
    return rows, cols


def build(sprites_zip, icon_dir, log=print):
    from PIL import Image

    z = zipfile.ZipFile(sprites_zip)
    mapping_path = os.path.join(icon_dir, "_mapping.json")
    mapping = {}
    if os.path.exists(mapping_path):
        mapping = json.load(open(mapping_path, encoding="utf-8"))

    made, skipped = 0, []
    for base, parts in sorted(families().items()):
        sprite = BASE.get(base)
        if not sprite:
            skipped.append(f"{base}({len(parts)}칸)")
            continue
        raw = Image.open(io.BytesIO(z.read(f"Sprite/{sprite}.png"))).convert("RGBA")
        bb = raw.getbbox()
        if bb:
            raw = raw.crop(bb)
        rows, cols = grid(parts)
        cw, ch = raw.width / len(cols), raw.height / len(rows)
        n = 0
        for pos, tids in sorted(parts.items()):
            r, c = rows.index(ROW[pos[0]]), cols.index(COL[pos[1]])
            cell = raw.crop((round(c * cw), round(r * ch),
                             round((c + 1) * cw), round((r + 1) * ch)))
            cell.thumbnail((256, 256), Image.LANCZOS)
            for tid in tids:
                cell.save(os.path.join(icon_dir, f"type{tid}.png"))
                mapping[str(tid)] = f"{sprite}#{pos}"
                made += 1
                n += 1
        log(f"  {base:<16} {len(rows)}×{len(cols)} ← {sprite} ({n}개 타입)")

    json.dump(mapping, open(mapping_path, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    log(f"[icons] 다중칸 조각 {made}개 생성")
    if skipped:
        log(f"[icons] 원본을 못 찾아 건너뜀 — {', '.join(skipped)}")
    return made, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sprites", required=True, help="RoyalKingdom_sprites.zip 경로")
    ap.add_argument("--icons", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "icons", "royalkingdom"))
    a = ap.parse_args()
    build(a.sprites, a.icons)


if __name__ == "__main__":
    main()
