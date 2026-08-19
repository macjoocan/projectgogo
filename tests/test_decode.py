"""코덱 스텝·체인·자동 감지 회귀 테스트.

CLAUDE.md 지침: decode 자동 감지를 고치면 여기 합성 케이스를 반드시 통과시킨다.
"""
import base64
import binascii
import bz2
import gzip
import importlib.util
import json
import lzma
import unittest
import zlib

from levelscope import decode

PAYLOAD = {"levels": [1, 2, 3], "name": "테스트", "nested": {"a": True}}
PJSON = json.dumps(PAYLOAD, ensure_ascii=False)
PBYTES = PJSON.encode("utf-8")


def has(mod):
    return importlib.util.find_spec(mod) is not None


class ApplyStep(unittest.TestCase):
    def test_strip_bom(self):
        self.assertEqual(decode.apply_step("﻿  {}  ", "strip_bom"), "{}")
        self.assertEqual(decode.apply_step(b"\xef\xbb\xbf{}", "strip_bom"), "{}")

    def test_prefix_required(self):
        self.assertEqual(decode.apply_step("gzip:abc", "prefix:gzip:"), "abc")
        with self.assertRaises(decode.CodecError):
            decode.apply_step("abc", "prefix:gzip:")

    def test_prefix_optional(self):
        self.assertEqual(decode.apply_step("gzip:abc", "prefix?:gzip:"), "abc")
        self.assertEqual(decode.apply_step("abc", "prefix?:gzip:"), "abc")

    def test_base64_variants(self):
        self.assertEqual(decode.apply_step(base64.b64encode(PBYTES).decode(), "base64"), PBYTES)
        url = base64.urlsafe_b64encode(b"\xfb\xff\xfe").decode().rstrip("=")
        self.assertEqual(decode.apply_step(url, "base64url"), b"\xfb\xff\xfe")

    def test_base64_with_whitespace(self):
        enc = base64.b64encode(PBYTES).decode()
        wrapped = "\n".join(enc[i:i + 20] for i in range(0, len(enc), 20))
        self.assertEqual(decode.apply_step(wrapped, "base64"), PBYTES)

    def test_hex(self):
        self.assertEqual(decode.apply_step(PBYTES.hex().upper(), "hex"), PBYTES)

    def test_compressions(self):
        cases = [("gunzip", gzip.compress(PBYTES)),
                 ("zlib", zlib.compress(PBYTES)),
                 ("inflate", zlib.compressobj(wbits=-15).compress(PBYTES)
                  + zlib.compressobj(wbits=-15).flush()),
                 ("bunzip2", bz2.compress(PBYTES)),
                 ("unxz", lzma.compress(PBYTES))]
        for step, blob in cases:
            with self.subTest(step=step):
                if step == "inflate":
                    co = zlib.compressobj(wbits=-15)
                    blob = co.compress(PBYTES) + co.flush()
                self.assertEqual(decode.apply_step(blob, step), PBYTES)

    def test_utf16(self):
        self.assertEqual(decode.apply_step(PJSON.encode("utf-16"), "utf16"), PJSON)

    def test_xor_roundtrip(self):
        for keyhex in ("5a", "deadbeef", "0102030405060708"):
            with self.subTest(key=keyhex):
                key = binascii.unhexlify(keyhex)
                ct = bytes(c ^ key[i % len(key)] for i, c in enumerate(PBYTES))
                self.assertEqual(decode.apply_step(ct, f"xor:{keyhex}"), PBYTES)

    def test_json(self):
        self.assertEqual(decode.apply_step(PJSON, "json"), PAYLOAD)

    def test_unknown_step_lists_available(self):
        with self.assertRaises(decode.CodecError) as cm:
            decode.apply_step(b"x", "rot13")
        self.assertIn("gunzip", str(cm.exception))

    @unittest.skipUnless(has("zstandard"), "zstandard 미설치")
    def test_zstd(self):
        import zstandard
        blob = zstandard.ZstdCompressor().compress(PBYTES)
        self.assertEqual(decode.apply_step(blob, "zstd"), PBYTES)

    @unittest.skipUnless(has("lz4"), "lz4 미설치")
    def test_lz4(self):
        import lz4.frame
        self.assertEqual(decode.apply_step(lz4.frame.compress(PBYTES), "lz4"), PBYTES)

    @unittest.skipUnless(has("brotli"), "Brotli 미설치")
    def test_brotli(self):
        import brotli
        self.assertEqual(decode.apply_step(brotli.compress(PBYTES), "brotli"), PBYTES)

    @unittest.skipUnless(has("msgpack"), "msgpack 미설치")
    def test_msgpack(self):
        import msgpack
        self.assertEqual(decode.apply_step(msgpack.packb(PAYLOAD), "msgpack"), PAYLOAD)

    @unittest.skipUnless(has("Crypto"), "pycryptodome 미설치")
    def test_aes_cbc(self):
        from Crypto.Cipher import AES
        key, iv = bytes(range(16)), bytes(range(16, 32))
        pad = 16 - len(PBYTES) % 16
        ct = AES.new(key, AES.MODE_CBC, iv).encrypt(PBYTES + bytes([pad]) * pad)
        step = f"aes_cbc:{key.hex()}:{iv.hex()}"
        self.assertEqual(decode.apply_step(ct, step), PBYTES)

    def test_missing_module_message(self):
        """미설치 코덱은 pip 안내와 함께 CodecError로 실패한다."""
        for mod, stepname in (("zstandard", "zstd"), ("msgpack", "msgpack"), ("brotli", "brotli")):
            if has(mod):
                continue
            with self.subTest(step=stepname), self.assertRaises(decode.CodecError) as cm:
                decode.apply_step(b"\x00" * 8, stepname)
            self.assertIn("pip install", str(cm.exception))


