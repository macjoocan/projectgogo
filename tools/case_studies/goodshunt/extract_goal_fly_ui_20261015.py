from pathlib import Path
import json,zipfile,hashlib,UnityPy
p=Path(__file__).resolve().parent;out=p/'goal_fly_ui_audit_20261015';out.mkdir(exist_ok=True)
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};index={}
for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
 r=json.loads(line)
 if r.get('json_file'):index[(r['serialized_file'],r['path_id'])]=r
roots=[];nodes=[];sprites={};errors=[]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 def read(key):
  o=objs[key];r=index.get(key)
  return json.loads(z.read(r['json_file'])) if o.type.name=='MonoBehaviour' and r else o.read_typetree()
 def resolve(f,ptr):
  target=f
  if ptr['m_FileID']:
   owner=next(o for (n,_),o in objs.items() if n==f).assets_file
   target=owner.externals[ptr['m_FileID']-1].path.replace('\\','/').split('/')[-1]
  return target,ptr['m_PathID']
 def walk(f,tid,parent=''):
  tr=read((f,tid));gid=tr['m_GameObject']['m_PathID'];go=read((f,gid));path=parent+'/'+go['m_Name'];cs=[]
  for c in go['m_Component']:
   pid=c['component']['m_PathID'];key=(f,pid);o=objs[key];r=index.get(key,{});rec=dict(type=o.type.name,path_id=str(pid),script_class=r.get('script_class'),raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest())
   try:rec['fields']=fields=read(key)
   except Exception as e:rec['error']=str(e);errors.append(dict(file=f,path_id=str(pid),error=str(e)));cs.append(rec);continue
   if fields.get('m_Sprite',{}).get('m_PathID'):
    sk=resolve(f,fields['m_Sprite']);rec['sprite_key']=f'{sk[0]}#{sk[1]}'
    if sk not in sprites:
     so=objs[sk];im=so.read().image;fn=f'{sk[0]}_{sk[1]}_sprite.png';im.save(out/fn)
     sprites[sk]=dict(file=sk[0],path_id=str(sk[1]),raw_sha256=hashlib.sha256(so.get_raw_data()).hexdigest(),fields=so.read_typetree(),png=dict(file=fn,size=im.size,sha256=hashlib.sha256((out/fn).read_bytes()).hexdigest(),pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest()))
   cs.append(rec)
  nodes.append(dict(file=f,path=path,game_object_id=str(gid),game_object=go,transform_id=str(tid),transform=tr,components=cs))
  assert len(nodes)<128,'selected subtree exceeded cap'
  for child in tr['m_Children']:
   cf,ct=resolve(f,child);walk(cf,ct,path)
 for key,r in index.items():
  if key[0]!='level2' or r.get('script_class')!='GameRefManager':continue
  manager=read(key);ref=manager['ItemSampleMoveTile'];target=resolve(key[0],ref);item=read(target);gid=item['m_GameObject']['m_PathID'];go=read((target[0],gid));tid=next(c['component']['m_PathID'] for c in go['m_Component'] if objs[(target[0],c['component']['m_PathID'])].type.name in ('Transform','RectTransform'))
  roots.append(dict(manager_provenance=r,manager_fields=manager,source_ref=ref,resolved_file=target[0],resolved_component_id=str(target[1]),item_fields=item,root_game_object_id=str(gid),root_transform_id=str(tid)));walk(target[0],tid)
def enc(v):
 if isinstance(v,(bytes,bytearray)):return dict(opaque_bytes=len(v),sha256=hashlib.sha256(v).hexdigest())
 raise TypeError(type(v).__name__)
result=dict(boundary='Exact scene level2 GameRefManager.ItemSampleMoveTile referenced subtree only; stored Sprite may be runtime-replaced by UID icon. No original execution or implementation edit.',roots=roots,nodes=nodes,sprites=list(sprites.values()),errors=errors)
(out/'native_ui_chain.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8')
print('ROOTS',[(r['manager_provenance']['path_id'],r['source_ref'],r['resolved_file'],r['resolved_component_id'],r['root_game_object_id']) for r in roots]);print('NODES',len(nodes),'SPRITES',len(sprites),'ERRORS',len(errors));print('ITEM',[(r['item_fields']) for r in roots])
