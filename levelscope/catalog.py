"""Addressables 카탈로그 해독 — 번들 해시명을 원본 프로젝트 경로로 되돌린다.

Addressables를 쓰는 게임의 번들 이름은 `room10__a259fe9091a05b92773fd5c141a7db0a.bundle`
처럼 해시가 붙어 있어서, 추출물만 봐서는 그게 뭔지 알 수 없다. `catalog.json` 에
주소(address) ↔ 리소스 매핑이 들어 있고 풀면 이런 게 나온다:

    bamboo_forest__7f7728...bundle
      → Assets/Modules/ThemeModule/Prefabs/Backgrounds/Bamboo/Background/Bamboo_tiny.png

포맷은 Unity `ContentCatalogData` 의 직렬화 형태다. 주의할 점이 두 개 있었다:

1. **키 오프셋 표는 `m_KeyDataString` 이 아니라 `m_BucketDataString` 에 있다.**
   키 블롭 머리에 오프셋 테이블이 있다고 가정하면 IndexError로 터진다.
2 . 에셋이 어느 번들에 들어 있는지는 엔트리의 `dependencyKeyIndex` 를 따라가야 한다
   (그 버킷이 가리키는 엔트리 중 `.bundle` 로 끝나는 것이 담긴 번들이다).

해독 결과는 반드시 검증한다 — 버킷 파싱이 블롭을 정확히 소진하는지, 엔트리 블롭
크기가 `4 + count*28` 과 맞는지, 인덱스가 범위 안인지. 하나라도 어긋나면 해독을
포기하고 `m_InternalIds` 목록만 쓴다 (그것만으로도 번들·에셋 경로는 읽을 수 있다).
잘못 푼 매핑으로 이름을 붙이는 건 이름을 안 붙이는 것보다 나쁘다.

포맷이 세 갈래다.

1. `catalog.json` — 구형. 위에 적은 방식으로 직접 푼다.
2. `catalog.bin` — Addressables 1.21+ / Unity 2023+. 선택 의존성
   `addressablestools` 가 있을 때만 매핑까지 풀고, 없으면 문자열 목록만 낸다.
3. **`catalog.bundle` 안 TextAsset** — 카탈로그를 Unity 번들로 한 번 더 싼 것.
   내용이 Unity 표준 바이너리가 아니라 **게임 고유 FlatBuffers** 인 경우가 있다
   (Clash of Critters: 루트 테이블 `AddressablesMainContentCatalog`). 이때는
   `flatbuf` 로 풀어 문자열 벡터에서 경로를 건진다 — 실측 13,001개
   (`Assets/Res/Audio/...`, `Assets/Res/UI/...`).

    cat = load_catalog(apk)
    cat.addresses_for("room10__a259fe9091a05b92773fd5c141a7db0a.bundle")
    cat.remote_bundles           # 카탈로그엔 있지만 APK엔 없는 것 = CDN 배포분
"""
import base64
import dataclasses
import json
import os
import struct

from . import container

#: 카탈로그 위치 후보.
#:
#: `catalog.bundle` 은 **카탈로그를 Unity 번들 안 TextAsset 으로 싸서** 넣은 것이다
#: (Clash of Critters: `assets/aa/catalog.bundle` 안 `catalog` TextAsset 5.7MB).
#: 이 경로를 안 보면 카탈로그가 있는데도 "카탈로그 없음"이 되고, 추출한 아트에
#: 원본 프로젝트 경로를 붙일 수 없다.
CATALOG_GLOB = ["assets/aa/*/catalog.json", "*/catalog.json", "catalog.json",
                "assets/aa/*/catalog.bin", "*/catalog.bin",
                "assets/aa/catalog.bundle", "*/catalog.bundle"]

#: ContentCatalogData 의 엔트리 하나는 int32 7개다
_ENTRY_SIZE = 28


class CatalogUnavailable(Exception):
    """카탈로그가 없거나 해독할 수 없다."""


