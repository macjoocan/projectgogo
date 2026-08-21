"""IL2CPP MonoBehaviour typetree 복원.

IL2CPP 빌드는 커스텀 스크립트의 필드 구조(typetree)를 번들에 담지 않는다. 그래서
UnityPy가 MonoBehaviour를 읽으면 대부분 실패한다 — SheepNSheep은 1659개 중 1653개가
`ValueError: Expected to read N bytes` 로 떨어졌다. 이름과 컴포넌트 타입까지는 보이는데
"이 Image가 어떤 스프라이트를 쓰는가", "이 Text의 문자열은 무엇인가"를 못 읽는 상태다.

`libil2cpp.so` + `global-metadata.dat` 를 TypeTreeGeneratorAPI에 먹이면 구조가 되살아난다.
IL2CppDumper를 따로 돌릴 필요는 없다 (dump.cs 89MB를 만들던 그 과정이 통째로 불필요하다).

백엔드 하나로는 부족하다. 실측(SheepNSheep, 1659개):

    AssetRipper 단독      1364 / 1659  (82.2%)
    + AssetStudio 폴백    1659 / 1659  (100%)

AssetRipper가 못 읽는 쪽은 I2.Loc.Localize(200개)·UI LayoutGroup 계열(52개)·
Spine 계열(33개)로 뚜렷하게 갈린다. 그래서 클래스별로 성공한 백엔드를 기억해두고
그쪽을 계속 쓴다 (매번 첫 백엔드부터 재시도하면 객체 수천 개에서 헛일이 쌓인다).

    mono = MonoReader.open(input_path, cfg, unity_version, log=print)
    cls, tree = mono.read(obj)      # 못 읽으면 tree=None. cls는 그래도 준다.
    log(mono.summary())
"""
import dataclasses
import os

from . import container, unity
from .container import as_list

#: 폴백 순서. 앞쪽이 더 많이 맞고, 뒤쪽이 앞쪽의 사각지대를 메운다.
DEFAULT_BACKENDS = ("AssetRipper", "AssetStudio", "AssetsTools")

#: 재료 기본 위치 — 대부분의 Unity 안드로이드 빌드가 이 경로를 쓴다.
DEFAULT_IL2CPP = ["lib/arm64-v8a/libil2cpp.so", "lib/armeabi-v7a/libil2cpp.so",
                  "lib/*/libil2cpp.so"]
DEFAULT_METADATA = ["assets/bin/Data/Managed/Metadata/global-metadata.dat",
                    "*/Metadata/global-metadata.dat"]


class TypeTreeUnavailable(RuntimeError):
    """typetree 복원에 필요한 것이 없다 (패키지 미설치 또는 재료 파일 부재)."""


@dataclasses.dataclass
class ScriptRef:
    assembly: str
    namespace: str
    cls: str

    @property
    def fullname(self):
        return f"{self.namespace}.{self.cls}" if self.namespace else self.cls


def _ref_from(ms):
    cls = getattr(ms, "m_ClassName", "") or ""
    if not cls:
        return None
    return ScriptRef(getattr(ms, "m_AssemblyName", "") or "",
                     getattr(ms, "m_Namespace", "") or "", cls)


