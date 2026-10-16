from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;source=p/'extract_shader_glsl.py';s=source.read_text(encoding='utf-8')
old="[('omnishade','globalgamemanagers.assets',23),('toony','sharedassets2.assets',589),('worlduv','resources.assets',1175)]"
assert s.count(old)==1
s=s.replace("out=p/'shader_audit_20261014'","out=p/'prop_shader_audit_20261015'")
s=s.replace("p/'input_prepared/assets/bin/Data/data.unity3d'","p/'input_prepared/assets/aa/Android/propsdependencies_assets_assets_omnishade_shaders_omnishadeurp.shader_252f808c015943bc0904a80b2aa1ec4d.bundle'")
s=s.replace(old,"[('prop_omnishade','CAB-132b7aa310b4a64d3f77f2b71c0dbd0c',-8143037723478795692)]")
exec(compile(s,str(source),'exec'))
new=json.loads((out/'inventory.json').read_text(encoding='utf-8'))[0];old=json.loads((p/'shader_audit_20261014/inventory.json').read_text(encoding='utf-8'))[0]
def flat(r):return [x for seg in r['segments'] for x in seg['programs']]
a=flat(old);b=flat(new);sa={x['sha256'] for x in a};sb={x['sha256'] for x in b};ka={(tuple(x['keywords'] or []),x['sha256']) for x in a};kb={(tuple(x['keywords'] or []),x['sha256']) for x in b}
comparison={'old_name':old['name'],'new_name':new['name'],'old_raw_sha':old['raw_sha256'],'new_raw_sha':new['raw_sha256'],'old_programs':len(a),'new_programs':len(b),'unique_sha_old':len(sa),'unique_sha_new':len(sb),'common_unique_code_sha':len(sa&sb),'common_keyword_sha_pairs':len(ka&kb),'only_new_keyword_sha_pairs':len(kb-ka),'only_old_keyword_sha_pairs':len(ka-kb),'boundary':'Compiler text byte equality only; no full shader equivalence or runtime variant/material/GPU parity claim.'}
(out/'comparison.json').write_text(json.dumps(comparison,indent=1),encoding='utf-8');print(json.dumps(comparison))
