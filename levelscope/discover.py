"""Unity 에셋 소스 자동 발견 — 설정 없이 "이 APK 어디에 뭐가 있나"를 찾는다.

이 모듈이 생기기 전에는 `sources` 를 사람이 적어야 했고 기본값이
`assets/bin/Data/data.unity3d` 하나였다. 그래서 Addressables를 쓰는 게임은
`assets/aa/Android/*.bundle` 을 **통째로 놓쳤다** (Zen Match 15개 번들 7.5MB,
PixelFlow 24개). 여기서 컨테이너를 훑어 Unity로 열리는 것을 전부 찾는다.

함정이 하나 있다. **`UnityPy.load()` 는 아무 파일에나 성공한다** — JSON이든
boot.config든 오브젝트 0개인 env를 돌려준다. 그래서 "열리는지"로는 판별할 수 없고
`objects > 0` 을 봐야 한다. 순진하게 "열리면 Unity"로 잡으면 조용히 쓰레기를 훑는다.

    for src in find_sources(apk):
        print(src.name, src.kind, src.n_objects, src.top_types(3))
"""
import dataclasses
import fnmatch
import os

from . import container, unity

#: Unity 번들 매직. 이게 있으면 확실하다.
BUNDLE_MAGIC = (b"UnityFS", b"UnityWeb", b"UnityRaw", b"UnityArchive")

#: 확장자만 보고 후보로 올릴 것
ASSET_EXT = (".unity3d", ".bundle", ".assets", ".ab", ".unity")

#: 확장자가 있어도 Unity 에셋일 수 없는 것 — 후보에서 먼저 걷어낸다
SKIP_EXT = (
    ".dex", ".so", ".arsc", ".apk", ".obb", ".apks", ".jar", ".zip", ".aar",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ktx", ".astc",
    ".xml", ".json", ".html", ".js", ".css", ".md", ".txt", ".properties",
    ".version", ".proto", ".kotlin_module", ".kotlin_builtins", ".pro", ".cfg",
    ".ttf", ".otf", ".ttc", ".woff", ".woff2",
    ".mp3", ".ogg", ".wav", ".m4a", ".mp4", ".webm", ".fsb",
    ".resource", ".ress", ".dll", ".pdb", ".mdb", ".sf", ".rsa", ".mf",
)

#: 스트리밍 페이로드 — 에셋 파일이 아니라 텍스처/오디오 원본 덩어리다
SKIP_SUFFIX = (".resS", ".resource")

#: 확장자가 없어도 후보로 볼 경로 조각 (Unity 빌드가 확장자 없이 두는 파일들)
NOEXT_HINT = ("bin/data", "_data/", "/data/", "streamingassets", "/aa/", "resources/")

#: 이만큼보다 작으면 볼 것도 없다
MIN_SIZE = 64

#: Unity 내장 리소스 — 게임 에셋이 아니다 (기본 셰이더·폰트·Mesh).
#: 발견은 하되 추출 기본값에서는 뺀다. 안 그러면 모든 게임에서 같은 내장 에셋이
#: 산출물에 섞여 "이 게임 리소스"를 보는 데 방해가 된다.
BUILTIN_HINTS = ("unity default resources", "unity_builtin_extra", "unitybuiltinshaders")


@dataclasses.dataclass
class UnitySource:
    """Unity로 열리는 파일 하나."""
    container_label: str
    name: str                      # 컨테이너 안 상대경로
    kind: str                      # "bundle" | "serialized"
    size: int
    n_objects: int
    type_counts: dict = dataclasses.field(default_factory=dict)
    files: list = dataclasses.field(default_factory=list)   # 번들 내부 SerializedFile 이름

    @property
    def label(self):
        return f"{self.container_label}!{self.name}"

    @property
    def basename(self):
        return os.path.basename(self.name)

    @property
    def builtin(self):
        """Unity 내장 리소스인가 — 게임 에셋이 아니므로 추출 기본값에서 뺀다."""
        low = self.name.lower()
        return any(h in low for h in BUILTIN_HINTS)

    def top_types(self, n=5):
        return sorted(self.type_counts.items(), key=lambda kv: -kv[1])[:n]

    def to_dict(self):
        return {"container": self.container_label, "name": self.name, "kind": self.kind,
                "size": self.size, "objects": self.n_objects, "builtin": self.builtin,
                "files": self.files, "types": self.type_counts}


