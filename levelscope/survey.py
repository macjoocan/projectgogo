"""survey — 처음 보는 APK를 프로파일해 "뭐가 어디에 있나"를 한 번에 보고한다.

지금까지 새 게임 온보딩은 `ls` → `detect` → `inspect` → YAML 손작업이었다. 그 전에
"이 게임이 Unity인가, IL2CPP인가, Addressables를 쓰는가, 리소스가 얼마나 있나,
레벨로 쓸 만한 후보가 뭔가"를 알려주는 단계가 없었다. 이 모듈이 그 자리를 맡는다.

내는 것:
  - 스크립팅 백엔드(IL2CPP/Mono)와 Unity 버전
  - Unity 소스 목록 (discover) + 타입 집계
  - Addressables 카탈로그 요약 — 특히 **원격 배포분** (APK엔 없고 카탈로그엔 있는 번들)
  - 레벨 데이터 후보 (TextAsset/MonoBehaviour 중 길이 있는 것) + 인코딩 감지
  - configs/_suggested_<게임>.yaml 초안

레벨 후보 판정은 어림짐작이다 — 확정은 `inspect` 로 사람이 봐야 한다. 그래서
초안 파일 이름에 `_suggested_` 를 붙이고 그대로 쓰지 말라고 적어 둔다.
"""
import collections
import dataclasses
import json
import os

from . import catalog as catalog_mod
from . import container, decode, discover, typetree, unity

#: 레벨 데이터가 들어 있을 만한 타입
LEVEL_TYPES = ("TextAsset", "MonoBehaviour")

#: 이보다 짧은 페이로드는 레벨로 보지 않는다
MIN_LEVEL_BYTES = 64

#: 리소스 규모 보고에 쓰는 타입
RESOURCE_TYPES = ("Sprite", "Texture2D", "AudioClip", "Material", "Font", "Shader",
                  "Mesh", "AnimationClip", "GameObject", "MonoBehaviour", "TextAsset")


@dataclasses.dataclass
class Report:
    input_path: str = ""
    package: str = ""
    app_name: str = ""
    unity_version: str = ""
    backend: str = ""
    sources: list = dataclasses.field(default_factory=list)
    type_totals: dict = dataclasses.field(default_factory=dict)
    catalog: object = None
    #: 에셋형 레벨 후보 계열 — 디코딩 실패한 계열도 함께 담긴다(decodable 로 구분)
    level_families: list = dataclasses.field(default_factory=list)
    #: 파일형 레벨 후보 — [(glob, 개수, codec)]
    file_levels: list = dataclasses.field(default_factory=list)
    scenes: list = dataclasses.field(default_factory=list)
    notes: list = dataclasses.field(default_factory=list)

    def to_dict(self):
        return {
            "input": self.input_path, "package": self.package, "app_name": self.app_name,
            "unity_version": self.unity_version, "backend": self.backend,
            "sources": [s.to_dict() for s in self.sources],
            "type_totals": self.type_totals,
            "catalog": self.catalog.to_dict() if self.catalog else None,
            "level_families": self.level_families,
            "file_levels": [{"glob": g, "count": n, "codec": c}
                            for g, n, c in self.file_levels],
            "scenes": self.scenes, "notes": self.notes,
        }


# ─────────────────────────── 조각별 조사 ───────────────────────────

def _app_identity(input_path):
    """XAPK manifest.json 에서 패키지명·앱이름. 없으면 파일명으로 때운다."""
    data, _ = container.find_first(input_path, ["manifest.json"])
    if data:
        try:
            d = json.loads(data)
            return d.get("package_name") or "", d.get("name") or ""
        except Exception:  # noqa: BLE001
            pass
    return "", os.path.splitext(os.path.basename(str(input_path)))[0]


