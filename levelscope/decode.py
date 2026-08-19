"""코덱 체인 + 자동 감지.

■ 명시 체인 (설정 codec: [스텝, ...]) — 순서대로 적용
  strip_bom            UTF-8 BOM/앞뒤 공백 제거 (str)
  prefix:<p>           접두어 확인 후 제거. 없으면 오류
  prefix?:<p>          접두어 있으면 제거, 없으면 통과
  base64 / base64url   base64 디코드 (str→bytes)
  hex                  16진 문자열 디코드
  gunzip               gzip 해제           zlib   zlib(deflate+헤더) 해제
  inflate              raw deflate 해제     bunzip2  bz2 해제
  unxz                 xz/lzma 해제         zstd   zstd 해제 (pip install zstandard)
  lz4                  lz4 frame 해제 (pip install lz4)
  brotli               brotli 해제 (pip install Brotli)
  utf16                UTF-16 디코드 (BOM 기준)
  xor:<hexkey>         반복 XOR 복호화 (예: xor:5A / xor:DEADBEEF)
  aes_cbc:<hexkey>:<hexiv>   AES-CBC 복호화+PKCS7 언패딩 (pip install pycryptodome)
  aes_ecb:<hexkey>           AES-ECB 복호화+PKCS7 언패딩
  msgpack              MessagePack 파싱 → obj (pip install msgpack)
  json                 JSON 파싱 → obj

■ 자동 감지 (설정 codec: auto)
  detect_chain(raw)이 매직바이트·문자 집합 검사로 체인을 추론해 (steps, obj) 반환.
  압축 7종, base64(+url변형), hex, 접두어(`xxx:`), UTF-16, msgpack, 중첩(깊이 8)까지.
  XOR/AES는 키가 필요하므로 여기서는 감지하지 않는다 —
  반복키 XOR은 xorscan.scan()이 known-plaintext로 복구를 시도한다.

■ 새 스텝 추가
  @step("이름") 또는 @step("접두어:", prefix=True) 데코레이터를 붙이면 끝.
  (구버전처럼 apply_step의 if-체인을 고칠 필요 없음)
"""
import base64 as _b64
import binascii
import bz2 as _bz2
import gzip as _gzip
import json as _json
import lzma as _lzma
import re
import zlib as _zlib


class CodecError(Exception):
    pass


_MOD_CACHE = {}


def _need(mod, pipname):
    """선택 의존 모듈 로드. 성공·실패를 모두 캐시한다 —
    자동 감지·XOR 전수 탐색에서 같은 임포트를 수만 번 재시도하면 그게 병목이 된다."""
    if mod in _MOD_CACHE:
        got = _MOD_CACHE[mod]
        if got is None:
            raise CodecError(f"'{mod}' 모듈 필요 → pip install {pipname}")
        return got
    try:
        _MOD_CACHE[mod] = __import__(mod, fromlist=["_"])
    except ImportError as e:
        _MOD_CACHE[mod] = None
        raise CodecError(f"'{mod}' 모듈 필요 → pip install {pipname}") from e
    return _MOD_CACHE[mod]


def _to_text(v):
    if isinstance(v, (bytes, bytearray)):
        return bytes(v).decode("utf-8-sig")
    return v


def _to_bytes(v):
    return v.encode("utf-8") if isinstance(v, str) else bytes(v)


def _unpad_pkcs7(b):
    if b and 1 <= b[-1] <= 16 and b[-b[-1]:] == bytes([b[-1]]) * b[-1]:
        return b[: -b[-1]]
    return b


# ─────────────────────────── 스텝 레지스트리 ───────────────────────────

_EXACT = {}      # "gunzip" -> fn(v)
_PREFIXED = []   # ("xor:", fn(v, arg))


def step(*names, prefix=False):
    """코덱 스텝 등록 데코레이터. prefix=True면 fn(v, 인자) 형태로 호출된다."""
    def deco(fn):
        for n in names:
            if prefix:
                _PREFIXED.append((n, fn))
                _PREFIXED.sort(key=lambda kv: -len(kv[0]))   # 긴 접두어 우선
            else:
                _EXACT[n] = fn
        return fn
    return deco


