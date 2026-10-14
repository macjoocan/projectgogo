import importlib.util
from pathlib import Path
import tempfile
import unittest
import os
import signal
import sys
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('rea_bridge', Path(__file__).resolve().parents[1] / 'tools/rea_bridge.py')
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class ReaBridgeTests(unittest.TestCase):
    def test_query_is_one_argument_not_shell(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'binary with spaces.dll'
            target.write_bytes(b'MZ')
            query = 'x & echo secret $(foo)'
            args = bridge.rea_args('native-search', target, query)
            self.assertEqual(args, ['search', str(target.resolve()), query, '--provider', 'ghidra', '--json'])

    def test_missing_query_and_target_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                bridge.rea_args('native-decompile', folder)
        with self.assertRaises(ValueError):
            bridge.rea_args('managed')

    def test_managed_does_not_select_native_provider(self):
        with tempfile.TemporaryDirectory() as folder:
            args = bridge.rea_args('managed', folder)
            self.assertEqual(args[0], 'inspect-managed-artifact')
            self.assertNotIn('--provider', args)

    def test_capabilities_needs_no_target(self):
        self.assertEqual(bridge.rea_args('capabilities'), ['capabilities', '--json'])

    def test_hash_reads_original(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input'
            path.write_bytes(b'abc')
            self.assertEqual(bridge.sha256_file(path), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')

    def test_har_selection_is_bounded_and_unique(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'capture.har'
            path.write_text('{}')
            self.assertEqual(bridge.rea_args('har', path, records=[2, 0])[-6:], ['har', '--record', '2', '--record', '0', '--json'])
            for records in ([1, 1], [-1]):
                with self.assertRaises(ValueError):
                    bridge.rea_args('har', path, records=records)

    def test_streamed_workflow_preserves_saved_inputs(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            left, right, output = root / 'left.json', root / 'right.json', root / 'workflow.json'
            left.write_bytes(b'\xef\xbb\xbf{"evidence_id":"left"}')
            right.write_bytes(b'{"evidence_id":"right"}')
            original = left.read_bytes()
            bridge.write_workflow(output, 'compare', left, right)
            self.assertEqual(json.loads(output.read_text()), {'left': {'evidence_id': 'left'}, 'right': {'evidence_id': 'right'}})
            self.assertEqual(left.read_bytes(), original)
            bridge.write_workflow(output, 'modules', left, offset=4, limit=8)
            self.assertEqual(json.loads(output.read_text())['view'], {'kind':'page','collection':'modules','offset':4,'limit':8})
            with self.assertRaises(ValueError):
                bridge.write_workflow(output, 'modules', left, limit=0)

    def test_native_snapshot_never_replaces_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'binary.dll'
            path.write_bytes(b'MZ')
            with self.assertRaises(ValueError):
                bridge.rea_args('native', path, snapshot=path)
            self.assertEqual(bridge.rea_args('native-doctor'), ['doctor','--provider','ghidra','--json'])

    @unittest.skipUnless(os.name == 'nt', 'Windows execution guard')
    def test_exit_zero_upstream_error_is_not_success(self):
        monitor = SimpleNamespace(tree_commit=lambda pid: 0,
                                  _kill_tree=lambda pid: os.kill(pid, signal.SIGTERM))
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, watchdog=monitor):
            result = bridge.execute([sys.executable, '-c', 'print(\'{"error":"bad input"}\')'], folder, 1.5, 10, 1)
            self.assertEqual(result['exit_code'], 0)
            self.assertEqual(result['status'], 'failed_or_stopped')
            self.assertTrue(result['upstream_error'])

    @unittest.skipUnless(os.name == 'nt', 'Windows execution guard')
    def test_projected_error_without_error_key_is_failure(self):
        monitor = SimpleNamespace(tree_commit=lambda pid: 0,
                                  _kill_tree=lambda pid: os.kill(pid, signal.SIGTERM))
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, watchdog=monitor):
            result = bridge.execute([sys.executable, '-c', 'print(\'{"code":"invalid_input","category":"input","message":"bad"}\')'], folder, 1.5, 10, 1)
            self.assertEqual(result['exit_code'], 0)
            self.assertTrue(result['upstream_error'])
            self.assertEqual(result['status'], 'failed_or_stopped')

    @unittest.skipUnless(os.name == 'nt', 'Windows execution guard')
    def test_failed_process_keeps_evidence_and_exit_code(self):
        monitor = SimpleNamespace(tree_commit=lambda pid: 0,
                                  _kill_tree=lambda pid: os.kill(pid, signal.SIGTERM))
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, watchdog=monitor):
            result = bridge.execute([sys.executable, '-c', 'print("{}"); raise SystemExit(7)'], folder, 1.5, 10, 1)
            self.assertEqual(result['exit_code'], 7)
            self.assertEqual(result['status'], 'failed_or_stopped')
            self.assertEqual(result['json_check'], 'valid_json')
            self.assertTrue(Path(result['evidence']).is_file())
            self.assertFalse(result['semantic_completeness_verified'])

    @unittest.skipUnless(os.name == 'nt', 'Windows execution guard')
    def test_timeout_keeps_partial_output(self):
        monitor = SimpleNamespace(tree_commit=lambda pid: 0,
                                  _kill_tree=lambda pid: os.kill(pid, signal.SIGTERM))
        with tempfile.TemporaryDirectory() as folder, patch.dict(sys.modules, watchdog=monitor):
            # Do not confuse a slow Windows interpreter startup with truncation.
            result = bridge.execute([sys.executable, '-u', '-c', 'import time; print("partial"); time.sleep(20)'], folder, 1.5, 2, 1)
            self.assertEqual(result['stop_reason'], 'timeout')
            self.assertEqual(result['status'], 'failed_or_stopped')
            self.assertIn('partial', Path(result['evidence']).read_text())