def _backend(input_path):
    """IL2CPP / Mono 판별. 재료가 어디 있는지까지 확인한다."""
    so, _ = container.find_first(input_path, typetree.DEFAULT_IL2CPP)
    md, _ = container.find_first(input_path, typetree.DEFAULT_METADATA)
    if so is not None and md is not None:
        return "IL2CPP"
    dll, _ = container.find_first(input_path, ["assets/bin/Data/Managed/Assembly-CSharp.dll",
                                              "*/Managed/Assembly-CSharp.dll"])
    if dll is not None:
        return "Mono"
    if so is not None or md is not None:
        return "IL2CPP(재료 일부 누락)"
    return "불명"


def _scan_source(src, input_path, want_levels=True, per_family=3):
    """소스 하나를 열어 타입 집계·레벨 후보 **계열**·씬 목록을 뽑는다.

    후보를 계열 단위로 센다. 예전에는 페이로드 큰 순으로 앞 400개만 검사했는데,
    Royal Kingdom에서 그 400개가 전부 Spine `.skel`(최대 517KB)로 채워져
    정작 레벨인 "1~4500" 계열 4,500개를 통째로 놓쳤다. 덩치는 판별 기준이 못 된다.

    디코딩에 실패한 계열도 버리지 않고 함께 돌려준다 — "이름이 1~4500인 에셋이
    4,500개 있는데 못 읽는다"는 사실 자체가 침묵보다 훨씬 쓸모 있다.
    """
    from . import assets as assets_mod

    data, _ = container.find_first(input_path, [src.name, f"*/{src.name}"])
    if data is None:
        return {}, [], []
    types = collections.Counter()
    scenes, families = [], []
    counts = collections.Counter()          # 계열 → 개수
    samples = {}                            # 계열 → [(이름, bytes, 타입)]
    sizes = collections.defaultdict(list)
    with unity.load_bytes(data, suffix=os.path.splitext(src.name)[1] or ".unity3d") as env:
        by_file = collections.defaultdict(set)
        targets = []
        for o in env.objects:
            types[o.type.name] += 1
            by_file[unity.file_name(o)].add(o.type.name)
            if want_levels and o.type.name in LEVEL_TYPES:
                targets.append(o)
        for fname, tset in by_file.items():
            if tset & {"RenderSettings", "LightmapSettings"}:
                scenes.append(f"{src.basename}!{fname}")

        # 계열별로 표본만 모은다. 페이로드는 한 번씩만 읽는다.
        for o in targets:
            raw = _payload(o)
            if raw is None or len(raw) < MIN_LEVEL_BYTES:
                continue
            name = unity.name_of(o) or ""
            if assets_mod._is_spine(name, raw):
                continue                       # Spine 데이터는 레벨이 아니다
            fam = _norm_name(name) if name else "(무명)"
            counts[fam] += 1
            sizes[fam].append(len(raw))
            if len(samples.setdefault(fam, [])) < per_family:
                samples[fam].append((name, raw, o.type.name))

    for fam, n in counts.items():
        codec = None
        for _nm, raw, _t in samples.get(fam, []):
            try:
                codec = list(decode.detect_chain(raw)[0])
                break
            except Exception:  # noqa: BLE001 - 표본이 안 풀리면 다음 표본
                continue
        s = sorted(sizes[fam])
        head_name, head_raw, head_type = samples.get(fam, [("", b"", "")])[0]
        families.append({
            "source": src.name, "family": fam, "count": n, "type": head_type,
            "codec": codec, "decodable": codec is not None,
            "median_bytes": s[len(s) // 2] if s else 0,
            "sample_name": head_name,
            "sample_head": bytes(head_raw[:16]).hex(),
        })
    families.sort(key=lambda f: -f["count"])
    return dict(types), families, scenes


def _payload(o):
    try:
        return unity.payload_bytes(o)
    except Exception:  # noqa: BLE001
        return None


#: 파일형 레벨 후보에서 볼 확장자 (없는 것도 포함 — 확장자 없는 레벨 파일이 흔하다)
_FILE_LEVEL_EXT = (".json", ".txt", ".dat", ".bytes", ".bin", ".lvl", ".xml", "")

#: 레벨 파일일 리 없는 경로
_FILE_LEVEL_SKIP = ("META-INF/", "res/", "lib/", "kotlin/", "okhttp3/", "assets/bin/",
                    "assets/aa/", "firebase", "google")


def file_level_candidates(input_path, log=print, per_group=3, max_files=60000):
    """레벨이 Unity 에셋이 아니라 **파일**로 든 게임을 위한 후보 탐색.

    PixelFlow가 그렇다 — `assets/Levels/<세트>/<번호>.json` 수천 개다. survey가
    Unity 에셋만 보면 이 게임은 "레벨 후보 없음"으로 나와 쓸모가 없다.

    같은 모양의 경로를 묶어 계열로 세고, 계열마다 표본 몇 개만 디코딩해 본다
    (수천 개를 다 디코딩하면 느리다). 반환: [(glob패턴, 개수, codec)]
    """
    counts = collections.Counter()
    samples = collections.defaultdict(list)          # 패턴 → 표본 bytes (스캔 중에 확보)
    seen = 0
    for c in container.iter_containers(input_path):
        with c:
            for n in c.names():
                seen += 1
                if seen > max_files:
                    break
                low = n.lower()
                if any(s in low for s in _FILE_LEVEL_SKIP):
                    continue
                ext = os.path.splitext(low)[1]
                if ext not in _FILE_LEVEL_EXT:
                    continue
                d = os.path.dirname(n)
                if not d:
                    continue
                # 두 갈래로 묶는다 — 한 폴더에 몰린 경우와 세트 폴더로 갈린 경우
                pats = [f"{d}/*{ext}"]
                parent = os.path.dirname(d)
                if parent:
                    pats.append(f"{parent}/*/*{ext}")
                need = [p for p in pats if len(samples[p]) < per_group]
                data = None
                if need:
                    try:
                        data = c.read(n)            # 표본이 필요할 때만 읽는다
                    except Exception:  # noqa: BLE001
                        data = None
                for p in pats:
                    counts[p] += 1
                    if data and len(samples[p]) < per_group:
                        samples[p].append(data)

    out = []
    for pattern, n in counts.items():
        if n < 3:
            continue
        codec = None
        for data in samples.get(pattern, []):
            if len(data) < MIN_LEVEL_BYTES:
                continue
            try:
                codec = list(decode.detect_chain(data)[0])
                break
            except Exception:  # noqa: BLE001 - 디코딩 안 되면 레벨 후보가 아니다
                continue
        if codec is None:
            continue
        out.append((pattern, n, codec))
    out.sort(key=lambda x: -x[1])
    # 같은 개수를 덮는 좁은 패턴은 버리고 넓은 쪽만 남긴다
    # (`a/Levels/*.json` 와 `a/*/*.json` 이 둘 다 7개면 후자가 더 쓸모 있다)
    kept = []
    for pat, n, codec in sorted(out, key=lambda x: (-x[1], -x[0].count("*"))):
        if any(n <= kn and _covers(kpat, pat) for kpat, kn, _ in kept):
            continue
        kept.append((pat, n, codec))
    if kept:
        log(f"[survey] 파일형 레벨 후보: " +
            ", ".join(f"{p}×{n}" for p, n, _ in kept[:4]))
    return kept


def _covers(broad, narrow):
    """`a/*/*.json` 이 `a/b/*.json` 을 덮는가 — 같은 확장자·같은 뿌리면 그렇다."""
    import fnmatch as _fn
    return broad != narrow and _fn.fnmatch(narrow.replace("*", "x"), broad)


def decodable(families):
    return [f for f in families if f["decodable"]]


def undecodable(families):
    return [f for f in families if not f["decodable"]]


def _dominant_codec(families, log):
    """설정에 넣을 codec 값. 체인이 섞여 있으면 None → `auto` 를 쓰게 한다.

    계열 개수로 가중치를 준다 — 4,500개짜리 계열과 1개짜리 계열을 똑같이 세면
    소수 계열이 결과를 뒤집는다.
    """
    ok = decodable(families)
    if not ok:
        return None
    dist = collections.Counter()
    for f in ok:
        dist[tuple(f["codec"])] += f["count"]
    best, n = dist.most_common(1)[0]
    if len(dist) > 1:
        log("[survey] 레벨 후보 인코딩이 섞여 있습니다 — "
            + ", ".join(f"{list(k)}×{v}" for k, v in dist.most_common(4))
            + " → codec: auto 권장")
        return None
    log(f"[survey] 레벨 후보 인코딩: {list(best)} ({n}개)")
    return list(best)


def _norm_name(name):
    """이름의 숫자를 [0-9]+ 로 뭉쳐 '계열'을 만든다. Level_37 · Level_912 → Level_[0-9]+"""
    import re as _re
    return _re.sub(r"\d+", "[0-9]+", _re.escape(str(name)).replace(r"\ ", " "))


def name_families(families, limit=8):
    """[(계열 패턴, 개수)] — 많은 것부터. 여러 소스에 걸친 같은 계열은 합친다.

    크기순으로 뽑으면 안 된다. 제일 큰 TextAsset은 보통 설정 덩어리
    (`ZenMasterConfigDataModel`)거나 Spine 바이너리고, 레벨은 **번호가 붙은
    큰 계열**을 이룬다 (`Level_[0-9]+` ×377, `[0-9]+` ×4500).
    """
    groups = collections.Counter()
    for f in families:
        groups[f["family"]] += f["count"]
    return groups.most_common(limit)


def _name_hint(families, limit=6):
    """name_pattern 초안 — **디코딩되는** 계열만, 멤버가 많은 순."""
    fams = name_families(decodable(families), limit)
    return "|".join(p for p, _n in fams) if fams else ".*"


# ─────────────────────────── 진입점 ───────────────────────────

def run_survey(input_path, out_dir=None, log=print, max_sources=0, deep=True):
    """APK 하나를 프로파일해 Report 를 낸다. out_dir 을 주면 설정 초안까지 쓴다."""
    rep = Report(input_path=str(input_path))
    rep.package, rep.app_name = _app_identity(input_path)
    rep.backend = _backend(input_path)
    log(f"[survey] {rep.app_name or '?'} ({rep.package or '패키지 불명'}) · 백엔드 {rep.backend}")

    rep.sources = discover.find_sources(input_path, log=log, max_sources=max_sources)
    if not rep.sources:
        rep.notes.append("Unity 소스를 못 찾았습니다 — Unity 게임이 아닐 수 있습니다")
        log("[survey] Unity 소스 없음 — Unity 빌드가 아닐 가능성이 있습니다")

    # Unity 버전은 가장 큰 소스에서 감지한다
    for src in rep.sources:
        data, _ = container.find_first(input_path, [src.name, f"*/{src.name}"])
        if data is None:
            continue
        try:
            with unity.load_bytes(data, suffix=".unity3d") as env:
                v = typetree.detect_unity_version(env)
            if v:
                rep.unity_version = v
                break
        except Exception:  # noqa: BLE001
            continue
    if rep.unity_version:
        log(f"[survey] Unity {rep.unity_version}")

    totals = collections.Counter()
    game_srcs = [s for s in rep.sources if not s.builtin]
    for src in (game_srcs if deep else game_srcs[:1]):
        types, families, scenes = _scan_source(src, input_path)
        totals.update(types)
        rep.level_families.extend(families)
        rep.scenes.extend(scenes)
    rep.type_totals = {t: totals[t] for t in RESOURCE_TYPES if totals.get(t)}
    other = sum(v for k, v in totals.items() if k not in rep.type_totals)
    if other:
        rep.type_totals["(그 외)"] = other

    log("[survey] 리소스 규모: " + " · ".join(
        f"{k} {v:,}" for k, v in rep.type_totals.items() if k != "(그 외)") or "(없음)")
    if rep.scenes:
        log(f"[survey] 씬 {len(rep.scenes)}개: {', '.join(rep.scenes[:5])}"
            + (" ..." if len(rep.scenes) > 5 else ""))

    rep.catalog = catalog_mod.try_load(input_path, log=log)
    if rep.catalog is not None:
        present = [s.basename for s in rep.sources]
        missing = rep.catalog.missing_bundles(present)
        if missing:
            msg = (f"카탈로그 번들 {len(rep.catalog.bundle_ids)}개 중 {len(missing)}개가 "
                   f"APK에 없습니다 — 원격(CDN) 배포분이라 추출 대상이 아닙니다")
            rep.notes.append(msg)
            log(f"[survey] {msg}")

    rep.level_families.sort(key=lambda f: -f["count"])
    rep.file_levels = file_level_candidates(input_path, log=log)
    codec = _dominant_codec(rep.level_families, log)
    if prefers_file_levels(rep):
        codec = rep.file_levels[0][2]
        log(f"[survey] 레벨이 Unity 에셋이 아니라 파일로 든 게임입니다 "
            f"— levels_glob: {rep.file_levels[0][0]} ({rep.file_levels[0][1]}개), codec: {codec}")

    ok, bad = decodable(rep.level_families), undecodable(rep.level_families)
    if ok:
        log("[survey] 디코딩되는 계열: "
            + ", ".join(f"{p}×{n}" for p, n in name_families(ok, 4)))
    if bad:
        top = name_families(bad, 3)
        log("[survey] ! 디코딩 안 되는 계열: "
            + ", ".join(f"{p}×{n}" for p, n in top))
        biggest = max(bad, key=lambda f: f["count"])
        rep.notes.append(
            f"'{biggest['family']}' 계열 {biggest['count']}개가 디코딩되지 않음 "
            f"(표본 머리 {biggest['sample_head'][:16]}) — 커스텀 바이너리 포맷일 수 있음")
        log(f"[survey]   가장 큰 것: {biggest['family']} ×{biggest['count']}"
            f" · 중간 크기 {biggest['median_bytes']:,}B · 머리 {biggest['sample_head'][:16]}")
        log("[survey]   압축·base64가 아니라면 게임 고유 포맷임. "
            "`detect --xor-scan` 으로 XOR 여부부터 확인")
    if not ok and not bad:
        log("[survey] 레벨 후보 없음 — 레벨이 파일로 들어 있거나(levels_glob) "
            "암호화됐을 수 있습니다. `detect --xor-scan` 을 보세요")

    if out_dir:
        path = write_suggested_config(rep, out_dir, codec=codec, log=log)
        rep.notes.append(f"설정 초안: {path}")
    return rep


def write_suggested_config(rep, out_dir, codec=None, log=print):
    """설정 초안 YAML. **그대로 쓰라는 게 아니라 출발점이다.**"""
    os.makedirs(out_dir, exist_ok=True)
    game = _slug(rep.app_name or rep.package or "mygame")
    path = os.path.join(out_dir, f"_suggested_{game}.yaml")
    cands = decodable(rep.level_families)
    lvl_type = collections.Counter(
        {f["type"]: f["count"] for f in cands if f["type"]}).most_common(1)
    lvl_type = lvl_type[0][0] if lvl_type else "TextAsset"
    biggest = max(rep.sources, key=lambda s: s.n_objects).name if rep.sources else \
        "assets/bin/Data/data.unity3d"

    lines = [
        f"# {rep.app_name or game} — levelscope survey 자동 초안",
        "#",
        "# 이 파일은 출발점입니다. 그대로 돌리지 말고 아래를 확인하세요:",
        "#   1) input.unity.name_pattern 이 정말 레벨 에셋만 고르는지",
        "#      python -m levelscope inspect --config <이 파일> --input <apk>",
        "#   2) fields / board 를 실제 JSON 구조에 맞게 채우기",
        "#   3) codec 이 맞는지 (python -m levelscope detect --input <apk>)",
        "#",
        f"# 조사 결과: 백엔드 {rep.backend} · Unity {rep.unity_version or '불명'}"
        f" · Unity 소스 {len(rep.sources)}개",
        f"game: {game}",
        "",
    ] + _input_block(rep, cands, lvl_type, biggest) + [
        f"codec: {json.dumps(codec) if codec else 'auto'}",
        "",
        "fields:",
        "  scalars: {}       # 예: level_id: id",
        "  counts: {}        # 예: tile_count: tiles.*",
        "",
        "# 리소스·계층은 sources 를 비워 두면 자동 발견합니다 (Addressables 번들 포함).",
        "sprites:",
        "  sources: auto",
        "  types: [Sprite]",
        "  max_count: 1000",
        "",
        "assets:",
        "  sources: auto",
        f"  kinds: [{', '.join(_kinds_for(rep))}]",
        "",
        "hierarchy:",
        "  sources: auto",
        "  scenes: true",
        "  prefabs: true",
        "  fields: full",
        "",
        "notes:",
        f'  - "조사: {rep.backend} · Unity {rep.unity_version or "불명"}"',
    ]
    for n in rep.notes:
        lines.append(f'  - "{n}"')
    lines += ["", "outputs: [xlsx, html, zip, sprites, assets, hierarchy]", ""]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"[survey] 설정 초안 저장: {path}")
    return path


