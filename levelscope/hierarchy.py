"""씬·프리팹 계층 복원 — GameObject 트리를 JSON으로.

빌드된 게임에는 .unity/.prefab 파일이 없다. 씬은 `level0`·`level1` 같은
SerializedFile로, Resources 프리팹은 `resources.assets` 안의 GameObject 뭉치로
녹아 들어간다. 둘을 갈라내는 단서는 파일 이름과 씬 전용 오브젝트
(RenderSettings·LightmapSettings)의 존재 여부다.

    SheepNSheep(BBB) 실측
      level0            루트 3개  (EventSystem / Adjust / Canvas)
      level1            루트 2개
      resources.assets  루트 57개 (GameMain, AdventureSuccessPanel, ...)

컴포넌트 필드는 typetree.MonoReader 가 있어야 알맹이가 채워진다. 없으면 IL2CPP
빌드에서 이름·타입만 남는다 — 그래서 여기서는 리더를 필수 인자로 받고,
못 읽은 컴포넌트는 조용히 빼지 않고 `"fields": null` 로 남겨 표시한다.

설정 예:
  hierarchy:
    sources: [assets/bin/Data/data.unity3d]
    scenes: true
    prefabs: true
    fields: full          # full | none
    max_nodes: 200000
"""
import dataclasses
import json
import math
import os
import re
import zipfile

from . import container, discover, typetree, unity
from .container import as_list

#: 이 오브젝트가 있으면 그 SerializedFile은 씬이다
_SCENE_MARKERS = ("RenderSettings", "LightmapSettings", "OcclusionCullingSettings", "NavMeshSettings")

#: 계층 트리에 담을 가치가 없는 필드 — 전부 남기면 JSON이 참조 쓰레기로 뒤덮인다
_NOISE_FIELDS = frozenset((
    "m_GameObject", "m_ObjectHideFlags", "m_Script", "m_GameObjectHideFlags",
    "m_CorrespondingSourceObject", "m_PrefabInstance", "m_PrefabAsset",
    "m_PrefabParentObject", "m_PrefabInternal", "m_ExtensionPtr",
))

#: transform 정보는 노드의 transform 칸으로 따로 빼므로 컴포넌트 목록에서 뺀다
_TRANSFORM_TYPES = ("Transform", "RectTransform")


@dataclasses.dataclass
class HierarchyResult:
    path: str = ""
    scenes: int = 0
    prefabs: int = 0
    nodes: int = 0
    failures: list = dataclasses.field(default_factory=list)
    sources: list = dataclasses.field(default_factory=list)
    truncated: bool = False


def _v(d, *keys):
    """{'x':1,'y':2} → [1,2]. 필드가 없으면 None (0으로 채우면 원본과 구별이 안 된다)."""
    if not isinstance(d, dict):
        return None
    out = [d.get(k) for k in keys]
    return None if all(x is None for x in out) else [_round(x) for x in out]


def _round(x):
    """좌표를 4자리로 줄인다. NaN/Inf는 None으로 — 실제로 나오고, JSON에 담을 수 없다."""
    if isinstance(x, float):
        if not math.isfinite(x):
            return None
        r = round(x, 4)
        return int(r) if r == int(r) else r
    return x


def _safe(name, fallback="unnamed"):
    return re.sub(r'[\\/:*?"<>|]', "_", (name or "").strip()) or fallback


def _unique(path, seen):
    """zip 엔트리 이름 중복 방지.

    프리팹 이름은 유일하지 않다 — ZenMatch의 resources.assets 에는 같은 이름
    ('TooltipEntity' 등)이 여러 개 있다. 그대로 쓰면 zip에 같은 이름이 두 번 들어가
    한쪽이 사실상 사라진다 (zipfile은 경고만 내고 계속 쓴다).
    """
    if path not in seen:
        seen.add(path)
        return path
    base, ext = os.path.splitext(path)
    n = 2
    while f"{base}_{n}{ext}" in seen:
        n += 1
    out = f"{base}_{n}{ext}"
    seen.add(out)
    return out


