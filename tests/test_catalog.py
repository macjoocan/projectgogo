"""catalog — Addressables 카탈로그 해독과 검증 실패 시 안전한 후퇴."""
import base64
import json
import os
import struct
import sys
import tempfile
import types
import unittest
from unittest import mock

from levelscope import catalog

from .helpers import write_zip


def _ascii_obj(s):
    """SerializationUtilities 형식의 AsciiString 하나."""
    b = s.encode("ascii")
    return b"\x00" + struct.pack("<i", len(b)) + b


def _build_catalog(entries, ids):
    """테스트용 catalog.json 만들기.

    entries: [(키문자열, [internalId 인덱스, ...])] — 버킷 하나가 키 하나에 대응.
    """
    key_blob, offsets = bytearray(), []
    for key, _ in entries:
        offsets.append(len(key_blob))
        key_blob += _ascii_obj(key)

    # 엔트리 테이블: 버킷이 가리키는 엔트리들을 평평하게 펼친다
    flat, bucket_entries = [], []
    for _key, id_list in entries:
        idxs = []
        for internal_id in id_list:
            idxs.append(len(flat))
            flat.append(internal_id)
        bucket_entries.append(idxs)

    bucket_blob = bytearray(struct.pack("<i", len(entries)))
    for off, idxs in zip(offsets, bucket_entries):
        bucket_blob += struct.pack("<2i", off, len(idxs))
        bucket_blob += struct.pack(f"<{len(idxs)}i", *idxs) if idxs else b""

    entry_blob = bytearray(struct.pack("<i", len(flat)))
    for i, internal_id in enumerate(flat):
        # internalId, provider, dependencyKey, depHash, dataIndex, primaryKey, resourceType
        dep = _dep_bucket_for(i, entries, bucket_entries)
        entry_blob += struct.pack("<7i", internal_id, 0, dep, 0, 0, 0, 0)

    return {
        "m_InternalIds": ids,
        "m_KeyDataString": base64.b64encode(bytes(key_blob)).decode(),
        "m_BucketDataString": base64.b64encode(bytes(bucket_blob)).decode(),
        "m_EntryDataString": base64.b64encode(bytes(entry_blob)).decode(),
        "m_resourceTypes": [{"m_ClassName": "UnityEngine.Sprite"}],
    }


def _dep_bucket_for(entry_index, entries, bucket_entries):
    """이 엔트리가 속한 버킷의 '의존 버킷' 인덱스 — 테스트에서는 마지막 버킷(번들)을 쓴다."""
    for bi, idxs in enumerate(bucket_entries):
        if entry_index in idxs:
            return len(entries) - 1 if bi != len(entries) - 1 else bi
    return 0


