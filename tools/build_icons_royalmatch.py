"""Royal Match 타일 아이콘 생성.

스프라이트 이름 규칙이 두 갈래다 (전부 이름으로 확인한 것이다):

    Items-<이름>Item-<부위>     기믹 본체. Vase → Items-VaseItem-vase_0
    <이름>_Goal_Icon 류          목표 아이콘. ConveyorBelt → Conveyor_Belt_Goal_Icon

`Parts-<이름>-<조각>` 도 많지만 잎사귀·머리 같은 **조각**이라 한 칸 그림이 못 된다.
그래서 안 쓴다. 이름이 안 맞으면 아이콘을 만들지 않는다 — 뷰어가 타입 번호를 그대로
보여주므로 "그림이 없다"가 드러난다. 이름 유사도로 아무거나 붙였다가 Royal Kingdom
에서 상자에 남색 사각형이 붙은 적이 있다.

여러 칸을 차지하는 기믹은 이름 끝에 칸 위치가 붙는다(CupboardTL·PotionBR …).
원본을 행×열로 잘라 각 칸에 제 조각을 준다 — 나란히 놓이면 원래 그림이 된다.

    python tools/build_icons_royalmatch.py --sprites <RoyalMatch_sprites.zip>
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from levelscope.plugins.royalmatch import TILED_ID, is_gimmick  # noqa: E402

ITEM = re.compile(r"(?i)^(?:Static)?Items-([A-Za-z0-9]+)Item-(.+)$")
CORNER = re.compile(r"(TL|TR|BL|BR|TM|BM|ML|MR|MM)(\d*)$")
ROW = {"T": 0, "M": 1, "B": 2}
COL = {"L": 0, "M": 1, "R": 2}

#: 본체가 아닌 부위 — 그림자·목표아이콘·패치·파티클은 칸 그림으로 못 쓴다
_SKIP_PART = re.compile(r"(?i)shadow|goal|patch|particle|effect|_shd|back|front|glow|light")


def base_name(name):
    """`Grass2`·`CupboardTL` → `grass`·`cupboard`. 칸 위치와 끝 숫자를 뗀다."""
    return re.sub(r"\d+$", "", CORNER.sub("", name)).lower()


def index_sprites(z):
    """(Item 그룹 → {부위: 경로}, 목표아이콘 → {정규화이름: 경로})."""
    groups, goals = collections.defaultdict(dict), {}
    for n in z.namelist():
        b = os.path.splitext(os.path.basename(n))[0]
        m = ITEM.match(b)
        if m:
            groups[m.group(1).lower()][m.group(2).lower()] = n
        if re.search(r"(?i)goal", b):
            key = re.sub(r"(?i)[_\- ]|goal|icon", "", b)
            goals.setdefault(key.lower(), n)
    return groups, goals


def pick_part(parts, base):
    """그룹에서 본체 부위를 고른다. 이름이 기믹 이름과 같은 것을 최우선."""
    for want in (base, base + "_0", base + "_1", "01_top", "0"):
        if want in parts:
            return parts[want]
    plain = [k for k in sorted(parts) if not _SKIP_PART.search(k)]
    return parts[plain[0]] if plain else None


def resolve(name, groups, goals):
    """타일 이름 → (스프라이트 경로, 근거). 못 찾으면 (None, None)."""
    b = base_name(name)
    if b in groups:
        p = pick_part(groups[b], b)
        if p:
            return p, "Items"
    g = goals.get(b)
    return (g, "Goal") if g else (None, None)


def build(sprites_zip, icon_dir, log=print):
    from PIL import Image

    z = zipfile.ZipFile(sprites_zip)
    groups, goals = index_sprites(z)
    os.makedirs(icon_dir, exist_ok=True)
    log(f"[icons] Item 그룹 {len(groups)}개 · 목표 아이콘 {len(goals)}개")

    # 여러 칸 기믹은 칸 위치별로 모아 원본을 잘라 쓴다
    fam = collections.defaultdict(dict)
    single = {}
    for tid, name in TILED_ID.items():
        if not is_gimmick(tid):
            continue
        m = CORNER.search(name)
        if m and CORNER.sub("", name):
            fam[base_name(name)].setdefault(m.group(1), []).append(tid)
        else:
            single[tid] = name

    mapping, made, miss = {}, 0, []
    cache = {}

    def load(path):
        if path not in cache:
            im = Image.open(io.BytesIO(z.read(path))).convert("RGBA")
            bb = im.getbbox()
            cache[path] = im.crop(bb) if bb else im
        return cache[path]

    for tid, name in sorted(single.items()):
        path, why = resolve(name, groups, goals)
        if not path:
            miss.append(name)
            continue
        im = load(path).copy()
        im.thumbnail((256, 256), Image.LANCZOS)
        im.save(os.path.join(icon_dir, f"type{tid}.png"))
        mapping[str(tid)] = f"{os.path.splitext(os.path.basename(path))[0]} ({why})"
        made += 1

    for base, parts in sorted(fam.items()):
        path, why = resolve(base, groups, goals)
        if not path:
            miss.extend(TILED_ID[t] for tids in parts.values() for t in tids)
            continue
        raw = load(path)
        rows = sorted({ROW[p[0]] for p in parts})
        cols = sorted({COL[p[1]] for p in parts})
        cw, ch = raw.width / len(cols), raw.height / len(rows)
        for pos, tids in sorted(parts.items()):
            r, c = rows.index(ROW[pos[0]]), cols.index(COL[pos[1]])
            cell = raw.crop((round(c * cw), round(r * ch),
                             round((c + 1) * cw), round((r + 1) * ch)))
            cell.thumbnail((256, 256), Image.LANCZOS)
            for tid in tids:
                cell.save(os.path.join(icon_dir, f"type{tid}.png"))
                mapping[str(tid)] = (f"{os.path.splitext(os.path.basename(path))[0]}"
                                     f"#{pos} ({why})")
                made += 1
        log(f"  {base:<18} {len(rows)}×{len(cols)} ← {os.path.basename(path)}")

    json.dump(mapping, open(os.path.join(icon_dir, "_mapping.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    log(f"[icons] {made}개 생성 · 이름이 안 맞아 못 만든 타일 {len(miss)}종")
    return made, miss


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sprites", required=True)
    ap.add_argument("--icons", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "icons", "royalmatch"))
    a = ap.parse_args()
    build(a.sprites, a.icons)


if __name__ == "__main__":
    main()