class Chains(unittest.TestCase):
    #: PixelFlow 실제 체인
    PIXELFLOW = ["strip_bom", "prefix:gzip:", "base64", "gunzip", "json"]

    def pixelflow_blob(self):
        return b"\xef\xbb\xbf" + b"gzip:" + base64.b64encode(gzip.compress(PBYTES))

    def test_explicit_chain(self):
        self.assertEqual(decode.apply_chain(self.pixelflow_blob(), self.PIXELFLOW), PAYLOAD)

    def test_capture_matches_decode_bytes_only(self):
        blob = self.pixelflow_blob()
        obj, plain = decode.apply_chain(blob, self.PIXELFLOW, capture=True)
        self.assertEqual(obj, PAYLOAD)
        self.assertEqual(plain, PBYTES)
        self.assertEqual(plain, decode.decode_bytes_only(blob, self.PIXELFLOW))

    def test_capture_without_terminal_step(self):
        """json 스텝이 없으면 마지막 값이 곧 평문이다."""
        obj, plain = decode.apply_chain(gzip.compress(PBYTES), ["gunzip"], capture=True)
        self.assertEqual(obj, PBYTES)
        self.assertEqual(plain, PBYTES)

    def test_chain_failure_names_step(self):
        with self.assertRaises(decode.CodecError) as cm:
            decode.apply_chain(b"not gzip at all", ["gunzip", "json"])
        self.assertIn("gunzip", str(cm.exception))


class DetectChain(unittest.TestCase):
    def assert_detects(self, raw, expect_steps):
        steps, obj = decode.detect_chain(raw)
        self.assertEqual(steps, expect_steps)
        self.assertEqual(obj, PAYLOAD)

    def test_plain_json(self):
        self.assert_detects(PBYTES, ["json"])

    def test_bom_json(self):
        steps, obj = decode.detect_chain(b"\xef\xbb\xbf" + PBYTES)
        self.assertEqual(obj, PAYLOAD)
        self.assertEqual(steps[-1], "json")

    def test_gzip(self):
        self.assert_detects(gzip.compress(PBYTES), ["gunzip", "json"])

    def test_zlib(self):
        self.assert_detects(zlib.compress(PBYTES), ["zlib", "json"])

    def test_bz2(self):
        self.assert_detects(bz2.compress(PBYTES), ["bunzip2", "json"])

    def test_xz(self):
        self.assert_detects(lzma.compress(PBYTES), ["unxz", "json"])

    def test_base64_gzip(self):
        self.assert_detects(base64.b64encode(gzip.compress(PBYTES)), ["base64", "gunzip", "json"])

    def test_pixelflow_full(self):
        """BOM은 utf-8-sig 디코드에서 이미 사라지므로 strip_bom 스텝은 안 붙는다.
        (설정에 적어둔 명시 체인의 strip_bom은 무해한 여분 — MANUAL 3-2 예시 참고)"""
        raw = b"\xef\xbb\xbf" + b"gzip:" + base64.b64encode(gzip.compress(PBYTES))
        steps, obj = decode.detect_chain(raw)
        self.assertEqual(obj, PAYLOAD)
        self.assertEqual(steps, ["prefix:gzip:", "base64", "gunzip", "json"])
        # 문서에 적힌 명시 체인도 같은 결과를 낸다
        self.assertEqual(decode.apply_chain(raw, Chains.PIXELFLOW), PAYLOAD)

    def test_nested_double_base64(self):
        inner = base64.b64encode(gzip.compress(PBYTES))
        self.assert_detects(base64.b64encode(inner), ["base64", "base64", "gunzip", "json"])

    def test_utf16(self):
        steps, obj = decode.detect_chain(PJSON.encode("utf-16"))
        self.assertEqual(obj, PAYLOAD)
        self.assertEqual(steps, ["utf16", "json"])

    def test_hex_beats_base64_when_ambiguous(self):
        """hex ⊂ base64 문자셋 — 결과 타당성으로 hex를 골라야 한다."""
        payload = b'{"ab":1}'                       # hex 16자 → base64 후보도 성립
        raw = payload.hex().encode()
        self.assertEqual(len(payload.hex()) % 4, 0)
        steps, obj = decode.detect_chain(raw)
        self.assertEqual(steps, ["hex", "json"])
        self.assertEqual(obj, {"ab": 1})

    def test_uppercase_hex(self):
        steps, obj = decode.detect_chain(PBYTES.hex().upper().encode())
        self.assertEqual(steps, ["hex", "json"])
        self.assertEqual(obj, PAYLOAD)

    def test_custom_prefix(self):
        raw = b"lv1:" + base64.b64encode(gzip.compress(PBYTES))
        steps, obj = decode.detect_chain(raw)
        self.assertEqual(steps, ["prefix:lv1:", "base64", "gunzip", "json"])
        self.assertEqual(obj, PAYLOAD)

    def test_prefix_not_stolen_from_json(self):
        """`{"a:b"...}` 처럼 콜론이 있는 JSON을 접두어로 오인하지 않는다."""
        raw = json.dumps({"a:b": 1}).encode()
        steps, obj = decode.detect_chain(raw)
        self.assertEqual(steps, ["json"])
        self.assertEqual(obj, {"a:b": 1})

    @unittest.skipUnless(has("brotli"), "Brotli 미설치")
    def test_brotli_without_magic(self):
        import brotli
        self.assert_detects(brotli.compress(PBYTES), ["brotli", "json"])

    @unittest.skipUnless(has("msgpack"), "msgpack 미설치")
    def test_msgpack(self):
        import msgpack
        self.assert_detects(msgpack.packb(PAYLOAD), ["msgpack"])

    def test_encrypted_bytes_raise_with_hint(self):
        blob = bytes((i * 37 + 11) % 256 for i in range(512))
        with self.assertRaises(decode.CodecError) as cm:
            decode.detect_chain(blob)
        self.assertIn("암호화", str(cm.exception))

    def test_depth_limit(self):
        raw = PBYTES
        for _ in range(12):
            raw = base64.b64encode(raw)
        with self.assertRaises(decode.CodecError) as cm:
            decode.detect_chain(raw, max_depth=4)
        self.assertIn("최대 깊이", str(cm.exception))


