from pathlib import Path
import json,hashlib,struct
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;out=p/'growth_fx_shader_audit_20261015';summ=[]
for r in json.loads((out/'inventory.json').read_text()):
 form=json.loads((out/r['label']/'parsed_form.json').read_text());passes=[]
 for si,ss in enumerate(form['m_SubShaders']):
  for pi,ps in enumerate(ss['m_Passes']):
   s=ps['m_State'];refs=[]
   def walk(v,path):
    if isinstance(v,dict):
     if 'm_BlobIndex' in v:refs.append(dict(path=path,blob_index=v['m_BlobIndex'],gpu_type=v.get('m_GpuProgramType'),keywords=v.get('m_KeywordIndices')))
     for k,x in v.items():walk(x,path+'/'+k)
    elif isinstance(v,list):
     for i,x in enumerate(v):walk(x,path+'/'+str(i))
   walk(ps,'')
   passes.append(dict(subshader=si,pass_index=pi,name=s['m_Name'],blend=s['rtBlend0'],zTest=s['zTest'],zWrite=s['zWrite'],culling=s['culling'],tags=s['m_Tags'],program_refs=refs))
 for seg in r['segments']:
  for pr in seg['programs']:
   raw=(out/r['label']/pr['file']).read_bytes();assert len(raw)==pr['code_bytes'] and hashlib.sha256(raw).hexdigest()==pr['sha256'] and pr['keyword_prefix_verified']
 summ.append(dict(label=r['label'],shader=r['name'],passes=passes,programs=sum(len(seg['programs']) for seg in r['segments'])))
(out/'pass_summary.json').write_text(json.dumps(summ,indent=1),encoding='utf-8')
for r in summ:
 print('SHADER',r['label'],r['programs'])
 if r['label']=='holy_smoke':
  for ps in r['passes']:
   refs=[x for x in ps['program_refs'] if x['blob_index'] in (8,21)];
   if refs:print('HOLY_PASS',ps['subshader'],ps['name'],refs)
from PIL import Image
for r in json.loads((out/'holy_smoke_textures.json').read_text()):
 raw=(out/r['png']['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['png']['sha256']
 with Image.open(out/r['png']['file']) as im:assert list(im.size)==r['png']['size'] and hashlib.sha256(im.tobytes()).hexdigest()==r['png']['pixel_sha256']
print('PASS GLSL69 SHA/length/keywordprefix + HolyPNG2 dimensions/pixelSHA')
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);loads=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD'];vals=[]
 for a in (0xe0a804,):
  seg=next(s for s in loads if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-seg['p_vaddr']+seg['p_offset'];f.seek(off);raw=f.read(4);vals.append(dict(address=hex(a),ELF_offset=hex(off),hex=raw.hex(),value=struct.unpack('<f',raw)[0]))
 a=0xe0cbba;seg=next(s for s in loads if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);f.seek(a-seg['p_vaddr']+seg['p_offset']);table=list(f.read(5));vals.append(dict(address=hex(a),switch_base='0x21e9f04',input_base=100,bytes=table,targets=[hex(0x21e9f04+x*4) for x in table]))
 (p/'growth_fx_code_audit_20261015/literals_and_switch.json').write_text(json.dumps(vals,indent=1),encoding='utf-8');print('LITERALS',vals)