@dataclasses.dataclass
class Catalog:
    label: str = ""
    internal_ids: list = dataclasses.field(default_factory=list)
    resource_types: list = dataclasses.field(default_factory=list)
    #: 번들 basename → 그 번들에 담긴 주소·경로 목록
    bundle_map: dict = dataclasses.field(default_factory=dict)
    decoded: bool = False
    note: str = ""

    @property
    def bundle_ids(self):
        return [s for s in self.internal_ids if s.endswith(".bundle")]

    @property
    def asset_paths(self):
        return [s for s in self.internal_ids if s.startswith("Assets/")]

    def addresses_for(self, bundle_basename):
        return self.bundle_map.get(os.path.basename(bundle_basename), [])

    def missing_bundles(self, present_basenames):
        """카탈로그엔 있는데 입력에는 없는 번들 — 원격(CDN) 배포분이다."""
        have = {os.path.basename(b) for b in present_basenames}
        return sorted({os.path.basename(b) for b in self.bundle_ids} - have)

    def to_dict(self):
        return {"label": self.label, "decoded": self.decoded, "note": self.note,
                "bundles": len(self.bundle_ids), "asset_paths": len(self.asset_paths),
                "resource_types": self.resource_types,
                "bundle_map": {k: v[:200] for k, v in self.bundle_map.items()}}


# ─────────────────────────── 문자열 블롭 ───────────────────────────

def _read_object(blob, off):
    """SerializationUtilities.ReadObjectFromByteArray 대응 — [1바이트 타입][페이로드]."""
    t = blob[off]
    p = off + 1
    if t == 0:                                          # AsciiString
        ln = struct.unpack_from("<i", blob, p)[0]
        return blob[p + 4:p + 4 + ln].decode("ascii", "replace")
    if t == 1:                                          # UnicodeString
        ln = struct.unpack_from("<i", blob, p)[0]
        return blob[p + 4:p + 4 + ln].decode("utf-16-le", "replace")
    if t == 2:
        return struct.unpack_from("<H", blob, p)[0]
    if t == 3:
        return struct.unpack_from("<I", blob, p)[0]
    if t == 4:
        return struct.unpack_from("<i", blob, p)[0]
    if t == 5:                                          # Hash128
        return blob[p:p + 16].hex()
    raise ValueError(f"모르는 키 타입 {t}")


def _parse_buckets(blob):
    """[int32 개수] + 개수 × ([int32 키오프셋][int32 엔트리수][엔트리수 × int32])."""
    n = struct.unpack_from("<i", blob, 0)[0]
    pos, out = 4, []
    for _ in range(n):
        koff, ecount = struct.unpack_from("<2i", blob, pos)
        pos += 8
        ents = struct.unpack_from(f"<{ecount}i", blob, pos)
        pos += 4 * ecount
        out.append((koff, ents))
    if pos != len(blob):
        raise ValueError(f"버킷 파싱 후 {len(blob) - pos}바이트 남음 — 포맷 불일치")
    return out


def _parse_entries(blob):
    n = struct.unpack_from("<i", blob, 0)[0]
    expect = 4 + n * _ENTRY_SIZE
    if expect != len(blob):
        raise ValueError(f"엔트리 블롭 크기 불일치 (기대 {expect}, 실제 {len(blob)})")
    return [struct.unpack_from("<7i", blob, 4 + i * _ENTRY_SIZE) for i in range(n)]


def _build_bundle_map(doc, log):
    """번들 basename → 담긴 주소·에셋경로 목록. 검증 실패 시 예외."""
    ids = doc["m_InternalIds"]
    keys_blob = base64.b64decode(doc["m_KeyDataString"])
    buckets = _parse_buckets(base64.b64decode(doc["m_BucketDataString"]))
    entries = _parse_entries(base64.b64decode(doc["m_EntryDataString"]))

    for e in entries:
        if not 0 <= e[0] < len(ids):
            raise ValueError(f"internalId 인덱스 범위 초과: {e[0]} / {len(ids)}")

    def key_at(bucket_index):
        if not 0 <= bucket_index < len(buckets):
            return None
        try:
            return _read_object(keys_blob, buckets[bucket_index][0])
        except Exception:  # noqa: BLE001
            return None

    out = {}
    for koff, ents in buckets:
        try:
            key = _read_object(keys_blob, koff)
        except Exception:  # noqa: BLE001 - 키 하나를 못 읽어도 나머지는 쓴다
            continue
        if not isinstance(key, str):
            continue
        for ei in ents:
            if not 0 <= ei < len(entries):
                continue
            internal_id, _prov, dep_key, _dep_hash, _data, _pk, _rt = entries[ei]
            target = ids[internal_id]
            if target.endswith(".bundle"):
                continue                              # 번들 자체를 가리키는 주소는 건너뛴다
            dep = key_at(dep_key)
            if dep is None:
                continue
            for de in buckets[dep_key][1]:
                if not 0 <= de < len(entries):
                    continue
                dt = ids[entries[de][0]]
                if dt.endswith(".bundle"):
                    out.setdefault(os.path.basename(dt), set()).add(key)
    return {k: sorted(v) for k, v in out.items()}


