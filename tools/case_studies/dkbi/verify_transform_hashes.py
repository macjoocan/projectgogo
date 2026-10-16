import json,struct,mmap
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected'
selected=[]
with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as f:
    for l in f:
        t=json.loads(l)
        if t['image']=='Unity.Transforms.dll' or (t['ns']=='Unity.Mathematics' and t['name'] in {'float3','float4','float4x4','quaternion'}) or (t['ns']=='System' and t['name']=='Single'):
            selected.append(t)
known={t['ns']+'.'+t['name']:t for t in selected}
layout={'System.Single':[], 'Unity.Mathematics.float3':[('x','System.Single'),('y','System.Single'),('z','System.Single')], 'Unity.Mathematics.float4':[(n,'System.Single') for n in 'xyzw'], 'Unity.Mathematics.quaternion':[('value','Unity.Mathematics.float4')], 'Unity.Mathematics.float4x4':[(n,'Unity.Mathematics.float4') for n in ['c0','c1','c2','c3']], 'Unity.Transforms.LocalToWorld':[('Value','Unity.Mathematics.float4x4')], 'Unity.Transforms.LocalTransform':[('Position','Unity.Mathematics.float3'),('Scale','System.Single'),('Rotation','Unity.Mathematics.quaternion')]}
mask=(1<<64)-1;basis=14695981039346656037;prime=1099511628211
def fnv(b):
    h=basis
    for c in b:h=((h^c)*prime)&mask
    return h
def s(x):return fnv(x.encode('utf-16le'))
def c(h,v):return ((h^v)*prime)&mask
def namehash(n):
    ns,name=n.rsplit('.',1);return c(c(basis,s(ns)),s(name))
def old(n):
    h=namehash(n)
    for _,typ in layout[n]:h=c(h,old(typ))
    return h
zero=fnv(struct.pack('<i',0))
def modern(n):
    image=known[n]['image'].removesuffix('.dll')
    h=c(namehash(n),s(image))
    if n=='System.Single':return h
    h=c(h,zero)
    for i,(_,typ) in enumerate(layout[n]):h=c(h,c(modern(typ),i))
    return h
results=[]
for n,expected in [('Unity.Transforms.LocalToWorld','8e54084ebb177ef0'),('Unity.Transforms.LocalTransform','001f79e44e197fd0')]:
    calculated=f'{c(zero,old(n)):016x}'
    latest=f'{modern(n):016x}'
    results.append({'component_name':n,'expected_hash':expected,'ilpp_legacy_hash':calculated,'runtime_modern_hash':latest,'match':latest==expected or calculated==expected})
for n,fields in layout.items():
    if n=='System.Single':continue
    saved=[f['name'] for f in known[n]['fields']]
    assert [x[0] for x in fields]==saved[:len(fields)],(n,saved)
data={'provenance':'verified' if all(x['match'] for x in results) else 'inferred','reference_source':'tools/entities_reference_1.4.3/CodeGen_TypeHash.cs','algorithm':'ILPP FNV-1a64 UTF-16LE namespace/name, recursively combines instance field type hashes, final combine of FNV1A64(int32 version0) and type hash.','results':results,'layout_input':[{'type':n,'instance_fields':v} for n,v in layout.items()],'original_declarations':selected,'limitations':['Version0 inferred for calculation; exact original hash equality is independent corroboration.','Full runtime Types pointer array still unavailable.','Chunk component offsets not established by this file.']}
(out/'transform_hash_verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results))