class _Builder:
    """SerializedFile 하나 안의 GameObject 트리를 만든다."""

    def __init__(self, index, fname, mono, want_fields=True, max_nodes=200000):
        self.index = index
        self.fname = fname
        self.mono = mono
        self.want_fields = want_fields
        self.max_nodes = max_nodes
        self.nodes = 0
        self.truncated = False
        self.failures = []
        self._tree_cache = {}
        self._by_id = index.by_file.get(fname, {})

    # ── 기본 조회 ───────────────────────────────────────────────────

    def _tt(self, o):
        """typetree를 한 번만 읽는다 (트리 순회에서 같은 오브젝트를 여러 번 만난다)."""
        if o.path_id not in self._tree_cache:
            try:
                self._tree_cache[o.path_id] = o.read_typetree()
            except Exception:  # noqa: BLE001
                self._tree_cache[o.path_id] = None
        return self._tree_cache[o.path_id]

    def _local(self, pptr):
        """같은 파일 안 PPtr → reader. 계층은 파일 경계를 넘지 않는다."""
        if not isinstance(pptr, dict):
            return None
        if (pptr.get("m_FileID") or 0) != 0:
            return None
        return self._by_id.get(pptr.get("m_PathID") or 0)

    # ── 루트 찾기 ───────────────────────────────────────────────────

    def roots(self):
        """부모가 없는 Transform들 → (이름, transform reader) 목록."""
        out = []
        for o in self._by_id.values():
            if o.type.name not in _TRANSFORM_TYPES:
                continue
            t = self._tt(o)
            if t is None:
                continue
            if (t.get("m_Father") or {}).get("m_PathID") or 0:
                continue
            go = self._local(t.get("m_GameObject") or {})
            name = (self._tt(go) or {}).get("m_Name") if go is not None else None
            out.append((name or f"path_{o.path_id}", o))
        out.sort(key=lambda kv: kv[0].lower())
        return out

    # ── 노드 만들기 ─────────────────────────────────────────────────

    def build(self, tr, depth=0):
        """transform reader → 노드 dict (자식 재귀)."""
        if self.nodes >= self.max_nodes:
            self.truncated = True
            return None
        if depth > 200:                      # 순환 참조 방어 (정상 UI는 20단을 안 넘는다)
            self.failures.append(f"{self.fname}: 계층 깊이 200 초과 — 순환 의심")
            return None
        t = self._tt(tr)
        if t is None:
            return None
        self.nodes += 1

        go = self._local(t.get("m_GameObject") or {})
        gt = self._tt(go) if go is not None else None
        node = {"name": (gt or {}).get("m_Name") or "", "transform": self._transform(tr, t)}
        if gt is not None:
            if not gt.get("m_IsActive", True):
                node["active"] = False
            if gt.get("m_Layer"):
                node["layer"] = gt.get("m_Layer")

        comps = self._components(go, gt)
        if comps:
            node["components"] = comps

        kids = []
        for cp in t.get("m_Children") or []:
            ch = self._local(cp)
            if ch is None:
                continue
            sub = self.build(ch, depth + 1)
            if sub is not None:
                kids.append(sub)
        if kids:
            node["children"] = kids
        return node

    def _transform(self, tr, t):
        d = {"kind": tr.type.name,
             "pos": _v(t.get("m_LocalPosition"), "x", "y", "z"),
             "scale": _v(t.get("m_LocalScale"), "x", "y", "z")}
        rot = _v(t.get("m_LocalRotation"), "x", "y", "z", "w")
        if rot and rot != [0, 0, 0, 1]:
            d["rot"] = rot
        if tr.type.name == "RectTransform":
            d.update({"anchorMin": _v(t.get("m_AnchorMin"), "x", "y"),
                      "anchorMax": _v(t.get("m_AnchorMax"), "x", "y"),
                      "anchoredPos": _v(t.get("m_AnchoredPosition"), "x", "y"),
                      "sizeDelta": _v(t.get("m_SizeDelta"), "x", "y"),
                      "pivot": _v(t.get("m_Pivot"), "x", "y")})
        return {k: v for k, v in d.items() if v is not None}

    def _components(self, go, gt):
        """GameObject의 컴포넌트 목록. transform은 노드의 transform 칸에 이미 있으므로 뺀다."""
        if gt is None:
            return []
        out = []
        for cp in gt.get("m_Component") or []:
            ptr = cp.get("component") if isinstance(cp, dict) else None
            if ptr is None and isinstance(cp, dict):     # 구버전 Unity: {"first","second"}
                ptr = cp.get("second")
            c = self._local(ptr or {})
            if c is None:
                continue
            if c.type.name in _TRANSFORM_TYPES:
                continue
            out.append(self._component(c))
        return out

    def _component(self, c):
        entry = {"type": c.type.name}
        if c.type.name == "MonoBehaviour":
            cls, tree = self.mono.read(c)
            entry["script"] = cls or "(불명)"
            if not self.want_fields:
                return entry
            entry["fields"] = self._fields(c, tree) if tree is not None else None
            return entry
        if not self.want_fields:
            return entry
        entry["fields"] = self._fields(c, self._tt(c))
        return entry

    def _fields(self, owner, tree):
        if not isinstance(tree, dict):
            return None
        out = {}
        for k, v in tree.items():
            if k in _NOISE_FIELDS:
                continue
            if k == "m_Name" and not v:
                continue
            out[k] = self.index.expand(owner, v)
        return out


