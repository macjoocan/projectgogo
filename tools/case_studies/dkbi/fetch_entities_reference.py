import urllib.request,tarfile,hashlib,json
from pathlib import Path
r=Path(__file__).parent/'tools/entities_reference_1.4.3';r.mkdir(exist_ok=True)
url='https://download.packages.unity.com/com.unity.entities/-/com.unity.entities-1.4.3.tgz'
p=r/'package.tgz'
with urllib.request.urlopen(url,timeout=30) as response,p.open('wb') as out:
    total=0
    while True:
        b=response.read(65536)
        if not b:break
        total+=len(b)
        if total>24*1024*1024:raise RuntimeError('reference download size cap')
        out.write(b)
names=[]
with tarfile.open(p,'r:gz') as t:
    for m in t:
        if m.isfile() and (m.name.endswith('/TypeHash.cs') or m.name.endswith('/TypeManager.cs') or m.name.endswith('/SerializeUtility.cs') or m.name.endswith('/StaticTypeRegistryPostProcessor.cs') or m.name.endswith('/EntityComponentStore.cs')):
            b=t.extractfile(m).read();q=r/Path(m.name).name;q.write_bytes(b);names.append({'package_path':m.name,'file':q.name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(r/'provenance.json').write_text(json.dumps({'source_url':url,'version':'1.4.3','archive_bytes':p.stat().st_size,'archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':names,'limitations':['Reference version not yet matched to original package; original byte validation required.','Downloaded source only; not installed into Unity or system.']},indent=2),encoding='utf-8')
print(json.dumps(names))
