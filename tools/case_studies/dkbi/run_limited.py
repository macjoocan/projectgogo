import sys, os, json, subprocess, time
from pathlib import Path
sys.path.insert(0, r'D:\99.기타')
from dkbi_full_extract import memory_job, psutil
root = Path(__file__).parent
label = sys.argv[1]
command = sys.argv[2:]
if psutil.virtual_memory().available < 6 * 1024**3:
    raise SystemExit('Insufficient available RAM; need 6 GiB')
start = time.time()
peak = 0
reason = None
with (root / (label + '.log')).open('w', encoding='utf-8') as log:
    p = subprocess.Popen(command, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         env=dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', MSBUILDDISABLENODEREUSE='1'))
    api, job = memory_job(p, 1536)
    try:
        while p.poll() is None:
            try:
                peak = max(peak, psutil.Process(p.pid).memory_info().rss)
            except psutil.Error:
                pass
            if peak > 1280 * 1024**2 or psutil.virtual_memory().available < 4 * 1024**3 or time.time()-start > 240:
                reason = 'memory_or_time_guard'
                api.CloseHandle(job)
                job = None
                break
            time.sleep(.25)
        p.wait(timeout=10)
    finally:
        if job:
            api.CloseHandle(job)
result = dict(command=command, exit_code=p.returncode, peak_rss_bytes=peak,
              elapsed_seconds=time.time()-start, stop_reason=reason, process_commit_limit_mb=1536)
(root / (label+'.result.json')).write_text(json.dumps(result, indent=2),encoding='utf-8')
print(json.dumps(result))
