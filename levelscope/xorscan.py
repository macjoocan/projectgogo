"""반복키 XOR 자동 복구 + 바이트 진단.

XOR/AES는 키가 필요해 detect_chain이 손대지 않는다. 다만 **반복키 XOR**은
평문 머리를 안다면(레벨 데이터는 거의 항상 JSON `{"` 또는 압축 매직으로 시작)
키를 되찾을 수 있다. 이 모듈이 그 시도를 담당한다.

전략 3종 (싼 것부터)
  1) 1바이트 전수      0x01~0xFF 256가지
  2) known-plaintext   평문 머리를 가정하고 key = cipher[:L] ^ crib[:L]
  3) 열별 빈도 분석    키 길이 L을 가정, 각 열의 최빈 바이트가 평문 최빈 바이트
                       (JSON은 '"' 0x22, 공백, ',')라고 보고 키를 세운다 — 긴 키 대응

검증은 "복호 결과가 detect_chain으로 구조(dict/list)까지 풀리는가"로 한다.
우연히 통과하기 어려운 조건이라 오탐이 사실상 없다.

    hit = xorscan.scan(raw)
    if hit:
        print(hit.codec)      # ['xor:5a3f', 'base64', 'gunzip', 'json']
"""
import bz2 as _bz2
import collections
import dataclasses
import itertools
import lzma as _lzma
import math
import time
import zlib as _zlib

from . import decode

#: 평문 머리 후보 — JSON, 압축 매직, 그리고 base64로 감싼 그 둘.
#: 긴 크립이 곧 긴 키를 복구할 수 있는 범위다 (key = cipher[:L] ^ crib[:L], L ≤ len(crib)).
CRIBS = [
    # gzip 헤더 10바이트 — .NET GZipStream·Java·Unity는 mtime을 0으로 쓰는 일이 흔해
    # 헤더 전체가 사실상 상수다. 이 경우 10바이트 키까지 바로 복구된다.
    b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x00",
    b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff",
    b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x0b",
    b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00",
    b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff",
    b"\x1f\x8b\x08\x00",        # mtime을 실제로 쓰는 gzip은 여기까지만
    b"\x1f\x8b\x08",
    b'{"', b"{\n", b"{ ", b'[{"', b"[\n", b"[ ", b"[[",
    b"BZh9", b"\x78\x9c", b"\x78\xda", b"\x78\x01",
    b"\xfd7zXZ\x00",            # xz
    b"\x28\xb5\x2f\xfd",        # zstd
    b"\x04\x22\x4d\x18",        # lz4
    b"PK\x03\x04\x14\x00", b"PK\x03\x04",
    b"eyJ",                      # base64('{"')
    b"H4sIA",                    # base64(gzip 헤더)
    b"\xef\xbb\xbf{",           # BOM + {
]

#: 평문에서 가장 흔할 법한 바이트 (JSON 기준 우선순위)
COMMON_PLAIN = (0x22, 0x20, 0x2C, 0x00, 0x30, 0x65, 0x3A)

