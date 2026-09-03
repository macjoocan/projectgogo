"""번들이 여러 개 이어붙은 엔트리를 펼치는지 (`concat` + `container.ConcatView`).

실제 사례는 Clash of Critters 의 `inpackage_aa_1.lpak` — UnityFS 번들 1,369개가
연달아 붙어 있고, 그냥 열면 UnityPy 가 첫 번들만 읽는다. 여기서는 같은 모양의
합성 데이터로 판정·펼치기·경계 조건을 굳힌다.
"""
import os
import struct
import tempfile
import unittest
import zipfile

from levelscope import concat, container


def fake_bundle(size, body=b"", version=b"2022.3.62f3", revision=b"0.0.0"):
    """`size` 바이트짜리 가짜 UnityFS 번들. 헤더 크기 필드가 실제 길이와 맞는다."""
    head = concat.MAGIC + struct.pack(">I", 8) + version + b"\x00" + revision + b"\x00"
    head += struct.pack(">q", size)
    pad = size - len(head) - len(body)
    assert pad >= 0, f"size {size} 가 헤더({len(head)})+본문({len(body)})보다 작다"
    return head + body + b"\x00" * pad


class HeaderSize(unittest.TestCase):
    def test_reads_size_field(self):
        self.assertEqual(concat.header_size(fake_bundle(500)[:concat.HEAD]), 500)

    def test_long_version_string_still_fits(self):
        b = fake_bundle(400, version=b"2022.3.62f3-DWR-Custom-Build")
        self.assertEqual(concat.header_size(b[:concat.HEAD]), 400)

    def test_not_a_bundle(self):
        self.assertIsNone(concat.header_size(b'{"levels": []}'))
        self.assertIsNone(concat.header_size(b""))
        self.assertIsNone(concat.header_size(None))

    def test_truncated_header_gives_none_not_crash(self):
        self.assertIsNone(concat.header_size(fake_bundle(500)[:12]))

    def test_zero_or_negative_size_rejected(self):
        head = concat.MAGIC + struct.pack(">I", 8) + b"5.x.x\x00" + b"0.0.0\x00"
        self.assertIsNone(concat.header_size(head + struct.pack(">q", 0)))
        self.assertIsNone(concat.header_size(head + struct.pack(">q", -1)))


class LooksConcat(unittest.TestCase):
    def test_single_bundle_is_not_concat(self):
        b = fake_bundle(500)
        self.assertFalse(concat.looks_concat(b[:concat.HEAD], len(b)))

    def test_bigger_file_than_first_bundle_is_candidate(self):
        b = fake_bundle(500)
        self.assertTrue(concat.looks_concat(b[:concat.HEAD], 5000))

    def test_non_bundle_never_candidate(self):
        self.assertFalse(concat.looks_concat(b"PK\x03\x04rest", 10_000_000))


class Segments(unittest.TestCase):
    def test_walks_three_bundles(self):
        data = fake_bundle(200) + fake_bundle(300) + fake_bundle(150)
        self.assertEqual(concat.segments(data), [(0, 200), (200, 300), (500, 150)])

    def test_covers_every_byte(self):
        """세그먼트 합계가 원본과 정확히 같아야 한다 — 실측에서 100.0000% 였다."""
        data = fake_bundle(200) + fake_bundle(300) + fake_bundle(150)
        self.assertEqual(sum(ln for _o, ln in concat.segments(data)), len(data))

    def test_single_bundle_gives_nothing(self):
        self.assertEqual(concat.segments(fake_bundle(500)), [])

    def test_trailing_garbage_rejects_whole_file(self):
        """절반만 인정하면 '일부만 뽑힌 것'이 정상처럼 보인다. 전부 아니면 안 펼친다."""
        self.assertEqual(concat.segments(fake_bundle(200) + fake_bundle(300) + b"junk"), [])

    def test_size_running_past_end_rejected(self):
        self.assertEqual(concat.segments(fake_bundle(200) + fake_bundle(9999)[:100]), [])

    def test_empty(self):
        self.assertEqual(concat.segments(b""), [])


