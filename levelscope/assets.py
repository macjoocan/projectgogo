"""이미지가 아닌 게임 리소스 추출 — 사운드·머티리얼·폰트·Spine·텍스트.

sprites.py 는 `obj.image` → PNG 한 갈래뿐이어서 이미지가 없는 타입은 전부
"이미지 없음" 실패로 떨어졌다. 여기서 그 나머지를 담당한다.

가장 손이 많이 간 건 오디오다. AudioClip의 소리 데이터는 번들 안에 없고
`m_Resource = {m_Source: 'resources.resource', m_Offset, m_Size}` 로 **번들 밖 파일**을
가리킨다. UnityPy는 그 파일을 못 찾아 빈 바이트로 디코딩을 시도하고
`FmodError('FORMAT')` 을 낸다. 그래서 컨테이너에서 .resource 를 직접 찾아
오프셋만큼 잘라 넣어준다 (그러면 FSB5 청크가 나오고 정상 디코딩된다).

설정 예:
  assets:
    sources: [assets/bin/Data/data.unity3d]
    kinds: [audio, material, font, spine, text]   # 생략 시 전체
    max_count: 4000

CLI 단독 실행:
  python -m levelscope assets --input <apk> --out out --game SheepNSheep
"""
import dataclasses
import io
import json
import os
import re
import zipfile

from . import container, discover, unity
from .container import as_list

#: 다룰 수 있는 갈래
ALL_KINDS = ("audio", "material", "font", "spine", "text")

#: 스트리밍 오디오 원본을 찾을 기본 위치
DEFAULT_RESOURCE_GLOB = ["assets/bin/Data/*.resource", "*.resource"]

#: Spine 으로 볼 TextAsset 확장자 (.json은 내용까지 확인한다)
_SPINE_EXT = (".atlas", ".skel", ".skel.bytes", ".atlas.txt")

#: ResourceStore 캐시 상한(바이트). 오디오 스트리밍 리소스는 개당 수십 MB 이고
#: Royal Kingdom 은 291개다 — 전부 들고 있으면 그것만으로 수 GB 가 된다.
#: 넘으면 오래된 것부터 버린다(다시 필요하면 다시 읽는다 — 결과는 같다).
RESOURCE_CACHE_BUDGET = 256 * 2**20

#: 폰트 매직 → 확장자
_FONT_MAGIC = {b"OTTO": ".otf", b"true": ".ttf", b"ttcf": ".ttc", b"\x00\x01\x00\x00": ".ttf"}


@dataclasses.dataclass
class AssetResult:
    counts: dict = dataclasses.field(default_factory=dict)
    path: str = ""
    failures: list = dataclasses.field(default_factory=list)
    sources: list = dataclasses.field(default_factory=list)
    truncated: bool = False

    @property
    def total(self):
        return sum(self.counts.values())


