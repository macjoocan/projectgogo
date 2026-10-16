import json,UnityPy,zipfile,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'code_audit_20261014';env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};f='sharedassets3.assets'
chain=json.loads((p/'ingame_handoff_20261014/player_native_visual_physics_chain.json').read_text());nodes={n['transform_path_id']:n for n in chain['nodes']};hits=[]
for n in nodes.values():
 cs=[c for c in n['components'] if c['type'].endswith('Collider') and c['fields'].get('m_IsTrigger')]
 if not cs:continue
 t=n['transform'];gid=t['m_GameObject']['m_PathID'];go=objs[(f,gid)].read_typetree();parents=[];cur=n['transform_path_id'];visited=set()
 while cur in nodes and cur not in visited:
  visited.add(cur);node=nodes[cur];parents.append({'name':node['name'],'transform_path_id':cur,'transform':node['transform']});cur=node['transform']['m_Father']['m_PathID']
 hits.append({'name':n['name'],'file':f,'game_object_path_id':gid,'layer':go['m_Layer'],'active':go['m_IsActive'],'colliders':cs,'transform_chain_child_to_root':parents})
scriptrefs=[]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
  r=json.loads(line)
  if r.get('script_class') in ['PropPuller','GroundBehavior','GroundMesh','PropActiveCounter','PropAutoSleep'] and r.get('json_file'):
   scriptrefs.append({'source':r,'fields':json.loads(z.read(r['json_file']))})
(out/'hole_trigger_native_chain.json').write_text(json.dumps({'grade':'original_stored_value','triggers':hits,'related_components':scriptrefs},ensure_ascii=False,indent=1),encoding='utf-8')
for h in hits:print(h['name'],'layer',h['layer'],'parents',[(x['name'],x['transform']['m_LocalScale']) for x in h['transform_chain_child_to_root']])
print('components',len(scriptrefs))