def prefers_file_levels(rep):
    """레벨이 파일 쪽인가 에셋 쪽인가.

    양쪽에 후보가 나오는 게임이 있다 — Zen Match는 에셋 레벨 `Level_[0-9]+`×377 과
    미니게임 파일 `assets/FindingFred/Levels/*.json`×7 이 함께 있다. 그래서 단순히
    "파일 후보가 있으면 파일형"으로 하면 안 된다. 규모 차이로 가른다.

    실측: SheepNSheep 3 vs 3 → 에셋 / Zen Match 7 vs 377 → 에셋 /
          PixelFlow 2384 vs 1 → 파일
    """
    if not rep.file_levels:
        return False
    ok = decodable(rep.level_families)
    if not ok:
        return True
    fams = name_families(ok, 1)
    best_asset = fams[0][1] if fams else 0
    best_file = rep.file_levels[0][1]
    return best_file >= 10 and best_file > best_asset * 2


def _input_block(rep, cands, lvl_type, biggest):
    """`input:` 블록. 레벨이 Unity 에셋인 게임과 파일인 게임은 설정 모양이 다르다."""
    if cands and not prefers_file_levels(rep):
        lines = [
            "input:",
            "  unity:",
            f"    data_file: {_level_source(rep) or biggest}",
            f"    type: {lvl_type}",
            f'    name_pattern: "{_name_hint(cands)}"',
            "    # ↑ 이름 계열(숫자를 [0-9]+로 뭉친 것)을 멤버 수 순으로 넣은 초안입니다.",
            "    #   레벨이 아닌 계열이 섞여 있을 수 있으니 inspect 로 확인하고 지우세요.",
            "    # 계열: " + ", ".join(f"{p}×{n}" for p, n in name_families(cands, 8)),
        ]
        if rep.file_levels:
            lines.append("    # 파일형 후보도 있습니다 (둘 중 맞는 쪽을 쓰세요): "
                         + ", ".join(f"{g}×{n}" for g, n, _ in rep.file_levels[:3]))
        return lines + [""]

    if rep.file_levels:
        glob, n, _codec = rep.file_levels[0]
        lines = ["input:",
                 f"  levels_glob: {glob}      # {n}개 일치",
                 "  # 레벨이 Unity 에셋이 아니라 파일로 들어 있는 게임입니다."]
        if len(rep.file_levels) > 1:
            lines.append("  # 다른 후보: "
                         + ", ".join(f"{g}×{c}" for g, c, _ in rep.file_levels[1:4]))
        if cands:
            lines.append("  # Unity 에셋 후보도 있습니다(규모가 작아 뒤로 밀었습니다): "
                         + ", ".join(f"{p}×{c}" for p, c in name_families(cands, 3)))
        return lines + [""]

    return ["input:",
            "  # 레벨 후보를 못 찾았습니다. 다음을 확인하세요:",
            "  #   python -m levelscope ls     --input <apk>",
            "  #   python -m levelscope detect --input <apk> --xor-scan",
            "  levels_glob: assets/**/*.json",
            ""]


