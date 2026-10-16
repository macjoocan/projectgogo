from pathlib import Path
import json,hashlib
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent
md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN); rows=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
    e=ELFFile(f); loads=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
    for address,size,label in [(0x32a4644,16,'SkeletonGraphic.get_color slot22'),(0x32a4654,16,'SkeletonGraphic.set_color slot23'),(0x1d9843c,60,'PlayLogo color get/alpha/set'),(0x1d98504,20,'PlayLogo DOFade target1 duration0.5')]:
        s=next(s for s in loads if s['p_vaddr']<=address<s['p_vaddr']+s['p_filesz'])
        offset=address-s['p_vaddr']+s['p_offset']; f.seek(offset); raw=f.read(size)
        rows.append(dict(label=label,rva=hex(address),ELF_offset=hex(offset),sha256=hashlib.sha256(raw).hexdigest(),instructions=[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(raw,address)]))
out=dict(getter_slot=22,setter_slot=23,derived_vtable_base='0x138',slot_entry_size=16,getter_entry='0x298',setter_entry='0x2a8',initial_alpha=0.5,target_alpha=1.0,duration=0.5,records=rows)
(p/'end_flow_audit_20261015/logo_alpha_evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
