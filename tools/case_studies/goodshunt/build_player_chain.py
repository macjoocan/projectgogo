import json,hashlib,UnityPy
from pathlib import Path
p=Path(__file__).resolve().parent
out=p/'ingame_handoff_20261014'
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'))
objs={(o.assets_file.name,o.path_id):o for o in env.objects}
f='sharedassets3.assets'
rows=[];seen=set();queue=[705]
while queue:
 tid=queue.pop(0)
 if tid in seen:continue
 seen.add(tid); t=objs[(f,tid)].read_typetree(); go=objs[(f,t['m_GameObject']['m_PathID'])].read_typetree()
 row={'file':f,'transform_path_id':tid,'name':go['m_Name'],'transform':t,'components':[]}
 for c in go['m_Component']:
  ptr=c['component'];o=objs.get((f,ptr['m_PathID']))
  if o and o.type.name in ['MeshFilter','MeshRenderer','SkinnedMeshRenderer','SphereCollider','BoxCollider','CapsuleCollider','MeshCollider','Rigidbody']:
   fields=o.read_typetree(); row['components'].append({'type':o.type.name,'path_id':o.path_id,'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'fields':fields})
 rows.append(row)
 queue.extend(x['m_PathID'] for x in t['m_Children'] if x['m_FileID']==0)
(out/'player_native_visual_physics_chain.json').write_text(json.dumps({'grade':'original_stored_value','root_game_object':609,'root_transform':705,'nodes':rows},ensure_ascii=False,indent=1),encoding='utf-8')
print('nodes',len(rows),'components',sum(len(r['components']) for r in rows))