def list_steps():
    """등록된 스텝 이름 목록 (접두어형은 'xor:' 처럼 콜론까지)."""
    return sorted(_EXACT) + sorted(p for p, _ in _PREFIXED)


@step("strip_bom")
def _s_strip_bom(v):
    return _to_text(v).lstrip("﻿").strip()


@step("prefix?:", prefix=True)
def _s_prefix_opt(v, p):
    s = _to_text(v)
    return s[len(p):] if s.startswith(p) else s


@step("prefix:", prefix=True)
def _s_prefix(v, p):
    s = _to_text(v)
    if not s.startswith(p):
        raise CodecError(f"prefix '{p}' 없음 (첫 20자: {s[:20]!r})")
    return s[len(p):]


@step("base64")
def _s_base64(v):
    return _b64.b64decode(re.sub(r"\s+", "", _to_text(v)))


@step("base64url")
def _s_base64url(v):
    s = re.sub(r"\s+", "", _to_text(v))
    return _b64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


@step("hex")
def _s_hex(v):
    return binascii.unhexlify(re.sub(r"\s+", "", _to_text(v)))


@step("gunzip")
def _s_gunzip(v):
    return _gzip.decompress(_to_bytes(v))


@step("zlib")
def _s_zlib(v):
    return _zlib.decompress(_to_bytes(v))


@step("inflate")
def _s_inflate(v):
    return _zlib.decompress(_to_bytes(v), -15)


@step("bunzip2")
def _s_bunzip2(v):
    return _bz2.decompress(_to_bytes(v))


@step("unxz")
def _s_unxz(v):
    return _lzma.decompress(_to_bytes(v))


@step("zstd")
def _s_zstd(v):
    z = _need("zstandard", "zstandard")
    return z.ZstdDecompressor().decompress(_to_bytes(v), max_output_size=1 << 30)


@step("lz4")
def _s_lz4(v):
    frame = _need("lz4.frame", "lz4")
    return frame.decompress(_to_bytes(v))


@step("brotli")
def _s_brotli(v):
    br = _need("brotli", "Brotli")
    return br.decompress(_to_bytes(v))


@step("utf16")
def _s_utf16(v):
    return _to_bytes(v).decode("utf-16")


@step("xor:", prefix=True)
def _s_xor(v, keyhex):
    key = binascii.unhexlify(keyhex)
    if not key:
        raise CodecError("xor: 키가 빈 값")
    b = _to_bytes(v)
    return bytes(c ^ key[i % len(key)] for i, c in enumerate(b))


@step("aes_cbc:", prefix=True)
def _s_aes_cbc(v, arg):
    k, _, iv = arg.partition(":")
    _need("Crypto.Cipher.AES", "pycryptodome")
    from Crypto.Cipher import AES
    cipher = AES.new(binascii.unhexlify(k), AES.MODE_CBC, binascii.unhexlify(iv))
    return _unpad_pkcs7(cipher.decrypt(_to_bytes(v)))


@step("aes_ecb:", prefix=True)
def _s_aes_ecb(v, k):
    _need("Crypto.Cipher.AES", "pycryptodome")
    from Crypto.Cipher import AES
    return _unpad_pkcs7(AES.new(binascii.unhexlify(k), AES.MODE_ECB).decrypt(_to_bytes(v)))


@step("msgpack")
def _s_msgpack(v):
    mp = _need("msgpack", "msgpack")
    return mp.unpackb(_to_bytes(v), raw=False, strict_map_key=False)


@step("json")
def _s_json(v):
    return _json.loads(_to_text(v))


@step("flatbuffers")
def _s_flatbuffers(v):
    """FlatBuffers 바이너리 → dict.

    스키마(.fbs)가 없어도 vtable 을 따라가면 구조는 복원된다. 다만 타입이 안 적혀
    있어서 슬롯 하나만 보고는 스칼라인지 오프셋인지 못 가리는 경우가 남는다.
    같은 스키마의 표본이 여럿이면 `flatbuf.infer_schema` 로 확정할 수 있고,
    파이프라인은 디코딩 전에 그걸 돌려 `set_default_schema` 로 걸어 둔다.
    """
    from . import flatbuf
    if isinstance(v, str):
        v = v.encode("utf-8", "surrogateescape")
    try:
        return flatbuf.decode(v, names=flatbuf.default_names(),
                              schema=flatbuf.default_schema())
    except flatbuf.NotFlatBuffers as e:
        raise CodecError(f"FlatBuffers 아님: {e}") from e


