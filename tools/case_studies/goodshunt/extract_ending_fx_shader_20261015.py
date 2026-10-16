from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent
source=p/'extract_shader_glsl.py';s=source.read_text(encoding='utf-8')
old="[('omnishade','globalgamemanagers.assets',23),('toony','sharedassets2.assets',589),('worlduv','resources.assets',1175)]"
assert s.count(old)==1
s=s.replace("out=p/'shader_audit_20261014'","out=p/'ending_fx_shader_audit_20261015'")
s=s.replace(old,"[('ending_fx','resources.assets',1198)]")
exec(compile(s,str(source),'exec'))
rows=[]
for pid in (1141,842):
 o=objs[('resources.assets',pid)];t=o.read_typetree();d=o.read();im=d.image
 dest=out/f'resources_assets_{pid}.png';im.save(dest)
 fields={k:v for k,v in t.items() if k not in ('image data','m_ImageData')}
 def enc(x):
  if isinstance(x,(bytes,bytearray)):return dict(bytes=len(x),sha256=hashlib.sha256(x).hexdigest())
  raise TypeError(type(x).__name__)
 rows.append(dict(file='resources.assets',path_id=str(pid),name=t['m_Name'],raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest(),fields=fields,png=dict(file=dest.name,size=im.size,mode=im.mode,bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest())))
 (out/f'resources_assets_{pid}.json').write_text(json.dumps(rows[-1],ensure_ascii=False,indent=1,default=enc),encoding='utf-8')
 print('TEXTURE',pid,t['m_Name'],im.size,'colorspace',t.get('m_ColorSpace'),flush=True)
materials=[]
for pid in (100,101):
 o=objs[('resources.assets',pid)];t=o.read_typetree()
 materials.append(dict(file='resources.assets',path_id=str(pid),raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest(),fields=t))
(out/'materials.json').write_text(json.dumps(materials,ensure_ascii=False,indent=1),encoding='utf-8')
