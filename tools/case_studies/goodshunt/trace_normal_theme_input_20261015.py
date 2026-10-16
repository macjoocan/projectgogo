from pathlib import Path
import json,re,bisect,numpy as np
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent;out=p/'drop_gauge_audit_20261015';m={};cur='';pending=None
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
 if '// TypeDefIndex:' in line and not line.startswith('\t'):cur=line.strip();pending=None
 r=re.search(r'RVA: (0x[0-9A-F]+)',line)
 if r:pending=int(r[1],16)
 elif pending and '{ }' in line:m.setdefault(pending,[]).append({'class':cur,'signature':line.strip()});pending=None
lib=p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so';ks=sorted(m);md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
with lib.open('rb') as f:
 e=ELFFile(f);s=e.get_section_by_name('.text');a=s['sh_addr'];raw=s.data();w=np.frombuffer(raw[:len(raw)//4*4],dtype='<u4');idx=np.flatnonzero((w&0x7c000000)==0x14000000);imm=(w[idx]&0x3ffffff).astype(np.int64);imm=np.where(imm&(1<<25),imm-(1<<26),imm);targets=a+idx*4+imm*4;hits=idx[targets==0x21f3a2c];rows=[]
 for i in hits:
  va=a+int(i)*4;j=bisect.bisect_right(ks,va)-1;start=max(a,va-100);code=raw[start-a:va+24-a];ls=[]
  for ins in md.disasm(code,start):
   ann=''
   if ins.mnemonic in ['b','bl'] and ins.op_str.startswith('#0x'):ann=' ; '+str(m.get(int(ins.op_str[1:],16),[]))
   ls.append(f'{ins.address:08x} {ins.mnemonic:8} {ins.op_str}{ann}')
  rows.append({'call':hex(va),'candidate_enclosing_method':m.get(ks[j]),'disasm':ls})
(out/'normal_theme_factory_calls.json').write_text(json.dumps({'target':'0x21f3a2c','boundary':'Direct B/BL only; nearest declared RVA is candidate owner, not validated symbol extent.','calls':rows},indent=1),encoding='utf-8');print(json.dumps(rows))
