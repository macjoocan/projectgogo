from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(R),str(R/'cdn_extraction_deps')]
import export_ingame_art_assets_20260928 as ex
from audit_ingame_scene_ui_20260928 import Reader,HEADER
O=Path(__file__).resolve().parent
file='assets/bin/Data/95094b71c5d0049f188cddc77bd37f68'
env,obs=ex.load_apk(file)
ob=obs[142]; raw=ob.get_raw_data();r=Reader(raw)
header=r.fields_read(HEADER)
schema=[('m_endA','ptr'),('m_endB','ptr'),('m_extraLength','f'),('m_visualExtensionA','f'),('m_segmentCount','i'),('m_ropeRadius','f'),('m_segmentMass','f'),('m_rigidLinks','bool'),('m_linearSpring','f'),('m_linearDamper','f'),('m_maxStretch','f'),('m_bendSpring','f'),('m_bendDamper','f'),('m_solverIterations','i'),('m_solverVelocityIterations','i'),('m_linearDamping','f'),('m_angularDamping','f'),('m_loadMassEqualization','f'),('m_segmentGravityScale','f'),('m_sleepOnSpawn','bool'),('m_maxAngularVelocity','f'),('m_maxLinearVelocity','f'),('m_segmentMesh','ptr'),('m_ropeMaterial','ptr')]
values=r.fields_read(schema)
assert r.p==len(raw),(r.p,len(raw))
refs={}
for k,p in dict(header,**values).items():
 if not isinstance(p,dict):continue
 other=ex.resolve(ob,p)
 if other is None:refs[k]=None;continue
 refs[k]=dict(**ex.identity(other),type=other.type.name,data=other.read_typetree(check_read=False))
 if other.type.name=='Transform':
  go=ex.resolve(other,refs[k]['data']['m_GameObject'])
  refs[k]['game_object']=dict(**ex.identity(go),data=go.read_typetree())
out=dict(evidence_grade='original serialized values',source=ex.identity(ob),header=header,values=values,fields=r.fields,byte_count=len(raw),consumed=r.p,sha256=hashlib.sha256(raw).hexdigest(),references=refs)
(O/'rope_saved_values.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=lambda x:{'bytes_hex':x.hex()} if isinstance(x,bytes) else str(x)),encoding='utf8')
(O/'rope_142.bin').write_bytes(raw)
print(json.dumps(dict(values=values,consumed=r.p,bytes=len(raw)),indent=2))
