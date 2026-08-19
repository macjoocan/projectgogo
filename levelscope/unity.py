"""UnityPy 공통 헬퍼 — extract·palette·sprites 가 공유한다.

전에는 세 모듈이 각자 "bytes를 임시파일로 떨어뜨리고 UnityPy.load 하고 unlink"를
반복했다. UnityPy 1.x 는 bytes를 바로 받으므로 여기서 한 번만 처리하고,
안 되는 버전에서는 임시파일로 자동 폴백한다.

    with unity.load_bytes(data) as env:
        for o in unity.iter_objects(env, ["TextAsset"]):
            raw = unity.payload_bytes(o)
"""
import contextlib
import os
import tempfile


class UnityUnavailable(RuntimeError):
    """UnityPy 미설치."""


def _unitypy():
    try:
        import UnityPy
    except ImportError as e:  # pragma: no cover - 설치 환경 의존
        raise UnityUnavailable("UnityPy 모듈 필요 → pip install UnityPy") from e
    return UnityPy


@contextlib.contextmanager
def load_bytes(data, suffix=".unity3d", deps=()):
    """Unity 파일 bytes → env. bytes 직접 로드가 안 되면 임시파일로 폴백.

    deps 에 다른 번들의 bytes 를 주면 **같은 환경에** 함께 올린다. 스프라이트의
    텍스처가 다른 번들의 SerializedFile 에 있는 경우가 있어서(Royal Kingdom의
    `sharedassets0.assets`), 혼자 열면 UnityPy가 그 파일을 현재 작업 폴더에서 찾다가
    FileNotFoundError 로 실패한다. 같이 올리면 참조가 풀린다.

    yield를 try 안에 두면 안 된다. with 블록 **본문**에서 난 예외가 여기 except로
    잡혀 삼켜지고, 제너레이터가 폴백 경로로 흘러가 두 번째 yield에 닿아
    `RuntimeError: generator didn't stop after throw()` 로 바꿔치기된다.
    그러면 호출자는 진짜 원인을 못 본다. 그래서 load 호출만 감싼다.
    """
    UnityPy = _unitypy()
    try:
        env = UnityPy.load(data, *deps) if deps else UnityPy.load(data)
    except UnityUnavailable:
        raise
    except Exception:  # noqa: BLE001 - 구버전/특이 번들은 파일 경로로만 열린다
        env = None
    if env is not None:
        yield env
        return
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
        tf.write(data)
        tmp = tf.name
    try:
        yield UnityPy.load(tmp)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def iter_objects(env, types=None):
    """env의 오브젝트 중 원하는 타입만. types=None 이면 전부."""
    want = set(types) if types else None
    for o in env.objects:
        if want is None or o.type.name in want:
            yield o


def read_obj(o):
    """오브젝트 파싱. MonoBehaviour처럼 스크립트 의존 타입은 check_read=False 로 재시도."""
    try:
        return o.read()
    except Exception:  # noqa: BLE001
        return o.read(check_read=False)


def has_pixels(obj):
    """Texture2D 에 실제 픽셀 데이터가 있는지.

    픽셀은 파일 안(`image_data`)이나 밖(`m_StreamData`)에 있다. **둘 다 빈 텍스처가
    실제로 있다** — TextMeshPro 의 동적 폰트 아틀라스는 런타임에 만들어지므로 APK
    안에는 0x0 / 0바이트로 들어 있다(PixelFlow 의 `Font Texture` 14개).

    먼저 걸러야 하는 이유: UnityPy 는 `m_StreamData` 가 **있기만 하면** path 가 빈
    문자열이어도 리소스 파일로 열려 든다. 빈 경로는 현재 작업 폴더로 풀려서 폴더를
    open 하게 되고, Windows 에서 `PermissionError(13)` 가 난다. 그러면 실패 사유가
    "권한 문제"로 적혀 엉뚱한 데를 보게 된다 — 진짜 사유는 "픽셀이 없다" 다.
    정작 UnityPy 자신의 이미지 setter 는 `path=""` 를 "스트리밍 없음" 표시로 쓴다.
    """
    if getattr(obj, "image_data", None):
        return True
    sd = getattr(obj, "m_StreamData", None)
    return bool(getattr(sd, "path", "") and getattr(sd, "size", 0))


def name_of(o):
    """오브젝트 이름.

    Shader만 예외다 — m_Name이 비어 있고 실제 이름("Nox/OutlineEx")은
    m_ParsedForm.m_Name 안에 들어 있다. 이걸 안 보면 머티리얼 JSON에서
    가장 중요한 "어떤 셰이더냐"가 빈칸으로 나온다.
    """
    name = None
    try:
        name = read_obj(o).m_Name
    except Exception:  # noqa: BLE001 - 이름조차 못 읽는 오브젝트는 건너뛴다
        name = None
    if not name and getattr(o.type, "name", None) == "Shader":
        try:
            name = (o.read_typetree().get("m_ParsedForm") or {}).get("m_Name")
        except Exception:  # noqa: BLE001
            pass
    return name


def script_class(o):
    """MonoBehaviour가 참조하는 스크립트 클래스명 (없으면 None)."""
    try:
        return o.read(check_read=False).m_Script.deref().read().m_ClassName
    except Exception:  # noqa: BLE001
        return None


def file_name(o):
    """오브젝트가 속한 SerializedFile 이름 (level0 / resources.assets / ...).

    한 번들 안에서 씬(level0·level1)과 프리팹 저장소(resources.assets)를 갈라내는
    유일한 단서다. path_id는 파일마다 1부터 다시 시작하므로 이 이름과 짝지어야 한다.
    """
    return getattr(getattr(o, "assets_file", None), "name", None) or "?"


