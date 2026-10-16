from pathlib import Path
import json,hashlib,UnityPy
p=Path(__file__).resolve().parent;out=p/'card_fx_asset_audit_20261015';out.mkdir(exist_ok=True)
d=json.loads((p/'goal_card_ui_audit_20261015/native_ui_chain.json').read_text(encoding='utf-8'))
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};files={o.assets_file.name:o.assets_file for o in env.objects}
def resolve(owner,ptr):
 if not ptr['m_PathID']:return None
 name=owner
 if ptr['m_FileID']:name=files[owner].externals[ptr['m_FileID']-1].path.replace('\\','/').split('/')[-1]
 return objs.get((name,ptr['m_PathID']))
def rec(o):return dict(file=o.assets_file.name,path_id=str(o.path_id),type=o.type.name,raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest(),fields=o.read_typetree())
def ident(o):return None if o is None else dict(file=o.assets_file.name,path_id=str(o.path_id),type=o.type.name)
def key(o):return (o.assets_file.name,o.path_id)
mats={};sprites={};textures={};joins=[];nodes=[];shaders={}
for n in d['nodes']:
 if not (n['path'].startswith('/PointsExplode') or n['path'].startswith('/GoalCardPrefab/UIParticle')):continue
 nodes.append(n)
 for c in n['components']:
  if c['type']=='ParticleSystemRenderer':
   for slot,ptr in enumerate(c['fields']['m_Materials']):
    o=resolve(n['file'],ptr);joins.append(dict(node=n['path'],renderer=c['path_id'],enabled=c['fields']['m_Enabled'],slot=slot,ref=ptr,resolved=ident(o)))
    if o:mats[key(o)]=o
  if c['type']=='ParticleSystem':
   uv={k:v for k,v in c['fields'].items() if 'uvmodule' in k.lower()}
   def walk(v,path):
    if isinstance(v,dict):
     if 'm_FileID' in v and 'm_PathID' in v:
      o=resolve(n['file'],v);joins.append(dict(node=n['path'],ps=c['path_id'],uv_path=path,ref=v,resolved=ident(o)))
      if o and o.type.name=='Sprite':sprites[key(o)]=o
     else:
      for k,x in v.items():walk(x,path+'/'+k)
    elif isinstance(v,list):
     for i,x in enumerate(v):walk(x,path+'/'+str(i))
   walk(uv,'')
mr=[]
for o in mats.values():
 r=rec(o);s=resolve(o.assets_file.name,r['fields']['m_Shader']);r['shader_resolved']=ident(s)
 if s:
  sr=rec(s);sf=sr.pop('fields');sr['name']=sf.get('m_ParsedForm',{}).get('m_Name');sr['parsed_form']=sf.get('m_ParsedForm');shaders[key(s)]=sr;r['shader_raw_sha256']=sr['raw_sha256']
 for slot,v in r['fields']['m_SavedProperties']['m_TexEnvs']:
  t=resolve(o.assets_file.name,v['m_Texture']);joins.append(dict(material=ident(o),slot=slot,ref=v['m_Texture'],resolved=ident(t)))
  if t and t.type.name=='Texture2D':textures[key(t)]=t
 mr.append(r)
def png(o,kind):
 r=rec(o);im=o.read().image;fn=f'{o.assets_file.name}_{o.path_id}_{kind}.png';im.save(out/fn);r['png']=dict(file=fn,size=im.size,sha256=hashlib.sha256((out/fn).read_bytes()).hexdigest(),pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest());return r
spr=[]
for o in sprites.values():
 r=png(o,'sprite');spr.append(r)
 for slot in ('texture','alphaTexture'):
  t=resolve(o.assets_file.name,r['fields']['m_RD'][slot])
  if t and t.type.name=='Texture2D':textures[key(t)]=t
tex=[]
for o in textures.values():
 r=png(o,'texture');r['fields']={k:v for k,v in r['fields'].items() if k not in ('image data','m_ImageData')};tex.append(r)
def enc(v):
 if isinstance(v,(bytes,bytearray)):return dict(opaque_bytes=len(v),sha256=hashlib.sha256(v).hexdigest())
 raise TypeError(type(v).__name__)
result=dict(nodes=nodes,materials=mr,shaders=list(shaders.values()),sprites=spr,textures=tex,joins=joins)
(out/'chains.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8')
print('PS',[(n['path'],n['game_object'].get('m_IsActive'),[(c['path_id'],c['fields'].get('m_Enabled')) for c in n['components'] if c['type']=='ParticleSystemRenderer']) for n in nodes if any(c['type']=='ParticleSystem' for c in n['components'])])
print('MAT',[(r['file'],r['path_id'],r['fields']['m_Name'],r['shader_resolved']) for r in mr]);print('SHADER',[(r['file'],r['path_id'],r['name'],r['raw_sha256']) for r in shaders.values()]);print('PNG',len(spr),len(tex))
