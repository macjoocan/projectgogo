from pathlib import Path
import json,zipfile,hashlib,UnityPy
p=Path(__file__).resolve().parent;out=p/'ending_spine_audit_20261015';out.mkdir(exist_ok=True);payload=out/'payload';payload.mkdir(exist_ok=True)
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};files={o.assets_file.name:o.assets_file for o in env.objects};idx={}
for l in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
 r=json.loads(l);idx[(r['serialized_file'],r['path_id'])]=r
records=[];links=[];exports=[]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 def read(key):
  ob=objs[key];r=idx.get(key,{})
  d=json.loads(z.read(r['json_file'])) if ob.type.name=='MonoBehaviour' and r.get('json_file') else ob.read_typetree()
  records.append({'file':key[0],'path_id':str(key[1]),'type':ob.type.name,'native_index':r,'raw_sha256':hashlib.sha256(ob.get_raw_data()).hexdigest(),'fields':d});return d
 def resolve(f,r,label):
  fileid=r['m_FileID'];target=f
  if fileid:target=files[f].externals[fileid-1].path.replace('\\','/').split('/')[-1]
  key=(target,r['m_PathID']);links.append({'label':label,'from_file':f,'pptr':r,'target_file':target,'target_path_id':str(key[1])});assert key in objs;return key
 def text(key,label):
  d=read(key);v=d['m_Script'];b=v if isinstance(v,bytes) else v.encode('utf-8',errors='surrogateescape');ext='.json' if b.lstrip().startswith(b'{') else ('.atlas' if label=='atlas' else '.skel.bytes');fn=label+'_'+str(key[1])+ext;(payload/fn).write_bytes(b);rec={'kind':'TextAsset','file':key[0],'path_id':str(key[1]),'name':d['m_Name'],'output':'payload/'+fn,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};exports.append(rec);print(label,rec['name'],len(b));return b
 sg=read(('level2',26899));sk=resolve('level2',sg['skeletonDataAsset'],'SkeletonGraphic.skeletonDataAsset');sd=read(sk)
 for field in ('m_Material','additiveMaterial','multiplyMaterial','screenMaterial'):
  if sg.get(field,{}).get('m_PathID'):read(resolve('level2',sg[field],'SkeletonGraphic.'+field))
 skeleton=text(resolve(sk[0],sd['skeletonJSON'],'SkeletonDataAsset.skeletonJSON'),'skeleton')
 skeleton_summary=None
 if skeleton.lstrip().startswith(b'{'):
  sj=json.loads(skeleton);skeleton_summary={'skeleton':sj.get('skeleton'),'animations':list(sj.get('animations',{})),'bones':len(sj.get('bones',[])),'slots':len(sj.get('slots',[]))}
 seenmat=set();seentex=set()
 for ar in sd['atlasAssets']:
  ak=resolve(sk[0],ar,'SkeletonDataAsset.atlasAssets');ad=read(ak);text(resolve(ak[0],ad['atlasFile'],'SpineAtlasAsset.atlasFile'),'atlas')
  for mr in ad['materials']:
   mk=resolve(ak[0],mr,'SpineAtlasAsset.materials')
   if mk in seenmat:continue
   seenmat.add(mk);mat=read(mk)
   for slot,te in mat['m_SavedProperties']['m_TexEnvs']:
    if not te['m_Texture']['m_PathID']:continue
    tk=resolve(mk[0],te['m_Texture'],'Material.'+slot)
    if tk in seentex:continue
    seentex.add(tk);td=read(tk);fn='texture_'+str(tk[1])+'.png';objs[tk].read().image.save(payload/fn);png=payload/fn;exports.append({'kind':'Texture2D_RGBA_PNG','file':tk[0],'path_id':str(tk[1]),'name':td['m_Name'],'output':'payload/'+fn,'bytes':png.stat().st_size,'sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
def enc(v):
 if isinstance(v,(bytes,bytearray)):return {'opaque_bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}
 raise TypeError(type(v).__name__)
result={'boundary':'Exact original stored PPtr chain, TextAsset payload and decoded Texture2D PNG; original source unchanged, no Spine runtime/GPU playback parity verified. Texture native opaque bytes summarized with hash; retained in original native raw archive.','links':links,'records':records,'exports':exports,'skeleton_summary':skeleton_summary}
(out/'chain.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8');print('records',len(records),'exports',len(exports),'skeleton',skeleton_summary)
