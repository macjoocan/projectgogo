"""스키마 없는 FlatBuffers 해독기.

FlatBuffers로 직렬화된 레벨을 쓰는 게임이 있다 (Royal Kingdom: 이름이 `1`~`4500` 인
TextAsset 4,500개). 압축도 base64도 아니라서 기존 코덱 체인은 전부 실패한다.

`.fbs` 스키마가 없어도 **구조는 되살릴 수 있다.** FlatBuffers 버퍼는 각 테이블이
자기 vtable(필드 슬롯 → 테이블 내 오프셋)을 들고 다니기 때문이다. 다만 **타입은
적혀 있지 않아서** 값이 정수인지 오프셋인지 검증으로 가려내야 한다:

    문자열   길이 뒤에 널 종료자가 붙고 내용이 유효한 UTF-8
    테이블   그 위치의 soffset 이 버퍼 안의 멀쩡한 vtable 을 가리킴
    벡터     길이만큼의 바이트가 버퍼 안에 들어감

필드 이름은 스키마에만 있으므로 슬롯 번호로 `f0`·`f1` 처럼 낸다. 이름을 붙이려면
설정의 `flatbuffers.names` 로 매핑을 준다.

    from levelscope import flatbuf
    doc = flatbuf.decode(raw)          # dict
    doc = flatbuf.decode(raw, names={"": ["id", "moves", "board"], "board": [...]})
"""
import struct

#: 재귀 깊이 상한 — 순환·손상 버퍼 방어
MAX_DEPTH = 24

#: 스칼라 벡터를 int32로 볼지 판단하는 최소 "상위 바이트가 0" 비율
_I32_ZERO_RATIO = 0.6


class NotFlatBuffers(ValueError):
    """FlatBuffers 로 보이지 않는다."""


