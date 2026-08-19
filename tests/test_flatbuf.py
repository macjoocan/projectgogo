"""flatbuf — 스키마 없는 FlatBuffers 해독기."""
import struct
import unittest

from levelscope import decode, flatbuf


def build(fields, string_pad=0, misalign_string=False, no_terminator=False):
    """테스트용 최소 FlatBuffers 버퍼.

    fields: [("i32", 값)] 또는 [("str", "문자열")] — 슬롯 순서대로.
    수작업으로 배치해 오프셋을 눈으로 확인할 수 있게 한다.
    """
    n = len(fields)
    vsize = 4 + 2 * n
    tsize = 4 + 4 * n
    vt = 4
    tbl = vt + vsize
    tbl += (-tbl) % 4                       # 테이블은 4바이트 정렬
    buf = bytearray(4)
    buf += struct.pack("<2H", vsize, tsize)
    for i in range(n):
        buf += struct.pack("<H", 4 + 4 * i)
    buf += b"\x00" * (tbl - len(buf))
    struct.pack_into("<I", buf, 0, tbl)     # 루트 오프셋
    buf += struct.pack("<i", tbl - vt)      # soffset → vtable
    field_pos = []
    for _ in range(n):
        field_pos.append(len(buf))
        buf += b"\x00" * 4

    for pos, (kind, val) in zip(field_pos, fields):
        if kind == "i32":
            struct.pack_into("<i", buf, pos, val)
            continue
        buf += b"\x00" * ((-len(buf)) % 4)  # 문자열도 4바이트 정렬
        if misalign_string:
            buf += b"\x00"
        s = len(buf)
        raw = val.encode("utf-8")
        buf += struct.pack("<I", len(raw)) + raw
        buf += b"\xff" if no_terminator else b"\x00"
        struct.pack_into("<I", buf, pos, s - pos)
    buf += b"\x00" * (string_pad + 8)
    return bytes(buf)


class Basic(unittest.TestCase):
    def test_scalar_and_string(self):
        d = flatbuf.decode(build([("i32", 42), ("str", "hi")]))
        self.assertEqual(d, {"f0": 42, "f1": "hi"})

    def test_looks_like(self):
        self.assertTrue(flatbuf.looks_like(build([("i32", 1)])))
        self.assertFalse(flatbuf.looks_like(b"{\"a\":1}"))
        self.assertFalse(flatbuf.looks_like(b"short"))

    def test_garbage_raises(self):
        with self.assertRaises(flatbuf.NotFlatBuffers):
            flatbuf.decode(b"not flatbuffers at all")

    def test_too_short(self):
        with self.assertRaises(flatbuf.NotFlatBuffers):
            flatbuf.decode(b"\x04\x00")

    def test_root_offset_out_of_range(self):
        b = bytearray(build([("i32", 7)]))
        struct.pack_into("<I", b, 0, 9999)
        with self.assertRaises(flatbuf.NotFlatBuffers):
            flatbuf.decode(bytes(b))


class StringRules(unittest.TestCase):
    """문자열 판정의 두 근거 — 널 종료자와 4바이트 정렬."""

    def test_missing_null_terminator_is_not_string(self):
        d = flatbuf.decode(build([("str", "hi")], no_terminator=True))
        self.assertNotEqual(d["f0"], "hi")

    def test_misaligned_target_is_not_string(self):
        d = flatbuf.decode(build([("str", "hi")], misalign_string=True))
        self.assertNotEqual(d["f0"], "hi")

    def test_alignment_guard_keeps_small_ints_scalar(self):
        """정렬 검사가 없으면 작은 정수가 벡터로 둔갑한다 (Royal Kingdom 실제 사례)."""
        for v in (7, 9, 11, 13):
            with self.subTest(v=v):
                d = flatbuf.decode(build([("i32", v)], string_pad=512))
                self.assertEqual(d["f0"], v)


class Names(unittest.TestCase):
    def test_labels_applied(self):
        b = build([("i32", 30), ("str", "0001v01_E")])
        d = flatbuf.decode(b, names={"": ["moves", "name"]})
        self.assertEqual(d, {"moves": 30, "name": "0001v01_E"})

    def test_partial_labels_fall_back_to_slot_numbers(self):
        d = flatbuf.decode(build([("i32", 1), ("i32", 2)]), names={"": ["first"]})
        self.assertEqual(sorted(d), ["f1", "first"])


