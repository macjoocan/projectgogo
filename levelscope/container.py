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


def iter_containers(input_path):
    """입력 자체 → 내부 아카이브(base.apk·split apk·obb) 순으로 Container를 낸다.

    호출자가 다 쓴 컨테이너의 close()를 책임진다. 열리지 않는 아카이브는 건너뛴다.
    내부 아카이브를 꺼낼 때는 **별도 핸들**을 쓴다 — 호출자가 root를 이미 닫았을 수 있다.
    """
    root = open_root(input_path)
    names = root.names()          # 닫히기 전에 목록을 확보해 둔다
    yield root

    nested = nested_names(names)
    if not nested:
        return
    if isinstance(root, DirContainer):
        for n in nested:
            try:
                zf = zipfile.ZipFile(root.path_of(n))          # 실제 파일 — 메모리 복사 불필요
            except (zipfile.BadZipFile, OSError):
                continue
            yield ZipContainer(zf, os.path.join(root.label, n))
        return
    with zipfile.ZipFile(input_path) as outer:                 # root와 독립된 핸들
        for n in nested:
            try:
                zf = zipfile.ZipFile(io.BytesIO(outer.read(n)))
            except (zipfile.BadZipFile, KeyError, OSError):
                continue
            yield ZipContainer(zf, f"{root.label}!{n}")


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
