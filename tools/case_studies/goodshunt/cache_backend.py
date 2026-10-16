from pathlib import Path
import sys, json, zipfile, dataclasses, gc, hashlib
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[1]/'levelscope-publish-20261014'))
from levelscope import typetree
import UnityPy
base=root/'input_prepared'
backend=sys.argv[1]
refsfile=root/'used_script_refs.json'
if not refsfile.exists():
    refs=set()
    reg=typetree.ScriptRegistry()
    paths=[base/'assets/bin/Data/data.unity3d']
    paths += [p for p in sorted((base/'assets/aa/Android').glob('*.bundle')) if not p.name.startswith('levels_assets_')]
    for p in paths:
        env=UnityPy.load(str(p));reg.add_env(env,p.name,alias=p.name)
        for obj in env.objects:
            if obj.type.name=='MonoBehaviour':
                ref=typetree.script_ref(obj,reg)
                if ref:refs.add((ref.assembly,ref.fullname))
        del env;gc.collect()
    refsfile.write_text(json.dumps(sorted(refs)),encoding='utf-8')
refs=json.loads(refsfile.read_text())
reader=typetree.MonoReader.open(str(base),{'backends':[backend]},'2022.3.62f2')
generator=reader._gens[backend]
success=[];failures=[]
with zipfile.ZipFile(root/f'typetrees_{backend}.zip','w',zipfile.ZIP_DEFLATED) as z:
    for i,(assembly,fullname) in enumerate(refs):
        try:
            nodes=[dataclasses.asdict(n) for n in generator.get_nodes(assembly,fullname)]
            if not nodes:raise ValueError('empty nodes')
            entry=f'nodes/{i}.json';z.writestr(entry,json.dumps(nodes))
            success.append(dict(assembly=assembly,fullname=fullname,entry=entry))
        except Exception as e:failures.append(dict(assembly=assembly,fullname=fullname,error=repr(e)))
        if i%100==0:print(backend,i,len(success),len(failures),flush=True)
    metadata=base/'assets/bin/Data/Managed/Metadata/global-metadata.dat'
    il2cpp=base/'lib/armeabi-v7a/libil2cpp.so'
    z.writestr('index.json',json.dumps(dict(backend=backend,unity_version='2022.3.62f2',metadata_sha256=hashlib.sha256(metadata.read_bytes()).hexdigest(),il2cpp_sha256=hashlib.sha256(il2cpp.read_bytes()).hexdigest(),success=success,failures=failures)))
print('DONE',backend,'success',len(success),'failures',len(failures),flush=True)