# ─────────────────────────── 진입점 ───────────────────────────

def load_catalog(input_path, globs=None, log=print):
    """카탈로그를 찾아 해독. 없으면 CatalogUnavailable."""
    pats = container.as_list(globs) or CATALOG_GLOB
    data, label = container.find_first(input_path, pats)
    if data is None:
        raise CatalogUnavailable(f"카탈로그 없음 (탐색: {pats})")

    if label.lower().endswith(".bundle"):
        inner = _unwrap_bundle(data, label, log)
        if inner is None:
            raise CatalogUnavailable(
                f"{label}: 번들 안에서 카탈로그 TextAsset 을 찾지 못했습니다")
        data = inner

    if label.lower().endswith((".bin", ".bundle")):
        cat = _binary_catalog(data, label, log)
        if cat is None:
            cat = _flatbuffers_catalog(data, label, log)
        if cat is not None:
            return cat
        # 폴백: 읽을 수 있는 문자열만 건져 목록으로 낸다 — 매핑은 못 하지만
        # "뭐가 들어 있나"는 보인다.
        ids = _strings_from_binary(data)
        note = "catalog.bin(바이너리 포맷) — 문자열만 추출, 주소 매핑 불가"
        log(f"[catalog] {label}: {note}")
        return Catalog(label, ids, [], {}, False, note)

    try:
        doc = json.loads(data)
    except Exception as e:  # noqa: BLE001
        raise CatalogUnavailable(f"카탈로그 JSON 파싱 실패: {e}") from e

    ids = doc.get("m_InternalIds") or []
    rtypes = [t.get("m_ClassName", "") for t in (doc.get("m_resourceTypes") or [])]
    try:
        bmap = _build_bundle_map(doc, log)
    except Exception as e:  # noqa: BLE001 - 잘못 푼 매핑보다 없는 게 낫다
        note = f"주소 매핑 해독 실패({e}) — m_InternalIds 목록만 사용"
        log(f"[catalog] {label}: {note}")
        return Catalog(label, ids, rtypes, {}, False, note)

    log(f"[catalog] {label}: 번들 {len(_bundles(ids))}개 · 에셋경로 {len(_assets(ids))}개 · "
        f"주소 매핑 {len(bmap)}개 번들분 해독")
    return Catalog(label, ids, rtypes, bmap, True, "")


def _bundles(ids):
    return [s for s in ids if s.endswith(".bundle")]


def _assets(ids):
    return [s for s in ids if s.startswith("Assets/")]


def _plain_id(s):
    """내부 id 에서 런타임 경로 치환자를 떼어 실제 파일 경로만 남긴다.

    바이너리 카탈로그의 번들 id 는
    `{UnityEngine.AddressableAssets.Addressables.RuntimePath}/Android/x.bundle`
    처럼 앞에 치환자가 붙어 있다. 이걸 떼야 JSON 카탈로그의 id 와 같은 모양이 되고,
    `bundle_ids`·`asset_paths` 판정이 두 포맷에서 같게 동작한다.
    """
    s = str(s or "")
    if s.startswith("{"):
        end = s.find("}")
        if end != -1:
            s = s[end + 1:].lstrip("/\\")
    return s

