from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent;R=O.parent
p=R/'destruction_fx_audit/original_effects.json';j=json.loads(p.read_text('utf8'))
objects=[o for o in j['objects'] if 'JamJar' in o['id']]
effects={k:v for k,v in j['effects'].items() if v['source']['name'].startswith('PS_Jar_')}
o=dict(source=str(p),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),scope='Original serialized settings. Invocation is proven separately by native call path; saved BrokenPieces are NOT evidence of runtime spawning.',objects=objects,effects=effects)
(O/'jar_effects_saved.json').write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf8')
print('jar objects',len(objects),'effect packs',len(effects))
for ob in objects:print(ob['id'],ob['explodes'],ob['effects']['impactEffect'],ob['effects']['explosionEffect']['name'])
for k,e in effects.items():
 print(e['source'],[(n['name'],[c['type'] for c in n['components']]) for n in e['nodes']])