class ResourceStore:
    """`.resource` / `.resS` 스트리밍 파일 바이트 공급자 (지연 로딩 + 캐시).

    한 번 찾은 파일은 메모리에 들고 있는다 — 오디오 클립마다 3MB 파일을 다시 열면
    클립 수만큼 압축 해제가 반복된다. 단 **총량에 상한을 둔다**
    (`RESOURCE_CACHE_BUDGET`). 상한 없이 들고 있으면 리소스가 수백 개인 게임에서
    이 캐시만으로 수 GB 가 쌓인다.
    """

    def __init__(self, input_path, globs=None, log=print):
        self.input_path = input_path
        self.globs = as_list(globs) or DEFAULT_RESOURCE_GLOB
        self.log = log
        self._cache = {}          # base → bytes (삽입 순서 = LRU 순서)
        self._cache_bytes = 0
        self._missing = set()
        self._env = None

    def bind(self, env):
        """지금 처리 중인 번들을 알려준다 — 내부 리소스를 먼저 찾기 위해."""
        self._env = env

    def get(self, source):
        """m_Resource.m_Source 문자열 → bytes. 못 찾으면 None.

        찾는 순서가 중요하다.

        1. **지금 열어 둔 번들 내부** — Addressables류 번들은 자기 오디오를
           `CAB-<hash>.resource` 로 번들 안에 품는다. 밖에서 찾으면 없다.
        2. 컨테이너 안의 같은 이름 파일 — `assets/bin/Data/resources.resource` 같은 것.
        3. 이름이 안 맞으면 후보가 딱 하나일 때만 대체하고 그 사실을 로그에 남긴다.

        오프셋·길이는 **원래 파일 기준**이라 다른 파일에서 자르면 소리가 쓰레기가
        된다. 그래서 `CAB-` 로 시작하는 번들 내부 리소스는 3단계 대체를 하지 않는다
        (Royal Kingdom에서 실제로 291개가 엉뚱한 파일에서 잘려 나갔다).
        """
        if not source:
            return None
        base = os.path.basename(str(source).replace("\\", "/"))
        if base in self._cache:
            data = self._cache.pop(base)      # 다시 넣어 최근 사용으로 올린다
            self._cache[base] = data
            return data
        if base in self._missing:
            return None

        data = _from_env(self._env, base)
        label = "번들 내부"
        if data is None:
            data, label = container.find_first(self.input_path, [base, f"*/{base}"])
        if data is None:
            if base.upper().startswith("CAB-"):
                self._missing.add(base)
                self.log(f"[assets] 경고: 번들 내부 리소스 '{base}' 를 찾지 못했습니다"
                         " — 다른 파일로 대체하면 소리가 깨지므로 원본(.fsb)만 저장합니다")
                return None
            cands = self._candidate_names()
            if len(cands) == 1:
                name, inner = next(iter(cands.items()))
                data, label = container.find_first(
                    self.input_path, [inner, f"*/{inner}"])
                if data is None:
                    self._missing.add(base)
                    self.log(f"[assets] 경고: 후보 '{name}' 를 읽지 못했습니다"
                             " — 해당 오디오는 원본(.fsb)으로만 저장됩니다")
                    return None
                self.log(f"[assets] 주의: '{base}' 이름은 없고 후보가 하나뿐이라 "
                         f"'{name}' 로 대체합니다")
            else:
                self._missing.add(base)
                hint = f" (후보 {sorted(cands)})" if cands else ""
                self.log(f"[assets] 경고: 스트리밍 리소스 '{base}' 를 찾지 못했습니다{hint}"
                         " — 해당 오디오는 원본(.fsb)으로만 저장됩니다")
                return None
        self.log(f"[assets] 스트리밍 리소스 {base} 확보 ({len(data) / 1e6:.1f}MB, {label})")
        self._cache[base] = data
        self._cache_bytes += len(data)
        self._evict()
        return data

    def _evict(self):
        """상한을 넘으면 오래된 것부터 버린다. 방금 넣은 건 남긴다."""
        while self._cache_bytes > RESOURCE_CACHE_BUDGET and len(self._cache) > 1:
            old = next(iter(self._cache))
            self._cache_bytes -= len(self._cache.pop(old))
            self.log(f"[assets] 리소스 캐시 상한({RESOURCE_CACHE_BUDGET / 1e6:.0f}MB) "
                     f"— '{old}' 를 캐시에서 내렸습니다")

    def unbind(self):
        self._env = None

    def _candidate_names(self):
        """resource_glob 에 맞는 파일들 — {파일명: 컨테이너 내부 경로}.

        **bytes 를 읽지 말 것.** 후보 개수를 세려고 전부 읽으면 리소스 파일
        전체가 한꺼번에 메모리에 올라온다(Royal Kingdom 291개). 실제로 필요한
        건 "후보가 딱 하나인가" 뿐이고, 그때만 읽으면 된다.
        """
        out = {}
        for c in container.iter_containers(self.input_path):
            with c:
                for n in c.glob(self.globs):
                    out.setdefault(os.path.basename(n), n)
        return out


def _from_env(env, basename):
    """번들 내부 파일에서 바이트를 꺼낸다. 없으면 None.

    UnityPy는 번들 내부 `.resource`/`.resS` 를 EndianBinaryReader 로 들고 있고
    `.bytes` 로 전체를 준다. 이름은 대소문자가 흔들리므로 낮춰서 맞춘다.
    """
    if env is None:
        return None
    want = basename.lower()
    try:
        for f in getattr(env, "files", {}).values():
            sub = getattr(f, "files", None)
            if not isinstance(sub, dict):
                continue
            for k, v in sub.items():
                if not isinstance(k, str) or os.path.basename(k).lower() != want:
                    continue
                raw = getattr(v, "bytes", None)
                if raw:
                    return bytes(raw)
    except Exception:  # noqa: BLE001 - 내부 구조가 다르면 밖에서 찾게 둔다
        return None
    return None


def _safe(name, fallback="unnamed"):
    n = re.sub(r'[\\/:*?"<>|]', "_", (name or "").strip())
    return n or fallback


def _unique(base, ext, seen):
    key, n = base + ext, 2
    while key in seen:
        key = f"{base}_{n}{ext}"
        n += 1
    seen.add(key)
    return key