class ScriptRegistry:
    """여러 번들에 흩어진 MonoScript 를 모아 **번들 경계를 넘는** 참조를 푼다.

    Royal Kingdom은 스크립트 정의(MonoScript 7,616개)를 `data.unity3d` 에 두고
    그걸 쓰는 MonoBehaviour 는 `datapack.unity3d` 에 둔다. 번들을 하나씩 열면
    UnityPy의 `deref()` 가 상대 파일을 못 찾아 실패한다 — 실측 복원율 14%.
    여기에 스크립트 보유 번들을 미리 등록해 두면 직접 찾아갈 수 있다.
    """

    def __init__(self):
        self._by_file = {}          # SerializedFile 이름 → {path_id: ScriptRef}
        self.sources = []

    def __bool__(self):
        return bool(self._by_file)

    @property
    def count(self):
        return sum(len(v) for v in self._by_file.values())

    def add_env(self, env, label=""):
        """이 번들의 MonoScript 를 **지금 읽어 값만** 색인에 남긴다.

        reader(`o`)를 그대로 담으면 그 안의 `assets_file`·`reader` 때문에 번들
        env 전체가 색인이 사는 동안 메모리에 붙잡힌다. 그래서 예전에는 호출자가
        번들들을 ExitStack 에 열어 둔 채 런이 끝날 때까지 유지해야 했다.
        여기서 `ScriptRef`(문자열 3개)로 줄여 두면 호출자가 번들을 바로 닫을 수 있다.
        """
        n = 0
        for o in env.objects:
            if o.type.name != "MonoScript":
                continue
            try:
                ref = _ref_from(o.read())
            except Exception:  # noqa: BLE001 - 못 읽는 MonoScript 는 색인에서 뺀다
                continue
            if ref is None:
                continue
            self._by_file.setdefault(unity.file_name(o), {})[o.path_id] = ref
            n += 1
        if n:
            self.sources.append((label, n))
        return n

    def resolve(self, obj):
        """MonoBehaviour → ScriptRef. 못 풀면 None."""
        try:
            sc = obj.read(check_read=False).m_Script
            fid, pid = getattr(sc, "file_id", None), getattr(sc, "path_id", None)
        except Exception:  # noqa: BLE001
            return None
        if not pid:
            return None
        if fid:
            ext = getattr(getattr(obj, "assets_file", None), "externals", None) or []
            if not 0 <= fid - 1 < len(ext):
                return None
            fname = getattr(ext[fid - 1], "name", None) or "?"
        else:
            fname = unity.file_name(obj)
        return self._by_file.get(fname, {}).get(pid)


def script_ref(obj, registry=None):
    """MonoBehaviour → ScriptRef. m_Script를 못 따라가면 None.

    같은 파일 안이면 UnityPy의 deref 가 바로 풀어준다. 실패하면 등록해 둔
    ScriptRegistry 로 번들 경계를 넘어 찾아본다.
    """
    try:
        ref = _ref_from(obj.read(check_read=False).m_Script.deref().read())
        if ref is not None:
            return ref
    except Exception:  # noqa: BLE001 - 스크립트 참조가 끊긴 오브젝트는 흔하다
        pass
    return registry.resolve(obj) if registry is not None else None


def detect_unity_version(env):
    """번들 안 SerializedFile에서 Unity 버전 문자열 (예: '2021.3.42f1')."""
    for f in getattr(env, "files", {}).values():
        v = getattr(f, "unity_version", None)
        if v:
            return v
        for sf in getattr(f, "files", {}).values():
            v = getattr(sf, "unity_version", None)
            if v:
                return v
    return None


def find_materials(input_path, cfg=None):
    """(il2cpp_bytes, metadata_bytes, labels). 하나라도 없으면 TypeTreeUnavailable.

    XAPK는 libil2cpp.so가 config.arm64_v8a.apk 안, metadata는 base apk 안에 따로
    들어있다. container.find_first가 중첩 아카이브를 훑으므로 그대로 넘긴다.
    """
    cfg = cfg or {}
    so_pats = as_list(cfg.get("il2cpp")) or DEFAULT_IL2CPP
    md_pats = as_list(cfg.get("metadata")) or DEFAULT_METADATA
    so, so_label = container.find_first(input_path, so_pats)
    if so is None:
        raise TypeTreeUnavailable(f"libil2cpp.so 없음 (탐색: {so_pats})")
    md, md_label = container.find_first(input_path, md_pats)
    if md is None:
        raise TypeTreeUnavailable(f"global-metadata.dat 없음 (탐색: {md_pats})")
    return so, md, (so_label, md_label)


