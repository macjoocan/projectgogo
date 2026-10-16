from pathlib import Path
import json,hashlib,UnityPy
p=Path(__file__).resolve().parent;out=p/'end_flow_audit_20261015'/'exact_sprites';out.mkdir(exist_ok=True)
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};o=objs[('resources.assets',1387)];d=o.read_typetree();im=o.read().image;fn='resources_assets_1387_MБz_Btn_Exit.png'.replace('Б','B');im.save(out/fn)
refs=[]
for key in ('texture','alphaTexture'):
 r=d['m_RD'][key]
 if not r['m_PathID']:continue
 f='resources.assets'
 if r['m_FileID']:f=o.assets_file.externals[r['m_FileID']-1].path.replace('\\','/').split('/')[-1]
 t=objs[(f,r['m_PathID'])];td=t.read_typetree();refs.append({'slot':key,'file_id':r['m_FileID'],'file':f,'path_id':str(t.path_id),'raw_sha256':hashlib.sha256(t.get_raw_data()).hexdigest(),'name':td['m_Name'],'width':td['m_Width'],'height':td['m_Height'],'format':td['m_TextureFormat'],'color_space':td.get('m_ColorSpace')})
result={'boundary':'One exact native Sprite via UnityPy Sprite.image, no resize/recenter/repaint. Native float rect and textureRect kept as stored. Decoded PNG is derivative of stored image, raw SHA is separate.','file':'resources.assets','path_id':'1387','name':d['m_Name'],'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'fields':d,'texture_refs':refs,'png':{'file':fn,'size':im.size,'mode':im.mode,'bytes':(out/fn).stat().st_size,'sha256':hashlib.sha256((out/fn).read_bytes()).hexdigest(),'pixel_sha256':hashlib.sha256(im.tobytes()).hexdigest()}}
def enc(x):
 if isinstance(x,(bytes,bytearray)):return {'opaque_bytes':len(x),'sha256':hashlib.sha256(x).hexdigest()}
 raise TypeError(type(x).__name__)
(out/'resources_assets_1387.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8');print('Sprite',d['m_Name'],'PNG',im.size,'rect',d['m_Rect'],'textureRect',d['m_RD']['textureRect'],'refs',refs)