# ─────────────────────────── 갈래별 추출 ───────────────────────────

def _audio(o, obj, store, index, fail):
    """AudioClip → [(경로, bytes)]. WAV 변환 실패 시 FSB5 원본이라도 남긴다."""
    tree = o.read_typetree()
    name = _safe(tree.get("m_Name"), "clip")
    res = tree.get("m_Resource") or {}
    chunk = None
    if res.get("m_Size"):
        data = store.get(res.get("m_Source"))
        if data is not None:
            off, size = res.get("m_Offset") or 0, res["m_Size"]
            chunk = data[off:off + size]
            if len(chunk) != size:
                fail.append(f"audio/{name}: 리소스 범위 초과 (기대 {size}, 실제 {len(chunk)})")
                chunk = None
    if chunk is None:
        raw = getattr(obj, "m_AudioData", None)
        chunk = bytes(raw) if raw else None
    if not chunk:
        fail.append(f"audio/{name}: 소리 데이터 없음")
        return []

    out = []
    try:
        obj.m_AudioData = chunk
        for fn, wav in (obj.samples or {}).items():
            out.append((f"audio/{_safe(fn, name + '.wav')}", wav))
    except Exception as e:  # noqa: BLE001 - FMOD 미설치/미지원 포맷
        fail.append(f"audio/{name}: WAV 변환 실패 ({e!r}) — 원본만 저장")
    if not out:
        out.append((f"audio/_raw/{name}.fsb", chunk))
    return out


def _material(o, obj, store, index, fail):
    """Material → JSON. 셰이더·텍스처 참조를 이름으로 풀어서 담는다."""
    tree = o.read_typetree()
    name = _safe(tree.get("m_Name"), "material")
    doc = index.expand(o, tree) if index else tree
    return [(f"material/{name}.json",
             json.dumps(doc, ensure_ascii=False, indent=1, default=str).encode("utf-8"))]


def _font(o, obj, store, index, fail):
    """Font → .ttf/.otf. 확장자는 파일 매직으로 정한다 (m_Name엔 확장자가 없다)."""
    name = _safe(getattr(obj, "m_Name", None), "font")
    fd = getattr(obj, "m_FontData", None)
    if not fd:
        fail.append(f"font/{name}: m_FontData 비어 있음 (시스템 폰트 참조일 수 있습니다)")
        return []
    raw = bytes(fd)
    ext = next((e for m, e in _FONT_MAGIC.items() if raw.startswith(m)), ".bin")
    return [(f"font/{name}{ext}", raw)]


def _is_spine(name, raw):
    low = (name or "").lower()
    if low.endswith(_SPINE_EXT):
        return True
    if low.endswith(".json") and raw[:400].find(b'"skeleton"') >= 0:
        return True
    return raw[:64].find(b"spine") >= 0 and not low.endswith(".txt")


def _text(o, obj, store, index, fail, spine_only=False, text_only=False):
    """TextAsset → spine/ 또는 text/. 게임 애니메이션의 실체가 Spine인 경우가 많다."""
    raw = unity.payload_bytes(o, obj=obj)
    name = getattr(obj, "m_Name", None) or "asset"
    if raw is None:
        fail.append(f"text/{_safe(name)}: 페이로드 없음")
        return []
    spine = _is_spine(name, raw)
    if spine_only and not spine:
        return []
    if text_only and spine:
        return []
    safe = _safe(name, "asset")
    if spine:
        return [(f"spine/{safe if os.path.splitext(safe)[1] else safe + '.txt'}", raw)]
    ext = "" if os.path.splitext(safe)[1] else (".txt" if _looks_text(raw) else ".bin")
    return [(f"text/{safe}{ext}", raw)]


def _looks_text(raw):
    sample = raw[:512]
    if not sample:
        return True
    printable = sum(1 for b in sample if 9 <= b <= 13 or 32 <= b < 127 or b >= 128)
    return printable / len(sample) > 0.85


#: 갈래 → (UnityPy 타입, 처리함수)
_HANDLERS = {
    "audio": ("AudioClip", _audio),
    "material": ("Material", _material),
    "font": ("Font", _font),
    "spine": ("TextAsset", lambda *a: _text(*a, spine_only=True)),
    "text": ("TextAsset", lambda *a: _text(*a, text_only=True)),
}


# ─────────────────────────── 진입점 ───────────────────────────

