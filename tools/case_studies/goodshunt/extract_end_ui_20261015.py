from pathlib import Path
import json,hashlib,zipfile,base64,UnityPy
p=Path(__file__).resolve().parent;out=p/'end_flow_audit_20261015';src=p/'input_prepared/assets/bin/Data/data.unity3d'
env=UnityPy.load(str(src));objs={(o.assets_file.name,o.path_id):o for o in env.objects};index={}
for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
 r=json.loads(line)
 if r.get('json_file'):index[(r['serialized_file'],r['path_id'])]=r
stored=json.loads((out/'stored_ui_components.json').read_text(encoding='utf-8'));rows=[];sprites={};errors=[]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 def read(f,pid):
  o=objs[(f,pid)];r=index.get((f,pid))
  if o.type.name=='MonoBehaviour' and r:return json.loads(z.read(r['json_file']))
  return o.read_typetree()
 def ref(f,r):
  fileid=r['m_FileID'];pid=r['m_PathID'];target=f;external=None
  if fileid:
   ext=next(o for (fn,_),o in objs.items() if fn==f).assets_file.externals[fileid-1];external=ext.path;target=external.replace('\\','/').split('/')[-1]
  return {'source_file':f,'file_id':fileid,'external_path':external,'file':target,'path_id':str(pid)}
 def walk(f,tid,parent=''):
  tr=read(f,tid);gid=tr['m_GameObject']['m_PathID'];go=read(f,gid);path=parent+'/'+go['m_Name'];components=[]
  for c in go['m_Component']:
   pid=c['component']['m_PathID'];o=objs[(f,pid)];ix=index.get((f,pid),{});rr={'type':o.type.name,'script_class':ix.get('script_class'),'path_id':str(pid),'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest()}
   try:rr['fields']=d=read(f,pid)
   except Exception as ex:
    rr['unresolved']=str(ex);errors.append({'file':f,'path_id':str(pid),'type':o.type.name,'error':str(ex)});components.append(rr);continue
   if isinstance(d,dict) and d.get('m_Sprite',{}).get('m_PathID'):
    sr=ref(f,d['m_Sprite']);rr['sprite_reference']=sr;key=sr['file']+'#'+sr['path_id']
    if key not in sprites:
     so=objs.get((sr['file'],int(sr['path_id'])))
     if so:
      sprites[key]={'reference':sr,'raw_sha256':hashlib.sha256(so.get_raw_data()).hexdigest(),'fields':so.read_typetree()}
     else:errors.append({'sprite_unresolved':sr})
   components.append(rr)
  row={'file':f,'path':path,'game_object_path_id':str(gid),'game_object':go,'transform_path_id':str(tid),'transform':tr,'components':components};rows.append(row)
  if len(rows)>6000:raise RuntimeError('bounded UI node cap6000 exceeded')
  for c in tr['m_Children']:
   if c['m_FileID']==0:walk(f,c['m_PathID'],path)
 roots=[]
 for r in stored:
  if r['provenance']['script_class'] not in {'StateCompliment','StateFail','StateTimeUp','StateOutOfBox','StateLevelCompleteTransition'}:continue
  f=r['provenance']['serialized_file'];gid=r['fields']['m_GameObject']['m_PathID'];go=read(f,gid)
  tid=next(c['component']['m_PathID'] for c in go['m_Component'] if objs[(f,c['component']['m_PathID'])].type.name in ('Transform','RectTransform'))
  roots.append({'class':r['provenance']['script_class'],'component_path_id':str(r['provenance']['path_id']),'file':f,'game_object_path_id':str(gid),'transform_path_id':str(tid),'name':go['m_Name']});walk(f,tid)
result={'source':str(src),'boundary':'Exact stored UI trees/native components and existing structured MonoBehaviour exports; no original runtime activation/layout/animations/pixels verified. Sprite metadata only, no new PNG export.','roots':roots,'nodes':rows,'sprites':sprites,'errors':errors}
def encode(v):
 if isinstance(v,(bytes,bytearray)):return {'encoding':'base64','bytes':len(v),'sha256':hashlib.sha256(v).hexdigest(),'data':base64.b64encode(v).decode('ascii')}
 raise TypeError(type(v).__name__)
(out/'ui_native_nodes.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=encode),encoding='utf-8');print('roots',len(roots),'nodes',len(rows),'spriteRefs',len(sprites),'errors',len(errors));print([(r['class'],r['file'],r['name']) for r in roots])