def rejected_by_name(name, size):
    """이름·크기만으로 "Unity 파일일 리 없다"가 확실한가.

    여기서 걸러내는 건 확실한 것만이다. 애매하면 통과시키고 매직으로 판정한다.
    """
    if size < MIN_SIZE:
        return True
    low = name.lower().replace("\\", "/")
    if any(low.endswith(s.lower()) for s in SKIP_SUFFIX):
        return True
    return os.path.splitext(low)[1] in SKIP_EXT


def name_suggests(name):
    """매직이 없어도 열어볼 만한 이름인가.

    원시 SerializedFile(`unity default resources`, `level0`)은 번들 매직이 없다.
    그래서 확장자나 경로 힌트로 한 번 더 건진다.
    """
    low = name.lower().replace("\\", "/")
    if os.path.splitext(low)[1] in ASSET_EXT:
        return True
    if os.path.splitext(low)[1]:
        return False
    return any(h in low for h in NOEXT_HINT)


def has_bundle_magic(head):
    return any(bytes(head[:16]).startswith(m) for m in BUNDLE_MAGIC)


def is_candidate(name, size, head=None):
    """열어볼 가치가 있나. head(앞부분 바이트)를 주면 매직까지 본다.

    Royal Kingdom은 Play Asset Delivery 팩 안에 **확장자 없는** 번들을 114개
    두는데(`assets/android/gameplay/hard_level/ui_v2`), 경로 힌트에 안 걸려서
    이름만으로는 전부 놓쳤다. 매직(`UnityFS`)이 있으면 이름이 뭐든 번들이다.
    """
    if rejected_by_name(name, size):
        return False
    if head is not None and has_bundle_magic(head):
        return True
    return name_suggests(name)


def probe(data, suffix=".unity3d"):
    """bytes → (kind, n_objects, type_counts, files). Unity가 아니면 (None, 0, {}, [])."""
    head = bytes(data[:16])
    kind = "bundle" if any(head.startswith(m) for m in BUNDLE_MAGIC) else "serialized"
    try:
        with unity.load_bytes(data, suffix=suffix) as env:
            counts, n = {}, 0
            for o in env.objects:
                n += 1
                t = o.type.name
                counts[t] = counts.get(t, 0) + 1
            # 내부 파일 목록은 **부수 정보**다. 이걸 본 try 안에 두면 여기서 난 예외가
            # 오브젝트 85개를 멀쩡히 읽어낸 판정까지 통째로 버린다 (실제로 그랬다 —
            # 원시 SerializedFile은 내부 키가 int라 문자열 취급이 터졌다).
            files = _inner_files(env)
    except unity.UnityUnavailable:
        raise
    except Exception:  # noqa: BLE001 - 깨진 번들은 그냥 아니라고 본다
        return None, 0, {}, []
    if n == 0:
        # UnityPy는 JSON·config에도 성공하고 오브젝트 0개를 준다. 번들 매직이
        # 확실한 경우만 (에셋이 비어 있을 수 있으므로) 살려 둔다.
        if kind == "bundle":
            return kind, 0, {}, files
        return None, 0, {}, []
    return kind, n, counts, files


def _inner_files(env):
    """번들 안 SerializedFile 이름들.

    원시 SerializedFile을 열면 내부 키가 **int(path_id)** 라 문자열이 아니다.
    번들일 때만 이름이 나오므로 문자열 키만 걸러 쓴다. 어떤 경우에도 예외를
    내지 않는다 — 호출자는 이 값이 없어도 정상 동작해야 한다.
    """
    out = []
    try:
        for f in getattr(env, "files", {}).values():
            sub = getattr(f, "files", None)
            if not isinstance(sub, dict):
                continue
            out.extend(k for k in sub
                       if isinstance(k, str) and not k.endswith((".resS", ".resource")))
    except Exception:  # noqa: BLE001 - 부수 정보이므로 조용히 비워 둔다
        return []
    return out


