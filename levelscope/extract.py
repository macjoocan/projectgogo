"""레벨 원본 수집 — 어떤 컨테이너에 어떤 형태로 들어있든 (set, id, bytes)로 만든다.

수집 경로 2가지
  1) 파일형   input.levels_glob 에 맞는 엔트리 (PixelFlow: assets/Levels/<해시>/<번호>.json)
  2) Unity형  input.unity — data.unity3d 등 안의 TextAsset / MonoBehaviour (Zen Match)

컨테이너 처리(폴더·apk·xapk·obb·중첩 apk)는 container.py 가 담당한다.

설정 (모두 문자열 하나 또는 목록 허용)
  input:
    levels_glob: "assets/Levels/*/*.json"      # 또는 [패턴, 패턴...]
    set_from: parent_dir | <정규식(그룹1)>
    level_id_from: stem | <정규식(그룹1)>
    merge_containers: false                    # true면 여러 컨테이너 결과를 합친다
    unity:
      data_file: assets/bin/Data/data.unity3d  # 목록·glob 가능
      type: TextAsset | MonoBehaviour
      field: levelJson                         # MonoBehaviour일 때 값이 담긴 프로퍼티
      script_class: LevelData                  # MonoBehaviour 스크립트 클래스 한정(선택)
      name_pattern: "Level_(\\d+)"             # 그룹1 = 레벨 id
      set_name: main
"""
import dataclasses
import os
import re
import zipfile
from pathlib import PurePosixPath

from . import container, unity
from .container import as_list


class ConfigError(Exception):
    """설정이 모자라 수집을 시작할 수 없음."""


@dataclasses.dataclass
class LevelRecord:
    set_name: str
    level_id: object
    raw: bytes
    source: str

    def __iter__(self):
        """구버전 코드의 `for s, lid, raw, src in recs` 언팩 호환."""
        return iter((self.set_name, self.level_id, self.raw, self.source))


@dataclasses.dataclass
class CollectResult:
    records: list
    container: object = None      # 부가 파일(팔레트 등)을 읽을 컨테이너
    source: str = ""              # 사람이 읽는 출처 표기
    warnings: list = dataclasses.field(default_factory=list)

    def __iter__(self):
        """구버전 `recs, container, path = collect_levels(...)` 호환."""
        return iter((self.records, self.container, self.source))

    def __len__(self):
        return len(self.records)


def _set_and_id(relpath, cfg):
    p = PurePosixPath(relpath)
    set_from = cfg.get("set_from", "parent_dir")
    if set_from == "parent_dir":
        set_name = p.parent.name
    else:  # 전체 상대경로에 정규식, 그룹1
        m = re.search(set_from, relpath)
        set_name = m.group(1) if m else ""
    id_from = cfg.get("level_id_from", "stem")
    if id_from == "stem":
        lid = p.stem
    else:
        m = re.search(id_from, relpath)
        lid = m.group(1) if m else p.stem
    return set_name, _maybe_int(lid)


def _maybe_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


# ─────────────────────────── 파일형 수집 ───────────────────────────

def _collect_files(input_path, input_cfg):
    patterns = as_list(input_cfg.get("levels_glob"))
    if not patterns:
        raise ConfigError("input.levels_glob (또는 input.unity) 설정이 필요합니다")
    merge = bool(input_cfg.get("merge_containers"))

    best, merged, tried = None, [], []
    keep = []
    for c in container.iter_containers(input_path):
        hits = c.glob(patterns)
        tried.append((c.label, len(hits)))
        if not hits:
            c.close()
            continue
        recs = [LevelRecord(*_set_and_id(n, input_cfg), c.read(n), f"{c.label}!{n}")
                for n in hits]
        if merge:
            merged.extend(recs)
            keep.append(c)
        elif best is None or len(recs) > len(best.records):
            if best is not None:
                best.container.close()
            best = CollectResult(recs, c, c.label)
        else:
            c.close()

    if merge and merged:
        for c in keep[1:]:
            c.close()                                  # 첫 컨테이너만 부가 파일용으로 남긴다
        labels = ", ".join(f"{lab}({n})" for lab, n in tried if n)
        return CollectResult(merged, keep[0], labels)
    if best is not None:
        return best

    seen = ", ".join(f"{lab}: 0" for lab, _ in tried) or "(컨테이너 없음)"
    raise FileNotFoundError(
        f"levels_glob {patterns} 에 맞는 파일이 없습니다: {input_path}\n"
        f"  훑어본 컨테이너 — {seen}\n"
        f"  힌트: `python -m levelscope ls --input <입력>` 으로 내부 경로를 확인하세요")