#: JSON 평문에 나올 수 있는 바이트 — ASCII 출력가능 + 공백류
JSON_OK = frozenset(range(0x20, 0x7F)) | {0x09, 0x0A, 0x0D}
#: 그중 특히 흔한 것 (열별 키 후보 점수용)
JSON_HOT = frozenset(b'",:{}[]-. 0123456789'
                     b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')

_HEAD = 512        # 후보 1차 검증에 쓰는 앞부분 크기
_STAT = 64 * 1024  # 통계 분석 상한
_SOLVE = 8 * 1024  # 열별 제약 풀이에 쓰는 창


@dataclasses.dataclass
class XorHit:
    key: bytes
    method: str
    steps: list          # XOR 이후의 체인 (예: ['base64', 'gunzip', 'json'])
    obj: object = None

    @property
    def key_hex(self):
        return self.key.hex()

    @property
    def codec(self):
        """설정에 그대로 넣을 수 있는 전체 체인."""
        return [f"xor:{self.key_hex}"] + list(self.steps)

    def __str__(self):
        printable = all(32 <= c < 127 for c in self.key)
        asc = f" ({self.key.decode('ascii')!r})" if printable else ""
        return f"xor:{self.key_hex}{asc} [{len(self.key)}바이트, {self.method}]"


def xor_bytes(b, key):
    """반복키 XOR. 큰 입력에서도 빠르게 (정수 한 번에 XOR)."""
    b = bytes(b)
    n = len(b)
    if n == 0 or not key:
        return b
    if len(key) == 1:
        return b.translate(bytes(x ^ key[0] for x in range(256)))
    k = (key * (n // len(key) + 1))[:n]
    return (int.from_bytes(b, "big") ^ int.from_bytes(k, "big")).to_bytes(n, "big")


def minimal_period(key):
    """'abab' → 'ab'. 빈도 분석이 만든 중복 키를 최소 주기로 줄인다."""
    n = len(key)
    for p in range(1, n):
        if n % p == 0 and key == key[:p] * (n // p):
            return key[:p]
    return key


def entropy(b):
    """바이트 엔트로피 (0~8). 압축·암호화 판별용."""
    b = bytes(b[:_STAT])
    if not b:
        return 0.0
    counts = collections.Counter(b)
    n = len(b)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def printable_ratio(b):
    b = bytes(b[:_STAT])
    if not b:
        return 0.0
    ok = sum(1 for c in b if 32 <= c < 127 or c in (9, 10, 13))
    return ok / len(b)


def estimate_keylens(b, max_keylen=32, top=4):
    """열별 일치지수(IoC)로 반복키 길이 후보를 추정. [(길이, 점수)] 내림차순."""
    b = bytes(b[:_STAT])
    scores = []
    for L in range(1, max_keylen + 1):
        if len(b) < L * 8:
            break
        vals = []
        for j in range(L):
            col = b[j::L]
            n = len(col)
            if n < 4:
                continue
            f = collections.Counter(col)
            vals.append(sum(c * (c - 1) for c in f.values()) / (n * (n - 1)))
        if vals:
            scores.append((L, sum(vals) / len(vals)))
    if not scores:
        return []
    # 배수 L(2L, 3L…)도 같이 높게 나오므로 점수 순으로만 정렬해 후보를 낸다
    return sorted(scores, key=lambda kv: -kv[1])[:top]


def _col_key_cands(col_bytes):
    """이 열을 전부 JSON 문자로 만드는 키 바이트 집합. 없으면 빈 집합."""
    us = list(dict.fromkeys(col_bytes))
    if not us:
        return set()
    cands = {us[0] ^ a for a in JSON_OK}
    for s in us[1:]:
        cands = {k for k in cands if (s ^ k) in JSON_OK}
        if not cands:
            break
    return cands


def ascii_keys(data, L, fixed=b"", cap=256):
    """평문이 ASCII JSON이라는 제약만으로 길이 L 키를 푼다.

    열마다 "이 열 전체를 JSON 문자로 만드는 키 바이트" 집합을 구하고, 흔한 문자로
    많이 매핑되는 순으로 세운다. 후보가 없는 열이 있으면 그 L은 탈락 — 키 길이
    필터도 겸한다. 빈도 분석보다 적은 데이터로 맞고 긴 키에서도 통한다.

    fixed: 앞쪽 열을 known-plaintext로 못박은 키 바이트 (예: 평문이 '{"'로 시작).
           열이 고정될수록 조합이 줄어 짧은 데이터에서도 정확해진다.
    """
    data = bytes(data[:_SOLVE])
    if len(data) < L * 4:
        return []
    ranked = []
    for j in range(L):
        col = data[j::L]
        cands = _col_key_cands(col)
        if j < len(fixed):
            cands &= {fixed[j]}
        if not cands:
            return []
        freq = collections.Counter(col)
        ranked.append(sorted(
            cands, key=lambda k: -sum(c for b, c in freq.items() if (b ^ k) in JSON_HOT)))
    per = max(1, min(6, int(cap ** (1.0 / L))))
    out = []
    for combo in itertools.product(*[r[:per] for r in ranked]):
        out.append(bytes(combo))
        if len(out) >= cap:
            break
    return out


def _candidate_keys(raw, max_keylen, brute_tail=2):
    """(key, method) 후보 생성기 — 싼 전략부터."""
    seen = set()

    def emit(key, method):
        key = minimal_period(bytes(key))
        if key and any(key) and key not in seen:
            seen.add(key)
            return (key, method)
        return None

    for k in range(1, 256):
        c = emit(bytes([k]), "1바이트 전수")
        if c:
            yield c

    head = bytes(raw[:64])
    for crib in CRIBS:
        if len(head) < len(crib):
            continue
        full = bytes(a ^ b for a, b in zip(head, crib))
        for L in range(1, len(crib) + 1):
            c = emit(full[:L], f"crib {crib!r}")
            if c:
                yield c

    # 평문 머리를 못박은 채로 나머지 열을 푼다 (짧은 데이터에서 특히 효과적)
    json_heads = [c for c in (b'{"', b"[{", b"{\n", b"[\n") if len(head) >= len(c)]
    for L in range(1, max_keylen + 1):
        pins = [bytes(a ^ b for a, b in zip(head, c))[:min(L, len(c))] for c in json_heads]
        for fixed in [b""] + pins:
            for key in ascii_keys(raw, L, fixed=fixed):
                c = emit(key, f"ASCII 제약 L={L}" + (" +crib" if fixed else ""))
                if c:
                    yield c

    # 크립으로 앞부분만 알고 키 길이는 IoC로 추정되는 경우 — 남은 1~2바이트는 전수 탐색.
    # 압축된 평문은 문자 제약을 쓸 수 없어 이 경로가 사실상 유일한 확장 수단이다.
    if brute_tail:
        ioc = {n for n, _s in estimate_keylens(raw, max_keylen, top=4)}
        for crib in CRIBS:
            known = min(len(crib), len(head))
            if not known:
                continue
            prefix = bytes(a ^ b for a, b in zip(head, crib))[:known]
            for unknown in range(1, brute_tail + 1):
                L = known + unknown
                # 1바이트 전수는 늘 돌린다(싸다). 2바이트 이상은 IoC가 그 길이를 지지할 때만.
                if L > max_keylen or (unknown >= 2 and L not in ioc):
                    continue
                for tail in itertools.product(range(256), repeat=unknown):
                    c = emit(prefix + bytes(tail), f"crib+전수 L={L} ({crib[:4].hex()}…)")
                    if c:
                        yield c

    stat = bytes(raw[:_STAT])
    for L in range(1, max_keylen + 1):
        if len(stat) < L * 8:
            break
        modes = []
        for j in range(L):
            col = stat[j::L]
            modes.append(collections.Counter(col).most_common(1)[0][0] if col else 0)
        for p in COMMON_PLAIN:
            c = emit(bytes(m ^ p for m in modes), f"빈도분석 L={L} p={p:#02x}")
            if c:
                yield c


def _magic_of(b):
    m = next((s for mg, s in decode.MAGICS if b.startswith(mg)), None)
    return m or ("zlib" if decode._is_zlib_head(b[:2]) else None)


def _prefix_decompresses(head, magic):
    """앞부분만 스트리밍 해제해 본다 — 전체 XOR을 피하려는 값싼 게이트.

    잘린 스트림이므로 "끝까지 풀렸는지"는 묻지 않는다. 틀린 키면 헤더 다음 블록에서
    바로 예외가 나므로 그것만 걸러낸다.
    """
    try:
        if magic == "gunzip":
            _zlib.decompressobj(16 + 15).decompress(head)
        elif magic == "zlib":
            _zlib.decompressobj().decompress(head)
        elif magic == "bunzip2":
            _bz2.BZ2Decompressor().decompress(head)
        elif magic == "unxz":
            _lzma.LZMADecompressor().decompress(head)
        else:
            return True          # zstd/lz4 등은 증분 검사를 생략하고 통과
    except Exception:  # noqa: BLE001
        return False
    return True


def _verify(raw, key):
    """키 적용 후 실제로 구조까지 풀리는지. (steps, obj) 또는 None."""
    head = xor_bytes(raw[:_HEAD], key)
    if not (decode._plausible(head) or head[:1] in (b"{", b"[")):
        return None
    # crib 전수 탐색은 후보 전부가 위 게이트를 통과하므로(헤더를 맞춰놨으니)
    # 여기서 앞부분만 해제해 걸러야 한다. 전체 XOR은 이걸 지난 후보에만.
    magic = _magic_of(head)
    if magic and not _prefix_decompresses(head, magic):
        return None
    dec = xor_bytes(raw, key)
    if magic and decode._try(dec, magic) is None:
        return None
    try:
        steps, obj = decode.detect_chain(dec)
    except decode.CodecError:
        return None
    return (steps, obj) if isinstance(obj, (dict, list)) else None


def scan(raw, max_keylen=32, max_tries=400000, brute_tail=2, time_budget=20.0):
    """반복키 XOR 복구 시도. 성공하면 XorHit, 실패하면 None.

    복구 가능 범위 (합성 케이스 실측)
      ASCII JSON 평문          키 길이 ≤ max_keylen (32까지 확인)
      gzip(mtime=0) 평문       키 길이 ≤ 10, brute_tail로 12까지
      gzip(실제 mtime) 평문    키 길이 ≤ 4,  brute_tail로 6까지
      zlib 평문                키 길이 ≤ 2,  brute_tail로 4까지

    한계 두 가지
      · 압축 평문 + 긴 키는 원리상 어렵다 (알려진 헤더 길이가 곧 복구 한계).
      · JSON 평문의 문자 다양성이 극히 낮으면(예: 숫자 배열만, 고유 바이트 20 미만)
        열별 후보가 모호해져 실패할 수 있다. 실제 레벨 JSON은 키·문자열이 섞여
        문제되지 않는다.
    실패하면 키를 알아낸 뒤 `xor:`/`aes_cbc:` 명시 체인으로 지정하면 된다.

    XOR이 안 걸린 데이터(그냥 감지되는 데이터)에는 아무 키도 만들어내지 않는다 —
    거의 0에 가까운 키로 JSON을 살짝 망가뜨린 채 "성공"하는 오탐을 막는다.
    """
    raw = bytes(raw)
    if not raw:
        return None
    try:
        _steps, obj = decode.detect_chain(raw)
        if isinstance(obj, (dict, list)):
            return None
    except decode.CodecError:
        pass
    tries, deadline = 0, (time.monotonic() + time_budget if time_budget else None)
    for key, method in _candidate_keys(raw, max_keylen, brute_tail=brute_tail):
        tries += 1
        if tries > max_tries:
            break
        if deadline and not tries % 2048 and time.monotonic() > deadline:
            break                      # 안전망 — 병적인 입력에서 무한정 돌지 않게
        got = _verify(raw, key)
        if got:
            steps, obj = got
            return XorHit(key=key, method=method, steps=steps, obj=obj)
    return None


def diagnose(raw):
    """감지 실패한 바이트 진단 — CLI detect 리포트용 dict."""
    raw = bytes(raw)
    ent = entropy(raw)
    pr = printable_ratio(raw)
    magic = next((s for m, s in decode.MAGICS if raw.startswith(m)), None)
    if magic is None and decode.looks_compressed(raw[:6]):
        magic = "zlib"
    if magic:
        verdict = f"압축 데이터 ({magic}) — codec에 '{magic}' 스텝 사용"
    elif pr > 0.95:
        verdict = "텍스트 — base64/hex/접두어 조합 확인"
    elif ent >= 7.5:
        verdict = "고엔트로피 + 압축 매직 없음 → 암호화(XOR/AES) 가능성 높음"
    elif ent >= 6.0:
        verdict = "이진 데이터 — 커스텀 포맷 또는 암호화"
    else:
        verdict = "저엔트로피 이진 데이터 — 커스텀 바이너리 포맷 가능성"
    return {
        "size": len(raw),
        "head_hex": raw[:16].hex(),
        "entropy": round(ent, 3),
        "printable": round(pr, 3),
        "magic": magic,
        "verdict": verdict,
        "keylen_candidates": estimate_keylens(raw),
    }
