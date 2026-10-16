from pathlib import Path
import json,re,struct,hashlib
from elftools.elf.elffile import ELFFile
import UnityPy
p=Path(__file__).resolve().parent;o=p/'booster_goal_audit_20261015'
result={'boundary':'Read-only native stored objects and bounded existing disassembly; linear register candidates are not CFG proofs.','bomb_nodes':[],'audio_call_candidates':[],'tag_managers':[]}
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'))
for ob in env.objects:
 if ob.type.name=='TagManager':
  result['tag_managers'].append({'file':ob.assets_file.name,'path_id':str(ob.path_id),'fields':ob.read_typetree(),'raw_sha256':hashlib.sha256(ob.get_raw_data()).hexdigest()})
 if ob.type.name!='GameObject':continue
 d=ob.read_typetree()
 if d.get('m_Name')!='Bomb':continue
 result['bomb_nodes'].append({'file':ob.assets_file.name,'path_id':str(ob.path_id),'raw_sha256':hashlib.sha256(ob.get_raw_data()).hexdigest(),'fields':d})
del env
src=p/'input_prepared/assets/aa/Android/props_assets_all_8cfb9dc23d45f5ca0c92cd5f38151ff7.bundle'
env=UnityPy.load(str(src));objs={(ob.assets_file.name,ob.path_id):ob for ob in env.objects}
f='CAB-5388c821bd9df28739ab71fc81803c09';mb=objs[(f,1181109212370131174)].read_typetree();rootid=mb['m_GameObject']['m_PathID']
root=objs[(f,rootid)];d=root.read_typetree()
result['bomb_nodes'].append({'source':str(src),'file':f,'path_id':str(rootid),'raw_sha256':hashlib.sha256(root.get_raw_data()).hexdigest(),'triggerable_component_path_id':'1181109212370131174','fields':d})
for c in d['m_Component']:
 ob=objs[(f,c['component']['m_PathID'])]
 if ob.type.name=='Transform':
  result['bomb_transform']={'path_id':str(ob.path_id),'fields':ob.read_typetree()}
del env,objs
b=(p/'input_prepared/assets/bin/Data/Managed/Metadata/global-metadata.dat').read_bytes()
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD'];rel={r['r_offset']:r['r_addend'] for sec in e.iter_sections() if sec['sh_type']=='SHT_RELA' for r in sec.iter_relocations() if r['r_info_type']==1027}
 def raw(a,n):
  s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);f.seek(a-s['p_vaddr']+s['p_offset']);return f.read(n)
 def literal(slot):
  try:
   addr=rel.get(slot,struct.unpack('<Q',raw(slot,8))[0]);token=struct.unpack('<Q',raw(addr,8))[0]
   if token>>29!=5:return None
   idx=(token&0x1ffffffe)>>1;lo=struct.unpack_from('<I',b,8)[0];size,di=struct.unpack_from('<II',b,lo+8*idx);ld=struct.unpack_from('<I',b,16)[0]
   return {'slot':hex(slot),'token':hex(token),'metadata_offset':ld+di,'text':b[ld+di:ld+di+size].decode('utf-8')}
  except (StopIteration,struct.error,UnicodeDecodeError):return None
 for folder in (p/'code_audit_20261014',o):
  for fp in folder.glob('disasm_*.txt'):
   lines=fp.read_text(encoding='utf-8').splitlines();regs={}
   for i,line in enumerate(lines):
    m=re.match(r'([0-9a-f]{8})\s+(\w+)\s+(.*?)(?: ;.*)?$',line)
    if not m:continue
    addr,ins,args=m.groups()
    ma=re.fullmatch(r'(x\d+), #0x([0-9a-f]+)',args)
    ml=re.fullmatch(r'(x\d+), \[(x\d+)(?:, #(0x[0-9a-f]+|\d+))?\]!?',args)
    mm=re.fullmatch(r'(x\d+), (x\d+)',args)
    if ins=='adrp' and ma:regs[ma[1]]=('addr',int(ma[2],16))
    elif ins=='mov' and mm:regs[mm[1]]=regs.get(mm[2])
    elif ins=='ldr' and ml:
     base=regs.get(ml[2]);value=None
     if base and base[0]=='addr':
      a=base[1]+int(ml[3] or '0',0);lit=literal(a)
      value=('literal_handle',lit) if lit else None
     elif base and base[0]=='literal_handle' and not ml[3]:value=('string',base[1])
     regs[ml[1]]=value
    if ins in ('bl','b') and ('#0x1d0b470' in args or '#0x1d11f44' in args):
     r=regs.get('x0');result['audio_call_candidates'].append({'file':str(fp.relative_to(p)),'owner':lines[:3],'call_rva':addr,'literal':r[1] if r and r[0]=='string' else None,'context':lines[max(0,i-12):i+1]})
    if ins=='bl':
     for j in range(19):regs.pop('x'+str(j),None)
 result['freeze_literal']=literal(0x41825d8)
(o/'followup_native_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
print('bomb_nodes',len(result['bomb_nodes']))
for r in result['bomb_nodes']:print(r['file'],r['path_id'],r['fields']['m_Layer'],r['fields']['m_Tag'])
print('freeze',result['freeze_literal'])
for r in result['audio_call_candidates']:
 if r['literal']:print(r['call_rva'],r['literal']['text'],r['owner'][:2])