def extract_assets(input_path, assets_cfg, out_dir, game="game", log=print):
    """사운드·머티리얼·폰트·Spine·텍스트를 <out_dir>/<game>_assets.zip 으로 뽑는다."""
    cfg = assets_cfg or {}
    kinds = [k for k in (as_list(cfg.get("kinds")) or list(ALL_KINDS)) if k in _HANDLERS]
    unknown = [k for k in as_list(cfg.get("kinds")) if k not in _HANDLERS]
    if unknown:
        log(f"[assets] 경고: 모르는 kind 무시 — {unknown} (가능: {list(ALL_KINDS)})")
    if not kinds:
        log("[assets] 추출할 갈래가 없습니다 (assets.kinds 확인)")
        return AssetResult()

    sources = discover.resolve_sources(input_path, cfg.get("sources"), log=log)
    max_count = cfg.get("max_count", 4000)
    want_types = {_HANDLERS[k][0] for k in kinds}
    store = ResourceStore(input_path, cfg.get("resource_glob"), log=log)

    os.makedirs(out_dir, exist_ok=True)
    zpath = os.path.join(out_dir, f"{game}_assets.zip")
    counts, failures, used, seen = {}, [], [], set()
    truncated = False
    manifest = []

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for label, data in _iter_sources(input_path, sources):
            used.append(label)
            if len(seen) >= max_count:
                truncated = True
                break
            suffix = os.path.splitext(label)[1] or ".unity3d"
            with unity.load_bytes(data, suffix=suffix) as env:
                index = unity.ObjectIndex(env)
                store.bind(env)      # 번들 내부 CAB 리소스를 먼저 찾게 한다
                for o in unity.iter_objects(env, want_types):
                    if len(seen) >= max_count:
                        truncated = True
                        break
                    for kind in kinds:
                        tname, fn = _HANDLERS[kind]
                        if o.type.name != tname:
                            continue
                        try:
                            obj = unity.read_obj(o)
                            for path, blob in fn(o, obj, store, index, failures):
                                base, ext = os.path.splitext(path)
                                final = _unique(base, ext, seen)
                                zf.writestr(final, blob)
                                counts[kind] = counts.get(kind, 0) + 1
                                manifest.append({"kind": kind, "path": final,
                                                 "bytes": len(blob), "source": label})
                        except Exception as e:  # noqa: BLE001 - 개별 실패는 기록하고 계속
                            failures.append(f"{kind}/{unity.name_of(o) or o.path_id}: {e!r}")
        zf.writestr("manifest.json", json.dumps(
            {"game": game, "sources": used, "counts": counts,
             "truncated": truncated, "failures": failures, "items": manifest},
            ensure_ascii=False, indent=1).encode("utf-8"))

    if not used:
        log(f"[assets] 경고: sources {sources} 에 맞는 Unity 파일을 찾지 못했습니다")
    breakdown = ", ".join(f"{k} {counts.get(k, 0)}" for k in kinds)
    log(f"[assets] {sum(counts.values())}개 추출 ({breakdown}) → {zpath}"
        + (f" · 실패 {len(failures)}개" if failures else "")
        + (f" · max_count({max_count}) 도달로 중단" if truncated else ""))
    if truncated:
        _warn_unprocessed(sources, used, max_count, log)
    for f in failures[:5]:
        log(f"  ! {f}")
    return AssetResult(counts, zpath, failures, used, truncated)


def _warn_unprocessed(sources, used, max_count, log):
    """상한에 걸려 **아예 열지도 못한** 소스를 짚어 준다.

    Zen Match에서 실제로 생긴 일이다 — data.unity3d 의 TextAsset 3486개가 상한을
    다 먹어서 Addressables 번들 14개는 손도 못 댔다. 로그가 "중단"만 말하면
    사용자는 그 번들이 비어 있었다고 오해한다.
    """
    touched = [s for s in sources if any(s in u for u in used)]
    left = [s for s in sources if s not in touched]
    if not left:
        return
    log(f"[assets] ! 상한 때문에 소스 {len(left)}개를 아예 열지 못했습니다: "
        + ", ".join(os.path.basename(s) for s in left[:5])
        + (f" 외 {len(left) - 5}개" if len(left) > 5 else ""))
    log(f"[assets]   max_count 를 {max_count} 보다 크게 하거나 kinds 를 좁히세요 "
        "(예: 레벨이 TextAsset인 게임은 kinds 에서 text 를 빼면 됩니다)")


def _iter_sources(input_path, sources):
    """sprites.iter_source_bytes 와 같은 일 — 컨테이너 안 Unity 파일들."""
    patterns = as_list(sources)
    if not patterns:
        return
    for c in container.iter_containers(input_path):
        with c:
            for n in c.glob(patterns):
                yield f"{c.label}!{n}", c.read(n)
