"""입력 컨테이너 추상화 — 폴더 / zip / apk / xapk / obb 를 한 인터페이스로 다룬다.

이 모듈이 생기기 전에는 extract.py·sprites.py가 "폴더인가 apk인가 xapk인가"를
각각 따로, 미묘하게 다르게 처리했다. 여기로 모아 동작을 일치시킨다.

    for c in iter_containers(input_path):     # 바깥 → 내부 아카이브 순
        for name in c.glob(["assets/Levels/*/*.json"]):
            data = c.read(name)

Container
    names()            내부 엔트리 상대경로 목록 (항상 '/' 구분자)
    glob(patterns)     문자열 또는 문자열 목록으로 매칭 (fnmatch)
    read(name)         엔트리 바이트
    label              출처 표기 ("base.apk", "app.xapk!base.apk")

iter_containers 는 XAPK 안의 base.apk·split apk·obb 까지 훑는다.
(구버전은 최상위 .apk 만 봤기 때문에 Android/obb/*.obb 안의 레벨을 놓쳤다.)
"""
import fnmatch
import io
import os
import zipfile
from pathlib import PurePosixPath

from . import concat

#: 내부를 다시 열어볼 아카이브 확장자
NESTED_EXT = (".apk", ".obb", ".apks")
#: 입력 자체로 받아들이는 zip 계열 확장자
ZIP_EXT = (".apk", ".xapk", ".zip", ".obb", ".apks", ".jar")


class UnsupportedInput(Exception):
    """폴더도 zip 계열도 아닌 입력."""


def as_list(v):
    """설정값을 목록으로 정규화 — 문자열 하나도, 목록도 받는다."""
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def _has_magic(pat):
    return any(c in pat for c in "*?[")


class Container:
    label = "?"

    def names(self):
        raise NotImplementedError

    def read(self, name):
        raise NotImplementedError

    def head(self, name, n=32):
        """엔트리 앞부분만 읽는다.

        매직 바이트로 Unity 번들인지 보려고 수백 MB를 통째로 푸는 건 낭비다.
        기본 구현은 전체를 읽으므로 하위 클래스가 필요하면 더 싸게 덮어쓴다.
        """
        return self.read(name)[:n]

    def size_of(self, name):
        """엔트리 크기(바이트). 내용을 읽지 않고 알 수 있으면 그렇게 한다."""
        return len(self.read(name))

    def close(self):
        pass

    def glob(self, patterns):
        """패턴에 맞는 엔트리들 (입력 순서 유지, 중복 제거).

        정확한 경로가 안 맞으면 경로 뒷부분으로도 맞춰본다 — apk 기준으로 쓴
        `assets/x.json` 를 XAPK 해제본(`base/assets/x.json`)에 그대로 쓸 수 있게.
        """
        names = self.names()
        out, seen = [], set()
        for pat in as_list(patterns):
            p = pat.replace("\\", "/")
            if _has_magic(p):
                hits = fnmatch.filter(names, p)
                if not hits:
                    hits = [n for n in names if fnmatch.fnmatch(n, "*/" + p.lstrip("/"))]
            else:
                hits = [p] if p in names else [n for n in names if n.endswith("/" + p)]
            for n in hits:
                if n not in seen:
                    seen.add(n)
                    out.append(n)
        return out

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()

    def __repr__(self):
        return f"<{type(self).__name__} {self.label}>"


class ZipContainer(Container):
    def __init__(self, zf, label):
        self._z = zf
        self.label = label
        self._names = None

    def names(self):
        if self._names is None:
            self._names = [n for n in self._z.namelist() if not n.endswith("/")]
        return self._names

    def read(self, name):
        return self._z.read(name)

    def head(self, name, n=32):
        try:
            with self._z.open(name) as f:
                return f.read(n)
        except Exception:  # noqa: BLE001 - 손상 엔트리는 빈 헤더로 취급
            return b""

    def size_of(self, name):
        return self._z.getinfo(name).file_size

    def close(self):
        try:
            self._z.close()
        except Exception:  # noqa: BLE001 - 닫기 실패는 무시
            pass


class DirContainer(Container):
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.label = self.root
        self._names = None

    def names(self):
        if self._names is None:
            out = []
            for r, _dirs, files in os.walk(self.root):
                for f in files:
                    rel = os.path.relpath(os.path.join(r, f), self.root)
                    out.append(rel.replace(os.sep, "/"))
            self._names = sorted(out)
        return self._names

    def path_of(self, name):
        return os.path.join(self.root, name.replace("/", os.sep))

    def read(self, name):
        with open(self.path_of(name), "rb") as f:
            return f.read()

    def head(self, name, n=32):
        try:
            with open(self.path_of(name), "rb") as f:
                return f.read(n)
        except OSError:
            return b""

    def size_of(self, name):
        return os.path.getsize(self.path_of(name))


