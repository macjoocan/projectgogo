from pathlib import Path
import json, zipfile, hashlib, collections, gc, sys, base64, math
import UnityPy
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[1] / 'levelscope-publish-20261014'))
from levelscope import typetree
import cached_reader
base = root / 'input_prepared'
out = root / 'results'
out.mkdir(exist_ok=True)
supplement = '--supplement' in sys.argv
ldplayer = '--ldplayer' in sys.argv
paths = [base/'assets/bin/Data/data.unity3d', base/'assets/bin/Data/unity default resources']
paths += [p for p in sorted((base/'assets/aa/Android').glob('*.bundle')) if not p.name.startswith('levels_assets_')]
if supplement:
    out = out / 'supplement'
    out.mkdir(exist_ok=True)
    paths = list(sorted((base/'assets/Android').glob('preload_*'))) + [base/'assets/aa/catalog.bundle']
if ldplayer:
    out = root/'ldplayer/results'
    out.mkdir(parents=True,exist_ok=True)
    paths=list(sorted((root/'ldplayer/analysis_input').glob('*.bundle')))
counts = collections.Counter()
decoded = collections.Counter()
failures = []
registry = typetree.ScriptRegistry()
mono = None
selected = {'MonoBehaviour','MonoScript','Mesh','Material','PhysicMaterial','AnimationClip',
            'AnimatorController','AnimatorOverrideController','Avatar','ParticleSystem',
            'ParticleSystemRenderer','MeshRenderer','SkinnedMeshRenderer','MeshFilter','SpriteRenderer',
            'BoxCollider','SphereCollider','MeshCollider','CapsuleCollider','Rigidbody','Camera','Light',
            'RenderSettings','PhysicsManager','TimeManager','QualitySettings','PlayerSettings','GraphicsSettings',
            'Sprite','SpriteAtlas','AssetBundle'}
selected.update({'Shader','ComputeShader','NavMeshData','TerrainData'})
if supplement or ldplayer: selected.add('TextAsset')
if ldplayer:
    original=UnityPy.load(str(base/'assets/bin/Data/data.unity3d'))
    registry.add_env(original,'data.unity3d',alias='data.unity3d')
    del original
    gc.collect()
def clean(v):
    if isinstance(v, bytes): return {'__bytes_base64__':base64.b64encode(v).decode('ascii')}
    if isinstance(v, float) and not math.isfinite(v): return {'__nonfinite_float__':str(v)}
    if isinstance(v, dict): return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v, (list,tuple)): return [clean(x) for x in v]
    return v
with zipfile.ZipFile(out/'GoodsHunt_native_raw.zip','w',zipfile.ZIP_DEFLATED) as rawz, \
     zipfile.ZipFile(out/'GoodsHunt_structured_objects.zip','w',zipfile.ZIP_DEFLATED) as jsonz, \
     zipfile.ZipFile(out/'GoodsHunt_meshes_obj.zip','w',zipfile.ZIP_DEFLATED) as meshz, \
     (out/'native_object_index.jsonl').open('w',encoding='utf-8') as index:
    for number,p in enumerate(paths,1):
        try:
            env=UnityPy.load(str(p))
            registry.add_env(env, p.name, alias=p.name)
            if mono is None:
                mono = typetree.open_reader(str(base), {}, '2022.3.62f2', registry=registry)
            source=p.relative_to(root/'ldplayer/analysis_input' if ldplayer else base).as_posix()
            sh=hashlib.sha256(p.read_bytes()).hexdigest()
            for obj in env.objects:
                kind=obj.type.name
                counts[kind]+=1
                if kind not in selected: continue
                file=obj.assets_file.name
                key=f'{number:04d}/{hashlib.sha256(str(file).encode()).hexdigest()[:12]}/{kind}/{obj.path_id}'
                raw=obj.get_raw_data()
                rawz.writestr(key+'.bin',raw)
                row=dict(source=source, source_sha256=sh, serialized_file=file, path_id=obj.path_id,
                         type=kind, raw_file=key+'.bin', raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest())
                try:
                    if kind == 'MonoBehaviour':
                        cls, data = mono.read(obj)
                        row['script_class'] = cls
                        if data is None:
                            raise ValueError('custom fields unresolved; raw object preserved')
                    else:
                        data=obj.read_typetree()
                    row['name']=data.get('m_Name') if isinstance(data,dict) else None
                    content=json.dumps(clean(data),ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8','backslashreplace')
                    jsonz.writestr(key+'.json',content)
                    row['json_file']=key+'.json'
                    decoded[kind]+=1
                except Exception as e:
                    row['decode_error']=repr(e)
                    failures.append(dict(source=source,file=file,path_id=obj.path_id,type=kind,operation='typetree',error=repr(e)))
                if kind=='Mesh':
                    try:
                        text=obj.read().export()
                        meshz.writestr(key+'.obj',text)
                        row['obj_file']=key+'.obj'
                    except Exception as e:
                        row['mesh_export_error']=repr(e)
                        failures.append(dict(source=source,file=file,path_id=obj.path_id,type=kind,operation='obj',error=repr(e)))
                index.write(json.dumps(row,ensure_ascii=False)+'\n')
            del env
            gc.collect()
        except Exception as e:
            failures.append(dict(source=str(p),operation='source',error=repr(e)))
        print(number,len(paths),p.name,'mesh',counts['Mesh'],'decodedMB',decoded['MonoBehaviour'],flush=True)
(root/('ldplayer/native_export_summary.json' if ldplayer else 'native_supplement_summary.json' if supplement else 'native_export_summary.json')).write_text(json.dumps(dict(source_count=len(paths),types=dict(counts),decoded_types=dict(decoded),header_checks=cached_reader.header_checks,failures=failures,limits='OBJ uses UnityPy export coordinate convention; raw Mesh and vertex payload remain separately preserved. JSON byte arrays use explicit base64 wrappers. Undecoded custom fields remain raw, not absent.'),ensure_ascii=False,indent=1),encoding='utf-8')
print('DONE',dict(counts),dict(decoded),'failures',len(failures))
