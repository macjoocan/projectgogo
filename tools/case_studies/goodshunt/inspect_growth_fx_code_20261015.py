from pathlib import Path
import re,bisect,json,hashlib
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;out=p/'growth_fx_code_audit_20261015';out.mkdir(exist_ok=True)
cur='';pending=None;methods={};want=[]
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
 if '// TypeDefIndex:' in line and not line.startswith('\t'):cur=line.strip()
 m=re.search(r'RVA: (0x[0-9A-F]+)',line)
 if m:pending=int(m[1],16)
 elif pending and '{ }' in line:
  a=pending;pending=None;rec=dict(type=cur,signature=line.strip());methods.setdefault(a,[]).append(rec)
  if ('class LevelBehavior.' in cur or 'class GrowthButton ' in cur or 'class PlayerFxComponent' in cur or 'class GrowthPowerUp ' in cur or 'class EffectEatObjectAnimator' in cur or 'class ItemSampleMoveTile' in cur or ('class PlayerBehavior ' in cur and any(t in line for t in ('OnPlayerLevelUpFx(', 'TryExpandHole(', 'SetPowerUpValue(', 'ResetPowerUpValue('))) or ('class LevelBehavior ' in cur and any(t in line for t in ('OnEffect(', 'OnPropEaten(', 'OnCardRemove(', 'OnCardAnimComplete(')))):want.append(a)
ks=sorted(methods);md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);decl=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 elf=ELFFile(f);loads=[s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
 for a in sorted(set(want)):
  end=ks[bisect.bisect_right(ks,a)];n=min(end-a,16384);seg=next(s for s in loads if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-seg['p_vaddr']+seg['p_offset'];f.seek(off);raw=f.read(n)
  rec=dict(rva=hex(a),ELF_offset=hex(off),next_declaration=hex(end),capped=n<end-a,sha256=hashlib.sha256(raw).hexdigest(),methods=methods[a]);decl.append(rec)
  lines=[json.dumps(rec),'Boundary next declaration, not independently verified symbol size; generic annotations may alias.']
  for i in md.disasm(raw,a):
   ann=''
   if i.mnemonic in ('bl','b') and i.op_str.startswith('#0x'):ann=' ; '+str(methods.get(int(i.op_str[1:],16),[]))
   lines.append(f'{i.address:08x} {i.mnemonic:8} {i.op_str}{ann}')
  (out/f'disasm_{a:08x}.txt').write_text('\n'.join(lines),encoding='utf-8')
(out/'declarations.json').write_text(json.dumps(decl,indent=1),encoding='utf-8');print('methods',len(decl),'capped',sum(r['capped'] for r in decl))
