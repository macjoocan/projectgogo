"""levelscope CLI.

  run      전체 파이프라인 (추출 → 디코딩 → xlsx/HTML/zip/sprites)
  inspect  샘플 1개 디코딩 결과 덤프 (설정 작성용)
  detect   인코딩 체인 자동 감지 (+ --xor-scan 으로 XOR 키 복구)
  ls        입력 컨테이너 안에 뭐가 있는지 훑기 (levels_glob 잡을 때)
  survey    처음 보는 APK 프로파일 + 설정 초안 (새 게임의 첫 명령)
  sprites   스프라이트/텍스처 추출
  assets    사운드·머티리얼·폰트·Spine·텍스트 추출
  hierarchy 씬·프리팹 계층 복원 (IL2CPP typetree 사용)

sprites/assets/hierarchy 의 `sources` 를 비우거나 `auto` 로 두면 Unity 소스를
자동 발견한다 (Addressables `assets/aa/**/*.bundle` 포함).
"""
import argparse
import collections
import contextlib
import gc
import dataclasses
import importlib
import json
import os
import sys
import zipfile

from . import container, decode, extract, palette as pal_mod, schema, viewer, xorscan


# ─────────────────────────── 설정·플러그인 ───────────────────────────

def _load_config(path):
    import yaml            # detect/ls/sprites 는 설정이 없어도 되므로 지연 임포트
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        sys.exit(f"설정 파일 형식 오류(딕셔너리가 아님): {path}")
    cfg["_config_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


@contextlib.contextmanager
def _extra_import_path(p):
    """플러그인 검색 경로를 임시로만 추가한다 (구버전은 sys.path를 영구 오염시켰다)."""
    p = os.path.abspath(p)
    added = os.path.isdir(p) and p not in sys.path
    if added:
        sys.path.insert(0, p)
    try:
        yield
    finally:
        if added:
            with contextlib.suppress(ValueError):
                sys.path.remove(p)


def _load_plugin(cfg):
    """플러그인 로드. 패키지 내장(levelscope/plugins/) 우선, 없으면 configs 옆 plugins/."""
    name = cfg.get("plugin")
    if not name:
        return None
    try:
        return importlib.import_module(f"levelscope.plugins.{name}")
    except ModuleNotFoundError:
        pass
    with _extra_import_path(os.path.join(cfg["_config_dir"], "..", "plugins")):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as e:
            sys.exit(f"플러그인 '{name}' 을 찾을 수 없습니다 "
                     f"(levelscope/plugins/{name}.py 또는 plugins/{name}.py): {e}")


def _plugin_hooks(plugin):
    return {h: getattr(plugin, h, None) for h in
            ("split_levels", "board", "level_extras", "entities", "viewer_level")} if plugin else {}


# ─────────────────────────── 디코딩 단계 ───────────────────────────

@dataclasses.dataclass
class DecodeOutcome:
    rows: list = dataclasses.field(default_factory=list)
    records: list = dataclasses.field(default_factory=list)
    entities_rows: list = dataclasses.field(default_factory=list)
    errors: list = dataclasses.field(default_factory=list)
    chains: object = dataclasses.field(default_factory=collections.Counter)


def _one_level(out, set_name, level_id, data, cfg, hooks):
    """디코딩된 레벨 하나 → Levels 행 + 뷰어 레코드."""
    row = {"set": set_name, "level": level_id}
    row.update(schema.extract_row(data, cfg.get("fields") or {}))
    board = hooks["board"](data) if hooks.get("board") else \
        schema.extract_board(data, cfg.get("board"))
    if board:
        row["grid_w"], row["grid_h"] = board["w"], board["h"]
        row["pixel_count"] = board["pixel_count"]
    if hooks.get("level_extras"):
        row.update(hooks["level_extras"](data))
    if hooks.get("entities"):
        out.entities_rows.extend(hooks["entities"](set_name, level_id, data))
    extra_v = hooks["viewer_level"](data) if hooks.get("viewer_level") else None
    out.rows.append(row)
    out.records.append({"set": set_name, "level": level_id, "row": row,
                        "board_enc": viewer.encode_board(board), "extra_viewer": extra_v})


#: `fields: auto` 가 컬럼을 추론할 때 볼 레코드 수
AUTO_SAMPLE = 200


def _resolve_auto_fields(records, cfg, log):
    """`fields: auto` → 표본에서 뽑은 실제 컬럼 지도. 실패하면 빈 지도.

    표본만 미리 디코딩한다. 전부 들고 있다가 추론하면 레벨 수천 개짜리 게임에서
    메모리가 다시 문제가 된다 — 앞 200개만 보고 정하고, 본 처리는 그대로 스트리밍한다.
    """
    codec_cfg = cfg.get("codec") or ["json"]
    subset = records[:AUTO_SAMPLE]
    samples = []
    auto = decode.AutoCodec(lambda *_a: None) if codec_cfg == "auto" else None
    for rec in subset:
        try:
            data = (auto.decode_capture(rec.raw)[0] if auto
                    else decode.apply_chain(rec.raw, codec_cfg))
        except Exception:  # noqa: BLE001 - 표본 실패는 본 처리에서 사유가 보고된다
            continue
        if isinstance(data, dict):
            samples.append(data)
    if not samples:
        log("[fields] auto: 표본에서 dict 형태 레벨을 찾지 못해 컬럼을 만들지 못했습니다"
            " — fields 를 직접 적어야 합니다 (원본 구조는 inspect 로 확인)")
        return {}
    fields, dropped, conflicts = schema.infer_fields(samples)
    n_s, n_c = len(fields["scalars"]), len(fields["counts"])
    log(f"[fields] auto: 표본 {len(samples)}개에서 컬럼 {n_s + n_c}개 추론 "
        f"(값 {n_s} · 개수 {n_c})")
    if conflicts:
        log(f"[fields] auto: 값 종류가 갈려 {len(conflicts)}개 제외 "
            f"— {', '.join(conflicts[:5])}{' 등' if len(conflicts) > 5 else ''}"
            " (레코드마다 스칼라·리스트가 섞이는 경로. 필요하면 fields 를 직접 적으세요)")
    if dropped:
        log(f"[fields] auto: 상한({schema.AUTO_MAX_COLS}개)에 걸려 {len(dropped)}개 제외 "
            f"— {', '.join(dropped[:5])}{' 등' if len(dropped) > 5 else ''}"
            " (필요하면 fields 를 직접 적으세요)")
    return fields


def _decode_all(records, cfg, plugin, log, on_plain=None):
    """레벨 원본 → 행/뷰어 레코드. on_plain(set, id, bytes) 가 있으면 평문도 넘긴다.

    플러그인이 `split_levels(data, record)` 를 제공하면 원본 하나가 레벨 여러 개로
    갈라진다 — 한 에셋/파일에 레벨을 몰아 담는 게임(예: SheepNSheep의 mapData)용.
    """
    codec_cfg = cfg.get("codec") or ["json"]
    auto = decode.AutoCodec(log) if codec_cfg == "auto" else None
    hooks = _plugin_hooks(plugin)
    _prepare_flatbuffers(records, codec_cfg, cfg, log)
    split = hooks.get("split_levels")
    want_plain = on_plain is not None
    out = DecodeOutcome()
    suggested = False

    for rec in records:
        try:
            if auto:
                data, steps, plain = auto.decode_capture(rec.raw, capture=want_plain)
            else:
                steps = codec_cfg
                if want_plain:
                    data, plain = decode.apply_chain(rec.raw, steps, capture=True)
                else:
                    data, plain = decode.apply_chain(rec.raw, steps), None
        except Exception as e:  # noqa: BLE001
            if not auto and not suggested:
                suggested = True
                _suggest_chain(rec.raw, log)
            out.errors.append((rec.source, repr(e)))
            continue
        out.chains[tuple(steps)] += 1

        if split is None:
            _one_level(out, rec.set_name, rec.level_id, data, cfg, hooks)
            if want_plain:
                on_plain(rec.set_name, rec.level_id, _plain_bytes(steps, plain, data))
            continue

        try:
            subs = list(split(data, rec))
        except Exception as e:  # noqa: BLE001
            out.errors.append((rec.source, f"split_levels 실패: {e!r}"))
            continue
        if not subs:
            out.errors.append((rec.source, "split_levels 결과 없음"))
            continue
        for set_name, level_id, sub in subs:
            _one_level(out, set_name, level_id, sub, cfg, hooks)
            if want_plain:
                on_plain(set_name, level_id,
                         json.dumps(sub, ensure_ascii=False, indent=1).encode("utf-8"))

    if auto and auto.variants:
        for k, n in auto.variants.items():
            log(f"[decode] 혼합 인코딩: {list(k)} × {n}개")
    return out


#: 종결 스텝이 이것들이면 "평문"이 바이너리다 — 그대로 .json 으로 저장하면 안 된다
_BINARY_TERMINALS = ("flatbuffers", "msgpack")


def _plain_bytes(steps, plain, data):
    """zip에 넣을 평문 바이트.

    보통은 파싱 직전의 텍스트를 그대로 쓴다. 하지만 FlatBuffers·msgpack 처럼
    **바이너리** 포맷이면 그 텍스트라는 게 원본 바이너리라서, 그대로 넣으면
    `levels/1.json` 안에 바이너리가 들어앉는다. 그 경우 디코딩 결과를 JSON 으로 낸다.
    """
    last = steps[-1] if steps else None
    if last not in _BINARY_TERMINALS and plain is not None:
        return plain
    return json.dumps(data, ensure_ascii=False, indent=1, default=str).encode("utf-8")


def _prepare_flatbuffers(records, codec_cfg, cfg, log):
    """FlatBuffers 체인이면 **디코딩 전에** 전체 표본으로 슬롯 타입을 확정한다.

    코덱 스텝은 버퍼를 하나씩 받아서 자기 힘으로는 표본을 못 모은다. 그런데
    FlatBuffers는 타입을 안 적어두기 때문에 한 버퍼만 보면 스칼라와 오프셋이
    헷갈린다 (Royal Kingdom: 보드 크기 정합성 4,500개 중 683개 실패).
    같은 스키마의 표본을 모아 다수결로 정하면 그 오차가 사라진다.
    """
    if "flatbuffers" not in (codec_cfg if isinstance(codec_cfg, list) else []):
        return
    from . import flatbuf
    fb_cfg = cfg.get("flatbuffers") or {}
    # 필드 이름 지도가 있으면 슬롯 번호 대신 원래 이름으로 낸다 (Royal Match).
    names = fb_cfg.get("names")
    if names:
        flatbuf.set_default_names(names)
        log(f"[flatbuf] 필드 이름 지도 {len(names)}경로 적용 — 슬롯 번호 대신 원래 이름")
    if fb_cfg.get("infer_schema") is False:
        return
    limit = fb_cfg.get("schema_samples", 0) or len(records)
    flatbuf.set_default_schema(
        flatbuf.infer_schema([r.raw for r in records[:limit]], log=log))


def _suggest_chain(raw, log):
    """설정 체인이 실패했을 때 자동 감지·XOR 스캔 결과를 제안으로 띄운다."""
    try:
        det, _ = decode.detect_chain(raw)
        log(f"[decode] 설정 체인 실패 — 자동 감지 제안: codec: {det}")
        return
    except Exception as e:  # noqa: BLE001
        log(f"[decode] 자동 감지도 실패: {e}")
    hit = xorscan.scan(raw)
    if hit:
        log(f"[decode] XOR 키 복구 성공: {hit} → codec: {json.dumps(hit.codec)}")
    else:
        log(f"[decode] 진단: {xorscan.diagnose(raw)['verdict']}")


#: xlsx 셀에 그대로 넣을 수 있는 값
_CELL_OK = (int, float, str, bool, type(None))


def _flatten_cell(v):
    """xlsx 가 못 받는 값(dict·리스트 등)을 짧은 문자열로 바꾼다.

    안전망이다. 한 셀 때문에 xlsx **전체**가 실패하면 안 된다 — Royal Match 를
    `fields: auto` 로 돌렸을 때 빈 벡터 dict 하나가 통째로 xlsx 를 죽였다.
    수동 설정도 dict 을 가리키면 같은 일이 난다. 원본은 zip 에 그대로 있으므로
    표에서는 길이를 줄여 보여주는 게 맞다.
    """
    if isinstance(v, _CELL_OK):
        return v
    if isinstance(v, (list, tuple, set)):
        return len(v)
    text = str(v)
    return text if len(text) <= 200 else text[:197] + "..."


def _build_dataframe(rows):
    import pandas as pd
    rows = [{k: _flatten_cell(v) for k, v in r.items()} for r in rows]
    df = pd.DataFrame(rows)
    sort_cols = [c for c in ("set", "level") if c in df.columns]
    if sort_cols:
        size = df.groupby("set")["level"].transform("count")
        df = (df.assign(_s=-size).sort_values(["_s"] + sort_cols)
                .drop(columns="_s").reset_index(drop=True))
    for c in df.columns:
        if df[c].dtype == object and all(isinstance(v, (int, float, type(None), bool)) for v in df[c]):
            df[c] = df[c].fillna(0)
    return df


def _write_error_report(out_dir, game, errors, warnings, log):
    if not errors and not warnings:
        return None
    path = os.path.join(out_dir, f"{game}_errors.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {game} — 추출/디코딩 실패 리포트\n")
        f.write(f"# 디코딩 실패 {len(errors)}건 / 수집 경고 {len(warnings)}건\n\n")
        for src, e in errors:
            f.write(f"[decode] {src}\n    {e}\n")
        for w in warnings:
            f.write(f"[collect] {w}\n")
    log(f"[errors] {len(errors)}건 실패 + {len(warnings)}건 경고 → {path}")
    return path


# ─────────────────────────── run ───────────────────────────

def run(args):
    cfg = _load_config(args.config)
    game = cfg.get("game", "levels")
    log = print
    log(f"[run] game={game} input={args.input}")

    result = extract.collect_levels(args.input, cfg["input"])
    records = result.records
    log(f"[input] 레벨 파일 {len(records)}개 발견 ({result.source})")
    for w in result.warnings[:5]:
        log(f"  ~ {w}")
    if not records:
        sys.exit("레벨 파일이 없습니다. levels_glob / input.unity 확인 필요")
    if args.limit:
        records = records[: args.limit]
        log(f"[input] --limit {args.limit} 적용 — {len(records)}개만 처리")

    plugin = _load_plugin(cfg)
    if schema.is_auto(cfg.get("fields")):
        # 장르마다 필드 이름이 다르다 — 손으로 적는 대신 표본에서 뽑는다
        cfg["fields"] = _resolve_auto_fields(records, cfg, log)
    outputs = cfg.get("outputs") or ["xlsx", "html"]
    os.makedirs(args.out, exist_ok=True)
    failed = []

    def emit(label, fn):
        """산출물 하나를 만든다. 실패해도 나머지는 계속 만든다.

        xlsx를 Excel로 열어둔 채 재실행하는 일이 흔한데, 예전에는 그 PermissionError가
        런 전체를 중단시켜 뷰어·zip까지 못 나왔다.

        **끝나면 반드시 gc 를 돌린다.** 단계가 끝나도 참조가 끊긴 Unity env 가 곧바로
        회수되지 않아, 다음 단계의 할당과 겹친다. CookieRun: Crumble 실측으로
        스프라이트(10,443장) 직후 3.63GB 가 남아 있었고, 이어서 에셋을 돌리면
        최고 커밋이 **5.50GB** 였다. 사이에 gc 를 넣으면 잔여가 0.74GB 로 떨어져
        **4.51GB** 로 끝난다 — 1.0GB(18%) 차이다.
        """
        try:
            fn()
            return True
        except Exception as e:  # noqa: BLE001
            hint = (" — 다른 프로그램(Excel 등)에서 열려 있는지 확인하세요"
                    if isinstance(e, PermissionError) else "")
            log(f"[{label}] 실패: {e}{hint}")
            failed.append(label)
            return False
        finally:
            gc.collect()

    zpath = os.path.join(args.out, f"{game}_levels_decoded.zip")
    zf = None
    if "zip" in outputs:
        try:
            zf = zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9)
        except Exception as e:  # noqa: BLE001
            log(f"[zip] 실패: {e}"
                + (" — 다른 프로그램에서 열려 있는지 확인하세요"
                   if isinstance(e, PermissionError) else ""))
            failed.append("zip")

    def on_plain(set_name, lid, plain):
        fn = f"levels/{set_name}/{lid}.json" if set_name else f"levels/{lid}.json"
        zf.writestr(fn, plain)

    try:
        got = _decode_all(records, cfg, plugin, log, on_plain=on_plain if zf else None)
        log(f"[decode] 성공 {len(got.rows)} / 실패 {len(got.errors)}")
        for src, e in got.errors[:5]:
            log(f"  ! {src}: {e}")
        if not got.rows:
            sys.exit("전부 디코딩 실패 — codec 설정을 확인하세요")

        colors, names = pal_mod.resolve_palette(
            cfg.get("palette"), extract.make_reader(result, args.input), log)

        if "xlsx" in outputs:
            def build_xlsx():
                from . import report_xlsx
                ents = None
                if got.entities_rows and plugin and hasattr(plugin, "ENTITY_SHEET"):
                    ents = (plugin.ENTITY_SHEET["name"], plugin.ENTITY_SHEET["headers"],
                            got.entities_rows)
                report_xlsx.build_workbook(
                    _build_dataframe(got.rows), cfg,
                    os.path.join(args.out, f"{game}_summary.xlsx"),
                    entities=ents, notes=cfg.get("notes"), log=log)
            emit("xlsx", build_xlsx)
        if "html" in outputs:
            emit("html", lambda: viewer.build_viewer(
                got.records, cfg, colors, names,
                os.path.join(args.out, f"{game}_viewer.html"), log=log))
        if zf is not None:
            zf.writestr("palette.json", json.dumps(
                [{"index": i, "name": names[i] if i < len(names) else "", "hex": c}
                 for i, c in enumerate(colors)], indent=1))
    finally:
        from . import flatbuf
        flatbuf.clear_default_schema()   # 다음 게임 런에 새면 안 된다
        if zf is not None:
            zf.close()
        if result.container is not None and hasattr(result.container, "close"):
            result.container.close()

    if zf is not None:
        log(f"[zip] 저장: {zpath} ({os.path.getsize(zpath) / 1e6:.1f}MB)")

    # 여기부터(sprites/assets/hierarchy)는 레벨 데이터를 쓰지 않는다. 그런데도 붙잡고
    # 있으면 Unity 번들 로딩과 겹쳐 커밋이 두 배로 뛴다 — 레벨 4,500개짜리 게임에서는
    # 이것만으로 수 GB 다. 뒤에 필요한 건 실패/경고 목록뿐이므로 그것만 남기고 놓는다.
    errors, warnings = got.errors, result.warnings
    del got, records, result, plugin, colors, names
    gc.collect()

    if "sprites" in outputs and cfg.get("sprites"):
        from . import sprites as sprites_mod
        emit("sprites", lambda: sprites_mod.extract_sprites(
            args.input, cfg["sprites"], args.out, game=game, log=log))
    if "assets" in outputs and cfg.get("assets"):
        from . import assets as assets_mod
        emit("assets", lambda: assets_mod.extract_assets(
            args.input, cfg["assets"], args.out, game=game, log=log))
    if "hierarchy" in outputs and cfg.get("hierarchy"):
        from . import hierarchy as hier_mod
        emit("hierarchy", lambda: hier_mod.extract_hierarchy(
            args.input, cfg["hierarchy"], args.out, game=game,
            mono_cfg=cfg.get("typetree"), log=log))

    _write_error_report(args.out, game, errors, warnings, log)
    if failed:
        log(f"[done] 산출물 {len(failed)}종 실패: {', '.join(failed)} — 나머지는 생성됨")
        sys.exit(1)
    log("[done]")


