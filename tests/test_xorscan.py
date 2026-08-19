"""반복키 XOR 복구 + 진단."""
import gzip
import io
import json
import os
import time
import unittest

from levelscope import xorscan


def xor(b, key):
    return bytes(c ^ key[i % len(key)] for i, c in enumerate(b))


#: 키 목록이 많아 열별 빈도 분석이 통하는 현실적인 레벨 JSON
BIG = json.dumps({f"tile{i}": {"x": i, "y": i * 2, "type": "normal"} for i in range(120)}
                 ).encode("utf-8")
SMALL = json.dumps({"levels": [1, 2, 3], "name": "abc"}).encode("utf-8")


class XorBytes(unittest.TestCase):
    def test_matches_naive(self):
        for key in (b"\x5a", b"\xde\xad\xbe\xef", b"secret"):
            with self.subTest(key=key):
                self.assertEqual(xorscan.xor_bytes(BIG, key), xor(BIG, key))

    def test_roundtrip_and_edges(self):
        self.assertEqual(xorscan.xor_bytes(xorscan.xor_bytes(BIG, b"ab"), b"ab"), BIG)
        self.assertEqual(xorscan.xor_bytes(b"", b"a"), b"")
        self.assertEqual(xorscan.xor_bytes(b"abc", b""), b"abc")

    def test_leading_zero_preserved(self):
        """정수 XOR 구현이 선행 0바이트를 잃지 않아야 한다."""
        data = b"\x00\x00\x01\x02"
        self.assertEqual(xorscan.xor_bytes(data, b"\x00"), data)
        self.assertEqual(len(xorscan.xor_bytes(data, b"\x01\x00")), 4)


class MinimalPeriod(unittest.TestCase):
    def test_reduces(self):
        self.assertEqual(xorscan.minimal_period(b"abab"), b"ab")
        self.assertEqual(xorscan.minimal_period(b"aaaa"), b"a")
        self.assertEqual(xorscan.minimal_period(b"abc"), b"abc")
        self.assertEqual(xorscan.minimal_period(b"abcabc"), b"abc")


class Scan(unittest.TestCase):
    def test_single_byte(self):
        hit = xorscan.scan(xor(SMALL, b"\x5a"))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, b"\x5a")
        self.assertEqual(hit.steps, ["json"])
        self.assertEqual(hit.codec, ["xor:5a", "json"])
        self.assertEqual(hit.obj["levels"], [1, 2, 3])

    def test_four_byte_key_via_crib(self):
        hit = xorscan.scan(xor(SMALL, b"\xde\xad\xbe\xef"))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, b"\xde\xad\xbe\xef")

    def test_six_byte_ascii_key(self):
        hit = xorscan.scan(xor(BIG, b"secret"))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, b"secret")
        self.assertIn("secret", str(hit))

    def test_xor_over_gzip(self):
        """압축 → XOR 순서로 감싼 경우: 키 복구 후 체인이 gunzip으로 이어져야 한다."""
        blob = xor(gzip.compress(BIG), b"\x11\x22\x33")
        hit = xorscan.scan(blob)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, b"\x11\x22\x33")
        self.assertEqual(hit.steps, ["gunzip", "json"])
        self.assertEqual(hit.codec, ["xor:112233", "gunzip", "json"])

    def test_xor_over_base64(self):
        import base64
        blob = xor(base64.b64encode(gzip.compress(BIG)), b"\x07\x0e")
        hit = xorscan.scan(blob)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.steps, ["base64", "gunzip", "json"])

    def test_rich_json_long_key(self):
        """실제 레벨 JSON 수준의 문자 다양성이면 긴 키도 ASCII 제약으로 풀린다."""
        rich = json.dumps({f"tile{i}": {"x": i, "y": i * 2, "type": "normal"}
                           for i in range(1500)}).encode()
        hit = xorscan.scan(xor(rich, b"longkey12345"))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, b"longkey12345")

    def test_gzip_mtime_zero_long_crib(self):
        """mtime=0 gzip(.NET/Java GZipStream 형태)은 헤더 10바이트가 상수 → 긴 키도 복구."""
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as g:
            g.write(BIG)
        key = b"\x9fZ\x13w\xc4\x02\xee"
        hit = xorscan.scan(xor(buf.getvalue(), key))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, key)
        self.assertEqual(hit.steps, ["gunzip", "json"])

    def test_gzip_real_mtime_brute_tail(self):
        """실제 mtime gzip은 크립이 4바이트 → 남은 1바이트를 전수로 메운다."""
        key = b"k3\x01Zq"
        hit = xorscan.scan(xor(gzip.compress(BIG), key))
        self.assertIsNotNone(hit)
        self.assertEqual(hit.key, key)

    def test_brute_tail_can_be_disabled(self):
        key = b"k3\x01Zq"                       # crib 4바이트로는 못 미치는 5바이트 키
        blob = xor(gzip.compress(BIG), key)
        self.assertIsNone(xorscan.scan(blob, brute_tail=0))
        self.assertIsNotNone(xorscan.scan(blob, brute_tail=1))

    def test_compressed_garbage_is_not_a_hit(self):
        """압축은 풀리지만 내용이 구조가 아니면 성공으로 보지 않는다."""
        self.assertIsNone(xorscan.scan(xor(gzip.compress(os.urandom(3000)), b"zz9")))

    def test_no_false_positive_on_random(self):
        self.assertIsNone(xorscan.scan(os.urandom(4096)))

    def test_time_budget_bounds_worst_case(self):
        t = time.monotonic()
        self.assertIsNone(xorscan.scan(os.urandom(32768), time_budget=2.0))
        self.assertLess(time.monotonic() - t, 15.0)

    def test_no_false_positive_on_plain_json(self):
        """XOR이 안 걸린 데이터에는 키를 만들어내지 않는다 (전부 0 키 배제)."""
        self.assertIsNone(xorscan.scan(SMALL))

    def test_empty_input(self):
        self.assertIsNone(xorscan.scan(b""))


class Diagnose(unittest.TestCase):
    def test_text_verdict(self):
        d = xorscan.diagnose(SMALL)
        self.assertGreater(d["printable"], 0.95)
        self.assertIn("텍스트", d["verdict"])

    def test_compressed_verdict(self):
        d = xorscan.diagnose(gzip.compress(BIG))
        self.assertEqual(d["magic"], "gunzip")
        self.assertIn("압축", d["verdict"])

    def test_zlib_magic_detected(self):
        import zlib
        self.assertEqual(xorscan.diagnose(zlib.compress(BIG))["magic"], "zlib")

    def test_encrypted_verdict(self):
        d = xorscan.diagnose(os.urandom(8192))
        self.assertIsNone(d["magic"])
        self.assertGreaterEqual(d["entropy"], 7.5)
        self.assertIn("암호화", d["verdict"])

    def test_entropy_range(self):
        self.assertAlmostEqual(xorscan.entropy(b"a" * 1000), 0.0, places=6)
        self.assertGreater(xorscan.entropy(os.urandom(8192)), 7.5)
        self.assertEqual(xorscan.entropy(b""), 0.0)

    def test_keylen_estimate_favours_true_length(self):
        """IoC 후보에 실제 키 길이(또는 그 배수)가 들어와야 한다."""
        blob = xor(BIG, b"key!")
        cands = [L for L, _s in xorscan.estimate_keylens(blob, max_keylen=16, top=6)]
        self.assertTrue(any(L % 4 == 0 for L in cands), cands)

    def test_keylen_needs_enough_data(self):
        self.assertEqual(xorscan.estimate_keylens(b"abc"), [])


if __name__ == "__main__":
    unittest.main()