#: 구조 파싱 스텝 — 여기까지 오면 체인 종료
TERMINAL_STEPS = ("json", "msgpack", "flatbuffers")


def apply_step(v, spec):
    fn = _EXACT.get(spec)
    if fn is not None:
        return fn(v)
    for p, fn in _PREFIXED:
        if spec.startswith(p):
            return fn(v, spec[len(p):])
    raise CodecError(f"알 수 없는 코덱 스텝: {spec} (사용 가능: {', '.join(list_steps())})")


def _as_plain(v):
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    if isinstance(v, str):
        return v.encode("utf-8")
    return _json.dumps(v, ensure_ascii=False).encode("utf-8")


def apply_chain(raw, steps, capture=False):
    """체인 적용. capture=True면 (결과, 구조 파싱 직전 평문 bytes) 를 함께 준다.

    capture는 zip 원문 저장용 — 예전처럼 decode_bytes_only로 체인을 한 번 더
    돌리지 않아도 되므로 레벨 수천 개에서 디코딩 비용이 절반이 된다.
    """
    v = raw
    plain = None
    for spec in steps:
        if capture and plain is None and spec in TERMINAL_STEPS:
            plain = _as_plain(v)
        try:
            v = apply_step(v, spec)
        except CodecError:
            raise
        except Exception as e:  # noqa: BLE001
            raise CodecError(f"스텝 '{spec}' 실패: {e!r}") from e
    if capture:
        return v, (plain if plain is not None else _as_plain(v))
    return v


def decode_bytes_only(raw, steps):
    """구조 파싱(json/msgpack) 직전까지 적용한 평문 바이트 (zip 원문 보존용)."""
    pre = [s for s in steps if s not in TERMINAL_STEPS]
    return _as_plain(apply_chain(raw, pre))


# ─────────────────────────── 자동 감지 ───────────────────────────

_B64_RE = re.compile(r"^[A-Za-z0-9+/\s]+={0,2}\s*$")
_B64URL_RE = re.compile(r"^[A-Za-z0-9_\-\s]+={0,2}\s*$")
_HEX_RE = re.compile(r"^[0-9a-fA-F\s]+$")
_PREFIX_RE = re.compile(r"^([A-Za-z0-9_\-]{1,16}):")

MAGICS = [
    (b"\x1f\x8b", "gunzip"),
    (b"BZh", "bunzip2"),
    (b"\xfd7zXZ\x00", "unxz"),
    (b"\x28\xb5\x2f\xfd", "zstd"),
    (b"\x04\x22\x4d\x18", "lz4"),
]
_ZLIB_2ND = (b"\x01", b"\x9c", b"\xda", b"\x5e")


def _is_zlib_head(head):
    return head[:1] == b"\x78" and head[1:2] in _ZLIB_2ND


def _try(v, spec):
    try:
        return apply_step(v, spec)
    except Exception:  # noqa: BLE001
        return None


def _looks_structured(obj):
    return isinstance(obj, (dict, list))


def looks_compressed(b):
    """압축/인코딩 매직으로 시작하는 바이트인지 — 진단·XOR 검증에서 공유."""
    head = bytes(b[:6])
    return any(head.startswith(m) for m, _ in MAGICS) or _is_zlib_head(head)


