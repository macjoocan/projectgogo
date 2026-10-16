from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;source=p/'extract_shader_glsl.py';s=source.read_text(encoding='utf-8')
old="[('omnishade','globalgamemanagers.assets',23),('toony','sharedassets2.assets',589),('worlduv','resources.assets',1175)]"
assert s.count(old)==1
s=s.replace("out=p/'shader_audit_20261014'","out=p/'growth_fx_shader_audit_20261015'")
s=s.replace(old,"[('circles_alpha','sharedassets0.assets',34),('circles_additive','resources.assets',1244),('drop_alpha','unity_builtin_extra',10721),('holy_smoke','resources.assets',1174)]")
exec(compile(s,str(source),'exec'))
o=objs[('sharedassets3.assets',27)];mat=o.read_typetree();ref=mat['m_Shader'];file='sharedassets3.assets'
if ref['m_FileID']:file=o.assets_file.externals[ref['m_FileID']-1].path.replace('\\','/').split('/')[-1]
sh=objs.get((file,ref['m_PathID']))
rec=dict(material_file='sharedassets3.assets',material_id=27,material=mat,shader_file=file,shader_id=ref['m_PathID'],shader_raw_sha256=None if sh is None else hashlib.sha256(sh.get_raw_data()).hexdigest(),shader_name=None if sh is None else sh.read_typetree()['m_ParsedForm']['m_Name'])
(out/'holy_smoke_shader_identity.json').write_text(json.dumps(rec,ensure_ascii=False,indent=1),encoding='utf-8');print('HOLY',file,ref['m_PathID'],rec['shader_name'])
textures=[]
for slot,v in mat['m_SavedProperties']['m_TexEnvs']:
 ptr=v['m_Texture']
 if not ptr['m_PathID']:continue
 file='sharedassets3.assets'
 if ptr['m_FileID']:file=o.assets_file.externals[ptr['m_FileID']-1].path.replace('\\','/').split('/')[-1]
 tex=objs[(file,ptr['m_PathID'])];td=tex.read_typetree();im=tex.read().image;fn=f'{file}_{tex.path_id}_texture.png';im.save(out/fn)
 textures.append(dict(slot=slot,file=file,path_id=str(tex.path_id),name=td['m_Name'],raw_sha256=hashlib.sha256(tex.get_raw_data()).hexdigest(),fields={k:v for k,v in td.items() if k not in ('image data','m_ImageData')},png=dict(file=fn,size=im.size,sha256=hashlib.sha256((out/fn).read_bytes()).hexdigest(),pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest())))
(out/'holy_smoke_textures.json').write_text(json.dumps(textures,ensure_ascii=False,indent=1),encoding='utf-8')
print('HOLYTEXTURES',[(r['slot'],r['name'],r['png']['size']) for r in textures])
