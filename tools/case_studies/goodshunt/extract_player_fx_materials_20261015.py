from pathlib import Path
import json,hashlib,UnityPy
p=Path(__file__).resolve().parent;out=p/'player_fx_material_audit_20261015';out.mkdir(exist_ok=True)
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects}
owner=objs[('sharedassets3.assets',1895)].assets_file
def resolve(file,ptr):
 if not ptr.get('m_PathID'):return None
 target=file
 if ptr['m_FileID']:target=objs[next(k for k in objs if k[0]==file)].assets_file.externals[ptr['m_FileID']-1].path.replace('\\','/').split('/')[-1]
 return objs.get((target,ptr['m_PathID']))
def record(o):return dict(file=o.assets_file.name,path_id=str(o.path_id),type=o.type.name,raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest(),fields=o.read_typetree())
materials=[];textures={};sprites={};joins=[]
for fid,pid in ((4,79),(4,80),(6,20)):
 ext=owner.externals[fid-1];name=ext.path.replace('\\','/').split('/')[-1];o=objs[(name,pid)];rec=record(o);rec['owner_reference']=dict(file='sharedassets3.assets',file_id=fid,path_id=str(pid),external_path=ext.path)
 shader=resolve(name,rec['fields']['m_Shader'])
 rec['shader_resolved']=None if shader is None else dict(file=shader.assets_file.name,path_id=str(shader.path_id),raw_sha256=hashlib.sha256(shader.get_raw_data()).hexdigest(),name=shader.read_typetree().get('m_ParsedForm',{}).get('m_Name'))
 materials.append(rec)
 print('MAT',fid,pid,name,rec['fields']['m_Name'],flush=True)
 for slot,v in rec['fields']['m_SavedProperties']['m_TexEnvs']:
  ptr=v['m_Texture'];tex=resolve(name,ptr)
  joins.append(dict(material_file=name,material_id=str(pid),slot=slot,ref=ptr,resolved=None if tex is None else dict(file=tex.assets_file.name,path_id=str(tex.path_id),type=tex.type.name)))
  if tex and tex.type.name=='Texture2D':textures[(tex.assets_file.name,tex.path_id)]=tex
chain=json.loads((p/'ingame_handoff_20261014/player_native_visual_physics_chain.json').read_text(encoding='utf-8'))['nodes']
nodebygo={int(n['transform']['m_GameObject']['m_PathID']):n for n in chain};nodebytid={int(n['transform_path_id']):n for n in chain}
fx=json.loads((p/'fx_existing_audit_20261015/existing_fx_records.json').read_text(encoding='utf-8'))['player_records'];psbyid={int(r['provenance']['path_id']):r for r in fx if r['provenance']['type']=='ParticleSystem'}
groups=[]
for root in (1520,1510,1487,1578):
 rr=psbyid[root];go=rr['fields']['m_GameObject']['m_PathID'];rn=nodebygo[go];seen=set();q=[int(rn['transform_path_id'])]
 while q:
  tid=q.pop();
  if tid in seen:continue
  seen.add(tid);n=nodebytid[tid];q.extend(x['m_PathID'] for x in n['transform']['m_Children'] if x['m_FileID']==0)
 group=[]
 for r in psbyid.values():
  n=nodebygo[r['fields']['m_GameObject']['m_PathID']]
  if int(n['transform_path_id']) not in seen:continue
  uv={k:v for k,v in r['fields'].items() if 'uvmodule' in k.lower() or 'texturesheet' in k.lower()}
  group.append(dict(file='sharedassets3.assets',path_id=str(r['provenance']['path_id']),name=n['name'],uv=uv))
  def walk(v,path):
   if isinstance(v,dict):
    if 'm_FileID' in v and 'm_PathID' in v and v['m_PathID']:
     obj=resolve('sharedassets3.assets',v)
     joins.append(dict(ps_id=str(r['provenance']['path_id']),uv_path=path,ref=v,resolved=None if obj is None else dict(file=obj.assets_file.name,path_id=str(obj.path_id),type=obj.type.name)))
     if obj and obj.type.name=='Sprite':sprites[(obj.assets_file.name,obj.path_id)]=obj
    else:
     for k,x in v.items():walk(x,path+'/'+k)
   elif isinstance(v,list):
    for i,x in enumerate(v):walk(x,path+'/'+str(i))
  walk(uv,'')
 groups.append(dict(root_ps_id=str(root),particles=group))
spr=[]
for key,o in sprites.items():
 rec=record(o);sp=o.read();im=sp.image;fn=f'{key[0]}_{key[1]}_sprite.png';im.save(out/fn);rec['png']=dict(file=fn,size=im.size,sha256=hashlib.sha256((out/fn).read_bytes()).hexdigest());spr.append(rec)
 for slot in ('texture','alphaTexture'):
  tex=resolve(key[0],rec['fields']['m_RD'][slot])
  if tex and tex.type.name=='Texture2D':textures[(tex.assets_file.name,tex.path_id)]=tex
texrows=[]
for key,o in textures.items():
 rec=record(o);rec['fields']={k:v for k,v in rec['fields'].items() if k not in ('image data','m_ImageData')};im=o.read().image;fn=f'{key[0]}_{key[1]}_texture.png';im.save(out/fn)
 rec['png']=dict(file=fn,size=im.size,mode=im.mode,sha256=hashlib.sha256((out/fn).read_bytes()).hexdigest(),pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest());texrows.append(rec)
 print('TEX',key,rec['fields']['m_Name'],im.size,flush=True)
def enc(x):
 if isinstance(x,(bytes,bytearray)):return dict(opaque_bytes=len(x),sha256=hashlib.sha256(x).hexdigest())
 raise TypeError(type(x).__name__)
result=dict(boundary='Selected existing original data only; no implementation/source change or GPU parity. Material texture joins and selected PS UV references only, not all FX.',materials=materials,texture_records=texrows,sprite_records=spr,ps_uv_groups=groups,joins=joins)
(out/'chains.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8');print('DONE',len(materials),len(texrows),len(spr),[len(g['particles']) for g in groups])
