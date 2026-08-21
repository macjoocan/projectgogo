"""typetree — 스크립트 참조, 백엔드 폴백/기억, 재료 탐색, 사용 불가 시 내려앉기."""
import os
import tempfile
import types
import unittest

from levelscope import typetree

from .helpers import FakeEnv, FakeFile, FakeObj, write_zip


class ScriptRef(unittest.TestCase):
    def _mb(self, cls="Image", ns="UnityEngine.UI", asm="UnityEngine.UI.dll"):
        script = types.SimpleNamespace(m_ClassName=cls, m_Namespace=ns, m_AssemblyName=asm)
        deref = types.SimpleNamespace(read=lambda: script)
        o = FakeObj("MonoBehaviour", 1, FakeFile("f"))
        o.read = lambda check_read=True: types.SimpleNamespace(
            m_Script=types.SimpleNamespace(deref=lambda: deref))
        return o

    def test_fullname_joins_namespace(self):
        self.assertEqual(typetree.script_ref(self._mb()).fullname, "UnityEngine.UI.Image")

    def test_fullname_without_namespace(self):
        ref = typetree.script_ref(self._mb(cls="GameMain", ns="", asm="Assembly-CSharp.dll"))
        self.assertEqual(ref.fullname, "GameMain")

    def test_missing_class_is_none(self):
        self.assertIsNone(typetree.script_ref(self._mb(cls="")))

    def test_broken_script_pointer_is_none(self):
        o = FakeObj("MonoBehaviour", 1, FakeFile("f"))

        def boom(check_read=True):
            raise RuntimeError("m_Script 끊김")

        o.read = boom
        self.assertIsNone(typetree.script_ref(o))


class DetectVersion(unittest.TestCase):
    def test_reads_from_nested_serialized_file(self):
        inner = FakeFile("level0", unity_version="2021.3.42f1")
        bundle = types.SimpleNamespace(files={"level0": inner}, unity_version=None)
        env = FakeEnv([], files={"cab": bundle})
        self.assertEqual(typetree.detect_unity_version(env), "2021.3.42f1")

    def test_none_when_absent(self):
        env = FakeEnv([], files={"cab": types.SimpleNamespace(files={}, unity_version=None)})
        self.assertIsNone(typetree.detect_unity_version(env))