class ObjectIndex:
    """번들 전체 오브젝트 색인 + PPtr 해석.

    PPtr은 {m_FileID, m_PathID} 쌍이고, m_FileID의 의미가 파일마다 다르다 —
    0이면 자기 파일, N>0이면 그 파일의 externals[N-1]이 가리키는 다른 파일이다.
    path_id만 보고 번들 전체에서 찾으면 파일 간 충돌로 엉뚱한 에셋이 잡힌다.
    (`unity default resources` 처럼 번들 밖 파일을 가리키는 참조는 해석 불가로 남긴다.)
    """

    def __init__(self, env):
        self.by_file = {}                    # file_name -> {path_id: reader}
        for o in env.objects:
            self.by_file.setdefault(file_name(o), {})[o.path_id] = o
        self._names = {}                     # (file, path_id) -> 이름 캐시

    def files(self):
        return list(self.by_file)

    def objects(self, fname, types=None):
        want = set(types) if types else None
        for o in self.by_file.get(fname, {}).values():
            if want is None or o.type.name in want:
                yield o

    def resolve(self, owner, pptr):
        """PPtr dict → 대상 ObjectReader. 못 찾으면 None."""
        if not isinstance(pptr, dict):
            return None
        pid = pptr.get("m_PathID") or 0
        if not pid:
            return None
        fid = pptr.get("m_FileID") or 0
        if fid == 0:
            fname = file_name(owner)
        else:
            ext = getattr(getattr(owner, "assets_file", None), "externals", None) or []
            # 음수 m_FileID 가 실제로 나온다(Royal Kingdom). 위쪽만 막으면 파이썬의
            # 음수 인덱싱에 걸려 엉뚱한 파일을 잡거나 IndexError 로 터진다.
            if not 0 <= fid - 1 < len(ext):
                return None
            fname = getattr(ext[fid - 1], "name", None) or "?"
        return self.by_file.get(fname, {}).get(pid)

    def describe(self, owner, pptr):
        """PPtr → {"name":..., "type":...}. 해석 실패면 None (참조 자체가 없으면 None)."""
        target = self.resolve(owner, pptr)
        if target is None:
            return None
        key = (file_name(target), target.path_id)
        if key not in self._names:
            self._names[key] = name_of(target)
        return {"name": self._names[key] or "", "type": target.type.name}

    def expand(self, owner, value, depth=0):
        """typetree 값 안의 PPtr을 사람이 읽을 이름으로 바꾼다.

        `{'m_FileID': 0, 'm_PathID': 511}` 만 남은 JSON은 아무 정보가 없다.
        해석되면 `"UI_vortex_Atlas (TextAsset)"`, 번들 밖 참조면 `"→ 미해석"`,
        빈 참조면 None으로 접는다. 재귀 깊이를 제한해 순환·거대 구조를 막는다.
        """
        if depth > 12:
            return "…"
        if is_pptr(value):
            if not (value.get("m_PathID") or 0):
                return None
            d = self.describe(owner, value)
            if d is None:
                return "→ 미해석"
            return f"{d['name']} ({d['type']})" if d["name"] else f"({d['type']})"
        if isinstance(value, dict):
            return {k: self.expand(owner, v, depth + 1) for k, v in value.items()}
        # 튜플도 반드시 함께 다뤄야 한다 — UnityPy는 머티리얼 프로퍼티 맵 같은
        # (이름, 값) 쌍을 tuple로 준다. list만 보면 그 안의 PPtr이 통째로 안 풀린다.
        if isinstance(value, (list, tuple)):
            return [self.expand(owner, v, depth + 1) for v in value]
        if isinstance(value, (bytes, bytearray)):
            return f"<{len(value)} bytes>"
        return value


def is_pptr(v):
    """PPtr 모양의 dict인지 — typetree 결과에서 참조를 알아보는 유일한 방법이다."""
    return isinstance(v, dict) and len(v) == 2 and "m_FileID" in v and "m_PathID" in v


def _as_bytes(v):
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    if isinstance(v, str):
        return v.encode("utf-8", "surrogateescape")
    return None


def payload_bytes(o, field=None, obj=None):
    """TextAsset / MonoBehaviour 에서 문자열·바이트 페이로드를 꺼낸다.

    field: MonoBehaviour일 때 값이 담긴 프로퍼티명. 생략하면 typetree 안에서
           가장 긴 문자열 프로퍼티를 고른다 (레벨 JSON이 보통 압도적으로 길다).
    obj:   이미 읽어둔 오브젝트 (있으면 재파싱하지 않는다 — 수천 개 순회에서 2배 차이)
    """
    if o.type.name == "TextAsset" and not field:
        return _as_bytes((obj if obj is not None else read_obj(o)).m_Script)
    tree = None
    try:
        tree = o.read_typetree()
    except Exception:  # noqa: BLE001
        tree = None
    if isinstance(tree, dict):
        if field:
            return _as_bytes(tree.get(field))
        best = None
        for k, v in tree.items():
            if k in ("m_Name", "m_Script", "m_GameObject") or not isinstance(v, (str, bytes, bytearray)):
                continue
            if best is None or len(v) > len(best):
                best = v
        return _as_bytes(best)
    if obj is None:
        obj = read_obj(o)
    if field:
        return _as_bytes(getattr(obj, field, None))
    return _as_bytes(getattr(obj, "m_Script", None))
