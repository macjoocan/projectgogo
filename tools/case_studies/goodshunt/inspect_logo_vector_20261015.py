from pathlib import Path
import re,hashlib,json
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent
active=False; pending=None; targets=[]; declarations=[]
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
    if '// TypeDefIndex:' in line and not line.startswith('\t'):
        active='// TypeDefIndex: 9861' in line
    if not active: continue
    if 'Vector;' in line: declarations.append(line.strip())
    m=re.search(r'RVA: (0x[0-9A-F]+)',line)
    if m: pending=int(m[1],16)
    elif pending and '{ }' in line:
        if 'get_one()' in line or '.cctor()' in line: targets.append((pending,line.strip()))
        pending=None
md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN); result=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
    elf=ELFFile(f); loads=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    for address,signature in targets:
        seg=next(s for s in loads if s['p_vaddr']<=address<s['p_vaddr']+s['p_filesz'])
        offset=address-seg['p_vaddr']+seg['p_offset']; f.seek(offset); raw=f.read(512)
        ins=[]
        for i in md.disasm(raw,address):
            ins.append(f'{i.address:08x} {i.mnemonic} {i.op_str}')
            if i.mnemonic=='ret': break
        result.append(dict(rva=hex(address),ELF_offset=hex(offset),signature=signature,read_window_sha256=hashlib.sha256(raw).hexdigest(),instructions=ins))
out=dict(type='UnityEngine.Vector3',type_def_index=9861,fields=declarations,methods=result)
(p/'end_flow_audit_20261015/logo_static_vector_evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
