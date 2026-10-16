from pathlib import Path
import json,hashlib,UnityPy
p=Path(__file__).resolve().parent
out=p/'prop_native_chain_20261014';out.mkdir(exist_ok=True)
request=json.loads(Path('C:/00.SVN/Goodhunt/public/reference/manifest.json').read_text(encoding='utf-8'))['unresolved']
source='assets/aa/Android/props_assets_all_8cfb9dc23d45f5ca0c92cd5f38151ff7.bundle'
src=p/'input_prepared'/source
source_sha=hashlib.sha256(src.read_bytes()).hexdigest()
env=UnityPy.load(str(src));objs={(o.assets_file.name,o.path_id):o for o in env.objects}
f='CAB-5388c821bd9df28739ab71fc81803c09';names={x['node'] for x in request}
cache={}
def read(pid):
 if pid not in cache:cache[pid]=objs[(f,pid)].read_typetree()
 return cache[pid]
def transform(go):
 for c in go['m_Component']:
  ptr=c['component'];o=objs.get((f,ptr['m_PathID']))
  if o and o.type.name=='Transform':return o.path_id
hits=[];roots=set()
for (file,pid),o in objs.items():
 if file!=f or o.type.name!='GameObject':continue
 d=o.read_typetree()
 if d['m_Name'] not in names:continue
 cache[pid]=d;tid=transform(d);root=tid;visited=set()
 while root and root not in visited:
  visited.add(root);parent=read(root)['m_Father']
  if parent['m_FileID'] or not parent['m_PathID']:break
  root=parent['m_PathID']
 roots.add(root);hits.append({'node_name':d['m_Name'],'game_object_path_id':pid,'transform_path_id':tid,'root_transform_path_id':root})
records=[];trees=[];seen=set()
def save(pid):
 if pid in seen:return
 seen.add(pid);o=objs[(f,pid)];d=read(pid);name=d.get('m_Name')
 filename=f'{o.type.name}/{pid}.json';target=out/filename;target.parent.mkdir(exist_ok=True)
 target.write_text(json.dumps(d,ensure_ascii=False,indent=1),encoding='utf-8')
 records.append({'source':source,'source_sha256':source_sha,'serialized_file':f,'path_id':pid,'type':o.type.name,'name':name,'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'raw_bytes':len(o.get_raw_data()),'json_file':filename})
def walk(tid,path=''):
 t=read(tid);gid=t['m_GameObject']['m_PathID'];go=read(gid);path=path+'/'+go['m_Name'];save(tid);save(gid)
 cs=[]
 for c in go['m_Component']:
  ptr=c['component'];o=objs.get((f,ptr['m_PathID']))
  if o and o.type.name in ['MeshFilter','MeshRenderer','SkinnedMeshRenderer','BoxCollider','SphereCollider','CapsuleCollider','MeshCollider','Rigidbody']:
   save(o.path_id);cs.append({'type':o.type.name,'path_id':o.path_id,'fields':read(o.path_id)})
 return {'node_path':path,'name':go['m_Name'],'game_object_path_id':gid,'transform_path_id':tid,'active':go['m_IsActive'],'transform':t,'components':cs,'children':[walk(c['m_PathID'],path) for c in t['m_Children'] if c['m_FileID']==0]}
for root in sorted(roots):trees.append(walk(root))
(out/'native_object_index.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
# Store index as ordinary JSON too, eliminating newline interpretation ambiguity.
(out/'records.json').write_text(json.dumps(records,ensure_ascii=False,indent=1),encoding='utf-8')
(out/'chains.json').write_text(json.dumps({'grade':'original_stored_value','source':source,'source_sha256':source_sha,'request':request,'name_selected_hits':hits,'roots':trees,'boundary':'Names selected candidate nodes only. Actual graph edges use native file/path IDs; runtime activation and UID/GUID root selection remain separate.'},ensure_ascii=False,indent=1),encoding='utf-8')
print('requested',len(request),'matched GO',len(hits),'roots',len(roots),'native records',len(records))