def _unwrap_bundle(data, label, log):
    """`catalog.bundle` → 안에 든 카탈로그 TextAsset bytes. 못 찾으면 None.

    이름이 `catalog` 인 TextAsset 을 먼저 찾고, 없으면 **가장 큰** TextAsset 을
    쓴다. 번들 안에 폰트 아틀라스 같은 다른 TextAsset 이 섞여 있을 수 있어서
    이름을 우선한다.
    """
    from . import unity
    best = None
    try:
        with unity.load_bytes(data, suffix=".bundle") as env:
            for o in unity.iter_objects(env, ["TextAsset"]):
                try:
                    d = unity.read_obj(o)
                except Exception:  # noqa: BLE001 - 못 읽는 엔트리는 넘긴다
                    continue
                raw = getattr(d, "m_Script", None)
                if raw is None:
                    continue
                blob = (raw.encode("utf-8", "surrogateescape")
                        if isinstance(raw, str) else bytes(raw))
                name = str(getattr(d, "m_Name", "") or "")
                if name.lower() == "catalog":
                    log(f"[catalog] {label}: 번들 안 TextAsset 'catalog' "
                        f"{len(blob):,}B 를 씁니다")
                    return blob
                if best is None or len(blob) > len(best[1]):
                    best = (name, blob)
    except unity.UnityUnavailable:
        raise
    except Exception as e:  # noqa: BLE001 - 번들이 안 열리면 카탈로그가 아닌 것으로 본다
        log(f"[catalog] {label}: 번들을 열지 못했습니다 ({e!r})")
        return None
    if best:
        log(f"[catalog] {label}: 'catalog' 이름이 없어 가장 큰 TextAsset "
            f"'{best[0]}' {len(best[1]):,}B 를 씁니다")
        return best[1]
    return None


#: FlatBuffers 카탈로그에서 경로로 인정할 최소 개수.
#: 이보다 적으면 엉뚱한 문자열을 경로로 착각한 것으로 보고 포기한다.
_FB_MIN_PATHS = 20


def _flatbuffers_catalog(data, label, log):
    """게임 고유 FlatBuffers 카탈로그 → Catalog. 아니거나 못 풀면 None.

    Unity 표준이 아니라 스튜디오가 직접 만든 카탈로그다(Clash of Critters:
    루트 테이블 이름이 `AddressablesMainContentCatalog`). 스키마가 없으니
    필드 이름은 못 얻고, **문자열 벡터에서 경로를 건지는 것까지** 한다.

    주소 ↔ 번들 매핑은 하지 않는다 — 슬롯 의미를 모르는 상태에서 매핑을 지어내면
    잘못 푼 이름을 붙이게 되고, 그건 이름을 안 붙이는 것보다 나쁘다(모듈 독스트링).
    경로 목록만으로도 추출물에 원본 폴더를 붙일 수 있다.
    """
    try:
        from . import flatbuf
    except Exception:  # noqa: BLE001
        return None
    if not flatbuf.looks_like(data):
        return None
    try:
        doc = flatbuf.decode(data)
    except Exception as e:  # noqa: BLE001 - FlatBuffers 가 아니었던 것으로 본다
        log(f"[catalog] {label}: FlatBuffers 해독 실패 ({e!r})")
        return None

    ids, root = [], None
    def walk(v, depth=0):
        if depth > 6:
            return
        if isinstance(v, str):
            ids.append(v)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k in ("of", "n"):
                    continue
                walk(x, depth + 1)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x, depth + 1)

    if isinstance(doc, dict):
        root = doc.get("f0") if isinstance(doc.get("f0"), str) else None
    walk(doc)

    seen, uniq = set(), []
    for x in ids:
        p = _plain_id(x)
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    n_paths = len(_assets(uniq)) + len(_bundles(uniq))
    if n_paths < _FB_MIN_PATHS:
        log(f"[catalog] {label}: FlatBuffers 로 풀렸지만 경로처럼 보이는 문자열이 "
            f"{n_paths}개뿐입니다 — 카탈로그가 아닌 것으로 봅니다")
        return None

    note = ("게임 고유 FlatBuffers 카탈로그"
            + (f" (루트 {root})" if root else "")
            + " — 경로 목록만, 주소↔번들 매핑 없음")
    log(f"[catalog] {label}: 번들 {len(_bundles(uniq)):,}개 · "
        f"에셋경로 {len(_assets(uniq)):,}개 · {note}")
    return Catalog(label, uniq, [], {}, False, note)


