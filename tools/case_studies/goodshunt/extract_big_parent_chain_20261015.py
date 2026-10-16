from pathlib import Path
import json, hashlib, UnityPy
p=Path(__file__).resolve().parent
src=p/'input_prepared/assets/aa/Android/props_assets_all_8cfb9dc23d45f5ca0c92cd5f38151ff7.bundle'
out=p/'drop_gauge_audit_20261015'
env=UnityPy.load(str(src)); f='CAB-5388c821bd9df28739ab71fc81803c09'
objs={o.path_id:o for o in env.objects if o.assets_file.name==f}; cache={}
def read(pid):
 if pid not in cache: cache[pid]=objs[pid].read_typetree()
 return cache[pid]
def tid(go):
 return next(c['component']['m_PathID'] for c in go['m_Component'] if objs[c['component']['m_PathID']].type.name=='Transform')
def walk(t,path=''):
 d=read(t);g=read(d['m_GameObject']['m_PathID']);path=path+'/'+g['m_Name'];cs=[]
 for c in g['m_Component']:
  o=objs[c['component']['m_PathID']]
  if o.type.name in ('CapsuleCollider','BoxCollider','SphereCollider','MeshCollider','Rigidbody','MeshFilter'):
   cs.append({'type':o.type.name,'path_id':str(o.path_id),'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'data':read(o.path_id)})
 return {'path':path,'game_object_path_id':str(d['m_GameObject']['m_PathID']),'layer':g['m_Layer'],'active':g['m_IsActive'],'transform_path_id':str(t),'transform':d,'components':cs,'children':[walk(c['m_PathID'],path) for c in d['m_Children'] if c['m_FileID']==0]}
roots=set();hits=[]
for pid,o in objs.items():
 if o.type.name!='GameObject':continue
 g=read(pid);n=g['m_Name']
 if not any(s.lower() in n.lower() for s in ('Kiwano','Mango_Red','Starfruit')):continue
 t=tid(g);r=t;seen=set()
 while r not in seen:
  seen.add(r);parent=read(r)['m_Father']
  if parent['m_FileID'] or not parent['m_PathID']:break
  r=parent['m_PathID']
 roots.add(r);hits.append({'name':n,'game_object_path_id':str(pid),'root_transform_path_id':str(r)})
result={'grade':'original_stored_value','source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'serialized_file':f,'selection':'Name candidates; native PPtr ancestry exact. UID identity remains separate. No runtime execution.','hits':hits,'roots':[walk(r) for r in sorted(roots)]}
(out/'big_prop_parent_chains.json').write_text(json.dumps(result,ensure_ascii=False,indent=1),encoding='utf-8')
print('hits',len(hits),'roots',len(roots))
for r in result['roots']:
 print(r['path'],r['transform']['m_LocalScale'])