class MonoReader:
    """MonoBehaviour를 typetree로 읽어주는 객체. 실패해도 예외를 밖으로 안 낸다."""

    def __init__(self, generators, log=print, registry=None, factory=None, backends=None):
        self.registry = registry             # 번들 경계를 넘는 MonoScript 조회용
        self._gens = dict(generators)        # 이미 올라온 {backend: TypeTreeGenerator}
        self._factory = factory              # 이름 -> 생성자. None 이면 지연 로드 없음
        self._order = list(backends or generators)
        self._dead = set()                   # 만들다 실패한 백엔드 (다시 시도하지 않는다)
        self._nodes = {}                     # (backend, asm, full) -> nodes | None
        self._winner = {}                    # (asm, full) -> backend (성공한 백엔드 기억)
        self.log = log
        self.ok = 0
        self.failed = 0
        self.no_script = 0
        self.fail_classes = {}

    # ── 생성 ────────────────────────────────────────────────────────

    @classmethod
    def open(cls, input_path, cfg, unity_version, log=print, registry=None):
        """설정·재료가 갖춰지면 MonoReader, 아니면 TypeTreeUnavailable."""
        cfg = cfg or {}
        if cfg.get("enabled") is False:
            raise TypeTreeUnavailable("typetree.enabled=false")
        try:
            from TypeTreeGeneratorAPI import TypeTreeGenerator
        except ImportError as e:
            raise TypeTreeUnavailable(
                "TypeTreeGeneratorAPI 미설치 → pip install TypeTreeGeneratorAPI") from e
        version = cfg.get("unity_version") or unity_version
        if not version:
            raise TypeTreeUnavailable("Unity 버전을 알 수 없음 (typetree.unity_version 지정 필요)")

        so, md, labels = find_materials(input_path, cfg)
        log(f"[typetree] il2cpp={_short(labels[0])} ({len(so) / 1e6:.1f}MB)"
            f" metadata={_short(labels[1])} ({len(md) / 1e6:.1f}MB) unity={version}")

        backends = as_list(cfg.get("backends")) or list(DEFAULT_BACKENDS)

        def factory(name):
            """백엔드 하나를 만든다. **부르는 시점에** IL2CPP 를 파싱한다.

            여기가 비싼 곳이다 — PixelFlow(libil2cpp 193MB · metadata 42MB) 실측으로
            AssetRipper 2.86GB · AssetStudio 1.38GB · AssetsTools 0.70GB 다.
            `so`·`md` 는 나중 백엔드를 위해 클로저가 붙잡는다(235MB) — 쓰지도 않을
            백엔드 하나를 미리 파싱하는 값(GB)보다 훨씬 싸다.
            """
            g = TypeTreeGenerator(version, name)
            g.load_il2cpp(so, md)
            return g

        reader = cls({}, log=log, registry=registry, factory=factory, backends=backends)
        errs = reader._warm_first()
        if not reader._gens:
            raise TypeTreeUnavailable("모든 백엔드 초기화 실패 — " + " / ".join(errs))
        rest = [b for b in backends if b not in reader._gens and b not in reader._dead]
        log(f"[typetree] 백엔드 {list(reader._gens)} 준비"
            + (f" · 나머지 {rest} 는 폴백이 필요해지면 로드" if rest else "")
            + (f" (실패: {', '.join(errs)})" if errs else ""))
        return reader

    # ── 백엔드 확보 (지연) ──────────────────────────────────────────

    def _warm_first(self):
        """첫 백엔드 **하나만** 미리 올린다. 실패 사유 목록을 돌려준다.

        재료(libil2cpp/metadata)가 아예 못 쓰는 것이면 지금 알아야 하므로 하나는
        올려 본다. 나머지는 `_generator` 가 필요해질 때 올린다 — 백엔드마다 IL2CPP
        파싱에 GB 단위가 들고, 대부분의 클래스는 첫 백엔드로 읽힌다.
        """
        errs = []
        for name in self._order:
            if self._generator(name, errs=errs) is not None:
                break
        return errs

    def _generator(self, name, errs=None):
        """백엔드를 돌려준다. 아직 없으면 **지금 만든다.** 못 만들면 None."""
        if name in self._gens:
            return self._gens[name]
        if name in self._dead or self._factory is None:
            return None
        try:
            g = self._factory(name)
        except Exception as e:  # noqa: BLE001 - 백엔드별로 지원 범위가 다르다
            self._dead.add(name)
            if errs is None:
                self.log(f"[typetree] 백엔드 {name} 초기화 실패 — 건너뜁니다: {e}")
            else:
                errs.append(f"{name}: {e}")
            return None
        self._gens[name] = g
        if errs is None:                 # 지연 로드된 것만 알린다 (첫 로드는 open 이 찍는다)
            self.log(f"[typetree] 백엔드 {name} 추가 로드 —"
                     " 앞 백엔드가 못 읽는 클래스가 나왔습니다")
        return g

    # ── 노드 확보 ───────────────────────────────────────────────────

    def _nodes_for(self, backend, ref):
        key = (backend, ref.assembly, ref.fullname)
        if key in self._nodes:
            return self._nodes[key]
        gen = self._generator(backend)
        if gen is None:
            return None       # 캐시하지 않는다 — 백엔드가 없는 것은 _dead 가 기억한다
        try:
            from UnityPy.helpers.TypeTreeNode import TypeTreeNode
            raw = gen.get_nodes(ref.assembly, ref.fullname)
            nodes = TypeTreeNode.from_list(
                [{"m_Type": n.m_Type, "m_Name": n.m_Name,
                  "m_Level": n.m_Level, "m_MetaFlag": n.m_MetaFlag} for n in raw])
        except Exception:  # noqa: BLE001 - 정의가 없는 클래스는 그냥 다음 백엔드로
            nodes = None
        self._nodes[key] = nodes
        return nodes

    # ── 읽기 ───────────────────────────────────────────────────────

    def read(self, obj):
        """MonoBehaviour → (클래스명, dict). 실패 시 (클래스명 또는 None, None)."""
        ref = script_ref(obj, self.registry)
        if ref is None:
            self.no_script += 1
            return None, None
        key = (ref.assembly, ref.fullname)

        order = self._order
        win = self._winner.get(key)
        if win is not None:
            order = [win] + [b for b in self._order if b != win]

        for b in order:
            nodes = self._nodes_for(b, ref)
            if nodes is None:
                continue
            try:
                tree = obj.read_typetree(nodes)
            except Exception:  # noqa: BLE001 - 바이트 수 불일치 → 다음 백엔드
                continue
            self._winner[key] = b
            self.ok += 1
            return ref.cls, tree

        self.failed += 1
        self.fail_classes[ref.fullname] = self.fail_classes.get(ref.fullname, 0) + 1
        return ref.cls, None

    # ── 보고 ───────────────────────────────────────────────────────

    def summary(self):
        tot = self.ok + self.failed + self.no_script
        if not tot:
            return "[typetree] 읽은 MonoBehaviour 없음"
        line = (f"[typetree] MonoBehaviour {self.ok}/{tot} 복원 ({self.ok / tot * 100:.1f}%)"
                f" · 실패 {self.failed} · 스크립트참조없음 {self.no_script}")
        if self.fail_classes:
            top = sorted(self.fail_classes.items(), key=lambda kv: -kv[1])[:5]
            line += "\n[typetree] 실패 상위: " + ", ".join(f"{k}×{v}" for k, v in top)
        return line


