from pathlib import Path
import json,sys,gc
import UnityPy
root=Path(__file__).resolve().parent
base=root/'input_prepared'
files=[base/'assets/bin/Data/data.unity3d',base/'assets/bin/Data/unity default resources']
files+=sorted((base/'assets/aa/Android').glob('*.bundle'))
with (root/'serialized_file_references.jsonl').open('w',encoding='utf-8') as out:
    for i,p in enumerate(files,1):
        env=UnityPy.load(str(p))
        seen=set()
        for o in env.objects:
            sf=o.assets_file
            if id(sf) in seen:continue
            seen.add(id(sf))
            refs=[]
            for n,x in enumerate(sf.externals,1):
                guid=x.guid
                refs.append(dict(file_id=n,path=x.path,guid=guid.hex() if isinstance(guid,bytes) else str(guid),type=x.type))
            out.write(json.dumps(dict(source=p.relative_to(base).as_posix(),serialized_file=sf.name,externals=refs),ensure_ascii=False)+'\n')
        del env;gc.collect()
        if i%200==0:print(i,len(files),flush=True)
print('done',len(files))