# ─────────────────────────── inspect / detect / ls ───────────────────────────

def inspect(args):
    cfg = _load_config(args.config)
    result = extract.collect_levels(args.input, cfg["input"])
    print(f"레벨 파일 {len(result.records)}개 ({result.source})")
    if not result.records:
        return
    rec = result.records[0]
    codec_cfg = cfg.get("codec") or ["json"]
    if codec_cfg == "auto":
        steps, data = decode.detect_chain(rec.raw)
        print(f"자동 감지 체인: {steps}")
    else:
        data = decode.apply_chain(rec.raw, codec_cfg)
    print(f"샘플: {rec.source} (set={rec.set_name}, level={rec.level_id})")
    print(json.dumps(data, ensure_ascii=False, indent=1)[: args.chars])


#: 레벨 데이터일 가능성이 없는 것들 — 설정 없는 detect에서 걸러낸다
_NOISE_EXT = (".dex", ".so", ".arsc", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ttf", ".otf",
              ".mp3", ".ogg", ".wav", ".mp4", ".apk", ".obb", ".unity3d", ".bundle", ".resource",
              ".resS", ".properties", ".version", ".kotlin_builtins", ".pro", ".xml")
_NOISE_DIR = ("META-INF/", "res/", "lib/", "kotlin/", "okhttp3/", "DebugProbesKt")


