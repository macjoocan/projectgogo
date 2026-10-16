from pathlib import Path
import re,json,hashlib,collections
p=Path(__file__).resolve().parent;rows=[];errors=[]
for f in sorted((p/'raw').rglob('*')):
 if f.suffix not in ('.md5anim','.md5mesh'):continue
 s=f.read_text();r=dict(path=str(f.relative_to(p)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),format=f.suffix[1:]);r['bones']=int(re.search(r'numJoints\s+(\d+)',s)[1]);key='hierarchy' if f.suffix=='.md5anim' else 'joints';block=re.search(key+r'\s*\{(.*?)\}',s,re.S)[1];names=re.findall(r'"(.*?)"',block);r['bone_names']=names;r['bone_names_sha256']=hashlib.sha256(json.dumps(names).encode()).hexdigest();assert len(names)==r['bones']
 if f.suffix=='.md5anim':
  r['frames']=int(re.search(r'numFrames\s+(\d+)',s)[1]);r['fps']=float(re.search(r'frameRate\s+(\S+)',s)[1]);r['sample_span_seconds']=(r['frames']-1)/r['fps'];r['sequence_name']=f.stem;r['animset']=f.parent.name;r['frame_blocks']=len(re.findall(r'\bframe\s+\d+\s*\{',s));assert r['frame_blocks']==r['frames'];r['parent_indices_exported']=[int(x) for x in re.findall(r'".*?"\s+(-?\d+)',block)]
 else:
  r['parent_indices']=[int(x) for x in re.findall(r'".*?"\s+(-?\d+)',block)];r['mesh_sections']=int(re.search(r'numMeshes\s+(\d+)',s)[1]);r['vertices']=sum(map(int,re.findall(r'numverts\s+(\d+)',s)));r['triangles']=sum(map(int,re.findall(r'numtris\s+(\d+)',s)));r['weights']=sum(map(int,re.findall(r'numweights\s+(\d+)',s)))
 rows.append(r)
(p/'motion_model_catalog.json').write_text(json.dumps(rows,indent=1),encoding='utf-8')
an=[x for x in rows if x['format']=='md5anim'];me=[x for x in rows if x['format']=='md5mesh'];byhash=collections.defaultdict(list)
for r in rows:byhash[r['sha256']].append(r['path'])
(p/'duplicate_groups.json').write_text(json.dumps({k:v for k,v in byhash.items() if len(v)>1},indent=1),encoding='utf-8')
inv=json.loads((p/'package_inventory.json').read_text());summary=dict(packages_scanned=len(inv),packages_with_targets=sum(bool(x['objects']) for x in inv),export_errors=[x['relative'] for x in inv if x.get('export_error') or x.get('export_exit',0)!=0],list_errors=[x['relative'] for x in inv if x['list_error']],model_files=len(me),animation_files=len(an),unique_model_sha=len({x['sha256'] for x in me}),unique_animation_sha=len({x['sha256'] for x in an}),unique_animation_names=len({x['sequence_name'] for x in an}),total_exported_bytes=sum(x['bytes'] for x in rows),bone_name_match_only_not_parity=True)
(p/'extraction_summary.json').write_text(json.dumps(summary,indent=1),encoding='utf-8');print(json.dumps(summary))