def detect_chain(raw, max_depth=8):
    """(steps, decoded_obj) 반환. 실패 시 CodecError."""
    steps, v = [], raw
    for _ in range(max_depth):
        # 1) bytes: 압축/인코딩 매직 검사
        if isinstance(v, (bytes, bytearray)):
            b = bytes(v)
            if b[:2] in (b"\xff\xfe", b"\xfe\xff"):
                nv = _try(b, "utf16")
                if nv is not None:
                    steps.append("utf16")
                    v = nv
                    continue
            hit = next((s for m, s in MAGICS if b.startswith(m)), None)
            if hit is None and _is_zlib_head(b):
                hit = "zlib"
            if hit:
                nv = _try(b, hit)
                if nv is not None:
                    steps.append(hit)
                    v = nv
                    continue
            # msgpack (설치돼 있을 때만, 구조가 나올 때만)
            nv = _try(b, "msgpack")
            if nv is not None and _looks_structured(nv):
                steps.append("msgpack")
                return steps, nv
            # brotli는 매직이 없어 마지막에 시도
            nv = _try(b, "brotli")
            if isinstance(nv, (bytes, bytearray)) and nv[:1] in (b"{", b"[", b"\x1f", b"g"):
                steps.append("brotli")
                v = nv
                continue
            try:
                s = b.decode("utf-8-sig")
            except UnicodeDecodeError as e:
                raise CodecError(f"바이트 해석 불가 (첫 8바이트: {b[:8].hex()}) — "
                                 f"암호화(xor:/aes_cbc:) 가능성, 명시 체인 필요") from e
            v = s
            continue
        # 2) str
        s = v.lstrip("﻿").strip()
        if s != v:
            if "strip_bom" not in steps:
                steps.append("strip_bom")
            v = s
        obj = _try(v, "json")
        if obj is not None and (_looks_structured(obj) or not steps):
            steps.append("json")
            return steps, obj
        m = _PREFIX_RE.match(v)
        if m and not v[:200].lstrip().startswith(("{", "[")):
            p = m.group(0)
            steps.append(f"prefix:{p}")
            v = v[len(p):]
            continue
        body = re.sub(r"\s+", "", v)
        if len(body) >= 8:
            # 문자셋이 겹치는 후보(hex ⊂ base64 ⊂ base64url)는 결과 타당성으로 판별
            cands = []
            if _HEX_RE.match(v) and len(body) % 2 == 0:
                cands.append("hex")
            if _B64_RE.match(v) and len(body) % 4 == 0:
                cands.append("base64")
            if _B64URL_RE.match(v):
                cands.append("base64url")
            decoded = [(st, nv) for st in cands if (nv := _try(v, st)) is not None]
            best = next(((st, nv) for st, nv in decoded if _plausible(nv)), None) \
                or (decoded[0] if decoded else None)
            if best:
                steps.append(best[0])
                v = best[1]
                continue
        raise CodecError(f"체인 감지 실패 (남은 값 첫 40자: {str(v)[:40]!r})")
    raise CodecError(f"최대 깊이({max_depth}) 초과 — 감지 중단. 현재 체인: {steps}")


def _plausible(b):
    """디코드 결과가 '다음 단계로 이어질 법한' 바이트인지 — 구조 시작, 압축 매직, 텍스트."""
    if not isinstance(b, (bytes, bytearray)) or not b:
        return False
    head = bytes(b[:6])
    if head[:1] in (b"{", b"["):
        return True
    if looks_compressed(head):
        return True
    if head[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return True
    try:
        s = bytes(b[:256]).decode("utf-8")
        printable = sum(c.isprintable() or c in "\r\n\t" for c in s)
        return printable / max(1, len(s)) > 0.95
    except UnicodeDecodeError:
        return False


class AutoCodec:
    """codec: auto 실행기 — 첫 파일에서 감지한 체인을 캐시하고, 실패 시 파일별 재감지."""

    def __init__(self, log=print):
        self.chain = None
        self.log = log
        self.variants = {}   # 추가로 발견된 체인들: tuple(steps) -> count

    def decode(self, raw):
        obj, steps, _plain = self.decode_capture(raw, capture=False)
        return obj, steps

    def decode_capture(self, raw, capture=True):
        """(obj, steps, 평문 bytes|None) — 캐시된 체인 우선, 실패하면 재감지."""
        if self.chain is not None:
            try:
                if capture:
                    obj, plain = apply_chain(raw, self.chain, capture=True)
                    return obj, self.chain, plain
                return apply_chain(raw, self.chain), self.chain, None
            except CodecError:
                pass
        steps, obj = detect_chain(raw)
        if self.chain is None:
            self.chain = steps
            self.log(f"[decode] 자동 감지 체인: {steps}")
        elif steps != self.chain:
            key = tuple(steps)
            if key not in self.variants:
                self.log(f"[decode] 추가 체인 발견: {steps}")
            self.variants[key] = self.variants.get(key, 0) + 1
        plain = decode_bytes_only(raw, steps) if capture else None
        return obj, steps, plain
