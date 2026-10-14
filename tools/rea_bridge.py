"""Optional local REA adapter. Plans by default; --execute runs static analysis.

No MCP/agent setup, target execution or automatic downloads. REA JSON is kept
verbatim on disk; process success is not evidence of complete reconstruction.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CLI = ROOT / 'out/rea_runtime/node_modules/rea-agents/scripts/rea.mjs'
OPERATIONS = {
    'javascript': 'analyze-javascript-application',
    'managed': 'inspect-managed-artifact',
    'managed-members': 'inspect-managed-members',
    'native': 'analyze',
    'native-search': 'search',
    'native-decompile': 'decompile',
    'native-function': 'function',
    'native-xrefs': 'xrefs',
    'native-trace': 'trace',
    'native-doctor': 'doctor',
    'har': 'inspect-web-network-capture',
    'summary': 'inspect-analysis-view',
    'modules': 'inspect-analysis-view',
    'compare': 'compare-application-versions',
    'managed-compare': 'compare-managed-members',
    'capabilities': 'capabilities',
}


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def rea_args(mode, target=None, query=None, provider='ghidra', other=None,
             records=(), snapshot=None):
    args = [OPERATIONS[mode]]
    if mode not in ('capabilities', 'native-doctor'):
        if target is None or not Path(target).exists():
            raise ValueError('An existing local --input is required')
        args.append(str(Path(target).resolve()))
    if mode in ('native-search', 'native-decompile', 'native-function', 'native-xrefs', 'native-trace'):
        if not query:
            raise ValueError('--query is required for search/decompile')
        args.append(query)
    elif query is not None:
        raise ValueError('--query is only supported for native function queries')
    if mode in ('compare', 'managed-compare'):
        if other is None or not Path(other).is_file():
            raise ValueError('An existing --other file is required')
        args.append(str(Path(other).resolve()))
    elif other is not None:
        raise ValueError('--other requires compare or managed-compare')
    if mode == 'har':
        if len(set(records)) != len(records):
            raise ValueError('Duplicate record ordinals are not allowed')
        args.append('har')
        for ordinal in records:
            if ordinal < 0:
                raise ValueError('Record ordinals must be nonnegative')
            args.extend(['--record', str(ordinal)])
    elif records:
        raise ValueError('--record requires har')
    if mode.startswith('native'):
        args.extend(['--provider', provider])
    if snapshot:
        if mode != 'native':
            raise ValueError('--snapshot currently supports native overview only')
        if Path(snapshot).resolve() == Path(target).resolve():
            raise ValueError('Snapshot must not overwrite the input binary')
        args.extend(['--snapshot', str(Path(snapshot).resolve())])
    args.append('--json')
    return args


def write_workflow(path, mode, source, other=None, offset=0, limit=32):
    """Stream saved Evidence into REA's inline contract, without huge Python JSON.

    Original Evidence is unchanged. REA validates schemas and provenance; this
    helper never calls analysis on the old target or claims a cache is current.
    """
    sources = [Path(source)] + ([Path(other)] if mode == 'compare' else [])
    if any(not p.is_file() for p in sources):
        raise ValueError('Saved Evidence inputs must be files')
    if sum(p.stat().st_size for p in sources) > 128 * 1024**2:
        raise ValueError('Inline Evidence budget is 128 MiB; use retained MCP views for larger results')
    if offset < 0 or limit < 1 or limit > 1000:
        raise ValueError('Page offset must be >=0 and limit within 1..1000')
    view = {'kind': 'summary'} if mode == 'summary' else {
        'kind': 'page', 'collection': 'modules', 'offset': offset, 'limit': limit}
    with Path(path).open('wb') as out:
        if mode == 'compare':
            out.write(b'{"left":')
        else:
            out.write(b'{"source":{"kind":"inline","evidence":')
        for index, source in enumerate(sources):
            if index:
                out.write(b',"right":')
            with source.open('rb') as stream:
                # Strip only the optional UTF-8 BOM, not source payload content.
                head = stream.read(3)
                if head != b'\xef\xbb\xbf':
                    out.write(head)
                shutil.copyfileobj(stream, out, 1024 * 1024)
        if mode == 'compare':
            out.write(b'}')
        else:
            out.write(b'},"view":')
            out.write(json.dumps(view).encode('utf-8'))
            out.write(b'}')


def execute(command, out, cap_gb, timeout, max_output_mb, environment=None):
    if os.name != 'nt':
        raise ValueError('Guarded execution currently requires Windows')
    # Existing monitor counts private commit of the complete process tree.
    import watchdog
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix='rea-', dir=out))
    stdout_path, stderr_path = run_dir / 'evidence.json', run_dir / 'stderr.log'
    env = dict(os.environ)
    env.update(environment or {})
    env['NODE_OPTIONS'] = '--max-old-space-size=768'
    started, peak, reason = time.monotonic(), 0.0, None
    with stdout_path.open('wb') as stdout, stderr_path.open('wb') as stderr:
        proc = subprocess.Popen(command, stdout=stdout, stderr=stderr,
                                stdin=subprocess.DEVNULL, cwd=run_dir, env=env,
                                shell=False)
        try:
            while proc.poll() is None:
                peak = max(peak, watchdog.tree_commit(proc.pid))
                if peak > cap_gb:
                    reason = 'process_tree_commit_limit'
                elif time.monotonic() - started > timeout:
                    reason = 'timeout'
                elif stdout_path.stat().st_size + stderr_path.stat().st_size > max_output_mb * 1024**2:
                    reason = 'output_limit'
                if reason:
                    watchdog._kill_tree(proc.pid)
                    break
                time.sleep(.1)
            proc.wait(timeout=10)
        finally:
            if proc.poll() is None:
                watchdog._kill_tree(proc.pid)
                proc.wait(timeout=10)
    output_bytes = stdout_path.stat().st_size
    if reason is None and output_bytes + stderr_path.stat().st_size > max_output_mb * 1024**2:
        reason = 'output_limit'
    # Never load a potentially hundreds-of-MB REA Evidence document wholesale.
    json_check, upstream_error = 'not_checked_large_output', False
    if output_bytes <= 4 * 1024**2:
        try:
            value = json.loads(stdout_path.read_text(encoding='utf-8-sig'))
            json_check = 'valid_json'
            upstream_error = isinstance(value, dict) and bool(
                value.get('error') or value.get('error_code') or
                (value.get('code') and value.get('category') and value.get('message')))
        except (ValueError, UnicodeError):
            json_check = 'invalid_or_empty_json'
    result = {
        'command': command, 'exit_code': proc.returncode, 'stop_reason': reason,
        'status': 'process_completed' if proc.returncode == 0 and reason is None and not upstream_error and json_check != 'invalid_or_empty_json' else 'failed_or_stopped',
        'upstream_error': upstream_error,
        'elapsed_seconds': time.monotonic() - started, 'peak_tree_commit_gb': peak,
        'cap_gb': cap_gb, 'evidence_bytes': output_bytes,
        'evidence_sha256': sha256_file(stdout_path), 'json_check': json_check,
        'semantic_completeness_verified': False,
        'evidence': str(stdout_path), 'stderr': str(stderr_path),
    }
    (run_dir / 'receipt.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=OPERATIONS)
    ap.add_argument('--input', type=Path)
    ap.add_argument('--query')
    ap.add_argument('--other', type=Path, help='Right-hand saved Evidence or managed assembly')
    ap.add_argument('--record', type=int, action='append', default=[])
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--limit', type=int, default=32)
    ap.add_argument('--snapshot', type=Path)
    ap.add_argument('--ghidra-dir', type=Path, help='Existing Ghidra installation; no automatic install')
    ap.add_argument('--settings', type=Path, default=ROOT / 'out/rea_runtime/bridge-settings.json')
    ap.add_argument('--provider', choices=('ghidra', 'hopper', 'ida'), default='ghidra')
    ap.add_argument('--cli', type=Path, default=DEFAULT_CLI)
    ap.add_argument('--out', type=Path, default=ROOT / 'out/rea')
    ap.add_argument('--cap', type=float, default=1.5, help='Process-tree private commit GB')
    ap.add_argument('--timeout', type=float, default=240)
    ap.add_argument('--max-output-mb', type=float, default=256)
    ap.add_argument('--execute', action='store_true')
    a = ap.parse_args()
    try:
        if a.settings.is_file():
            settings = json.loads(a.settings.read_text(encoding='utf-8-sig'))
            if not isinstance(settings, dict) or set(settings) - {'ghidra_dir'}:
                raise ValueError('Settings support only ghidra_dir')
            if not a.ghidra_dir and settings.get('ghidra_dir'):
                a.ghidra_dir = Path(settings['ghidra_dir'])
        if not all(math.isfinite(v) and v > 0 for v in (a.cap, a.timeout, a.max_output_mb)):
            raise ValueError('Memory/time/output limits must be finite and positive')
        if a.ghidra_dir and not (a.ghidra_dir / 'support/analyzeHeadless.bat').is_file():
            raise ValueError('--ghidra-dir must contain support/analyzeHeadless.bat')
        if a.input and a.input.is_dir() and a.out.resolve().is_relative_to(a.input.resolve()):
            raise ValueError('--out must not be inside the target directory')
        args = rea_args(a.mode, a.input, a.query, a.provider, a.other, a.record, a.snapshot)
        node = shutil.which('node')
        plan = {'mode': a.mode, 'rea_args': args, 'cli': str(a.cli.resolve()),
                'node': node, 'installed': a.cli.is_file(), 'execute': a.execute,
                'input_sha256': sha256_file(a.input) if a.input and a.input.is_file() else None,
                'other_sha256': sha256_file(a.other) if a.other and a.other.is_file() else None,
                'saved_evidence_reuse': a.mode in ('summary', 'modules', 'compare'),
                'ghidra_dir': str(a.ghidra_dir.resolve()) if a.ghidra_dir else None,
                'other': str(a.other.resolve()) if a.other else None,
                'input_identity_note': 'Directory identity not recursively hashed',
                'cap_gb': a.cap, 'timeout': a.timeout,
                'limitations': ['IL2CPP metadata is not PE/CLI managed metadata',
                                'Native analysis requires an available provider',
                                'Exit zero does not prove full semantic recovery']}
        if not a.execute:
            print(json.dumps(plan, ensure_ascii=False, indent=2))
            return 0
        if not node or not a.cli.is_file():
            raise ValueError('Node or local REA CLI missing; see tools/REA_INTEGRATION.md')
        if a.cli.suffix not in ('.mjs', '.js', '.cjs'):
            raise ValueError('--cli must name a Node entry point, not a shell script')
        if a.mode in ('summary', 'modules', 'compare'):
            a.out.mkdir(parents=True, exist_ok=True)
            workflow_dir = Path(tempfile.mkdtemp(prefix='workflow-', dir=a.out))
            workflow = workflow_dir / 'request.json'
            write_workflow(workflow, a.mode, a.input, a.other, a.offset, a.limit)
            args = [OPERATIONS[a.mode], str(workflow.resolve()), '--json']
            plan['workflow'] = str(workflow.resolve())
        environment = {'GHIDRA_INSTALL_DIR': str(a.ghidra_dir.resolve())} if a.ghidra_dir else None
        result = execute([node, str(a.cli.resolve()), *args], a.out, a.cap, a.timeout, a.max_output_mb, environment)
        Path(result['evidence']).with_name('plan.json').write_text(
            json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] == 'process_completed' else 1
    except (ValueError, OSError) as error:
        ap.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
