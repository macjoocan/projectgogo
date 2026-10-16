from pathlib import Path
import json,zipfile,hashlib,collections
p=Path(__file__).resolve().parent; out=p/'fx_existing_audit_20261015';out.mkdir(exist_ok=True)
ui=json.loads((p/'end_flow_audit_20261015/ui_native_nodes.json').read_text(encoding='utf-8'))
uirows=[n for n in ui['nodes'] if any(c['type'] in ('ParticleSystem','ParticleSystemRenderer') or c.get('script_class')=='UIParticle' for c in n['components'])]
player=json.loads((p/'ingame_handoff_20261014/player_native_visual_physics_chain.json').read_text(encoding='utf-8'))
gos={int(n['transform']['m_GameObject']['m_PathID']) for n in player['nodes']}
records=[]; materialkeys=set(); textureptrs=[]
index=[json.loads(s) for s in (p/'results/native_object_index.jsonl').open(encoding='utf-8')]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 for r in index:
  if r.get('serialized_file')!='sharedassets3.assets' or not r.get('json_file'):continue
  if r.get('type') not in ('ParticleSystem','ParticleSystemRenderer') and r.get('script_class')!='PlayerFxComponent':continue
  raw=z.read(r['json_file']); fields=json.loads(raw)
  if fields.get('m_GameObject',{}).get('m_PathID') not in gos:continue
  records.append(dict(provenance=r,json_sha256=hashlib.sha256(raw).hexdigest(),fields=fields))
 for n in uirows:
  for c in n['components']:
   if c['type']=='ParticleSystemRenderer':
    for ref in c['fields'].get('m_Materials',[]):
     if ref.get('m_FileID')==0 and ref.get('m_PathID'):materialkeys.add((n['file'],ref['m_PathID']))
 for rec in records:
  if rec['provenance']['type']=='ParticleSystemRenderer':
   for ref in rec['fields'].get('m_Materials',[]):
    if ref.get('m_FileID')==0 and ref.get('m_PathID'):materialkeys.add(('sharedassets3.assets',ref['m_PathID']))
 materials=[]
 for r in index:
  if r.get('type')!='Material' or (r.get('serialized_file'),r.get('path_id')) not in materialkeys or not r.get('json_file'):continue
  raw=z.read(r['json_file']); fields=json.loads(raw);materials.append(dict(provenance=r,json_sha256=hashlib.sha256(raw).hexdigest(),fields=fields))
data=dict(boundary='Existing exports only. Native references retained. External fileID, TextureSheetAnimation sprite refs, texture PNG identity and runtime/GPU equivalence require further join; no name-only PNG assertion.',ui_fx_nodes=uirows,player_records=records,local_material_records=materials,local_material_keys=sorted(materialkeys))
(out/'existing_fx_records.json').write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf-8')
print('ui_nodes',len(uirows),'ui_types',dict(collections.Counter(c['type'] for n in uirows for c in n['components'])),'player_types',dict(collections.Counter(r['provenance'].get('script_class') or r['provenance']['type'] for r in records)),'local_materials',len(materials),'output_bytes',(out/'existing_fx_records.json').stat().st_size)
for n in uirows:
 if any(c.get('script_class')=='UIParticle' for c in n['components']):print('UIParticle',n['file'],n['path'],[(c['path_id'],c['fields']) for c in n['components'] if c.get('script_class')=='UIParticle'])