class SubNames(unittest.TestCase):
    def test_roundtrip(self):
        n = concat.sub_name("assets/aa/x.lpak", 7)
        self.assertEqual(n, "assets/aa/x.lpak#0007")
        self.assertEqual(concat.parent_of(n), ("assets/aa/x.lpak", 7))

    def test_plain_name_untouched(self):
        self.assertEqual(concat.parent_of("assets/x.lpak"), ("assets/x.lpak", None))

    def test_hash_in_real_filename_not_split(self):
        self.assertEqual(concat.parent_of("assets/a#b/c.lpak"), ("assets/a#b/c.lpak", None))


class Tmp(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.tmp = self._d.name
        self.addCleanup(self._d.cleanup)

    def apk(self, entries, name="app.apk"):
        p = os.path.join(self.tmp, name)
        with zipfile.ZipFile(p, "w") as z:
            for k, v in entries.items():
                z.writestr(k, v)
        return p


class ConcatViewExpansion(Tmp):
    LPAK = "assets/aa/Android/inpackage_aa_1.lpak"

    def make(self, sizes=(200, 300, 150), extra=None):
        blob = b"".join(fake_bundle(s, body=b"S%d" % i) for i, s in enumerate(sizes))
        entries = {self.LPAK: blob, "assets/plain.json": b"{}"}
        entries.update(extra or {})
        return self.apk(entries), blob

    def only(self, path):
        c = next(container.iter_containers(path))
        self.addCleanup(c.close)
        return c

    def test_names_expand_into_segments(self):
        path, _ = self.make()
        names = self.only(path).names()
        self.assertIn(self.LPAK + "#0000", names)
        self.assertIn(self.LPAK + "#0002", names)
        self.assertNotIn(self.LPAK, names)          # 부모는 사라진다
        self.assertIn("assets/plain.json", names)   # 나머지는 그대로

    def test_read_returns_only_that_segment(self):
        path, _ = self.make()
        c = self.only(path)
        seg = c.read(self.LPAK + "#0001")
        self.assertEqual(len(seg), 300)
        self.assertTrue(seg.startswith(concat.MAGIC))
        self.assertEqual(concat.header_size(seg[:concat.HEAD]), 300)
        self.assertIn(b"S1", seg)

    def test_size_of_is_segment_size(self):
        path, _ = self.make()
        self.assertEqual(self.only(path).size_of(self.LPAK + "#0002"), 150)

    def test_head_does_not_run_into_next_segment(self):
        path, _ = self.make()
        h = self.only(path).head(self.LPAK + "#0002", 4096)
        self.assertEqual(len(h), 150)

    def test_segments_reassemble_to_original(self):
        path, blob = self.make()
        c = self.only(path)
        segs = [n for n in c.names() if n.startswith(self.LPAK + "#")]
        self.assertEqual(b"".join(c.read(n) for n in segs), blob)

    def test_glob_on_parent_expands(self):
        """설정에 부모 경로를 적어 둔 경우 — 세그먼트 전부로 펼쳐야 한다."""
        path, _ = self.make()
        hits = self.only(path).glob(["assets/aa/Android/*.lpak"])
        self.assertEqual(len(hits), 3)
        self.assertTrue(all("#" in h for h in hits))

    def test_glob_untouched_for_normal_entries(self):
        path, _ = self.make()
        self.assertEqual(self.only(path).glob(["assets/plain.json"]), ["assets/plain.json"])

    def test_plain_bundle_is_not_expanded(self):
        path = self.apk({"assets/one.bundle": fake_bundle(400)})
        self.assertEqual(self.only(path).names(), ["assets/one.bundle"])

    def test_non_unity_entries_pass_through(self):
        path = self.apk({"assets/a.json": b'{"x": 1}', "lib/x.so": b"\x7fELF" + b"\x00" * 200})
        c = self.only(path)
        self.assertEqual(c.read("assets/a.json"), b'{"x": 1}')
        self.assertEqual(sorted(c.names()), ["assets/a.json", "lib/x.so"])

    def test_logs_what_it_expanded(self):
        path, _ = self.make()
        # 세그먼트 표는 프로세스 단위로 캐시되고 로그는 **캐시 미스에서만** 나온다
        # (안 그러면 find_first 호출마다 같은 줄이 1,369번 찍힌다). 같은 합성
        # 파일을 쓰는 앞 테스트가 이미 담아 뒀을 수 있으니 비우고 본다.
        container._TABLES.clear()
        lines = []
        for c in container.iter_containers(path, log=lines.append):
            with c:
                c.names()
        joined = "\n".join(lines)
        self.assertIn("[concat]", joined)
        self.assertIn("번들 3개", joined)

    def test_parent_bytes_read_once_per_sweep(self):
        """세그먼트마다 부모를 다시 읽으면 108MB 를 1,369번 읽는다. 한 칸 캐시가 그걸 막는다."""
        path, _ = self.make(sizes=(200, 300, 150, 220, 260))
        c = self.only(path)
        inner, n_reads = c.inner, []
        real = inner.read

        def counting(name):
            n_reads.append(name)
            return real(name)

        inner.read = counting
        segs = [n for n in c.names() if n.startswith(self.LPAK + "#")]
        self.assertEqual(len(segs), 5)
        for n in segs:
            c.read(n)
        # 부모를 딱 한 번(판정할 때) 읽고, 세그먼트 5개는 캐시에서 잘라 준다.
        self.assertEqual(n_reads.count(self.LPAK), 1,
                         f"부모를 {n_reads.count(self.LPAK)}번 읽었다 — 캐시가 안 듣는다")


class ConcatViewInNestedApk(Tmp):
    def test_expands_inside_split_apk(self):
        """실제 배포 모양 — xapk 안의 UnityDataAssetPack.apk 안에 lpak 이 있다."""
        inner = os.path.join(self.tmp, "UnityDataAssetPack.apk")
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr("assets/aa/Android/inpackage_aa_1.lpak",
                       fake_bundle(200) + fake_bundle(300))
        with open(inner, "rb") as f:
            pack = f.read()
        xapk = os.path.join(self.tmp, "app.xapk")
        with zipfile.ZipFile(xapk, "w") as z:
            z.writestr("base.apk", b"not a zip")
            z.writestr("UnityDataAssetPack.apk", pack)

        found = []
        for c in container.iter_containers(xapk):
            with c:
                found.extend(n for n in c.names() if "#" in n)
        self.assertEqual(len(found), 2)


if __name__ == "__main__":
    unittest.main()


class PlaceholderVersion(unittest.TestCase):
    """`0.0.0` 을 진짜 Unity 버전으로 받지 않는지.

    Clash of Critters 의 lpak 세그먼트 1,369개는 헤더에 `5.x.x` / `0.0.0` 을 들고
    있다. 이걸 버전으로 받으면 survey 가 "Unity 0.0.0" 이라 보고하고(실제
    2022.3.62f3), 폴백으로 심으면 버전 없는 형제 번들이 잘못 열린다.
    """

    def test_placeholders_rejected(self):
        from levelscope import unity
        for v in ("0.0.0", "5.x.x", "", "   ", None):
            self.assertFalse(unity.is_real_version(v), v)

    def test_real_versions_accepted(self):
        from levelscope import unity
        for v in ("2022.3.62f3", "6000.3.15f1", "2019.4.8f1"):
            self.assertTrue(unity.is_real_version(v), v)

    def test_detect_version_skips_placeholder_file(self):
        """자리표시자를 든 파일을 지나쳐 진짜 버전을 든 파일을 찾아야 한다."""
        from levelscope import unity

        class F:
            def __init__(self, v):
                self.unity_version = v
                self.files = {}

        class Env:
            files = {"a": F("0.0.0"), "b": F("2022.3.62f3")}

        self.assertEqual(unity.detect_version(Env()), "2022.3.62f3")

    def test_detect_version_none_when_all_placeholder(self):
        from levelscope import unity

        class F:
            unity_version = "0.0.0"
            files = {}

        class Env:
            files = {"a": F()}

        self.assertIsNone(unity.detect_version(Env()))

    def test_set_fallback_ignores_placeholder(self):
        from levelscope import unity
        self.assertIsNone(unity.set_fallback_version("0.0.0"))
        self.assertIsNone(unity.set_fallback_version(""))
