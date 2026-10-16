import json,mmap,struct
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected'
base=Path(r'D:\99.기타\out_dkbi\source')
selected=[]
with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as f:
    for line in f:
        t=json.loads(line)
        if (t['ns']=='Unity.Entities.CodeGeneratedRegistry') or t['name']=='AssemblyTypeRegistry' or (t['index'] in {26493,26533}) or (t['name'] in {'LocalTransform','LocalToWorld','RenderMeshArray','TypeManager','TypeInfo','Chunk'} and t['ns'].startswith('Unity.')):
            selected.append(t)
(out/'registration_metadata.json').write_text(json.dumps({'provenance':'verified','types':selected,'limitations':['Declaration records only; no runtime pointer resolution']},ensure_ascii=False,indent=2),encoding='utf-8')
hashes=sorted(set(h for label in ['field_101002','town_100'] for h in json.loads((out/(label+'.json')).read_text('utf-8'))['container']['type_hashes']))
sources=[base/'GameAssembly.dll',base/'dokkaebi_Data/il2cpp_data/Metadata/global-metadata.dat']
report=[]
for p in sources:
    with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
        hits=[]
        for h in hashes:
            needle=bytes.fromhex(h)[::-1];positions=[];start=0
            while True:
                pos=b.find(needle,start)
                if pos<0:break
                positions.append(pos);start=pos+1
            if positions:hits.append({'stable_hash':h,'file_offsets':positions})
        report.append({'provenance':'verified','source':str(p),'file_bytes':len(b),'searched_hash_count':len(hashes),'hits':hits})
(out/'stable_hash_raw_matches.json').write_text(json.dumps({'results':report,'limitations':['An 8-byte occurrence is not by itself a type-name join.','No match does not prove runtime registration absent.']},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'types':len(selected),'hashes':len(hashes),'matched_hashes_by_source':[{'source':x['source'],'hits':len(x['hits'])} for x in report]},ensure_ascii=False))
header=json.loads((r/'metadata/metadata_header.json').read_text('utf-8'))
data_start=header['fieldAndParameterDefaultValueDataOffset']
with sources[1].open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
    blobs=[]
    default_positions=sorted({data_start+struct.unpack_from('<iii',b,header['fieldDefaultValuesOffset']+i*12)[2] for i in range(header['fieldDefaultValuesCount']) if struct.unpack_from('<iii',b,header['fieldDefaultValuesOffset']+i*12)[2]>=0})
    for t in selected:
        if t['name']=='AssemblyTypeRegistry':
            values=[x for x in t['fields'] if x.get('default_value')]
            for i,x in enumerate(values):
                start=data_start+x['default_value']['dataIndex']
                next_start=data_start+values[i+1]['default_value']['dataIndex'] if i+1<len(values) else next((p for p in default_positions if p>start),None)
                hits=[{'stable_hash':z['stable_hash'],'file_offset':p,'offset_from_default_record':p-start} for z in report[1]['hits'] for p in z['file_offsets'] if start<=p and next_start and p<next_start]
                if hits:
                    blobs.append({'image':t['image'],'field':x,'default_record_file_offset':start,'next_default_record_file_offset':next_start,'prefix_hex':b[start:start+64].hex(),'hash_matches':hits})
    (out/'registry_blob_hash_matches.json').write_text(json.dumps({'provenance':'verified','default_data_section_offset':data_start,'blobs':blobs,'limitations':['Blob interval defined by next saved registry default value, not decoded type size','Hash occurrence establishes source constant only; component identity needs registry order/type array mapping']},ensure_ascii=False,indent=2),encoding='utf-8')
    print('BLOB_MATCHES',[(z['image'],len(z['hash_matches']),z['prefix_hex'][:32]) for z in blobs])
for t in selected:
    if t['name']=='TypeInfo' and t['image']=='Unity.Entities.dll':print('TYPEINFO_FIELDS',[x['name'] for x in t['fields']])
for t in selected:
    if t['ns']=='Unity.Entities.CodeGeneratedRegistry':print(t['image'],t['name'],[(x['name'],x.get('default_value')) for x in t['fields']][:8])