#: 세그먼트 표 캐시 — {(라벨, 엔트리, 크기, 앞 64바이트): [(offset, length)]}.
#: 값은 세그먼트당 튜플 하나라 1,369개도 수십 KB 다. **bytes 는 담지 않는다.**
#:
#: 키에 **앞부분 바이트까지** 넣는다. root ZipContainer 의 label 은 basename 이라
#: (`app.apk`) 폴더가 다른 동명 파일이 같은 키를 갖는다. 크기·머리까지 같으면
#: 같은 파일로 봐도 된다.
_TABLES = {}


class ConcatView(Container):
    """번들 여러 개가 **이어붙은** 엔트리를 세그먼트별 가상 엔트리로 펼친다.

    Clash of Critters 의 `inpackage_aa_1.lpak` 은 UnityFS 번들 1,369개를 그냥
    연달아 붙인 파일이다. 그냥 열면 UnityPy 가 **첫 번들만 읽고 멈춰서** 108MB
    중 오브젝트 16개만 잡힌다(실측: 3,708 → 229,785). 근거는 `concat` 독스트링.

    이 층에서 펼치는 덕에 discover·sprites·assets·hierarchy·extract 는 고칠 게
    없다. 그쪽은 `names()`/`read()`/`glob()` 만 보기 때문이다.

    **부모 bytes 는 한 칸만 캐시한다.** 소비자들은 `names()` 순서대로 훑으므로
    한 부모의 세그먼트가 연속으로 들어온다. 캐시가 없으면 세그먼트마다 108MB 를
    다시 읽고, 무제한 캐시면 부모 여러 개가 동시에 상주한다.
    """

    def __init__(self, inner, log=None):
        self.inner = inner            # 감싼 원본 (테스트·타입 판정용)
        self._inner = inner
        self.label = inner.label
        self._log = log or (lambda *_a: None)
        self._map = None              # {부모 이름: [(offset, length)]}
        self._names = None
        self._cache = (None, None)    # (부모 이름, bytes) — 한 칸

    # -- 펼치기 ------------------------------------------------------------
    def _scan(self):
        """부모 후보를 찾아 세그먼트 표를 만든다. 앞 64바이트만 보고 고른다.

        표는 `_TABLES` 에 (컨테이너, 엔트리, 크기) 로 캐시한다. `find_first` 가
        소스마다 컨테이너를 새로 열기 때문에, 캐시가 없으면 108MB 부모를 소스
        1,369개마다 다시 읽고 다시 걸어간다.
        """
        if self._map is not None:
            return
        self._map = {}
        for n in self._inner.names():
            try:
                size = self._inner.size_of(n)
            except Exception:  # noqa: BLE001 - 크기를 못 읽는 엔트리는 그냥 둔다
                continue
            head = self._inner.head(n, concat.HEAD)
            if not concat.looks_concat(head, size):
                continue
            key = (self.label, n, size, bytes(head))
            if key in _TABLES:
                if _TABLES[key]:
                    self._map[n] = _TABLES[key]
                continue
            try:
                data = self._inner.read(n)
            except Exception:  # noqa: BLE001 - 읽을 수 없으면 펼치지 않는다
                continue
            segs = concat.segments(data)
            _TABLES[key] = segs
            if segs:
                self._map[n] = segs
                self._cache = (n, data)
                self._log(f"[concat] {n} — 번들 {len(segs):,}개가 이어붙어 있습니다"
                          f" ({size:,}B, 그냥 열면 첫 번들만 읽힙니다)")
            else:
                self._log(f"[concat] {n} — 번들 매직이 있지만 헤더를 따라가지"
                          " 못했습니다. 펼치지 않고 원본을 그대로 씁니다")

    def _parent_bytes(self, parent):
        if self._cache[0] == parent:
            return self._cache[1]
        data = self._inner.read(parent)
        self._cache = (parent, data)     # 한 칸이므로 이전 부모는 여기서 놓인다
        return data

    def _seg(self, name):
        """가상 엔트리면 (부모, offset, length), 아니면 None."""
        self._scan()
        parent, i = concat.parent_of(name)
        if i is None or parent not in self._map:
            return None
        segs = self._map[parent]
        return (parent,) + segs[i] if i < len(segs) else None

    # -- Container 인터페이스 ----------------------------------------------
    def names(self):
        if self._names is None:
            self._scan()
            out = []
            for n in self._inner.names():
                segs = self._map.get(n)
                if segs:
                    out.extend(concat.sub_name(n, i) for i in range(len(segs)))
                else:
                    out.append(n)
            self._names = out
        return self._names

    def read(self, name):
        seg = self._seg(name)
        if seg is None:
            return self._inner.read(name)
        parent, off, ln = seg
        return self._parent_bytes(parent)[off:off + ln]

    def head(self, name, n=32):
        seg = self._seg(name)
        if seg is None:
            return self._inner.head(name, n)
        parent, off, ln = seg
        return self._parent_bytes(parent)[off:off + min(n, ln)]

    def size_of(self, name):
        seg = self._seg(name)
        return seg[2] if seg else self._inner.size_of(name)

    def glob(self, patterns):
        """펼친 이름과 **부모 이름** 양쪽으로 맞춘다.

        두 갈래가 다 필요하다.
        ① 세그먼트 이름을 그대로 주는 경우 — `discover` 가 찾아 둔 소스 이름
           (`...lpak#0770`)으로 `find_first` 가 다시 조회한다. 이걸 빼먹었더니
           survey 의 리소스 집계가 세그먼트 1,369개를 통째로 놓쳤다.
        ② 설정에 부모 경로를 적어 둔 경우 (`sources: [assets/aa/Android/*.lpak]`)
           — 펼친 뒤에는 그 이름의 엔트리가 없으니 세그먼트 전부로 바꿔 준다.
        """
        self._scan()
        out, seen = [], set()

        def add(name):
            if name not in seen:
                seen.add(name)
                out.append(name)

        for n in Container.glob(self, patterns):      # ① 펼친 이름 기준
            add(n)
        for n in self._inner.glob(patterns):          # ② 부모 이름 기준
            if n in self._map:
                for i in range(len(self._map[n])):
                    add(concat.sub_name(n, i))
            else:
                add(n)
        return out

    def path_of(self, name):
        """DirContainer 위에 씌운 경우용. 세그먼트에는 실제 파일 경로가 없다."""
        parent, i = concat.parent_of(name)
        if i is not None and parent in (self._map or {}):
            raise ValueError(f"이어붙인 번들의 세그먼트에는 파일 경로가 없습니다: {name}")
        return self._inner.path_of(name)

    def close(self):
        self._cache = (None, None)
        self._inner.close()

    def __repr__(self):
        return f"<ConcatView {self.label}>"