class AutoCodecCache(unittest.TestCase):
    def test_caches_and_reports_variants(self):
        logs = []
        auto = decode.AutoCodec(log=logs.append)
        a = gzip.compress(PBYTES)
        b = base64.b64encode(gzip.compress(PBYTES))
        self.assertEqual(auto.decode(a)[0], PAYLOAD)
        self.assertEqual(auto.chain, ["gunzip", "json"])
        self.assertEqual(auto.decode(a)[0], PAYLOAD)          # 캐시 경로
        self.assertEqual(auto.decode(b)[0], PAYLOAD)          # 재감지 경로
        self.assertEqual(list(auto.variants.values()), [1])
        self.assertTrue(any("자동 감지 체인" in m for m in logs))

    def test_decode_capture_gives_plain(self):
        auto = decode.AutoCodec(log=lambda _m: None)
        obj, steps, plain = auto.decode_capture(gzip.compress(PBYTES))
        self.assertEqual(obj, PAYLOAD)
        self.assertEqual(steps, ["gunzip", "json"])
        self.assertEqual(plain, PBYTES)

    def test_decode_capture_on_cached_chain(self):
        auto = decode.AutoCodec(log=lambda _m: None)
        auto.decode_capture(gzip.compress(PBYTES))
        _obj, _steps, plain = auto.decode_capture(gzip.compress(PBYTES))
        self.assertEqual(plain, PBYTES)


class Registry(unittest.TestCase):
    def test_list_steps_covers_documented(self):
        steps = decode.list_steps()
        for name in ("strip_bom", "base64", "base64url", "hex", "gunzip", "zlib", "inflate",
                     "bunzip2", "unxz", "zstd", "lz4", "brotli", "utf16", "msgpack", "json"):
            self.assertIn(name, steps)
        for pref in ("prefix:", "prefix?:", "xor:", "aes_cbc:", "aes_ecb:"):
            self.assertIn(pref, steps)

    def test_longer_prefix_wins(self):
        """'prefix?:' 가 'prefix:' 보다 먼저 매칭돼야 한다."""
        self.assertEqual(decode.apply_step("abc", "prefix?:zz:"), "abc")

    def test_custom_step_registration(self):
        @decode.step("_test_upper")
        def _upper(v):
            return decode._to_text(v).upper()

        try:
            self.assertEqual(decode.apply_chain("ab", ["_test_upper"]), "AB")
        finally:
            decode._EXACT.pop("_test_upper", None)


if __name__ == "__main__":
    unittest.main()
