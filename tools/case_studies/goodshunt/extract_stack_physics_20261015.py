from pathlib import Path
import json,hashlib,UnityPy,gc
p=Path(__file__).resolve().parent;out=p/'drop_gauge_audit_20261015'
src=p/'input_prepared/assets/bin/Data/data.unity3d'
env=UnityPy.load(str(src));rows=[]
for o in env.objects:
 if o.type.name in ('PhysicsManager','TimeManager'):
  rows.append({'source':str(src),'file':o.assets_file.name,'path_id':str(o.path_id),'type':o.type.name,'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'data':o.read_typetree()})
(out/'stack_physics_settings.json').write_text(json.dumps(rows,indent=1),encoding='utf-8');print([(r['type'],r['file'],r['path_id']) for r in rows])
del env;gc.collect()
s=(p/'extract_big_parent_chain_20261015.py').read_text(encoding='utf-8')
s=s.replace("('Kiwano','Mango_Red','Starfruit')","('Plum_Red_Whole','Apple')").replace("any(s.lower() in n.lower() for s in ('Plum_Red_Whole','Apple'))","n in ('Plum_Red_Whole','Apple')").replace('big_prop_parent_chains.json','stack_prop_parent_chains.json')
exec(compile(s,str(p/'extract_big_parent_chain_20261015.py'),'exec'))