def open_root(input_path):
    """입력 경로 자체를 Container로 연다 (폴더 또는 zip 계열 파일)."""
    p = os.path.abspath(input_path)
    if os.path.isdir(p):
        return DirContainer(p)
    if not os.path.exists(p):
        raise FileNotFoundError(f"입력 경로 없음: {p}")
    if not p.lower().endswith(ZIP_EXT) and not zipfile.is_zipfile(p):
        raise UnsupportedInput(f"지원하지 않는 입력(폴더도 zip 계열도 아님): {p}")
    try:
        return ZipContainer(zipfile.ZipFile(p), os.path.basename(p))
    except zipfile.BadZipFile as e:
        raise UnsupportedInput(f"zip으로 열 수 없음: {p}") from e


def nested_names(names):
    """내부에서 다시 열어볼 아카이브 엔트리들. base.apk → 기타 apk → obb 순."""
    def rank(n):
        b = PurePosixPath(n).name.lower()
        return (0 if b == "base.apk" else 1 if b.endswith(".apk") else 2, b)

    return sorted((n for n in names if n.lower().endswith(NESTED_EXT)), key=rank)


def iter_containers(input_path, log=None):
    """입력 자체 → 내부 아카이브(base.apk·split apk·obb) 순으로 Container를 낸다.

    호출자가 다 쓴 컨테이너의 close()를 책임진다. 열리지 않는 아카이브는 건너뛴다.
    내부 아카이브를 꺼낼 때는 **별도 핸들**을 쓴다 — 호출자가 root를 이미 닫았을 수 있다.

    번들이 여러 개 이어붙은 엔트리는 `ConcatView` 가 세그먼트별 가상 엔트리로
    펼쳐서 낸다. `log` 를 주면 무엇을 펼쳤는지 남긴다.
    """
    log = log or (lambda *_a: None)
    root = open_root(input_path)
    names = root.names()          # 닫히기 전에 목록을 확보해 둔다
    yield ConcatView(root, log=log)

    nested = nested_names(names)
    if not nested:
        return
    if isinstance(root, DirContainer):
        for n in nested:
            try:
                zf = zipfile.ZipFile(root.path_of(n))          # 실제 파일 — 메모리 복사 불필요
            except (zipfile.BadZipFile, OSError):
                continue
            yield ConcatView(ZipContainer(zf, os.path.join(root.label, n)), log=log)
        return
    with zipfile.ZipFile(input_path) as outer:                 # root와 독립된 핸들
        for n in nested:
            try:
                zf = zipfile.ZipFile(io.BytesIO(outer.read(n)))
            except (zipfile.BadZipFile, KeyError, OSError):
                continue
            yield ConcatView(ZipContainer(zf, f"{root.label}!{n}"), log=log)


def find_first(input_path, patterns):
    """패턴에 맞는 첫 엔트리의 (bytes, label). 없으면 (None, None).

    팔레트·스프라이트처럼 "어느 컨테이너에 있든 하나만 찾으면 되는" 경우용.
    """
    for c in iter_containers(input_path):
        with c:
            hits = c.glob(patterns)
            if hits:
                return c.read(hits[0]), f"{c.label}!{hits[0]}"
    return None, None
