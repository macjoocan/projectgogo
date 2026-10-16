from pathlib import Path
import struct,json,re,bisect
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;methods={};cur='';pending=None
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
 if '// TypeDefIndex:' in line and not line.startswith('\t'):cur=line.strip()
 m=re.search(r'RVA: (0x[0-9A-F]+)',line)
 if m:pending=int(m[1],16)
 elif pending and '{ }' in line:methods.setdefault(pending,[]).append(dict(type=cur,signature=line.strip()));pending=None
ks=sorted(methods);targets={0x21ed0d8,0x21ed2b0,0x21ecdd8,0x21ecfd0,0x21e9eb0,0x21e9044};rows=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);segments=[dict(s.header) for s in e.iter_segments() if s['p_type']=='PT_LOAD' and s['p_flags']&1]
 for s in segments:
  for rel in range(0,s['p_filesz'],1024*1024):
   f.seek(s['p_offset']+rel);raw=f.read(min(1024*1024,s['p_filesz']-rel));raw=raw[:len(raw)//4*4]
   for i,(w,) in enumerate(struct.iter_unpack('<I',raw)):
    if w&0x7c000000!=0x14000000:continue
    a=s['p_vaddr']+rel+i*4;imm=w&0x3ffffff
    if imm&0x2000000:imm-=0x4000000
    target=a+imm*4
    if target not in targets:continue
    idx=bisect.bisect_right(ks,a)-1;start=ks[idx] if idx>=0 else None
    rows.append(dict(call_rva=hex(a),target=hex(target),kind='bl' if w&0x80000000 else 'b',nearest_preceding_method_rva=None if start is None else hex(start),method_candidates=methods.get(start,[])))
(p/'growth_fx_code_audit_20261015/direct_callers.json').write_text(json.dumps(dict(boundary='Exact immediate B/BL references in executable PT_LOAD only. Nearest preceding method is a declaration-bound candidate; no indirect/delegate references or runtime reachability proof.',calls=rows),indent=1),encoding='utf-8')
for r in rows:print(json.dumps(r))