class NullMonoReader:
    """typetree 없이도 파이프라인이 돌게 하는 대체물 — 기본 read만 시도한다."""

    def __init__(self, reason="", log=print, registry=None):
        self.registry = registry
        self.reason = reason
        self.ok = 0
        self.failed = 0
        self.no_script = 0
        self.fail_classes = {}

    def read(self, obj):
        ref = script_ref(obj, self.registry)
        cls = ref.cls if ref else None
        try:
            tree = obj.read_typetree()
            self.ok += 1
            return cls, tree
        except Exception:  # noqa: BLE001
            self.failed += 1
            return cls, None

    def summary(self):
        tot = self.ok + self.failed
        pct = f" ({self.ok / tot * 100:.1f}%)" if tot else ""
        return (f"[typetree] 비활성 — {self.reason}\n"
                f"[typetree] 기본 읽기로 {self.ok}/{tot}{pct} — "
                "IL2CPP 빌드라면 컴포넌트 필드 대부분이 비어 나옵니다")


def open_reader(input_path, cfg, unity_version, log=print, registry=None):
    """MonoReader를 열되, 안 되면 NullMonoReader로 내려앉는다 (런을 죽이지 않는다)."""
    try:
        return MonoReader.open(input_path, cfg, unity_version, log=log, registry=registry)
    except TypeTreeUnavailable as e:
        log(f"[typetree] 사용 불가: {e}")
        return NullMonoReader(str(e), log=log, registry=registry)


def _short(label):
    return os.path.basename(str(label).replace("!", "/"))
