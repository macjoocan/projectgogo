from pathlib import Path
import hashlib
p=Path(__file__).resolve().parent
source=p/'extract_shader_glsl.py'
s=source.read_text(encoding='utf-8')
old="[('omnishade','globalgamemanagers.assets',23),('toony','sharedassets2.assets',589),('worlduv','resources.assets',1175)]"
assert s.count(old)==1
s=s.replace("out=p/'shader_audit_20261014'","out=p/'shield_shader_audit_20261015'")
s=s.replace(old,"[('shield','sharedassets3.assets',103)]")
s=s.replace(";result=[]", ";result=[]\nmaterial_obj=objs[('sharedassets3.assets',13)];(out/'material13.json').write_text(json.dumps({'file':'sharedassets3.assets','path_id':13,'raw_sha256':hashlib.sha256(material_obj.get_raw_data()).hexdigest(),'fields':material_obj.read_typetree()},ensure_ascii=False,indent=1),encoding='utf-8')")
exec(compile(s,str(source),'exec'))
(out/'extractor_provenance.txt').write_text('Reused GLSL bounded parser '+str(source)+' SHA256 '+hashlib.sha256(source.read_bytes()).hexdigest()+'; selection only sharedassets3.assets Shader103/Material13.\n',encoding='utf-8')
