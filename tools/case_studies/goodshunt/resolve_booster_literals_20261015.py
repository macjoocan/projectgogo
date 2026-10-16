from pathlib import Path
import struct,json,hashlib,zipfile
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;out=p/'booster_goal_audit_20261015';b=(p/'input_prepared/assets/bin/Data/Managed/Metadata/global-metadata.dat').read_bytes();result={'literals':{},'strings':{},'audio_archive':'results/GoodsHunt_assets.zip','audio':[]}
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD'];rel={r['r_offset']:r['r_addend'] for s in e.iter_sections() if s['sh_type']=='SHT_RELA' for r in s.iter_relocations() if r['r_info_type']==1027}
 def raw(a,n):
  s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);f.seek(a-s['p_vaddr']+s['p_offset']);return f.read(n)
 def ptr(a):return rel.get(a,struct.unpack('<Q',raw(a,8))[0])
 for a,n,fmt in [(0xe0a2a0,4,'<f'),(0xe0a44c,4,'<f'),(0xe0a578,4,'<f'),(0xdba8e0,8,'<2i')]:
  v=raw(a,n);result['literals'][hex(a)]={'hex':v.hex(),'values':struct.unpack(fmt,v)}
 for label,slot in [('Growth.OnActivate.PlaySFX',0x4175f00),('Magnet.OnActivate.playEffectGlobal',0x4175f18),('Hint.OnActivate.PlaySFX',0x4196e48),('Shield.target.CompareTag',0x4175f80)]:
  addr=ptr(slot);token=struct.unpack('<Q',raw(addr,8))[0];r={'slot':hex(slot),'relocation_target':hex(addr),'token':hex(token)}
  if token>>29==5:
   idx=(token&0x1ffffffe)>>1;lo=struct.unpack_from('<I',b,8)[0];size,di=struct.unpack_from('<II',b,lo+8*idx);ld=struct.unpack_from('<I',b,16)[0];r.update(literal_index=idx,metadata_offset=ld+di,text=b[ld+di:ld+di+size].decode('utf-8'))
  result['strings'][label]=r
with zipfile.ZipFile(p/'results/GoodsHunt_assets.zip') as z:
 for i in z.infolist():
  if i.filename.lower().endswith(('.wav','.ogg','.mp3')):
   v=z.read(i);result['audio'].append({'entry':i.filename,'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()})
(out/'literal_audio_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8');print(json.dumps({'literals':result['literals'],'strings':result['strings'],'audio_count':len(result['audio'])}))
