from pathlib import Path
import hashlib,json
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent;out=p/'booster_goal_audit_20261015'
ranges=[('UpgradesController.GetUpgrade<object>',0x26fc314,512),('Upgrade<object>.GetCurrentStage',0x27f71b8,0x68),('Upgrade<object>.GetNextStage',0x27f7220,0x64),('Upgrade<object>.UpgradeStage',0x27f7284,0x50),('Upgrade<object>.GetStage',0x27f72d4,0x60)]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD'];md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);rows=[]
 for label,a,n in ranges:
  s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-s['p_vaddr']+s['p_offset'];f.seek(off);raw=f.read(n);row={'label':label,'rva':hex(a),'ELF_offset':hex(off),'read_bytes':len(raw),'code_sha256':hashlib.sha256(raw).hexdigest(),'boundary':'Explicit bounded range; first512B of GetUpgrade may include next function. Other ranges follow exact generic RVA list from dump.cs; no generic alias inference.'};rows.append(row)
  (out/f'generic_{a:08x}.txt').write_text(json.dumps(row)+'\n'+'\n'.join(f'{i.address:08x} {i.mnemonic:8} {i.op_str}' for i in md.disasm(raw,a)),encoding='utf-8')
(out/'generic_upgrade_ranges.json').write_text(json.dumps(rows,indent=1),encoding='utf-8');print('bounded generic bytes',sum(r['read_bytes'] for r in rows))