def _script_registry(input_path, sources, cfg, log):
    """스크립트 정의를 몰아둔 번들을 미리 열어 MonoScript 색인을 만든다.

    Royal Kingdom은 `data.unity3d`(3.8MB)에 MonoScript 7,616개만 두고, 그걸 쓰는
    MonoBehaviour 는 `datapack.unity3d`(88MB)에 둔다. 번들을 하나씩 열면 참조가
    끊겨 복원율이 14%까지 떨어진다.

    **스크립트 전용 번들만** 미리 연다 (MonoScript 가 많고 MonoBehaviour 는 적은 것).
    조건 없이 다 열면 Zen Match의 90MB 번들을 두 번 읽게 된다.

    번들은 **하나씩 열고 바로 닫는다.** 예전에는 ExitStack 에 넣어 런이 끝날 때까지
    열어 뒀는데, 그러면 스크립트 번들 전부가 뒤이은 씬·프리팹 처리 내내 메모리에
    같이 살아 있었다. `ScriptRegistry.add_env` 가 값(ScriptRef)만 뽑아 두므로
    닫아도 색인은 그대로 쓸 수 있다.
    """
    if cfg.get("script_registry") is False:
        return None
    min_scripts = cfg.get("script_registry_min", 100)
    picked = [s for s in sources
              if isinstance(s, discover.UnitySource)
              and s.type_counts.get("MonoScript", 0) >= min_scripts
              and s.type_counts.get("MonoScript", 0) > s.type_counts.get("MonoBehaviour", 0)]
    if not picked:
        return None

    reg = typetree.ScriptRegistry()
    for s in picked:
        data, _ = container.find_first(input_path, [s.name, f"*/{s.name}"])
        if data is None:
            continue
        try:
            with unity.load_bytes(
                    data, suffix=os.path.splitext(s.name)[1] or ".unity3d") as env:
                reg.add_env(env, s.basename)
        except Exception as e:  # noqa: BLE001 - 못 열면 그냥 없이 간다
            log(f"[hierarchy] 스크립트 번들 {s.basename} 열기 실패: {e}")
            continue
        del data                      # 색인에 값이 들어갔으니 번들 원본은 놓는다
    if not reg:
        return None
    log(f"[hierarchy] 스크립트 색인 {reg.count:,}개 등록 "
        f"({', '.join(f'{b}×{n}' for b, n in reg.sources[:3])}) — 번들 간 참조 해석용")
    return reg


def _classify(index):
    """파일 이름 → 'scene' | 'prefab' | None(계층 없음)."""
    kinds = {}
    for fname in index.files():
        types = {o.type.name for o in index.by_file[fname].values()}
        if not (types & set(_TRANSFORM_TYPES)):
            continue
        kinds[fname] = "scene" if types & set(_SCENE_MARKERS) else "prefab"
    return kinds