def find_sources(input_path, include=None, exclude=None, log=None, max_sources=0):
    """컨테이너를 훑어 Unity 소스 전부. include/exclude 는 glob 목록.

    바깥 컨테이너부터 중첩 아카이브(base.apk·split apk·obb)까지 순서대로 본다.
    """
    log = log or (lambda *_a: None)
    inc = container.as_list(include)
    exc = container.as_list(exclude)
    found, skipped = [], 0

    for c in container.iter_containers(input_path):
        with c:
            for name in c.names():
                if inc and not _match_any(name, inc):
                    continue
                if exc and _match_any(name, exc):
                    continue
                # 이름으로 먼저 걸러내고, 남은 것만 앞부분 32바이트를 본다.
                # 예전에는 후보 판단 전에 엔트리 전체를 읽어서 수백 MB짜리
                # 아카이브에서 통째로 압축을 풀곤 했다.
                try:
                    size = c.size_of(name)
                except Exception:  # noqa: BLE001
                    continue
                if rejected_by_name(name, size):
                    continue
                head = c.head(name, 32)
                if not is_candidate(name, size, head):
                    continue
                try:
                    data = c.read(name)
                except Exception:  # noqa: BLE001 - 읽을 수 없는 엔트리는 넘긴다
                    continue
                kind, n, counts, files = probe(data, suffix=_suffix(name))
                if kind is None:
                    skipped += 1
                    continue
                src = UnitySource(c.label, name, kind, len(data), n, counts, files)
                found.append(src)
                log(f"[discover] {kind:10} {name}  오브젝트 {n:,}"
                    + (f" · 내부파일 {len(files)}개" if len(files) > 1 else ""))
                if max_sources and len(found) >= max_sources:
                    log(f"[discover] max_sources({max_sources}) 도달로 중단")
                    return found

    found.sort(key=lambda s: -s.n_objects)
    n_builtin = sum(1 for s in found if s.builtin)
    log(f"[discover] Unity 소스 {len(found)}개 발견"
        f" (오브젝트 합계 {sum(s.n_objects for s in found):,})"
        + (f" · 내장 리소스 {n_builtin}개 포함" if n_builtin else "")
        + (f" · 후보였지만 Unity가 아닌 것 {skipped}개" if skipped else ""))
    return found


def _match_any(name, patterns):
    n = name.replace("\\", "/")
    return any(fnmatch.fnmatch(n, p) or fnmatch.fnmatch(n, "*/" + p.lstrip("/"))
               for p in patterns)


def _suffix(name):
    return os.path.splitext(name)[1] or ".unity3d"


def resolve_sources(input_path, cfg_sources, log=print, default=None, include_builtin=False):
    """설정의 `sources` 값을 실제 경로 목록으로 바꾼다."""
    return resolve_detailed(input_path, cfg_sources, log, default, include_builtin)[0]


def resolve_detailed(input_path, cfg_sources, log=print, default=None, include_builtin=False):
    """(경로 목록, UnitySource 목록).

    `auto`(또는 비어 있음)면 자동 발견 결과를 쓰고, 명시 목록이면 손대지 않는다
    (그 경우 UnitySource 목록은 비어 있다 — 타입 집계를 모르기 때문).
    자동 발견이 아무것도 못 찾으면 default 로 물러나되 그 사실을 로그에 남긴다.
    """
    vals = container.as_list(cfg_sources)
    if vals and vals != ["auto"]:
        return vals, []
    srcs = find_sources(input_path, log=log)
    if not include_builtin:
        dropped = [s for s in srcs if s.builtin]
        srcs = [s for s in srcs if not s.builtin]
        if dropped:
            log(f"[discover] Unity 내장 리소스 {len(dropped)}개 제외 "
                f"({', '.join(s.basename for s in dropped[:3])}) — 포함하려면 sources에 직접 적으세요")
    if not srcs:
        fallback = container.as_list(default) or ["assets/bin/Data/data.unity3d"]
        log(f"[discover] 자동 발견 실패 — 기본 경로로 시도: {fallback}")
        return fallback, []
    return [s.name for s in srcs], srcs