def _binary_catalog(data, label, log):
    """catalog.bin (Addressables 바이너리 카탈로그) → Catalog. 못 하면 None.

    JSON 카탈로그와 달리 바이너리 카탈로그는 버전이 여럿(Binv1~v3)이고 오프셋 기반
    객체 그래프다. 직접 파서를 쓰면 조용히 어긋날 위험이 큰데, 이 저장소 원칙은
    "잘못 푼 매핑은 이름을 안 붙이는 것보다 나쁘다"다. 그래서 검증된 외부 파서를
    **선택 의존성**으로 쓴다 — `pip install addressablestools` (MIT, 무의존).
    없으면 예전처럼 문자열만 건지는 폴백으로 내려간다.
    """
    try:
        import addressablestools
    except ImportError:
        log(f"[catalog] {label}: catalog.bin 을 읽으려면 addressablestools 가 필요합니다"
            " — `pip install addressablestools` (없어도 문자열 목록은 나옵니다)")
        return None
    try:
        parsed = addressablestools.parse_binary(data)
    except Exception as e:  # noqa: BLE001 - 새 포맷 버전은 폴백으로 넘긴다
        log(f"[catalog] {label}: catalog.bin 파싱 실패({e!r}) — 문자열 목록으로 폴백")
        return None

    resources = getattr(parsed, "resources", None) or {}
    ids, seen, bmap, rtypes = [], set(), {}, set()

    def remember(value):
        v = _plain_id(value)
        if v and v not in seen:
            seen.add(v)
            ids.append(v)
        return v

    for key, locs in resources.items():
        for loc in (locs or ()):
            iid = remember(getattr(loc, "internal_id", ""))
            t = getattr(loc, "type", None)
            if getattr(t, "class_name", ""):
                rtypes.add(t.class_name)
            if iid.endswith(".bundle"):
                continue          # 번들 자체를 가리키는 주소는 매핑에 넣지 않는다
            if isinstance(key, str):
                remember(key)
            # 이 에셋이 어느 번들에 담겼는지는 의존성이 알려준다
            for dep in (getattr(loc, "dependencies", None) or ()):
                dep_id = _plain_id(getattr(dep, "internal_id", ""))
                if dep_id.endswith(".bundle") and isinstance(key, str):
                    bmap.setdefault(os.path.basename(dep_id), set()).add(key)

    # 검증 — 쓰레기를 경로로 착각하지 않도록. 하나도 경로처럼 안 생겼으면 못 푼 것이다.
    if not ids or not (_bundles(ids) or _assets(ids)):
        log(f"[catalog] {label}: catalog.bin 해독 결과가 경로처럼 보이지 않습니다"
            " — 문자열 목록으로 폴백")
        return None

    bmap = {k: sorted(v) for k, v in bmap.items()}
    ver = getattr(parsed, "version", "?")
    log(f"[catalog] {label}: 번들 {len(_bundles(ids))}개 · 에셋경로 {len(_assets(ids))}개 · "
        f"주소 매핑 {len(bmap)}개 번들분 해독 (바이너리 v{ver}, addressablestools)")
    return Catalog(label, ids, sorted(rtypes), bmap, True,
                   f"catalog.bin (바이너리 v{ver}) — addressablestools 로 해독")


def _strings_from_binary(data, min_len=6, limit=4000):
    """바이너리에서 ASCII 문자열 건지기 — catalog.bin 용 최소한의 폴백."""
    out, cur = [], bytearray()
    for b in data:
        if 32 <= b < 127:
            cur.append(b)
            continue
        if len(cur) >= min_len:
            s = cur.decode("ascii", "replace")
            if "/" in s or s.endswith(".bundle"):
                out.append(s)
                if len(out) >= limit:
                    break
        cur.clear()
    return out


def try_load(input_path, globs=None, log=print):
    """실패해도 예외를 내지 않는 편의 함수 — 없으면 None."""
    try:
        return load_catalog(input_path, globs, log=log)
    except CatalogUnavailable as e:
        log(f"[catalog] {e}")
        return None
