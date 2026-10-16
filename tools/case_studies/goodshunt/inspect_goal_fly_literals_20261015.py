from pathlib import Path
import json,struct
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;out=p/'goal_fly_ui_audit_20261015';rows=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);loads=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
 for a,fmt,label in [(0xe0a874,'<f','AnimateToUI initial delay'),(0xe0a4f0,'<f','First Scale endValue'),(0xe0a7fc,'<f','First Scale duration'),(0xe0a3fc,'<f','Despawn callback delay after flight start'),(0xe0a1c4,'<f','PlayEffect alpha duration / shrink duration'),(0xe0a628,'<f','Scale shrink callback delay after first scale complete'),(0xe0a3b0,'<f','Scale shrink endValue'),(0xdb98f8,'<2f','static AnchorPos'),(0x0,'<f','unused')]:
  if not a:continue
  s=next(s for s in loads if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-s['p_vaddr']+s['p_offset'];f.seek(off);b=f.read(struct.calcsize(fmt));rows.append(dict(label=label,address=hex(a),ELF_offset=hex(off),hex=b.hex(),format=fmt,value=struct.unpack(fmt,b)))
rows.append(dict(label='DOPathPrimeWorld duration immediate',bits='0x3f19999a',value=struct.unpack('<f',struct.pack('<I',0x3f19999a))[0]))
(out/'literal_values.json').write_text(json.dumps(rows,indent=1),encoding='utf-8');print(json.dumps(rows))