def extract_hierarchy(input_path, hier_cfg, out_dir, game="game", mono_cfg=None, log=print):
    """씬·프리팹 계층을 <out_dir>/<game>_hierarchy.zip 으로 뽑는다."""
    cfg = hier_cfg or {}
    sources, src_objs = discover.resolve_detailed(input_path, cfg.get("sources"), log=log)
    want_scenes = cfg.get("scenes", True)
    want_prefabs = cfg.get("prefabs", True)
    want_fields = (cfg.get("fields") or "full") != "none"
    max_nodes = cfg.get("max_nodes", 200000)

    os.makedirs(out_dir, exist_ok=True)
    zpath = os.path.join(out_dir, f"{game}_hierarchy.zip")
    used, failures, entries = [], [], []
    n_scenes = n_prefabs = n_nodes = 0
    truncated = False
    mono_note = ""
    seen_paths, n_dupes = set(), 0

    mono = None                  # 소스마다 새로 만들면 안 된다 — 아래 주석 참고
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        registry = _script_registry(input_path, src_objs, cfg, log)
        for label, data in _iter_sources(input_path, sources):
            used.append(label)
            suffix = os.path.splitext(label)[1] or ".unity3d"
            with unity.load_bytes(data, suffix=suffix) as env:
                index = unity.ObjectIndex(env)
                if mono is None:
                    # MonoReader 하나를 모든 소스가 공유한다. 소스마다 만들면
                    # libil2cpp.so(112MB) + global-metadata.dat(20MB) 를 백엔드마다
                    # 다시 읽는다 — Zen Match는 소스가 16개라 그 로딩만 100초를 넘었다.
                    # 한 빌드 안에서는 Unity 버전과 스크립트 정의가 같으므로 공유해도 된다.
                    mono = typetree.open_reader(
                        input_path, mono_cfg, typetree.detect_unity_version(env),
                        log=log, registry=registry)
                kinds = _classify(index)
                log(f"[hierarchy] {os.path.basename(label)}: "
                    + (", ".join(f"{f}({k})" for f, k in kinds.items())
                       if kinds else "GameObject 계층 없음 (텍스처·머티리얼 전용 번들)"))

                for fname, kind in kinds.items():
                    if kind == "scene" and not want_scenes:
                        continue
                    if kind == "prefab" and not want_prefabs:
                        continue
                    b = _Builder(index, fname, mono, want_fields, max_nodes - n_nodes)
                    roots = b.roots()
                    if kind == "scene":
                        doc = {"file": fname, "kind": "scene",
                               "roots": [r for r in (b.build(tr) for _n, tr in roots) if r]}
                        path = _unique(f"scenes/{_safe(fname)}.json", seen_paths)
                        zf.writestr(path, _dump(doc))
                        entries.append({"path": path, "kind": "scene", "file": fname,
                                        "roots": len(doc["roots"]), "nodes": b.nodes})
                        n_scenes += 1
                    else:
                        for name, tr in roots:
                            doc = b.build(tr)
                            if doc is None:
                                continue
                            want = f"prefabs/{_safe(fname)}/{_safe(name)}.json"
                            path = _unique(want, seen_paths)
                            if path != want:
                                n_dupes += 1
                            zf.writestr(path, _dump({"file": fname, "kind": "prefab",
                                                     "root": doc}))
                            entries.append({"path": path, "kind": "prefab", "file": fname,
                                            "name": name})
                            n_prefabs += 1
                    n_nodes += b.nodes
                    truncated = truncated or b.truncated
                    failures.extend(b.failures)

        # 리더를 공유하므로 통계도 누적된다 — 소스마다 찍으면 같은 줄이 16번 나온다
        if mono is not None:
            mono_note = mono.summary()
            log(mono_note)

        zf.writestr("index.json", _dump({
            "game": game, "sources": used, "scenes": n_scenes, "prefabs": n_prefabs,
            "nodes": n_nodes, "name_collisions": n_dupes, "truncated": truncated,
            "typetree": mono_note, "failures": failures, "entries": entries}))

    if not used:
        log(f"[hierarchy] 경고: sources {sources} 에 맞는 Unity 파일을 찾지 못했습니다")
    log(f"[hierarchy] 씬 {n_scenes}개 · 프리팹 {n_prefabs}개 · 노드 {n_nodes}개 → {zpath}"
        f" ({os.path.getsize(zpath) / 1e6:.1f}MB)"
        + (f" · 이름중복 {n_dupes}건은 _2 접미로 분리" if n_dupes else "")
        + (f" · max_nodes({max_nodes}) 도달로 중단" if truncated else ""))
    for f in failures[:5]:
        log(f"  ! {f}")
    return HierarchyResult(zpath, n_scenes, n_prefabs, n_nodes, failures, used, truncated)


def _dump(doc):
    """항상 **규격에 맞는** JSON을 낸다.

    컴포넌트 필드에는 NaN/Infinity가 실제로 섞여 있다. json 기본 설정은 이걸
    `NaN` 리터럴로 뱉는데 그건 JSON이 아니라서 뷰어의 JSON.parse가 통째로 실패한다.
    그래서 allow_nan=False로 먼저 시도하고, 걸리면 그때만 값을 훑어 정리한다
    (정상 문서에서 전체 순회를 한 번 더 하지 않기 위해).
    """
    try:
        return json.dumps(doc, ensure_ascii=False, indent=1, default=str,
                          allow_nan=False).encode("utf-8")
    except ValueError:
        return json.dumps(_finite(doc), ensure_ascii=False, indent=1, default=str,
                          allow_nan=False).encode("utf-8")


def _finite(v, depth=0):
    if depth > 60:
        return "…"
    if isinstance(v, float):
        return v if math.isfinite(v) else None
    if isinstance(v, dict):
        return {k: _finite(x, depth + 1) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_finite(x, depth + 1) for x in v]
    return v


def _iter_sources(input_path, sources):
    patterns = as_list(sources)
    if not patterns:
        return
    for c in container.iter_containers(input_path):
        with c:
            for n in c.glob(patterns):
                yield f"{c.label}!{n}", c.read(n)
