"""게임 리소스(스프라이트/텍스처) 추출.

설정 예:
  sprites:
    sources:                       # 컨테이너 내 Unity 파일/번들 경로 (glob 가능)
      - assets/bin/Data/data.unity3d
      - "assets/aa/Android/*.bundle"
    include:                       # 에셋 이름 목록. "re:정규식" 접두로 정규식 사용
      - Butterfly
      - "re:.*[Tt]ile.*"
    types: [Sprite]                # 기본 [Sprite]; Texture2D 추가 가능
    max_count: 500                 # 안전 상한 (기본 1000)

CLI 단독 실행:
  python -m levelscope sprites --input <apk> --source assets/bin/Data/data.unity3d \
         --names "re:.*tile.*,Butterfly" --out sprites_out
"""
import contextlib
import dataclasses
import gc
import io
import os
import re
import tempfile
import zipfile

from . import categorize, container, discover, unity
from .container import as_list


@dataclasses.dataclass
class SpriteResult:
    count: int
    path: str
    failures: list = dataclasses.field(default_factory=list)
    sources: list = dataclasses.field(default_factory=list)
    truncated: bool = False

    def __iter__(self):
        """구버전 `count, zpath = extract_sprites(...)` 호환."""
        return iter((self.count, self.path))


def _compile(includes):
    pats = []
    for inc in includes or []:
        if inc.startswith("re:"):
            pats.append(re.compile(inc[3:]))
        else:
            pats.append(re.compile(re.escape(inc) + r"$"))
    return pats


def _name_matches(name, pats):
    return not pats or any(p.fullmatch(name) or p.match(name) for p in pats)


def iter_source_bytes(input_path, sources):
    """(source_label, bytes) — 컨테이너(폴더·apk·xapk·obb·중첩 apk) 안의 unity 파일들."""
    patterns = as_list(sources)
    if not patterns:
        return
    for c in container.iter_containers(input_path):
        with c:
            for n in c.glob(patterns):
                yield f"{c.label}!{n}", c.read(n)


#: UnityPy가 못 찾은 파일 이름을 실패 메시지에서 뽑는다
_MISSING_RE = re.compile(r"File (\S+) not found")

#: 소스별 내부 SerializedFile 목록 캐시 (입력 경로 → [(소스명, {내부파일 소문자})])
_files_cache = {}


def missing_files(failures):
    """실패 메시지들에서 "못 찾은 파일" 이름을 모은다."""
    out = set()
    for f in failures:
        m = _MISSING_RE.search(f)
        if m:
            out.add(m.group(1).lower())
    return out


def _dep_names(input_path, exclude_label, wanted, log):
    """`wanted` 에 든 SerializedFile 을 품고 있는 번들의 **이름** 목록.

    예전에는 "sharedassets 를 가진 번들"이라는 어림짐작으로 골랐다. 그러면 이름이
    `CAB-<hash>` 인 경우를 놓치고(Zen Match), 큰 번들은 크기 상한에 걸려 빠졌다.
    실패 메시지가 **못 찾은 파일 이름을 그대로 알려주므로** 그걸로 찾는 게 정확하다.

    **여기서 bytes 를 읽어 모으지 말 것.** 후보가 수십 개인 Addressables 게임에서
    90MB 번들이 한꺼번에 살아 있게 되고, UnityPy 가 그걸 다시 풀면 3~5배로 부푼다.
    커밋 54GB 로 PC 가 멈춘 실제 사고의 최대 지분이 이 리스트였다. 이름만 돌려주고
    읽기는 호출자가 `_dep_file` 로 하나씩 한다.
    """
    key = str(input_path)
    if key not in _files_cache:
        _files_cache[key] = [(s.name, {f.lower() for f in s.files})
                             for s in discover.find_sources(input_path, log=lambda *_a: None)]
    picked = [name for name, files in _files_cache[key]
              if not exclude_label.endswith(name) and (wanted & files)]
    if picked:
        log(f"[sprites] 참조 대상 번들 {len(picked)}개 확보 "
            f"({', '.join(os.path.basename(n) for n in picked[:3])})"
            " — 교차 참조 해석용, 하나씩 시도한다")
    return picked