class _Reader:
    def __init__(self, buf, names=None, schema=None, votes=None):
        self.b = bytes(buf)
        self.n = len(self.b)
        self.names = names or {}
        self.schema = schema or {}      # 슬롯경로 → "scalar"|"string"|"table"|"vector"
        self.votes = votes              # 주어지면 추론 투표를 기록한다

    # ── 원시 읽기 ───────────────────────────────────────────────────

    def u32(self, p):
        return struct.unpack_from("<I", self.b, p)[0]

    def i32(self, p):
        return struct.unpack_from("<i", self.b, p)[0]

    def vtable(self, t):
        """테이블 위치 t → (슬롯 오프셋 목록, 테이블 크기). 아니면 None."""
        if not (0 <= t <= self.n - 4):
            return None
        vt = t - self.i32(t)
        if not (0 <= vt <= self.n - 4):
            return None
        vsize, tsize = struct.unpack_from("<2H", self.b, vt)
        if vsize < 4 or vsize % 2 or vt + vsize > self.n:
            return None
        if tsize < 4 or t + tsize > self.n:
            return None
        offs = struct.unpack_from(f"<{(vsize - 4) // 2}H", self.b, vt + 4)
        if any(o and o >= tsize for o in offs):
            return None
        return list(offs), tsize

    def is_table(self, t):
        return t % 4 == 0 and self.vtable(t) is not None

    def vec_len(self, t, elem=1):
        """벡터/문자열 길이. **4바이트 정렬**을 요구한다.

        길이 필드가 uint32 라서 FlatBuffers는 이 위치를 항상 4바이트로 정렬한다.
        이 검사를 빼면 작은 정수 스칼라가 우연히 벡터로 읽힌다 — Royal Kingdom에서
        높이 7이 "길이 256짜리 u8 벡터"로 둔갑해 4,500개 중 1,462개가 깨졌다.
        """
        if t % 4 or not (0 <= t <= self.n - 4):
            return None
        L = self.u32(t)
        # 길이 0(빈 벡터)은 정상이다. 이걸 거부하면 "목표가 없는 레벨"의 빈 목록이
        # 통째로 해석 불가가 되고, 다수결이 그 슬롯을 스칼라로 잘못 확정한다
        # (Royal Kingdom 슬롯3: 600개 중 547개가 빈 벡터였다).
        if L * elem > self.n - t - 4:
            return None
        return L

    def as_string(self, t):
        """FlatBuffers 문자열은 **널 종료자**가 붙는다 — 이게 가장 확실한 단서다.

        길이 0은 문자열로 보지 않는다. 빈 벡터의 길이 필드(0)가 죄다 "빈 문자열"로
        읽혀 진짜 벡터를 가려버리기 때문이다.
        """
        L = self.vec_len(t)
        if not L or t + 4 + L >= self.n:
            return None
        if self.b[t + 4 + L] != 0:
            return None
        raw = self.b[t + 4:t + 4 + L]
        if any(c < 9 or 13 < c < 32 for c in raw):
            return None
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return None

    # ── 타입 추론 ───────────────────────────────────────────────────

    def _scalar_vector(self, t, L):
        """스칼라 벡터로 볼 수 있으면 dict, 아니면 **None**.

        FlatBuffers는 원소 크기를 적어두지 않는다. 작은 정수 배열은 int32일 때
        4바이트 중 상위 3개가 0이 되므로 그 비율로 판단한다 (타일 배열은 int32다 —
        21, 0,0,0 이 반복된다).

        int32로 안 보이면 **벡터가 아니라고 본다.** 예전엔 uint8 벡터로 폴백했는데,
        그러면 아무 쓰레기나 "벡터"가 되어 진짜 스칼라를 덮어썼다. Royal Kingdom
        Lv9 에서 얼음 27칸 중 25칸이 그렇게 u8 벡터로 둔갑해 사라졌다
        (실제 화면 목표는 "얼음 27").
        """
        base = t + 4
        if base + 4 * L > self.n:
            return None
        hi = self.b[base:base + 4 * L]
        zeros = sum(1 for i, c in enumerate(hi) if i % 4 and c == 0)
        if zeros < _I32_ZERO_RATIO * (3 * L):
            return None
        return {"of": "i32", "n": L,
                "items": list(struct.unpack_from(f"<{L}i", self.b, base))}

    def vector(self, t, depth, slot_path, name_path):
        L = self.vec_len(t)
        if L is None:
            return None
        if L == 0:
            return {"of": "empty", "n": 0, "items": []}
        base = t + 4
        if base + 4 * L <= self.n and depth < MAX_DEPTH:
            ptrs = struct.unpack_from(f"<{L}I", self.b, base)
            tgts = [base + 4 * i + p for i, p in enumerate(ptrs)]
            if all(p and 0 < g < self.n for p, g in zip(ptrs, tgts)):
                if all(self.is_table(g) for g in tgts):
                    return {"of": "table", "n": L,
                            "items": [self.table(g, depth + 1, slot_path + "/*",
                                                 name_path + "[]") for g in tgts]}
                ss = [self.as_string(g) for g in tgts]
                if all(s is not None for s in ss):
                    return {"of": "str", "n": L, "items": ss}
        return self._scalar_vector(t, L)

    def field(self, tpos, off, size, depth, slot_path, name_path):
        p = tpos + off
        if size == 1:
            return self.b[p]
        if size == 2:
            return struct.unpack_from("<H", self.b, p)[0]
        if size >= 8:
            return struct.unpack_from("<q", self.b, p)[0]

        want = self.schema.get(slot_path)
        if want == "scalar":
            return self.i32(p)

        u = self.u32(p)
        tgt = p + u
        kind, val = "scalar", self.i32(p)
        if u and 0 < tgt < self.n and depth < MAX_DEPTH:
            s = self.as_string(tgt)
            if s is not None and want in (None, "string"):
                kind, val = "string", s
            elif self.is_table(tgt) and want in (None, "table"):
                kind, val = "table", self.table(tgt, depth + 1, slot_path, name_path)
            elif want in (None, "vector"):
                v = self.vector(tgt, depth + 1, slot_path, name_path)
                if v is not None and v.get("of") == "empty":
                    # 빈 벡터는 정보가 없다. 스키마가 벡터라고 확정한 경우에만 받는다 —
                    # 그러지 않으면 0으로 채워진 자리를 가리키는 스칼라가 통째로
                    # "빈 벡터"로 둔갑한다.
                    if want == "vector":
                        kind, val = "empty", v
                    else:
                        kind = "empty"
                elif v is not None:
                    kind, val = "vector", v
        if self.votes is not None:
            self.votes.setdefault(slot_path, {})
            self.votes[slot_path][kind] = self.votes[slot_path].get(kind, 0) + 1
        return val

    def table(self, t, depth=0, slot_path="", name_path=""):
        v = self.vtable(t)
        if v is None or depth > MAX_DEPTH:
            return None
        offs, tsize = v
        present = sorted((o, i) for i, o in enumerate(offs) if o)
        labels = self.names.get(name_path) or []
        out = {}
        for k, (off, idx) in enumerate(present):
            nxt = present[k + 1][0] if k + 1 < len(present) else tsize
            key = labels[idx] if idx < len(labels) and labels[idx] else f"f{idx}"
            sp = f"{slot_path}/{idx}" if slot_path else str(idx)
            np_ = f"{name_path}.{key}" if name_path else key
            out[key] = self.field(t, off, min(nxt - off, 8), depth, sp, np_)
        return out