def _level_source(rep):
    """레벨 후보가 가장 많이 나온 소스 — 초안의 data_file 로 쓴다."""
    ok = decodable(rep.level_families)
    if not ok:
        return None
    per = collections.Counter()
    for f in ok:
        per[f["source"]] += f["count"]
    return per.most_common(1)[0][0]


def _kinds_for(rep):
    """실제로 있는 것만 kinds 에 넣는다 — 없는 갈래를 켜두면 로그가 헛돈다."""
    t = rep.type_totals
    out = []
    if t.get("AudioClip"):
        out.append("audio")
    if t.get("Material"):
        out.append("material")
    if t.get("Font"):
        out.append("font")
    if t.get("TextAsset"):
        out += ["spine", "text"]
    return out or ["text"]


def _slug(s):
    keep = [c if (c.isalnum() or c in "-_") else "_" for c in str(s).strip()]
    return "".join(keep).strip("_").lower() or "mygame"


def format_report(rep):
    """사람이 읽는 요약 텍스트."""
    L = [f"입력      : {rep.input_path}",
         f"앱        : {rep.app_name or '?'}  ({rep.package or '패키지 불명'})",
         f"엔진      : Unity {rep.unity_version or '불명'} · {rep.backend}",
         f"Unity 소스: {len(rep.sources)}개"]
    for s in rep.sources[:12]:
        tag = " [내장]" if s.builtin else ""
        L.append(f"   {s.kind:10} {s.basename[:52]:54} {s.n_objects:>8,} obj{tag}")
    if len(rep.sources) > 12:
        L.append(f"   ... {len(rep.sources) - 12}개 더")
    if rep.type_totals:
        L.append("리소스    : " + " · ".join(f"{k} {v:,}" for k, v in rep.type_totals.items()))
    if rep.scenes:
        L.append(f"씬        : {len(rep.scenes)}개 — {', '.join(rep.scenes[:4])}")
    if rep.catalog is not None:
        c = rep.catalog
        L.append(f"Addressables: 번들 {len(c.bundle_ids)}개 · 에셋경로 {len(c.asset_paths)}개"
                 f" · 주소매핑 {'해독' if c.decoded else '불가'}")
    ok, bad = decodable(rep.level_families), undecodable(rep.level_families)
    if ok:
        L.append(f"레벨 후보 : 디코딩되는 계열 {len(name_families(ok, 99))}종")
        for f in sorted(ok, key=lambda x: -x["count"])[:6]:
            L.append(f"      {f['family'][:44]:46} ×{f['count']:<6}"
                     f" {f['median_bytes']:>8,}B  {f['codec']}")
    if bad:
        L.append("디코딩 불가 계열: (커스텀 바이너리 포맷일 수 있음)")
        for f in sorted(bad, key=lambda x: -x["count"])[:5]:
            L.append(f"      {f['family'][:44]:46} ×{f['count']:<6}"
                     f" {f['median_bytes']:>8,}B  머리 {f['sample_head'][:16]}")
    if rep.file_levels:
        L.append("파일형 레벨: (레벨이 Unity 에셋이 아니라 파일인 게임)")
        for g, n, codec in rep.file_levels[:4]:
            L.append(f"      {g[:56]:58} ×{n:<6} {codec}")
    for n in rep.notes:
        L.append(f"주의      : {n}")
    return "\n".join(L)