@contextlib.contextmanager
def _dep_file(input_path, name):
    """번들 하나를 임시파일로 떨어뜨려 **경로**를 낸다. 못 찾으면 None.

    UnityPy 에 bytes 로 주면 원본과 해제본이 파이썬 힙에 동시에 남는다. 경로로
    주면 UnityPy 가 직접 열고 닫으므로 우리 쪽에 압축 원본이 남지 않는다
    (`unity.load_bytes` 의 폴백이 이미 쓰는 방식이다).
    """
    data, _ = container.find_first(input_path, [name, f"*/{name}"])
    if data is None:
        yield None
        return
    with tempfile.NamedTemporaryFile(
            suffix=os.path.splitext(name)[1] or ".unity3d", delete=False) as tf:
        tf.write(data)
        tmp = tf.name
    del data                      # 디스크로 넘겼으니 즉시 놓는다
    try:
        yield tmp
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _extract_one(data, suffix, label, want_types, pats, zf, seen, failures, budget,
                 deps=(), only_ids=None, budget_atlas=unity.ATLAS_CACHE_BUDGET,
                 tally=None):
    """소스 하나에서 스프라이트를 뽑는다.

    only_ids 를 주면 **그 오브젝트만** 처리한다 — 재시도에서 쓴다. 이름으로 거르면
    이름이 같은 다른 스프라이트를 조용히 흘리게 되므로 오브젝트 단위로 집는다.

    반환: {"count", "truncated", "failed_ids"}
    """
    count, truncated = 0, False
    failed_ids = set()
    if budget <= 0:
        return {"count": 0, "truncated": True, "failed_ids": failed_ids}
    with unity.load_bytes(data, suffix=suffix, deps=deps) as env:
        for o in unity.iter_objects(env, want_types):
            oid = (unity.file_name(o), o.path_id)
            if only_ids is not None and oid not in only_ids:
                continue
            if count >= budget:
                truncated = True
                break
            try:
                obj = unity.read_obj(o)
                name = getattr(obj, "m_Name", "") or ""
                if not _name_matches(name, pats):
                    continue
                if o.type.name == "Texture2D" and not unity.has_pixels(obj):
                    # 못 읽은 게 아니라 애초에 픽셀이 없는 텍스처다 (unity.has_pixels)
                    failures.append(
                        f"{label}!{name}: 픽셀 데이터 없음 "
                        f"({getattr(obj, 'm_Width', 0)}x{getattr(obj, 'm_Height', 0)}"
                        " — 런타임 생성 텍스처)")
                    continue
                img = obj.image
                if img is None:
                    failures.append(f"{label}!{name}: 이미지 없음")
                    continue
                safe = re.sub(r'[\\/:*?"<>|]', "_", name)
                if tally is None:
                    key = _unique_key(f"{o.type.name}/{safe}", seen)
                else:
                    # 분류를 폴더로도, 파일명 앞에도 붙인다 — 압축을 풀어 평평하게
                    # 봐도 묶여 보이게 (만 장을 훑으려면 이게 필요하다)
                    cat = tally.add(name)
                    key = _unique_key(f"{cat}/{cat}_{safe}", seen)
                buf = io.BytesIO()
                img.save(buf, "PNG")
                zf.writestr(f"{key}.png", buf.getvalue())
                count += 1
                # UnityPy 는 디코드한 아틀라스를 끝까지 들고 있다 (실측 1.86GB,
                # 피크의 43%). 상한 밑으로 유지한다 — 산출물은 그대로다.
                if budget_atlas and count % 16 == 0:
                    unity.trim_atlas_cache(env, budget_atlas)
            except Exception as e:  # noqa: BLE001 - 개별 에셋 실패는 계속 진행하되 기록
                failures.append(f"{label}!{getattr(o, 'path_id', '?')}: {e!r}")
                failed_ids.add(oid)
    return {"count": count, "truncated": truncated, "failed_ids": failed_ids}


def _retry_with_deps(input_path, label, data, suffix, want_types, pats, zf, seen,
                     failures, n_before, count, max_count, failed_ids, wanted, log,
                     budget_atlas=unity.ATLAS_CACHE_BUDGET, tally=None):
    """교차 번들 참조 실패를 **번들 하나씩** 같이 올려 다시 시도한다. 새 count 반환.

    한꺼번에 다 올리면 메모리가 터진다(`_dep_names` 독스트링). 하나씩 올리고,
    아직 못 푼 오브젝트만 다음 번들로 넘긴다.
    """
    deps = _dep_names(input_path, label, wanted, log)
    if not deps:
        return count
    orig_fail = failures[n_before:]        # 재시도가 성공하면 이 메시지들은 버린다
    del failures[n_before:]
    remaining, gained, tries, last_fail = set(failed_ids), 0, 0, []
    for name in deps:
        if not remaining or count >= max_count:
            break
        with _dep_file(input_path, name) as dep_path:
            if dep_path is None:
                continue
            n_try = len(failures)
            tries += 1
            retry = _extract_one(data, suffix, label, want_types, pats, zf, seen,
                                 failures, max_count - count, deps=[dep_path],
                                 only_ids=remaining, budget_atlas=budget_atlas,
                                 tally=tally)
        count += retry["count"]
        gained += retry["count"]
        remaining = retry["failed_ids"]
        # 같은 오브젝트가 시도마다 실패로 다시 적힌다 — 마지막 시도의 것만 남긴다
        last_fail = failures[n_try:]
        del failures[n_try:]
    # 아무 번들도 못 열었으면 원래 실패를 되돌린다 ("없다"와 "못 읽었다"는 다르다)
    failures.extend(last_fail if tries else orig_fail)
    if tries:
        log(f"[sprites] {os.path.basename(label)}: 교차 번들 참조 재시도 "
            f"({tries}/{len(deps)}개 번들) → {gained}개 추가 · "
            f"남은 실패 {len(failures) - n_before}개")
    return count