def _candidate_level_names(names):
    """레벨 파일일 법한 엔트리만. 'level'이 든 경로가 있으면 그쪽을 우선한다."""
    keep = [n for n in names
            if not n.lower().endswith(_NOISE_EXT) and not n.startswith(_NOISE_DIR)]
    hot = [n for n in keep if "level" in n.lower() or "stage" in n.lower()]
    return hot or keep


def _detect_samples(args):
    """(라벨, bytes) 샘플 목록 — 설정이 있으면 levels_glob으로, 없으면 컨테이너를 훑어서."""
    if args.config:
        cfg = _load_config(args.config)
        recs = extract.collect_levels(args.input, cfg["input"]).records
        stride = max(1, len(recs) // max(1, args.samples))
        return [(r.source, r.raw) for r in recs[::stride][: args.samples]]

    p = os.path.abspath(args.input)
    if os.path.isfile(p) and not zipfile.is_zipfile(p):
        with open(p, "rb") as fh:                       # 레벨 파일 하나를 직접 준 경우
            return [(p, fh.read())]

    out = []
    for c in container.iter_containers(p):
        with c:
            names = _candidate_level_names(c.names())
            if not names:
                continue
            stride = max(1, len(names) // max(1, args.samples))
            for n in names[::stride][: args.samples]:
                data = c.read(n)
                if data:
                    out.append((f"{c.label}!{n}", data))
        if len(out) >= args.samples:
            break
    return out[: args.samples]


def detect(args):
    """설정 없이도 동작: 샘플들의 인코딩 체인을 감지해 분포를 보고."""
    samples = _detect_samples(args)
    dist, fails = collections.Counter(), []
    for src, raw in samples:
        try:
            steps, _ = decode.detect_chain(raw)
            dist[tuple(steps)] += 1
        except Exception as e:  # noqa: BLE001
            fails.append((src, str(e), raw))

    print(f"샘플 {len(samples)}개 감지 결과:")
    for steps, n in dist.most_common():
        print(f"  {n:>5}개  codec: {list(steps)}")
    for src, e, _raw in fails[:5]:
        print(f"  실패: {src} — {e}")

    if dist:
        best = list(dist.most_common(1)[0][0])
        print(f"\n설정 제안 → codec: {json.dumps(best)}   (또는 codec: auto)")

    if fails:
        src, _e, raw = fails[0]
        d = xorscan.diagnose(raw)
        print(f"\n[진단] {os.path.basename(src)} — {d['size']}바이트, 머리 {d['head_hex']}")
        print(f"  엔트로피 {d['entropy']}/8 · 출력가능문자 {d['printable']:.0%}"
              f" · 매직 {d['magic'] or '없음'}")
        print(f"  판정: {d['verdict']}")
        if d["keylen_candidates"]:
            cands = ", ".join(f"{L}(IoC {s:.4f})" for L, s in d["keylen_candidates"])
            print(f"  반복키 길이 후보: {cands}")
        if args.xor_scan:
            print("  XOR 키 탐색 중...")
            hit = xorscan.scan(raw, max_keylen=args.max_keylen)
            if hit:
                print(f"  → 복구 성공: {hit}")
                print(f"  → 설정 제안: codec: {json.dumps(hit.codec)}")
            else:
                print(f"  → 반복키 XOR로는 복구 실패 (키 길이 ≤{args.max_keylen} 범위)."
                      " AES 등이면 키·IV를 확보해 aes_cbc: 스텝으로 지정하세요")
        else:
            print("  힌트: --xor-scan 을 붙이면 반복키 XOR 키 복구를 시도합니다")


def ls(args):
    """입력 컨테이너 내부 목록 — levels_glob / data_file 경로를 잡을 때."""
    patterns = [p.strip() for p in (args.glob or "").split(",") if p.strip()] or None
    for label, names, total in extract.list_entries(args.input, patterns, limit=args.limit):
        print(f"\n=== {label} — {total}개 엔트리"
              + (f" (패턴 {patterns} 일치)" if patterns else "") + " ===")
        for n in names:
            print(f"  {n}")
        if total > len(names):
            print(f"  ... {total - len(names)}개 더 (--limit 로 조절)")


def sprites_cmd(args):
    from . import sprites as sprites_mod, unity
    unity.set_fallback_version(getattr(args, "unity_version", None))
    if getattr(args, "split", False):
        from . import split as split_mod
        failed = split_mod.run_per_source(
            "sprites", args.input, args.out, args.game,
            ["--names", args.names, "--types", args.types, "--max", str(args.max)]
            + (["--categorize"] if args.categorize else []))
        if failed:
            sys.exit(1)
        return
    cfg = {"sources": [s.strip() for s in args.source.split(",") if s.strip()],
           "include": [n.strip() for n in args.names.split(",") if n.strip()],
           "types": [t.strip() for t in args.types.split(",") if t.strip()],
           "max_count": args.max,
           "categorize": args.categorize}
    sprites_mod.extract_sprites(args.input, cfg, args.out, game=args.game)


def recategorize_cmd(args):
    """이미 뽑아 둔 스프라이트 zip 에 분류만 다시 입힌다.

    APK 를 다시 열지 않으므로 몇 초에 끝나고 메모리도 거의 안 쓴다 — 예전에 뽑아 둔
    산출물을 버리지 않고 분류만 얹을 수 있다. 같은 zip 에 두 번 돌려도 결과가 같다.
    """
    from . import categorize
    extra = None
    if args.config:
        cfg = _load_config(args.config)
        extra = (cfg.get("sprites") or {}).get("categories")
    rules = categorize.compile_rules(extra)
    dst = args.out or args.zip
    tmp = dst + ".tmp"
    categorize.relabel_zip(args.zip, tmp, rules, log=print)
    if os.path.exists(dst):
        os.replace(tmp, dst)          # 같은 파일을 덮어쓰는 경우까지 안전하게
    else:
        os.rename(tmp, dst)
    print(f"[recategorize] 저장: {dst} ({os.path.getsize(dst) / 1e6:.1f}MB)")


def sources_cmd(args):
    """Unity 소스 이름만 한 줄에 하나씩 낸다.

    `--split` 이 자식으로 이걸 먼저 부른다 — 부모가 직접 발견하면 그 메모리(실측
    1.8GB)가 부모에 남아 자식 피크와 겹친다. 사람이 쓸 때도 "이 apk 에 Unity 소스가
    뭐가 있나"를 가장 싸게 보는 방법이다.
    """
    from . import discover, unity
    srcs = discover.find_sources(
        args.input, log=(print if args.verbose else (lambda *_a: None)))
    # 헤더로 Unity 버전을 알려 준다. 소스를 하나만 받는 자식은 버전을 배울 데가 없어서
    # 헤더에 버전이 없는 번들(Unity 6000 대)을 못 읽는다 — `--split` 이 이걸 넘긴다.
    ver = unity.fallback_version()
    if ver:
        print(f"#unity={ver}")
    for src in srcs:
        if src.builtin and not args.builtin:
            continue
        print(src.name)


def _sources_arg(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def assets_cmd(args):
    from . import assets as assets_mod, unity
    unity.set_fallback_version(getattr(args, "unity_version", None))
    if getattr(args, "split", False):
        from . import split as split_mod
        failed = split_mod.run_per_source(
            "assets", args.input, args.out, args.game,
            ["--kinds", args.kinds, "--max", str(args.max)])
        if failed:
            sys.exit(1)
        return
    cfg = {"sources": _sources_arg(args.source),
           "kinds": _sources_arg(args.kinds) or None,
           "max_count": args.max}
    r = assets_mod.extract_assets(args.input, cfg, args.out, game=args.game)
    if r.failures and not r.total:
        sys.exit(1)


def survey_cmd(args):
    """처음 보는 APK 프로파일 — 뭐가 어디 있나 + 설정 초안."""
    from . import survey as survey_mod
    rep = survey_mod.run_survey(args.input, out_dir=args.configs, log=print,
                                max_sources=args.max_sources, deep=not args.shallow)
    print("\n" + "=" * 72)
    print(survey_mod.format_report(rep))
    print("=" * 72)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rep.to_dict(), f, ensure_ascii=False, indent=1, default=str)
        print(f"\n[survey] JSON 저장: {args.json}")


def hierarchy_cmd(args):
    from . import hierarchy as hier_mod, unity
    unity.set_fallback_version(getattr(args, "unity_version", None))
    if getattr(args, "split", False):
        from . import split as split_mod
        extra = ["--max-nodes", str(args.max_nodes)]
        for flag, on in (("--scenes-only", args.scenes_only),
                         ("--prefabs-only", args.prefabs_only),
                         ("--no-fields", args.no_fields),
                         ("--no-typetree", args.no_typetree)):
            if on:
                extra.append(flag)
        if args.unity_version:
            extra += ["--unity-version", args.unity_version]
        failed = split_mod.run_per_source(
            "hierarchy", args.input, args.out, args.game, extra)
        if failed:
            sys.exit(1)
        return
    cfg = {"sources": _sources_arg(args.source),
           "scenes": not args.prefabs_only,
           "prefabs": not args.scenes_only,
           "fields": "none" if args.no_fields else "full",
           "max_nodes": args.max_nodes}
    mono = {"enabled": not args.no_typetree}
    if args.unity_version:
        mono["unity_version"] = args.unity_version
    hier_mod.extract_hierarchy(args.input, cfg, args.out, game=args.game,
                               mono_cfg=mono)


# ─────────────────────────── argparse ───────────────────────────

def build_parser():
    from .assets import ALL_KINDS as _ASSET_KINDS
    ap = argparse.ArgumentParser(prog="levelscope")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="전체 파이프라인 실행")
    p.add_argument("--config", required=True)
    p.add_argument("--input", required=True, help="apk/xapk/obb/zip 파일 또는 폴더")
    p.add_argument("--out", default="out")
    p.add_argument("--limit", type=int, default=0, help="앞 N개만 처리 (빠른 확인용)")
    p.set_defaults(func=run)

    p = sub.add_parser("inspect", help="샘플 레벨 디코딩 결과 확인")
    p.add_argument("--config", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--chars", type=int, default=3000)
    p.set_defaults(func=inspect)

    p = sub.add_parser("detect", help="인코딩 체인 자동 감지 (설정 없이도 가능)")
    p.add_argument("--input", required=True, help="파일/폴더/apk")
    p.add_argument("--config", default=None, help="levels_glob으로 대상 한정(선택)")
    p.add_argument("--samples", type=int, default=20)
    p.add_argument("--xor-scan", action="store_true",
                   help="감지 실패 시 반복키 XOR 키 복구 시도")
    p.add_argument("--max-keylen", type=int, default=32, help="XOR 키 길이 탐색 상한")
    p.set_defaults(func=detect)

    p = sub.add_parser("ls", help="입력 컨테이너 내부 경로 훑기")
    p.add_argument("--input", required=True)
    p.add_argument("--glob", default=None, help="패턴 쉼표 구분 (생략 시 전체)")
    p.add_argument("--limit", type=int, default=60)
    p.set_defaults(func=ls)

    p = sub.add_parser("sprites", help="게임 리소스(스프라이트) 추출 — 설정 없이도 가능")
    p.add_argument("--input", required=True, help="apk/xapk/폴더")
    p.add_argument("--source", default="auto",
                   help="컨테이너 내 Unity 파일 경로 (쉼표 구분, glob 가능). "
                        "기본 auto = Addressables 번들까지 자동 발견")
    p.add_argument("--names", default="", help="이름 목록 쉼표 구분, 're:정규식' 지원. 빈값=전체")
    p.add_argument("--types", default="Sprite", help="Sprite,Texture2D")
    p.add_argument("--max", type=int, default=1000)
    p.add_argument("--categorize", action="store_true",
                   help="이름 앞에 분류를 붙여 저장한다 (아이콘_ · 캐릭터_ · 이펙트_ …). "
                        "분류별 폴더로도 나뉘어 만 장도 훑을 수 있다. 근거는 zip 안 "
                        "_categories.json 에 남는다")
    p.add_argument("--unity-version", default=None,
                   help="번들 헤더에 Unity 버전이 없을 때 쓸 값 (예: 6000.3.11f1). 보통 자동으로 배우지만, 소스를 하나만 주면 배울 데가 없다")
    p.add_argument("--game", default="assets", help="출력 파일명 접두어")
    p.add_argument("--out", default="out")
    p.add_argument("--split", action="store_true",
                   help="소스마다 **별 프로세스**로 돌린다. 산출물이 소스별로 나뉘는 대신 메모리 피크가 '가장 무거운 소스 하나'로 내려간다 (실측 4.26GB → 소스별)")
    p.set_defaults(func=sprites_cmd)

    p = sub.add_parser("recategorize",
                       help="이미 뽑아 둔 스프라이트 zip 에 분류만 다시 입힌다 (APK 불필요)")
    p.add_argument("--zip", required=True, help="대상 <게임>_sprites.zip")
    p.add_argument("--config", default=None,
                   help="게임 설정 yaml — sprites.categories 의 게임 고유 규칙을 쓴다")
    p.add_argument("--out", default=None, help="생략하면 원본을 덮어쓴다")
    p.set_defaults(func=recategorize_cmd)

    p = sub.add_parser("sources", help="Unity 소스 이름만 한 줄에 하나씩 (--split 이 쓴다)")
    p.add_argument("--input", required=True, help="apk/xapk/폴더")
    p.add_argument("--builtin", action="store_true",
                   help="Unity 내장 리소스(unity default resources)도 포함")
    p.add_argument("--verbose", action="store_true", help="발견 로그도 함께 출력")
    p.set_defaults(func=sources_cmd)

    p = sub.add_parser("survey", help="처음 보는 APK 프로파일 + 설정 초안 (설정 불필요)")
    p.add_argument("--input", required=True, help="apk/xapk/obb/zip/폴더")
    p.add_argument("--configs", default=None,
                   help="설정 초안을 쓸 폴더 (예: configs). 생략하면 화면 보고만")
    p.add_argument("--json", default=None, help="조사 결과를 JSON으로 저장할 경로")
    p.add_argument("--shallow", action="store_true",
                   help="가장 큰 소스 하나만 훑기 (번들이 수십 개일 때 빠르게)")
    p.add_argument("--max-sources", type=int, default=0, help="소스 발견 상한 (0=무제한)")
    p.set_defaults(func=survey_cmd)

    p = sub.add_parser("assets", help="사운드·머티리얼·폰트·Spine·텍스트 추출")
    p.add_argument("--input", required=True, help="apk/xapk/폴더")
    p.add_argument("--source", default="auto",
                   help="컨테이너 내 Unity 파일 경로 (쉼표 구분, glob 가능). "
                        "기본 auto = Addressables 번들까지 자동 발견")
    p.add_argument("--kinds", default="",
                   help=f"쉼표 구분. 빈값=전체 ({','.join(_ASSET_KINDS)})")
    p.add_argument("--max", type=int, default=4000)
    p.add_argument("--unity-version", default=None,
                   help="번들 헤더에 Unity 버전이 없을 때 쓸 값 (예: 6000.3.11f1). 보통 자동으로 배우지만, 소스를 하나만 주면 배울 데가 없다")
    p.add_argument("--game", default="assets", help="출력 파일명 접두어")
    p.add_argument("--out", default="out")
    p.add_argument("--split", action="store_true",
                   help="소스마다 **별 프로세스**로 돌린다. 산출물이 소스별로 나뉘는 대신 메모리 피크가 '가장 무거운 소스 하나'로 내려간다 (실측 4.26GB → 소스별)")
    p.set_defaults(func=assets_cmd)

    p = sub.add_parser("hierarchy", help="씬·프리팹 계층을 JSON으로 복원")
    p.add_argument("--input", required=True, help="apk/xapk/폴더")
    p.add_argument("--source", default="auto",
                   help="컨테이너 내 Unity 파일 경로 (쉼표 구분, glob 가능). "
                        "기본 auto = Addressables 번들까지 자동 발견")
    p.add_argument("--scenes-only", action="store_true", help="씬만")
    p.add_argument("--prefabs-only", action="store_true", help="프리팹만")
    p.add_argument("--no-fields", action="store_true",
                   help="컴포넌트 필드 생략 (이름·타입만, 훨씬 빠르고 작다)")
    p.add_argument("--no-typetree", action="store_true",
                   help="IL2CPP typetree 복원 끄기 (IL2CPP 빌드면 필드가 대부분 빈다)")
    p.add_argument("--unity-version", default=None,
                   help="번들에서 자동 감지되지만 필요하면 직접 지정 (예: 2021.3.42f1)")
    p.add_argument("--max-nodes", type=int, default=200000)
    p.add_argument("--game", default="assets", help="출력 파일명 접두어")
    p.add_argument("--out", default="out")
    p.add_argument("--split", action="store_true",
                   help="소스마다 **별 프로세스**로 돌린다. 산출물이 소스별로 나뉘는 대신 메모리 피크가 '가장 무거운 소스 하나'로 내려간다 (실측 4.26GB → 소스별)")
    p.set_defaults(func=hierarchy_cmd)
    return ap


def force_utf8_output():
    """한국어 Windows 콘솔(cp949)에서 '—' 같은 문자로 UnicodeEncodeError가 나는 걸 막는다."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main():
    force_utf8_output()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