def looks_like(buf):
    """FlatBuffers 로 보이나 — 루트 오프셋과 vtable 이 규격에 맞는지."""
    if len(buf) < 12:
        return False
    r = _Reader(buf)
    root = r.u32(0)
    return 0 < root < r.n and r.is_table(root)


def decode(buf, names=None, schema=None, _votes=None):
    """FlatBuffers bytes → dict. 아니면 NotFlatBuffers.

    schema 를 주면 슬롯별 타입을 그것으로 고정한다 (infer_schema 참고).
    """
    r = _Reader(buf, names, schema, _votes)
    if len(buf) < 12:
        raise NotFlatBuffers("너무 짧습니다")
    root = r.u32(0)
    if not (0 < root < r.n):
        raise NotFlatBuffers(f"루트 오프셋이 범위 밖: {root}")
    doc = r.table(root)
    if doc is None:
        raise NotFlatBuffers("루트 테이블의 vtable 이 규격에 맞지 않습니다")
    return doc


def infer_schema(buffers, log=None):
    """같은 스키마의 버퍼 여러 개로 **슬롯별 타입을 다수결로 확정**한다.

    한 버퍼만 보면 타입을 못 가리는 경우가 남는다 — 4바이트 정렬을 우연히 만족하는
    작은 정수(보드 높이 8 등)가 벡터로 읽힌다. 하지만 같은 스키마의 표본이 많으면
    진짜 스칼라는 대다수 버퍼에서 스칼라로 읽히므로 다수결이 정답을 준다
    (Royal Kingdom 4,500개: 정합성 위반 683 → 0).

    반환: {슬롯경로: "scalar"|"string"|"table"|"vector"}
    """
    votes = {}
    used = 0
    for b in buffers:
        try:
            decode(b, _votes=votes)
            used += 1
        except Exception:  # noqa: BLE001 - 깨진 표본은 투표에서 뺀다
            continue
    # "empty"(빈 벡터) 표는 뺀다. 목록이 비어 있다는 사실은 그 슬롯이 스칼라라는
    # 근거가 못 되는데, 그대로 세면 대부분 비어 있는 벡터 슬롯이 스칼라로 뒤집힌다
    # (Royal Kingdom 루트 f3: 벡터 447 vs 빈 4,053).
    schema = {}
    for p, c in votes.items():
        real = {k: v for k, v in c.items() if k != "empty"}
        schema[p] = max(real.items(), key=lambda kv: kv[1])[0] if real else "scalar"
    if log:
        mixed = [p for p, c in votes.items() if len(c) > 1]
        log(f"[flatbuf] 표본 {used}개로 슬롯 {len(schema)}개 타입 확정"
            + (f" · 해석이 갈린 슬롯 {len(mixed)}개는 다수결로 결정" if mixed else ""))
    return schema


# ─────────────────── 파이프라인용 기본 스키마 ───────────────────
#
# 코덱 스텝은 버퍼를 하나씩 받으므로 자기 힘으로는 표본을 모을 수 없다.
# 그래서 파이프라인이 디코딩 **전에** 전체 표본으로 스키마를 확정해 여기 걸어 둔다.
# 런이 끝나면 반드시 clear_default_schema() 로 지운다 (다음 게임에 새면 안 된다).

_DEFAULT_SCHEMA = None

# 필드 이름 지도도 같은 방식으로 걸어 둔다. 앱 안에 FlatBuffers 생성 코드가 남아
# 있으면 슬롯 번호 대신 원래 이름을 쓸 수 있다 (Royal Match: `f0` 이 아니라 `Name`).
# tools/fbnames_from_dump.py 가 dump.cs 에서 이 지도를 만든다.
_DEFAULT_NAMES = None


def set_default_schema(schema):
    global _DEFAULT_SCHEMA
    _DEFAULT_SCHEMA = schema


def default_schema():
    return _DEFAULT_SCHEMA


def set_default_names(names):
    global _DEFAULT_NAMES
    _DEFAULT_NAMES = names


def default_names():
    return _DEFAULT_NAMES


def clear_default_schema():
    global _DEFAULT_SCHEMA, _DEFAULT_NAMES
    _DEFAULT_SCHEMA = None
    _DEFAULT_NAMES = None
