from pathlib import Path
import re,json,bisect,zipfile,hashlib
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent;out=p/'drop_gauge_audit_20261015';methods={};cur='';pending=None
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
 if '// TypeDefIndex:' in line and not line.startswith('\t'):cur=line.strip();pending=None
 m=re.search(r'RVA: (0x[0-9A-F]+)',line)
 if m:pending=int(m[1],16)
 elif pending and '{ }' in line:methods.setdefault(pending,[]).append({'class':cur,'signature':line.strip()});pending=None
ks=sorted(methods);lib=p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so'
with lib.open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD'];md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
 for a in [0x21B2628,0x1E42490,0x21DF174,0x21DC248]:
  n=min(16384 if a==0x21DC248 else 8192,ks[bisect.bisect_right(ks,a)]-a);s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-s['p_vaddr']+s['p_offset'];f.seek(off);b=f.read(n)
  ls=[str(methods[a]),f'RVA={a:#x} file_offset={off:#x} next_declared_bound={a+n:#x}, not independently verified symbol size; sha256={hashlib.sha256(b).hexdigest()}']
  for i in md.disasm(b,a):
   ann=''
   if i.mnemonic in ['bl','b'] and i.op_str.startswith('#0x'):ann=' ; '+str(methods.get(int(i.op_str[1:],16),[]))
   ls.append(f'{i.address:08x} {i.mnemonic:8} {i.op_str}{ann}')
  (out/f'bomb_disasm_{a:08x}.txt').write_text('\n'.join(ls),encoding='utf-8')
# Existing JSON exports only; no asset parsing, pixels or bundles loaded.
rows=[];n=0
index={}
for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
 rr=json.loads(line)
 if rr.get('json_file') and rr.get('script_class'):index[rr['json_file']]=rr
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 for item in z.infolist():
  if not item.filename.endswith('.json') or item.file_size>256000:continue
  raw=z.read(item)
  if b'"autoActivate"' not in raw and b'"isHolder"' not in raw:continue
  d=json.loads(raw);n+=1
  rr=index.get(item.filename);go_name=None
  if d.get('m_GameObject',{}).get('m_FileID')==0:
   gn=item.filename.rsplit('/MonoBehaviour/',1)[0]+'/GameObject/'+str(d['m_GameObject']['m_PathID'])+'.json'
   try:go_name=json.loads(z.read(gn)).get('m_Name')
   except KeyError:pass
  rows.append({'json_file':item.filename,'json_sha256':hashlib.sha256(raw).hexdigest(),'source_index':rr,'game_object_name':go_name,'fields':d})
(out/'prop_stored_activation_candidates.json').write_text(json.dumps({'boundary':'Previously exported structured records; source raw verification remains in original extraction index. Candidate fields, not runtime activation proof.','count':n,'records':rows},ensure_ascii=False,indent=1),encoding='utf-8')
print('selected methods4 existing flag records',n)
