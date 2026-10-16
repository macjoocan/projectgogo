from pathlib import Path
import json,hashlib,UnityPy
p=Path(__file__).resolve().parent;out=p/'booster_goal_audit_20261015';records=json.loads((out/'stored_components.json').read_text(encoding='utf-8'))['records']
src=p/'input_prepared/assets/bin/Data/data.unity3d';env=UnityPy.load(str(src));objs={(o.assets_file.name,o.path_id):o for o in env.objects}
def rd(f,pid):return objs[(f,pid)].read_typetree()
def gettr(f,g):
 for c in g['m_Component']:
  o=objs[(f,c['component']['m_PathID'])]
  if o.type.name in ('RectTransform','Transform'):return o.path_id
rows=[]
for rr in records:
 if rr['provenance']['script_class'] not in ('GrowthButton','CompassButton','MagnetButton','FreezeButton','ShieldButton'):continue
 f=rr['provenance']['serialized_file'];gid=rr['fields']['m_GameObject']['m_PathID'];g=rd(f,gid);tid=gettr(f,g);parents=[];t=tid
 while t:
  d=rd(f,t);go=rd(f,d['m_GameObject']['m_PathID']);o=objs[(f,t)];parents.append({'name':go['m_Name'],'game_object_id':str(d['m_GameObject']['m_PathID']),'active':go['m_IsActive'],'transform_id':str(t),'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'fields':d});father=d['m_Father']
  if father['m_FileID']:break
  t=father['m_PathID']
 rows.append({'class':rr['provenance']['script_class'],'file':f,'component_id':str(rr['provenance']['path_id']),'button_name':g['m_Name'],'parent_chain':parents})
(out/'native_ui_button_chains.json').write_text(json.dumps({'source':str(src),'grade':'original_stored_values','buttons':rows},ensure_ascii=False,indent=1),encoding='utf-8')
for r in rows:print(r['class'],[(x['name'],x['fields'].get('m_AnchoredPosition'),x['fields']['m_LocalPosition']) for x in r['parent_chain'][:3]])
