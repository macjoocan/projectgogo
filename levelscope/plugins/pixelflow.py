"""PixelFlow 전용 플러그인: 슈터 대기열 집계·엔티티 시트·뷰어 상세.

플러그인 인터페이스(모두 선택):
  level_extras(data) -> dict        Levels 시트 추가 컬럼
  entities(set, level, data) -> [tuple]   ENTITY_SHEET.headers 순서의 행들
  viewer_level(data) -> {'ma': [[mat,ammo]..], 'sq': [[라벨,[ [id,ammo,mat,태그str]..]]..]}
  ENTITY_SHEET = {'name':..., 'headers':[...]}
"""
import collections
import re

MATNAMES = ["Blue", "DarkBlue", "Black", "Green", "Orange", "Pink", "Purple", "Red",
            "Turquoise", "Yellow", "White", "Brown", "DarkGreen", "Emerald", "Lilac",
            "Sage", "Salmon", "Lavender", "Terracotta", "Parmesan", "Brick", "Gray",
            "DarkGray", "DarkPurple", "GypsyPink", "PowderPink", "PastelOrange",
            "Burgundy", "Olive", "DustyTeal", "MilkyBrown", "Toffee", "NeonPurple", "SharkGray"]

ENTITY_SHEET = {"name": "Shooters",
                "headers": ["set", "level", "source", "order", "shooter_id",
                            "ammo", "material", "material_name", "gimmicks"]}


def _tags(data):
    t = collections.defaultdict(list)
    for sid in data["SurpriseShooters"]["Shooters"]:
        t[sid].append("surprise")
    for sid in data["Locks"]["Shooters"]:
        t[sid].append("lock")
    for sid in data["Hammers"]["Shooters"]:
        t[sid].append("hammer")
    for sid in data["AstronautShooters"]["Shooters"]:
        t[sid].append("astronaut")
    for c in data["ConnectedShooters"]["Connections"]:
        for sid in c["Shooters"]:
            t[sid].append(f"connected(g{c['Id']})")
    for c in data["ChainedShooters"]["Chains"]:
        for sid in c["Shooters"]:
            t[sid].append(f"chained(g{c['Id']})")
    for x in data["ShooterIceBlocks"]["IceBlocks"]:
        t[x["ShooterId"]].append(f"ice(hp{x['Health']})")
    for x in data["BullTotems"]["Totems"]:
        t[x["ShooterId"]].append(f"totem(x{x['Count']})")
    for x in data["MusicToyMallets"]["Mallets"]:
        t[x["ShooterId"]].append(f"mallet(m{x['Material']})")
    for p in data["ShooterPipes"]["Pipes"]:
        t[p["ShooterId"]].append("pipe_exit")
    return t


def _queues(data):
    """[(라벨, [shooter dict ...])] — 메인 대기열 + 파이프 내부 대기열"""
    out = []
    for qi, q in enumerate(data["QueueGroup"]["shooterQueues"]):
        out.append((f"Q{qi + 1}", q.get("shooters", [])))
    for p in data["ShooterPipes"]["Pipes"]:
        out.append((f"P{p['ShooterId']}", (p.get("Queue") or {}).get("shooters", [])))
    return out


def level_extras(data):
    qs = _queues(data)
    allsh = [s for _, lst in qs for s in lst]
    main = [s for lab, lst in qs if lab[0] == "Q" for s in lst]
    ammo = collections.Counter(s["ammo"] for s in allsh)
    return {
        "queue_count": len(data["QueueGroup"]["shooterQueues"]),
        "shooter_count": len(main),
        "pipe_shooter_count": len(allsh) - len(main),
        "total_ammo": sum(s["ammo"] for s in allsh),
        "color_count": len({s["material"] for s in allsh}),
        "ammo_10": ammo.get(10, 0), "ammo_20": ammo.get(20, 0), "ammo_30": ammo.get(30, 0),
        "ammo_40": ammo.get(40, 0), "ammo_50": ammo.get(50, 0),
    }


def entities(set_name, level, data):
    t = _tags(data)
    rows = []
    for lab, lst in _queues(data):
        src = f"queue{int(lab[1:]) - 1}" if lab[0] == "Q" else f"pipe(exit_id={lab[1:]})"
        for oi, s in enumerate(lst):
            m = s["material"]
            rows.append((set_name, level, src, oi, s["id"], s["ammo"], m,
                         MATNAMES[m] if m < len(MATNAMES) else str(m),
                         ", ".join(t.get(s["id"], []))))
    return rows


_ABBR = [("surprise", "S"), ("lock", "L"), ("hammer", "H"), ("astronaut", "A"),
         ("pipe_exit", "E"), ("connected(g", "C"), ("chained(g", "X"),
         ("ice(hp", "I"), ("totem(x", "T"), ("mallet(m", "M")]


def _abbr(tags):
    out = []
    for tg in tags:
        for full, c in _ABBR:
            if tg.startswith(full):
                m = re.search(r"(\d+)", tg[len(full):])
                out.append(c + (m.group(1) if m else ""))
                break
    return ",".join(out)


def viewer_level(data):
    t = _tags(data)
    sq, matammo = [], collections.Counter()
    for lab, lst in _queues(data):
        chips = []
        for s in lst:
            matammo[s["material"]] += s["ammo"]
            tag = _abbr(t.get(s["id"], []))
            chips.append([s["id"], s["ammo"], s["material"]] + ([tag] if tag else []))
        sq.append([lab, chips])
    ma = sorted(matammo.items(), key=lambda x: -x[1])[:6]
    return {"ma": [[m, a] for m, a in ma], "sq": sq}
