import UnityPy,json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/"code_audit_20261014"
source=p/"input_prepared/assets/bin/Data/data.unity3d"
env=UnityPy.load(str(source));objs={(o.assets_file.name,o.path_id):o for o in env.objects}
obj=objs[("level3",41)];light=obj.read_typetree();go=objs[("level3",light["m_GameObject"]["m_PathID"])].read_typetree()
transforms=[]
for c in go["m_Component"]:
 r=c.get("component",c);ob=objs[("level3",r["m_PathID"])]
 if ob.type.name=="Transform":
  current=ob; seen=set()
  while current.path_id not in seen:
   seen.add(current.path_id);tr=current.read_typetree();g=objs[("level3",tr["m_GameObject"]["m_PathID"])].read_typetree()
   transforms.append({"file":"level3","path_id":current.path_id,"game_object":g,"transform":tr,"raw_sha256":hashlib.sha256(current.get_raw_data()).hexdigest()})
   pid=tr["m_Father"]["m_PathID"]
   if pid==0:break
   current=objs[("level3",pid)]
rows=json.loads((out/"lighting_stored_values.json").read_text());settings=next(r for r in rows if r["source"]["serialized_file"]=="level3" and r["source"]["type"]=="RenderSettings")
report={"grade":"original_stored_value","scene_file":"level3_not_stage_order3","light":{"file":"level3","path_id":41,"raw_sha256":hashlib.sha256(obj.get_raw_data()).hexdigest(),"data":light},"transform_chain_child_to_root":transforms,"render_settings":settings,"boundary":"Stored scene values; runtime uniform SH packing, active loaded scene set and light modifications not observed."}
(out/"level3_light_chain.json").write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding="utf-8")
for t in transforms:print(t["game_object"]["m_Name"],t["path_id"],t["transform"]["m_LocalRotation"],t["transform"]["m_LocalPosition"])
