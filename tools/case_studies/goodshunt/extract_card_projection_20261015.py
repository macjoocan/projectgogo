from pathlib import Path
import json,hashlib,zipfile,UnityPy
p=Path(__file__).resolve().parent;out=p/'card_projection_audit_20261015';out.mkdir(exist_ok=True)
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};files={o.assets_file.name:o.assets_file for o in env.objects};idx={}
for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
 r=json.loads(line)
 if r.get('json_file'):idx[(r['serialized_file'],r['path_id'])]=r
z=zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip')
def read(k):
 o=objs[k];i=idx.get(k)
 return json.loads(z.read(i['json_file'])) if o.type.name=='MonoBehaviour' and i else o.read_typetree()
def record(k):
 o=objs[k];return dict(file=k[0],path_id=str(k[1]),type=o.type.name,script_class=idx.get(k,{}).get('script_class'),raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest(),fields=read(k))
def resolve(f,ptr):
 return (files[f].externals[ptr['m_FileID']-1].path.replace('\\','/').split('/')[-1] if ptr['m_FileID'] else f,ptr['m_PathID'])
def ancestors(k):
 result=[];seen=set()
 while k[1]:
  assert k not in seen and len(seen)<40;seen.add(k);r=record(k);go=resolve(k[0],r['fields']['m_GameObject']);g=record(go);cs=[record(resolve(go[0],c['component'])) for c in g['fields']['m_Component'] if objs[resolve(go[0],c['component'])].type.name not in ('Transform','RectTransform')];result.append(dict(transform=r,game_object=g,components=cs));k=resolve(k[0],r['fields']['m_Father'])
 return result
canvas=record(('level2',17295));cg=resolve('level2',canvas['fields']['m_GameObject']);ct=next(resolve(cg[0],c['component']) for c in read(cg)['m_Component'] if objs[resolve(cg[0],c['component'])].type.name in ('Transform','RectTransform'))
controller=record(('level2',29706));ctgo=resolve('level2',controller['fields']['m_GameObject']);ctr=next(resolve(ctgo[0],c['component']) for c in read(ctgo)['m_Component'] if objs[resolve(ctgo[0],c['component'])].type.name in ('Transform','RectTransform'))
cameras=[]
for k,o in objs.items():
 if k[0]!='level2' or o.type.name!='Camera':continue
 c=record(k);go=resolve(k[0],c['fields']['m_GameObject']);t=next(resolve(go[0],x['component']) for x in read(go)['m_Component'] if objs[resolve(go[0],x['component'])].type.name in ('Transform','RectTransform'));cameras.append(dict(camera=c,ancestors=ancestors(t)))
result=dict(canvas=canvas,canvas_ancestors=ancestors(ct),controller_ancestors=ancestors(ctr),cameras=cameras,boundary='Stored level2 Canvas17295 and ancestors, Controller29706 ancestors, native Camera objects in level2 only. No runtime transform/canvas layout/Cinemachine state or active renderer assertion.')
def enc(x):
 if isinstance(x,(bytes,bytearray)):return dict(opaque_bytes=len(x),sha256=hashlib.sha256(x).hexdigest())
 raise TypeError(type(x).__name__)
(out/'chains.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8');print('CANVAS',canvas['fields']);print('CAMERAS',[(r['camera']['path_id'],r['ancestors'][0]['game_object']['fields']['m_Name'],r['camera']['fields']) for r in cameras]);print('ANCESTORS',[(r['game_object']['fields']['m_Name'],r['transform']['fields']) for r in result['canvas_ancestors']])