# ─────────────────────────── Unity 에셋 수집 ───────────────────────────

def _collect_unity(input_path, input_cfg):
    ucfg = input_cfg["unity"]
    patterns = as_list(ucfg.get("data_file") or ucfg.get("data_files"))
    if not patterns:
        raise ConfigError("input.unity.data_file 설정이 필요합니다")
    if not ucfg.get("name_pattern"):
        raise ConfigError("input.unity.name_pattern 설정이 필요합니다")
    pat = re.compile(ucfg["name_pattern"])
    set_name = ucfg.get("set_name", "main")
    want_type = ucfg.get("type", "TextAsset")
    field = ucfg.get("field")
    want_class = ucfg.get("script_class")

    out, warnings, seen = [], [], {}
    keep = None
    sources = []
    for c in container.iter_containers(input_path):
        hits = c.glob(patterns)
        if not hits:
            c.close()
            continue
        for n in hits:
            sources.append(f"{c.label}!{n}")
            with unity.load_bytes(c.read(n), suffix=os.path.splitext(n)[1] or ".unity3d") as env:
                for o in unity.iter_objects(env, [want_type]):
                    try:
                        obj = unity.read_obj(o)
                        name = getattr(obj, "m_Name", None)
                    except Exception as e:  # noqa: BLE001
                        warnings.append(f"{c.label}!{n}: 오브젝트 파싱 실패 {e!r}")
                        continue
                    if not name:
                        continue
                    m = pat.fullmatch(name)
                    if not m:
                        continue
                    if want_class and unity.script_class(o) != want_class:
                        continue
                    payload = unity.payload_bytes(o, field=field, obj=obj)
                    if payload is None:
                        warnings.append(f"{c.label}!{n}!{name}: 페이로드 없음"
                                        f"{' (field=' + field + ')' if field else ''}")
                        continue
                    lid = _maybe_int(m.group(1) if m.groups() else name)
                    k = seen.get(name, 0)
                    seen[name] = k + 1
                    sname = set_name if k == 0 else f"{set_name}_variant{k}"
                    out.append(LevelRecord(sname, lid, payload, f"{n}!{name}"))
        if keep is None:
            keep = c                     # 부가 파일(팔레트)용으로 첫 히트 컨테이너를 남긴다
        else:
            c.close()

    if not out:
        where = ", ".join(sources) or "(data_file 미발견)"
        raise FileNotFoundError(
            f"unity {want_type} 중 name_pattern '{ucfg['name_pattern']}' 에 맞는 게 없습니다\n"
            f"  훑어본 소스 — {where}")
    return CollectResult(out, keep, ", ".join(sources), warnings)


def collect_levels(input_path, input_cfg):
    """레벨 수집. CollectResult (records, container, source 로 언팩도 가능)."""
    input_path = os.path.abspath(input_path)
    if input_cfg.get("unity"):
        return _collect_unity(input_path, input_cfg)
    return _collect_files(input_path, input_cfg)


# ─────────────────────────── 부가 파일 읽기 ───────────────────────────

def read_from_container(c, inner_path):
    """컨테이너에서 부가 파일(팔레트 등) 읽기. glob 패턴도 허용. 없으면 None."""
    if c is None:
        return None
    if isinstance(c, container.Container):
        hits = c.glob([inner_path])
        return c.read(hits[0]) if hits else None
    if isinstance(c, zipfile.ZipFile):                  # 하위 호환
        try:
            return c.read(inner_path)
        except KeyError:
            return None
    p = os.path.join(c, inner_path)
    return open(p, "rb").read() if os.path.exists(p) else None


def make_reader(result, input_path):
    """부가 파일 리더. 선택된 컨테이너에 없으면 입력 전체에서 다시 찾는다.

    레벨은 obb에, 팔레트는 base.apk에 있는 split 배포에서 필요하다.
    """
    def read(inner_path):
        data = read_from_container(result.container, inner_path)
        if data is None:
            data, _ = container.find_first(input_path, [inner_path])
        return data
    return read


def list_entries(input_path, patterns=None, limit=200):
    """진단용: 입력 안에 뭐가 있는지 훑어본다. [(컨테이너, [경로...])]"""
    out = []
    for c in container.iter_containers(input_path):
        with c:
            names = c.glob(patterns) if patterns else c.names()
            out.append((c.label, names[:limit], len(names)))
    return out
