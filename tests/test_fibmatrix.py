"""FibMatrix Meta.bytes 디코더."""
import gzip
import json
import struct
import unittest

from levelscope import decode as codec
from levelscope import fibmatrix


def _s(value):
    raw = value.encode("utf-8")
    return bytes([len(raw)]) + raw


def _sample():
    strings = ["id", "name", "Alpha"]
    pool = (struct.pack("<i", len(strings)) + b"".join(_s(v) for v in strings) +
            struct.pack("<i", 0) * 4)
    row = bytes([2, 0x05, 7, 2, 0])  # 2값, 각 1바이트, id=7, string pool[2], extra=0
    table = (bytes([1]) + struct.pack("<ii", 1, 2) + struct.pack("<ii", 0, 1) +
             bytes([0x51]) + struct.pack("<i", 0) + struct.pack("<i", len(row)) + row)
    payload = (struct.pack("<i", len(pool)) + pool + struct.pack("<i", 1) + _s("Demo") +
               bytes([2]) + struct.pack("<i", len(table)) + table + struct.pack("<i", 0))
    packed = gzip.compress(payload)
    return bytes([1]) + struct.pack("<I", len(payload)) + packed


class Decode(unittest.TestCase):
    def test_decodes_gzip_wrapper_constant_pool_and_table_row(self):
        got = fibmatrix.decode(_sample())
        self.assertEqual(got["tables"], {"Demo": [{"id": 7, "name": "Alpha"}]})
        self.assertEqual(got["raw"], {})

    def test_rejects_wrong_declared_gzip_size(self):
        blob = bytearray(_sample())
        struct.pack_into("<I", blob, 1, 1)
        with self.assertRaisesRegex(fibmatrix.FibMatrixError, "크기 불일치"):
            fibmatrix.decode(bytes(blob))

    def test_codec_step_decodes_fibmatrix(self):
        got = codec.apply_chain(_sample(), ["fibmatrix"])
        self.assertEqual(got["tables"]["Demo"][0]["name"], "Alpha")

    def test_auto_detect_recognizes_fibmatrix_wrapper(self):
        steps, got = codec.detect_chain(_sample())
        self.assertEqual(steps, ["fibmatrix"])
        self.assertEqual(got["tables"]["Demo"][0]["id"], 7)
