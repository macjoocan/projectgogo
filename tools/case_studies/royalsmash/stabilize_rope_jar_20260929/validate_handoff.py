from pathlib import Path
import json,hashlib,re
O=Path(__file__).resolve().parent
checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
r=json.loads((O/'rope_saved_values.json').read_text('utf8'))
raw=(O/'rope_142.bin').read_bytes()
check('Rope serialized payload exactly consumed',r['consumed']==r['byte_count']==len(raw)==160)
check('Rope raw hash matches',hashlib.sha256(raw).hexdigest()==r['sha256'])
check('All serialized fields contiguous',r['fields'][0]['offset']==0 and all(a['end_offset']==b['offset'] for a,b in zip(r['fields'],r['fields'][1:])))
check('7 rods with rigid joints',r['values']['m_segmentCount']==7 and r['values']['m_rigidLinks'])
check('Both endpoints resolved',all(r['references'][k]['type']=='Transform' for k in ['m_endA','m_endB']))
j=json.loads((O/'jar_effects_saved.json').read_text('utf8'))
check('18 exploding jars; no impact effect',len(j['objects'])==18 and all(o['explodes'] and o['effects']['impactEffect'] is None for o in j['objects']))
check('6 jar FX packs each containing 5 ParticleSystems',len(j['effects'])==6 and all(sum(c['type']=='ParticleSystem' for n in e['nodes'] for c in n['components'])==5 for e in j['effects'].values()))
check('All Jar effect references resolve to exported pack',all(o['effects']['explosionEffect']['file']+':'+str(o['effects']['explosionEffect']['path_id']) in j['effects'] for o in j['objects']))
idx=json.loads((O/'asm_index.json').read_text('utf8'))
check('Every indexed disassembly exists',all((O/(k+'.asm')).exists() for k in idx))
check('Requested core RVAs match',idx['Obstacle_StabilizeIsland']['rva']=='0x383ca00' and idx['Platform_FixedUpdate']['rva']=='0x393fc20' and idx['Obstacle_Explode']['rva']=='0x383d600')
for p in O.glob('*.md'):
 check('Korean handoff text '+p.name,not re.search('[\u3040-\u30ff]',p.read_text('utf8')))
result=dict(status='passed',checks=checks,asm_methods=len(idx),engine_runtime_tested=False)
(O/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