class FindMaterials(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._td.cleanup()

    def _apk(self, entries):
        return write_zip(os.path.join(self._td.name, "g.apk"), entries)

    def test_finds_both_by_default_paths(self):
        apk = self._apk({
            "lib/arm64-v8a/libil2cpp.so": b"SO",
            "assets/bin/Data/Managed/Metadata/global-metadata.dat": b"MD",
        })
        so, md, labels = typetree.find_materials(apk)
        self.assertEqual((so, md), (b"SO", b"MD"))
        self.assertEqual(len(labels), 2)

    def test_falls_back_to_other_abi(self):
        apk = self._apk({
            "lib/armeabi-v7a/libil2cpp.so": b"SO32",
            "assets/bin/Data/Managed/Metadata/global-metadata.dat": b"MD",
        })
        self.assertEqual(typetree.find_materials(apk)[0], b"SO32")

    def test_missing_so_reports_which(self):
        apk = self._apk({"assets/bin/Data/Managed/Metadata/global-metadata.dat": b"MD"})
        with self.assertRaises(typetree.TypeTreeUnavailable) as cm:
            typetree.find_materials(apk)
        self.assertIn("libil2cpp.so", str(cm.exception))

    def test_missing_metadata_reports_which(self):
        apk = self._apk({"lib/arm64-v8a/libil2cpp.so": b"SO"})
        with self.assertRaises(typetree.TypeTreeUnavailable) as cm:
            typetree.find_materials(apk)
        self.assertIn("global-metadata.dat", str(cm.exception))

    def test_custom_paths_honored(self):
        apk = self._apk({"custom/il2cpp.bin": b"SO", "custom/meta.bin": b"MD"})
        so, md, _ = typetree.find_materials(
            apk, {"il2cpp": "custom/il2cpp.bin", "metadata": "custom/meta.bin"})
        self.assertEqual((so, md), (b"SO", b"MD"))


class _StubGen:
    """백엔드 대역.

    노드에 자기 이름을 새겨 준다 — 그러면 가짜 오브젝트가 "어느 백엔드의 노드로
    읽히는가"를 판정할 수 있고, MonoReader의 실제 경로(TypeTreeNode.from_list)를
    그대로 통과하게 된다.
    """

    def __init__(self, name, missing=()):
        self.name = name
        self.missing = set(missing)
        self.calls = 0

    def get_nodes(self, _asm, full):
        self.calls += 1
        if full in self.missing:
            raise KeyError(full)
        return [types.SimpleNamespace(m_Type="MonoBehaviour", m_Name=f"base:{self.name}",
                                      m_Level=0, m_MetaFlag=0)]


class BackendFallback(unittest.TestCase):
    """AssetRipper가 82%, 나머지를 AssetStudio가 메운다 — 그 폴백을 검증한다."""

    #: 클래스 → 그 클래스를 읽어낼 수 있는 백엔드들 (실측 분포를 축소한 모형)
    READABLE = {"Image": {"A", "B"}, "I2.Loc.Localize": {"B"}, "Mystery": set()}

    def setUp(self):
        self.a = _StubGen("A")
        self.b = _StubGen("B")
        self.reader = typetree.MonoReader({"A": self.a, "B": self.b}, log=lambda *_: None)

    def _obj(self, cls):
        script = types.SimpleNamespace(m_ClassName=cls, m_Namespace="", m_AssemblyName="x.dll")
        deref = types.SimpleNamespace(read=lambda: script)
        o = FakeObj("MonoBehaviour", 1, FakeFile("f"))
        allowed = self.READABLE[cls]

        def _read_typetree(nodes=None):
            if nodes is None:
                raise ValueError("typetree 없음")
            backend = str(nodes.m_Name).split(":")[-1]
            if backend not in allowed:
                raise ValueError("Expected to read 76 bytes, but only read 48 bytes")
            return {"ok": cls, "via": backend}

        o.read_typetree = _read_typetree
        o.read = lambda check_read=True: types.SimpleNamespace(
            m_Script=types.SimpleNamespace(deref=lambda: deref))
        return o

    def test_first_backend_used_when_it_works(self):
        cls, tree = self.reader.read(self._obj("Image"))
        self.assertEqual((cls, tree["ok"], tree["via"]), ("Image", "Image", "A"))
        self.assertEqual(self.b.calls, 0)

    def test_falls_back_to_second_backend(self):
        cls, tree = self.reader.read(self._obj("I2.Loc.Localize"))
        self.assertEqual(tree["via"], "B")

    def test_unreadable_everywhere_returns_class_but_no_tree(self):
        cls, tree = self.reader.read(self._obj("Mystery"))
        self.assertEqual(cls, "Mystery")
        self.assertIsNone(tree)
        self.assertEqual(self.reader.fail_classes["Mystery"], 1)

    def test_winning_backend_remembered(self):
        """같은 클래스 수백 개를 매번 첫 백엔드부터 재시도하면 헛일이 쌓인다."""
        for _ in range(5):
            self.reader.read(self._obj("I2.Loc.Localize"))
        self.assertEqual(self.reader.ok, 5)
        self.assertEqual(self.a.calls, 1)          # 노드 생성은 클래스당 한 번만

    def test_counts_and_summary(self):
        self.reader.read(self._obj("Image"))
        self.reader.read(self._obj("Mystery"))
        s = self.reader.summary()
        self.assertIn("1/2", s)
        self.assertIn("Mystery", s)

    def test_no_script_counted_separately(self):
        o = FakeObj("MonoBehaviour", 1, FakeFile("f"))

        def boom(check_read=True):
            raise RuntimeError("끊김")

        o.read = boom
        self.assertEqual(self.reader.read(o), (None, None))
        self.assertEqual(self.reader.no_script, 1)


class NullReader(unittest.TestCase):
    def test_falls_back_to_plain_read(self):
        r = typetree.NullMonoReader("테스트")
        o = FakeObj("MonoBehaviour", 1, FakeFile("f"), tree={"a": 1})
        o.read = lambda check_read=True: types.SimpleNamespace(
            m_Script=types.SimpleNamespace(deref=lambda: types.SimpleNamespace(
                read=lambda: types.SimpleNamespace(
                    m_ClassName="Image", m_Namespace="", m_AssemblyName="x"))))
        self.assertEqual(r.read(o), ("Image", {"a": 1}))

    def test_records_failure_when_plain_read_fails(self):
        r = typetree.NullMonoReader("테스트")
        o = FakeObj("MonoBehaviour", 1, FakeFile("f"), read_error=True)
        o.read = lambda check_read=True: types.SimpleNamespace(
            m_Script=types.SimpleNamespace(deref=lambda: types.SimpleNamespace(
                read=lambda: types.SimpleNamespace(
                    m_ClassName="Localize", m_Namespace="", m_AssemblyName="x"))))
        cls, tree = r.read(o)
        self.assertEqual(cls, "Localize")
        self.assertIsNone(tree)
        self.assertIn("비활성", r.summary())


class OpenReaderDegrades(unittest.TestCase):
    """재료가 없어도 런이 죽지 않고 NullMonoReader로 내려앉아야 한다."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.logs = []

    def tearDown(self):
        self._td.cleanup()

    def test_missing_materials(self):
        apk = write_zip(os.path.join(self._td.name, "g.apk"), {"a.txt": b"x"})
        r = typetree.open_reader(apk, {}, "2021.3.42f1", log=self.logs.append)
        self.assertIsInstance(r, typetree.NullMonoReader)
        self.assertTrue(any("사용 불가" in m for m in self.logs))

    def test_explicitly_disabled(self):
        apk = write_zip(os.path.join(self._td.name, "g.apk"), {"a.txt": b"x"})
        r = typetree.open_reader(apk, {"enabled": False}, "2021.3.42f1", log=self.logs.append)
        self.assertIsInstance(r, typetree.NullMonoReader)

    def test_missing_unity_version(self):
        apk = write_zip(os.path.join(self._td.name, "g.apk"), {
            "lib/arm64-v8a/libil2cpp.so": b"SO",
            "assets/bin/Data/Managed/Metadata/global-metadata.dat": b"MD"})
        r = typetree.open_reader(apk, {}, None, log=self.logs.append)
        self.assertIsInstance(r, typetree.NullMonoReader)
        self.assertIn("Unity 버전", r.reason)


if __name__ == "__main__":
    unittest.main()


class _RecordingAPI:
    """TypeTreeGeneratorAPI 대역 — 어느 백엔드가 **언제** 만들어졌는지 기록한다."""

    def __init__(self, readable, fail_ctor=()):
        self.readable = readable          # 클래스 → 노드를 줄 수 있는 백엔드 집합
        self.fail_ctor = set(fail_ctor)
        self.built = []                   # 생성자 호출 순서
        self.loaded = []                  # load_il2cpp 호출 순서 (실제 비용이 드는 곳)

    def TypeTreeGenerator(self, _version, backend):
        if backend in self.fail_ctor:
            raise RuntimeError(f"{backend} 초기화 실패")
        self.built.append(backend)
        missing = [c for c, bs in self.readable.items() if backend not in bs]
        gen = _StubGen(backend, missing=missing)
        gen.load_il2cpp = lambda _so, _md, _b=backend: self.loaded.append(_b)
        return gen


def _mono_obj(cls):
    """MonoBehaviour 대역 — 노드를 받기만 하면 읽어낸다.

    백엔드 선택이 오직 '노드를 줄 수 있는가'로만 결정되게 해서, 지연 로드가
    필요한 시점을 정확히 짚는다.
    """
    script = types.SimpleNamespace(m_ClassName=cls, m_Namespace="", m_AssemblyName="x.dll")
    o = FakeObj("MonoBehaviour", 1, FakeFile("f"))

    def _read_typetree(nodes=None):
        if nodes is None:
            raise ValueError("typetree 없음")
        return {"ok": cls, "via": str(nodes.m_Name).split(":")[-1]}

    o.read_typetree = _read_typetree
    o.read = lambda check_read=True: types.SimpleNamespace(
        m_Script=types.SimpleNamespace(deref=lambda: types.SimpleNamespace(
            read=lambda: script)))
    return o


class LazyBackendLoad(unittest.TestCase):
    """백엔드는 **필요할 때** 하나씩 올린다.

    셋을 미리 다 올리면 IL2CPP 를 세 번 파싱한다. PixelFlow(libil2cpp 193MB ·
    metadata 42MB · Unity 6000) 실측으로 AssetRipper 2.86GB + AssetStudio 1.38GB +
    AssetsTools 0.70GB = **4.94GB 가 아무것도 읽기 전에** 든다 — 계층 순회 자체는
    0.97GB 다. 그래서 첫 백엔드만 올리고 나머지는 폴백이 필요해질 때 올린다.
    """

    BACKENDS = ["A", "B", "C"]

    def _open(self, api, backends=None):
        import sys as _sys
        had = "TypeTreeGeneratorAPI" in _sys.modules
        old_mod = _sys.modules.get("TypeTreeGeneratorAPI")
        old_fm = typetree.find_materials
        _sys.modules["TypeTreeGeneratorAPI"] = api
        typetree.find_materials = lambda *_a, **_k: (b"so", b"md", ("so", "md"))
        try:
            return typetree.MonoReader.open(
                "in.apk", {"backends": backends or self.BACKENDS}, "2022.3.1f1",
                log=lambda *_: None)
        finally:
            typetree.find_materials = old_fm
            if had:
                _sys.modules["TypeTreeGeneratorAPI"] = old_mod
            else:
                del _sys.modules["TypeTreeGeneratorAPI"]

    def test_open_loads_only_the_first_backend(self):
        api = _RecordingAPI({"Image": {"A", "B", "C"}})
        self._open(api)
        self.assertEqual(api.built, ["A"])
        self.assertEqual(api.loaded, ["A"], "IL2CPP 를 한 번만 파싱해야 한다")

    def test_second_backend_loads_only_when_the_first_cannot_read(self):
        api = _RecordingAPI({"Image": {"A"}, "I2.Loc.Localize": {"B"}})
        reader = self._open(api)

        reader.read(_mono_obj("Image"))                  # A 로 해결 → 추가 로드 없음
        self.assertEqual(api.loaded, ["A"])

        cls, tree = reader.read(_mono_obj("I2.Loc.Localize"))
        self.assertEqual(tree["via"], "B")
        self.assertEqual(api.loaded, ["A", "B"])
        self.assertNotIn("C", api.loaded, "B 로 해결됐으면 C 는 올리지 않는다")

    def test_all_backends_load_when_nothing_can_read(self):
        api = _RecordingAPI({"Mystery": set()})
        reader = self._open(api)
        cls, tree = reader.read(_mono_obj("Mystery"))
        self.assertIsNone(tree)
        self.assertEqual(api.loaded, ["A", "B", "C"])    # 다 시도해야 실패라고 말할 수 있다

    def test_lazy_backend_that_fails_to_build_is_skipped_and_not_retried(self):
        api = _RecordingAPI({"Only C": {"C"}}, fail_ctor=["B"])
        reader = self._open(api)
        for _ in range(3):
            cls, tree = reader.read(_mono_obj("Only C"))
            self.assertEqual(tree["via"], "C")
        self.assertEqual(api.built, ["A", "C"])          # B 는 한 번만 시도하고 포기

    def test_open_raises_when_no_backend_can_be_built(self):
        api = _RecordingAPI({}, fail_ctor=["A", "B", "C"])
        with self.assertRaises(typetree.TypeTreeUnavailable) as e:
            self._open(api)
        self.assertIn("초기화 실패", str(e.exception))

    def test_open_skips_a_broken_first_backend(self):
        api = _RecordingAPI({"Image": {"B"}}, fail_ctor=["A"])
        reader = self._open(api)
        self.assertEqual(api.loaded, ["B"])
        self.assertEqual(reader.read(_mono_obj("Image"))[1]["via"], "B")

    def test_winner_is_remembered_so_the_first_backend_is_not_retried(self):
        api = _RecordingAPI({"I2.Loc.Localize": {"B"}})
        reader = self._open(api)
        reader.read(_mono_obj("I2.Loc.Localize"))
        before = dict(reader._nodes)
        reader.read(_mono_obj("I2.Loc.Localize"))
        self.assertEqual(reader._nodes, before, "캐시가 있으면 get_nodes 를 다시 부르지 않는다")