def _unique_key(base, seen):
    """겹치지 않는 zip 키. **대소문자를 무시해서** 비교한다.

    Windows·macOS 파일시스템은 대소문자를 구분하지 않는다. zip 안에서는 다른
    파일이어도 풀면 나중 것이 앞 것을 덮어써 **조용히 한 장이 사라진다**.
    원본이 표기를 혼용하는 경우가 실제로 많다 — `IconSnsFacebook` 과
    `IconSnsFaceBook`, `shadow` 와 `Shadow`. 실측 충돌 수: Zen Match 60 ·
    Royal Kingdom 58 · Royal Match 31 · CookieRun 1 · PixelFlow 1.
    """
    key, n = base, 2
    while key.lower() in seen:
        key = f"{base}_{n}"
        n += 1
    seen.add(key.lower())
    return key


def extract_sprites(input_path, sprites_cfg, out_dir, game="game", log=print):
    """스프라이트를 PNG로 추출해 <out_dir>/<game>_sprites.zip 생성.

    반환: SpriteResult. 실패한 에셋은 조용히 넘기지 않고 개수·사유를 남긴다.
    """
    pats = _compile(sprites_cfg.get("include"))
    want_types = set(sprites_cfg.get("types") or ["Sprite"])
    max_count = sprites_cfg.get("max_count", 1000)
    # 아틀라스 캐시 상한(MB). 0 이면 상한 없음(예전 동작). 낮추면 메모리가 줄고
    # 같은 아틀라스를 다시 디코드해 느려진다 — 산출물은 어느 쪽이든 같다.
    # 이미지가 만 장 단위면 타입 폴더 하나에 다 들어가 못 본다. 분류를 켜면
    # `아이콘/아이콘_foo.png` 처럼 나온다. 기본은 꺼 둔다 — 경로가 바뀌면
    # `tools/build_icons_*.py` 처럼 `Sprite/<이름>.png` 를 그대로 찾는 것이 깨진다.
    tally = (categorize.Tally(categorize.compile_rules(sprites_cfg.get("categories")))
             if sprites_cfg.get("categorize") else None)
    mb = sprites_cfg.get("atlas_cache_mb")
    budget_atlas = (int(mb) * 2**20) if mb is not None else unity.ATLAS_CACHE_BUDGET
    sources = discover.resolve_sources(input_path, sprites_cfg.get("sources"), log=log)
    # 소스 발견은 후보 번들을 **한 번 다 열어 본다**. 그 메모리가 회수되기 전에 추출이
    # 같은 번들을 다시 열면 두 벌이 겹친다 — 실측으로 번들 하나가 1.83GB 였다.
    gc.collect()
    os.makedirs(out_dir, exist_ok=True)
    zpath = os.path.join(out_dir, f"{game}_sprites.zip")

    count, seen, failures, used_sources = 0, set(), [], []
    truncated = False
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for label, data in iter_source_bytes(input_path, sources):
            used_sources.append(label)
            if count >= max_count:
                truncated = True
                break
            suffix = os.path.splitext(label)[1] or ".unity3d"
            n_before = len(failures)
            missed = _extract_one(data, suffix, label, want_types, pats, zf, seen,
                                  failures, max_count - count,
                                  budget_atlas=budget_atlas, tally=tally)
            count += missed["count"]
            truncated = truncated or missed["truncated"]

            # 텍스처가 다른 번들에 있어 실패한 게 있으면, 그 번들을 같이 올려 재시도한다.
            # 실패가 없으면 아무 비용도 들지 않는다.
            wanted = missing_files(failures[n_before:])
            if wanted:
                count = _retry_with_deps(
                    input_path, label, data, suffix, want_types, pats, zf, seen,
                    failures, n_before, count, max_count, missed["failed_ids"],
                    wanted, log, budget_atlas=budget_atlas, tally=tally)
            del data                  # 다음 소스를 읽기 전에 이 번들을 놓는다

        if tally is not None and tally.counts:
            # 어떤 규칙이 몇 개를 잡았는지·못 잡은 이름 표본을 함께 넣는다.
            # 분류가 마음에 안 들면 이걸 보고 설정을 고치면 된다.
            zf.writestr("_categories.json", tally.to_json())

    if tally is not None and tally.counts:
        log(f"[sprites] 분류: {tally.summary_line()}")
        if tally.unmatched:
            log(f"[sprites] 분류 못 한 이름 표본: "
                f"{', '.join(tally.unmatched[:4])} … (_categories.json 참고)")
    if not used_sources:
        log(f"[sprites] 경고: sources {sources} 에 맞는 Unity 파일을 찾지 못했습니다")
    log(f"[sprites] {count}개 추출 → {zpath}"
        + (f" (실패 {len(failures)}개)" if failures else "")
        + (f" · max_count({max_count}) 도달로 중단" if truncated else ""))
    for f in failures[:5]:
        log(f"  ! {f}")
    return SpriteResult(count, zpath, failures, used_sources, truncated)