class DecodeGood(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        # internalId 0 = 에셋 경로, 1 = 번들
        self.ids = ["Assets/Art/Hero.png",
                    "{Addressables.RuntimePath}/Android/hero__abc123.bundle"]
        doc = _build_catalog([("Hero", [0]), ("hero__abc123.bundle", [1])], self.ids)
        self.apk = write_zip(os.path.join(self._td.name, "g.apk"),
                             {"assets/aa/catalog.json": json.dumps(doc).encode()})
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def test_decodes_and_maps_bundle_to_address(self):
        c = catalog.load_catalog(self.apk, log=self.logs.append)
        self.assertTrue(c.decoded)
        self.assertEqual(c.addresses_for("hero__abc123.bundle"), ["Hero"])

    def test_splits_bundles_and_asset_paths(self):
        c = catalog.load_catalog(self.apk, log=self.logs.append)
        self.assertEqual(len(c.bundle_ids), 1)
        self.assertEqual(c.asset_paths, ["Assets/Art/Hero.png"])

    def test_missing_bundles_are_remote(self):
        """카탈로그엔 있고 APK엔 없는 번들 = CDN 배포분."""
        c = catalog.load_catalog(self.apk, log=self.logs.append)
        self.assertEqual(c.missing_bundles([]), ["hero__abc123.bundle"])
        self.assertEqual(c.missing_bundles(["a/hero__abc123.bundle"]), [])


class DecodeRefuses(unittest.TestCase):
    """잘못 푼 매핑으로 이름을 붙이는 건 이름을 안 붙이는 것보다 나쁘다."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def _apk(self, doc):
        return write_zip(os.path.join(self._td.name, f"g{len(self.logs)}.apk"),
                         {"assets/aa/catalog.json": json.dumps(doc).encode()})

    def test_truncated_bucket_blob_falls_back(self):
        doc = _build_catalog([("Hero", [0])], ["Assets/Hero.png"])
        raw = base64.b64decode(doc["m_BucketDataString"])
        doc["m_BucketDataString"] = base64.b64encode(raw + b"\x00\x00\x00\x00").decode()
        c = catalog.load_catalog(self._apk(doc), log=self.logs.append)
        self.assertFalse(c.decoded)
        self.assertIn("해독 실패", c.note)
        self.assertEqual(c.bundle_map, {})
        self.assertEqual(c.internal_ids, ["Assets/Hero.png"])   # 목록은 그대로 쓴다

    def test_entry_blob_size_mismatch_falls_back(self):
        doc = _build_catalog([("Hero", [0])], ["Assets/Hero.png"])
        raw = base64.b64decode(doc["m_EntryDataString"])
        doc["m_EntryDataString"] = base64.b64encode(raw[:-4]).decode()
        c = catalog.load_catalog(self._apk(doc), log=self.logs.append)
        self.assertFalse(c.decoded)

    def test_out_of_range_internal_id_falls_back(self):
        doc = _build_catalog([("Hero", [7])], ["Assets/Hero.png"])   # id 7 은 범위 밖
        c = catalog.load_catalog(self._apk(doc), log=self.logs.append)
        self.assertFalse(c.decoded)
        self.assertIn("범위 초과", c.note)

    def test_broken_json(self):
        apk = write_zip(os.path.join(self._td.name, "bad.apk"),
                        {"assets/aa/catalog.json": b"{not json"})
        with self.assertRaises(catalog.CatalogUnavailable):
            catalog.load_catalog(apk, log=self.logs.append)


class BinaryCatalog(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def test_bin_extracts_strings_only(self):
        blob = b"\x00\x01" + b"Assets/Art/Hero.png" + b"\x00" + b"hero__abc.bundle" + b"\x00"
        apk = write_zip(os.path.join(self._td.name, "g.apk"), {"assets/aa/catalog.bin": blob})
        c = catalog.load_catalog(apk, log=self.logs.append)
        self.assertFalse(c.decoded)
        self.assertIn("매핑 불가", c.note)
        self.assertIn("Assets/Art/Hero.png", c.internal_ids)
        self.assertIn("hero__abc.bundle", c.internal_ids)


class BinaryCatalogDecoded(unittest.TestCase):
    """catalog.bin — 선택 의존성(addressablestools)이 있을 때의 해독과, 없을 때의 후퇴.

    실제 라이브러리를 요구하지 않도록 sys.modules 에 가짜를 끼운다. 검사하려는 건
    라이브러리의 파싱이 아니라 **우리 쪽 변환·검증·후퇴** 로직이다.
    """

    #: catalog.bin 자리에 넣을 바이트. 후퇴 경로에서 문자열이 건져지는지도 같이 본다.
    BLOB = (bytes([0, 1]) + b"Assets/Art/Hero.png" + bytes([0])
            + b"hero__abc.bundle" + bytes([0]))
    PREFIX = "{UnityEngine.AddressableAssets.Addressables.RuntimePath}/Android/"

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.logs = []
        self.apk = write_zip(os.path.join(self._td.name, "g.apk"),
                             {"assets/aa/catalog.bin": self.BLOB})

    def tearDown(self):
        self._td.cleanup()

    def _loc(self, internal_id, deps=(), class_name=""):
        return types.SimpleNamespace(
            internal_id=internal_id, dependencies=list(deps),
            type=types.SimpleNamespace(class_name=class_name) if class_name else None)

    def _fake(self, resources, version=2, error=None):
        mod = types.ModuleType("addressablestools")

        def parse_binary(_data):
            if error is not None:
                raise error
            return types.SimpleNamespace(resources=resources, version=version)

        mod.parse_binary = parse_binary
        return mock.patch.dict(sys.modules, {"addressablestools": mod})

    def _load(self):
        return catalog.load_catalog(self.apk, log=self.logs.append)

    def test_asset_is_mapped_to_the_bundle_it_depends_on(self):
        bundle = self._loc(self.PREFIX + "hero__abc.bundle")
        asset = self._loc("Assets/Art/Hero.png", deps=[bundle], class_name="UnityEngine.Sprite")
        with self._fake({"hero__abc_hash": [bundle], "Assets/Art/Hero.png": [asset]}):
            c = self._load()
        self.assertTrue(c.decoded)
        self.assertEqual(c.addresses_for("hero__abc.bundle"), ["Assets/Art/Hero.png"])
        self.assertEqual(c.resource_types, ["UnityEngine.Sprite"])

    def test_runtime_path_prefix_is_stripped_so_ids_match_json_shape(self):
        bundle = self._loc(self.PREFIX + "hero__abc.bundle")
        asset = self._loc("Assets/Art/Hero.png", deps=[bundle])
        with self._fake({"a": [bundle], "Assets/Art/Hero.png": [asset]}):
            c = self._load()
        self.assertEqual(c.bundle_ids, ["Android/hero__abc.bundle"])
        self.assertEqual(c.asset_paths, ["Assets/Art/Hero.png"])
        self.assertEqual(c.missing_bundles(["hero__abc.bundle"]), [])

    def test_bundle_self_reference_is_not_an_address(self):
        bundle = self._loc(self.PREFIX + "hero__abc.bundle")
        with self._fake({"hero__abc_hash": [bundle]}):
            c = self._load()
        self.assertEqual(c.bundle_map, {})

    def test_missing_library_falls_back_to_strings(self):
        with mock.patch.dict(sys.modules, {"addressablestools": None}):
            c = self._load()
        self.assertFalse(c.decoded)
        self.assertIn("매핑 불가", c.note)
        self.assertIn("Assets/Art/Hero.png", c.internal_ids)
        self.assertTrue(any("addressablestools" in m for m in self.logs))

    def test_parse_error_falls_back_to_strings(self):
        with self._fake({}, error=ValueError("모르는 카탈로그 버전")):
            c = self._load()
        self.assertFalse(c.decoded)
        self.assertIn("Assets/Art/Hero.png", c.internal_ids)

    def test_result_that_is_not_path_like_is_refused(self):
        """쓰레기를 경로로 착각해 이름을 붙이면 안 붙이는 것보다 나쁘다."""
        junk = self._loc(chr(1) + chr(2) + " not a path")
        with self._fake({"k": [junk]}):
            c = self._load()
        self.assertFalse(c.decoded)
        self.assertIn("매핑 불가", c.note)


class Absent(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._td.cleanup()

    def test_no_catalog_raises(self):
        apk = write_zip(os.path.join(self._td.name, "g.apk"), {"a.txt": b"x"})
        with self.assertRaises(catalog.CatalogUnavailable):
            catalog.load_catalog(apk, log=lambda *_: None)

    def test_try_load_returns_none(self):
        apk = write_zip(os.path.join(self._td.name, "g.apk"), {"a.txt": b"x"})
        self.assertIsNone(catalog.try_load(apk, log=lambda *_: None))


class ObjectReader(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(catalog._read_object(_ascii_obj("Hero"), 0), "Hero")

    def test_unicode(self):
        s = "안녕".encode("utf-16-le")
        blob = b"\x01" + struct.pack("<i", len(s)) + s
        self.assertEqual(catalog._read_object(blob, 0), "안녕")

    def test_ints(self):
        self.assertEqual(catalog._read_object(b"\x02" + struct.pack("<H", 7), 0), 7)
        self.assertEqual(catalog._read_object(b"\x03" + struct.pack("<I", 9), 0), 9)
        self.assertEqual(catalog._read_object(b"\x04" + struct.pack("<i", -3), 0), -3)

    def test_unknown_type_raises(self):
        with self.assertRaises(ValueError):
            catalog._read_object(b"\x63" + b"\x00" * 8, 0)


if __name__ == "__main__":
    unittest.main()


class _ctx:
    """with 문 한 번만 받는 최소 컨텍스트 매니저."""

    def __init__(self, v):
        self.v = v

    def __enter__(self):
        return self.v

    def __exit__(self, *_e):
        return False


def _fake_unity(objs):
    """`levelscope.unity` 의 번들 읽기 3종을 objs 로 갈아끼운다.

    `_unwrap_bundle` 은 `from . import unity` 로 **패키지 속성**을 잡으므로
    sys.modules 를 갈아도 안 듣는다. 모듈 속성을 직접 패치해야 한다.
    """
    from levelscope import unity
    return (mock.patch.object(unity, "load_bytes", lambda *_a, **_k: _ctx(object())),
            mock.patch.object(unity, "iter_objects", lambda _env, _types: objs),
            mock.patch.object(unity, "read_obj", lambda o: o))


#: FlatBuffers 루트 오프셋만 들어간 최소 머리 (0x28 = 40). 백슬래시 escape 를 쓰지
#: 않으려고 bytes() 로 만든다 — 셸 heredoc 이 escape 를 먹는 사고가 반복됐다.
_FB_HEAD = bytes([0x28, 0x00, 0x00, 0x00])


class BundledCatalog(unittest.TestCase):
    """`catalog.bundle` — 카탈로그를 Unity 번들 안 TextAsset 으로 싼 배포.

    Clash of Critters 가 그렇다. 이 경로를 안 보면 카탈로그가 있는데도
    "카탈로그 없음"이 되고, 추출한 아트에 원본 프로젝트 경로를 못 붙인다.
    """

    def unwrap(self, objs):
        p1, p2, p3 = _fake_unity(objs)
        with p1, p2, p3:
            return catalog._unwrap_bundle(b"UnityFS", "x!catalog.bundle", lambda *_a: None)

    def test_glob_includes_catalog_bundle(self):
        self.assertTrue(any(p.endswith("catalog.bundle") for p in catalog.CATALOG_GLOB))

    def test_prefers_textasset_named_catalog(self):
        """이름이 'catalog' 인 것을 먼저 쓴다 — 번들에 다른 TextAsset 이 섞여 있다."""
        objs = [types.SimpleNamespace(m_Name="FontAtlas", m_Script=b"X" * 5000),
                types.SimpleNamespace(m_Name="catalog", m_Script=b"CATALOG-BLOB")]
        self.assertEqual(self.unwrap(objs), b"CATALOG-BLOB")

    def test_falls_back_to_biggest_textasset(self):
        objs = [types.SimpleNamespace(m_Name="small", m_Script=b"ab"),
                types.SimpleNamespace(m_Name="big", m_Script=b"abcdef")]
        self.assertEqual(self.unwrap(objs), b"abcdef")

    def test_str_script_is_encoded_back_to_bytes(self):
        """UnityPy 가 TextAsset 을 str 로 줄 때도 bytes 로 돌려줘야 한다."""
        objs = [types.SimpleNamespace(m_Name="catalog", m_Script="abc")]
        self.assertEqual(self.unwrap(objs), b"abc")

    def test_none_when_no_textasset(self):
        self.assertIsNone(self.unwrap([]))


class FlatBuffersCatalog(unittest.TestCase):
    """게임 고유 FlatBuffers 카탈로그 (Clash of Critters: AddressablesMainContentCatalog).

    Unity 표준이 아니라 스튜디오가 직접 만든 것이다. 스키마가 없으니 필드 이름은
    못 얻고 문자열 벡터에서 경로만 건진다. 실측 번들 10,810 · 에셋경로 12,945.
    """

    def parse(self, doc, looks=True):
        from levelscope import flatbuf
        with mock.patch.object(flatbuf, "looks_like", lambda _b: looks), \
             mock.patch.object(flatbuf, "decode", lambda _b: doc):
            return catalog._flatbuffers_catalog(_FB_HEAD, "x", lambda *_a: None)

    def test_harvests_paths_from_string_vectors(self):
        paths = [f"Assets/Res/UI/Textures/tx_{i:03d}.png" for i in range(30)]
        cat = self.parse({"f0": "AddressablesMainContentCatalog",
                          "f5": {"of": "str", "n": len(paths), "items": paths},
                          "f6": 12345})
        self.assertIsNotNone(cat)
        self.assertEqual(len(cat.asset_paths), 30)
        self.assertIn("AddressablesMainContentCatalog", cat.note)

    def test_walks_nested_tables(self):
        """경로가 중첩 테이블 벡터 안에 있어도 건진다."""
        paths = [f"Assets/Res/a{i}.png" for i in range(25)]
        cat = self.parse({"f9": {"of": "table", "n": 1, "items": [
            {"f0": {"of": "str", "n": len(paths), "items": paths}}]}})
        self.assertEqual(len(cat.asset_paths), 25)

    def test_strips_runtime_path_placeholder(self):
        pre = "{UnityEngine.AddressableAssets.Addressables.RuntimePath}/Android/"
        ids = [f"{pre}{i}.bundle" for i in range(25)]
        cat = self.parse({"f5": {"of": "str", "n": len(ids), "items": ids}})
        self.assertEqual(len(cat.bundle_ids), 25)
        self.assertTrue(all(b.startswith("Android/") for b in cat.bundle_ids),
                        cat.bundle_ids[:2])

    def test_deduplicates(self):
        ids = [f"Assets/Res/a{i}.png" for i in range(25)] * 3
        cat = self.parse({"f5": {"of": "str", "n": len(ids), "items": ids}})
        self.assertEqual(len(cat.asset_paths), 25)

    def test_gives_up_when_too_few_paths(self):
        """경로처럼 보이는 문자열이 몇 개뿐이면 카탈로그가 아니다 — 지어내지 않는다."""
        self.assertIsNone(self.parse(
            {"f0": "x", "f1": {"of": "str", "n": 2,
                               "items": ["Assets/a.png", "Assets/b.png"]}}))

    def test_not_flatbuffers_returns_none(self):
        self.assertIsNone(self.parse({}, looks=False))

    def test_decode_failure_returns_none(self):
        from levelscope import flatbuf

        def boom(_b):
            raise ValueError("nope")

        with mock.patch.object(flatbuf, "looks_like", lambda _b: True), \
             mock.patch.object(flatbuf, "decode", boom):
            self.assertIsNone(catalog._flatbuffers_catalog(b"x", "x", lambda *_a: None))

    def test_never_claims_decoded_mapping(self):
        """슬롯 의미를 모르므로 주소↔번들 매핑은 만들지 않는다 (잘못된 이름 금지)."""
        ids = [f"Assets/Res/a{i}.png" for i in range(25)]
        cat = self.parse({"f5": {"of": "str", "n": len(ids), "items": ids}})
        self.assertFalse(cat.decoded)
        self.assertEqual(cat.bundle_map, {})
