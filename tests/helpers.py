"""테스트용 합성 컨테이너 만들기 + UnityPy 없이 쓰는 가짜 오브젝트 하네스."""
import io
import json
import os
import types
import zipfile


def jbytes(obj):
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def level(n, **kw):
    d = {"id": n, "width": 3, "height": 2,
         "pixels": [{"x": 0, "y": 0, "material": 1}, {"x": 1, "y": 0, "material": 2}]}
    d.update(kw)
    return d


def make_zip_bytes(entries):
    """{경로: bytes} → zip 바이트."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries.items():
            z.writestr(name, data)
    return buf.getvalue()


def write_zip(path, entries):
    with open(path, "wb") as f:
        f.write(make_zip_bytes(entries))
    return path


def write_tree(root, files):
    """{상대경로: bytes} 를 실제 폴더로 풀어쓴다."""
    for rel, data in files.items():
        p = os.path.join(root, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
    return root


def apk_with_levels(ids, set_dir="3db5681e"):
    """레벨 json이 든 apk 바이트."""
    return make_zip_bytes({f"assets/Levels/{set_dir}/{i}.json": jbytes(level(i)) for i in ids})


# ─────────────── UnityPy 대역 — ObjectIndex/계층 로직을 실물 없이 검증 ───────────────
#
# 실제 번들을 합성할 수는 없으므로, levelscope가 UnityPy 오브젝트에서 실제로
# 만지는 표면(type.name / path_id / assets_file / read_typetree / read)만 흉내낸다.

class FakeFile:
    """SerializedFile 대역. externals 순서가 PPtr의 m_FileID-1 색인이 된다."""

    def __init__(self, name, externals=(), unity_version=None):
        self.name = name
        self.externals = [types.SimpleNamespace(name=e, path=e) for e in externals]
        self.unity_version = unity_version


class FakeObj:
    def __init__(self, type_name, path_id, file, tree=None, attrs=None, read_error=False):
        self.type = types.SimpleNamespace(name=type_name)
        self.path_id = path_id
        self.assets_file = file
        self._tree = tree if tree is not None else {}
        self._attrs = attrs or {}
        self._read_error = read_error

    def read_typetree(self, nodes=None):
        if self._read_error and nodes is None:
            raise ValueError("Expected to read 76 bytes, but only read 48 bytes")
        if nodes is not None and not getattr(nodes, "works", True):
            raise ValueError("nodes 불일치")
        return self._tree

    def read(self, check_read=True):
        return types.SimpleNamespace(**self._attrs)


class FakeEnv:
    def __init__(self, objects, files=None):
        self.objects = list(objects)
        self.files = files or {}


def pptr(path_id, file_id=0):
    return {"m_FileID": file_id, "m_PathID": path_id}


def go(path_id, file, name, components=(), active=True, layer=0):
    """GameObject 대역. components는 (path_id) 목록."""
    return FakeObj("GameObject", path_id, file,
                   tree={"m_Name": name, "m_IsActive": active, "m_Layer": layer,
                         "m_Component": [{"component": pptr(c)} for c in components]},
                   attrs={"m_Name": name})


def rect(path_id, file, gameobject, children=(), father=0, size=(100.0, 50.0), pos=(0.0, 0.0)):
    """RectTransform 대역."""
    return FakeObj("RectTransform", path_id, file, tree={
        "m_GameObject": pptr(gameobject),
        "m_Father": pptr(father),
        "m_Children": [pptr(c) for c in children],
        "m_LocalPosition": {"x": 0.0, "y": 0.0, "z": 0.0},
        "m_LocalScale": {"x": 1.0, "y": 1.0, "z": 1.0},
        "m_LocalRotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
        "m_SizeDelta": {"x": size[0], "y": size[1]},
        "m_AnchoredPosition": {"x": pos[0], "y": pos[1]},
        "m_AnchorMin": {"x": 0.0, "y": 0.0},
        "m_AnchorMax": {"x": 1.0, "y": 1.0},
        "m_Pivot": {"x": 0.5, "y": 0.5},
    })