class InferSchema(unittest.TestCase):
    """한 버퍼로는 못 가리는 타입을 표본 다수결로 확정한다."""

    def test_consensus_picks_scalar(self):
        # 대부분은 스칼라로 읽히고 일부만 다르게 읽히는 상황을 흉내낸다
        bufs = [build([("i32", v)], string_pad=64) for v in (5, 6, 7, 9, 11)]
        schema = flatbuf.infer_schema(bufs)
        self.assertEqual(schema.get("0"), "scalar")

    def test_consensus_picks_string(self):
        bufs = [build([("str", f"lv{i}")]) for i in range(6)]
        self.assertEqual(flatbuf.infer_schema(bufs).get("0"), "string")

    def test_schema_forces_scalar(self):
        b = build([("str", "hi")])
        self.assertEqual(flatbuf.decode(b, schema={"0": "scalar"})["f0"].__class__, int)

    def test_broken_samples_are_skipped(self):
        logs = []
        schema = flatbuf.infer_schema([build([("i32", 3)]), b"junk"], log=logs.append)
        self.assertEqual(schema.get("0"), "scalar")
        self.assertTrue(any("표본 1개" in m for m in logs))

    def test_empty_corpus(self):
        self.assertEqual(flatbuf.infer_schema([]), {})


class DefaultSchema(unittest.TestCase):
    """파이프라인이 걸어 두는 전역 스키마 — 런 사이에 새면 안 된다."""

    def tearDown(self):
        flatbuf.clear_default_schema()

    def test_set_and_clear(self):
        self.assertIsNone(flatbuf.default_schema())
        flatbuf.set_default_schema({"0": "scalar"})
        self.assertEqual(flatbuf.default_schema(), {"0": "scalar"})
        flatbuf.clear_default_schema()
        self.assertIsNone(flatbuf.default_schema())


class CodecStep(unittest.TestCase):
    def tearDown(self):
        flatbuf.clear_default_schema()

    def test_registered(self):
        self.assertIn("flatbuffers", decode.list_steps())

    def test_is_terminal(self):
        self.assertIn("flatbuffers", decode.TERMINAL_STEPS)

    def test_chain_decodes(self):
        got = decode.apply_chain(build([("i32", 30), ("str", "x")]), ["flatbuffers"])
        self.assertEqual(got, {"f0": 30, "f1": "x"})

    def test_non_flatbuffers_raises_codec_error(self):
        with self.assertRaises(decode.CodecError):
            decode.apply_chain(b"definitely not a buffer", ["flatbuffers"])

    def test_uses_default_schema(self):
        flatbuf.set_default_schema({"0": "scalar"})
        got = decode.apply_chain(build([("str", "hi")]), ["flatbuffers"])
        self.assertIsInstance(got["f0"], int)


class Vectors(unittest.TestCase):
    def test_i32_vector_detected_by_zero_pattern(self):
        """타일 배열은 int32다 — 상위 3바이트가 0인 비율로 가른다."""
        r = flatbuf._Reader(b"\x00" * 4 + struct.pack("<I", 4)
                            + struct.pack("<4i", 21, 21, 21, 21) + b"\x00" * 8)
        self.assertEqual(r._scalar_vector(4, 4),
                         {"of": "i32", "n": 4, "items": [21, 21, 21, 21]})

    def test_dense_bytes_are_not_a_vector(self):
        """int32 로 안 보이면 벡터가 아니라고 본다.

        예전엔 uint8 벡터로 폴백했는데, 그러면 아무 쓰레기나 "벡터"가 되어
        진짜 스칼라를 덮어썼다 — Royal Kingdom Lv9 에서 얼음 27칸 중 25칸이
        그렇게 사라졌다(실제 화면 목표는 "얼음 27").
        """
        payload = bytes(range(1, 33))
        r = flatbuf._Reader(b"\x00" * 4 + struct.pack("<I", 32) + payload + b"\x00" * 8)
        self.assertIsNone(r._scalar_vector(4, 32))

    def test_scalar_wins_when_vector_reading_is_garbage(self):
        """오프셋처럼 보이는 스칼라(32 = Ice2)가 벡터로 둔갑하면 안 된다."""
        buf = build([("i32", 32)], string_pad=256)
        self.assertEqual(flatbuf.decode(buf)["f0"], 32)


class DefaultNames(unittest.TestCase):
    """파이프라인이 걸어 두는 필드 이름 지도.

    앱에 FlatBuffers 생성 코드가 남아 있으면 슬롯 번호 대신 원래 이름을 쓸 수 있다.
    예전엔 설정에 `flatbuffers.names` 를 적어도 **배선이 없어서 무시됐다** —
    Royal Match 뷰어가 통째로 0 으로 나왔다.
    """

    def tearDown(self):
        flatbuf.clear_default_schema()

    def test_codec_step_applies_names(self):
        flatbuf.set_default_names({"": ["Move", "Name"]})
        got = decode.apply_chain(build([("i32", 30), ("str", "x")]), ["flatbuffers"])
        self.assertEqual(got, {"Move": 30, "Name": "x"})

    def test_clear_also_clears_names(self):
        flatbuf.set_default_names({"": ["Move"]})
        flatbuf.clear_default_schema()
        self.assertIsNone(flatbuf.default_names())

    def test_without_names_slots_stay_numbered(self):
        got = decode.apply_chain(build([("i32", 30)]), ["flatbuffers"])
        self.assertEqual(got, {"f0": 30})


if __name__ == "__main__":
    unittest.main()
