from pathlib import Path
import struct,json,hashlib
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;out=p/'end_flow_audit_20261015';rows=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
 for a,n,fmt,label in [(0xdb9f48,8,'<d','C_WaitForGoalCard initial scaled delay'),(0xe0a464,4,'<f','PlayWinFireworks return timeout'),(0xe0a8c0,4,'<f','EndingTransition auto close delay'),(0xe0a44c,4,'<f','EndingTransition skip delayed callback'),(0xe0a874,4,'<f','Card delayed flip additive'),(0xe0a994,4,'<f','Logo scale first multiplier'),(0xe0a9d0,4,'<f','Retry WaitForSeconds'),(0xe0a5f0,4,'<f','Logo hold interval')]:
  s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-s['p_vaddr']+s['p_offset'];f.seek(off);b=f.read(n);rows.append({'label':label,'address':hex(a),'ELF_offset':hex(off),'hex':b.hex(),'format':fmt,'value':struct.unpack(fmt,b)[0]})
(out/'literal_values.json').write_text(json.dumps(rows,indent=1),encoding='utf-8');print(json.dumps(rows))
