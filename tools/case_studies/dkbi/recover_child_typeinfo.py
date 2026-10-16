import json,struct,mmap,bisect,sys
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';header=json.loads((r/'metadata/metadata_header.json').read_text('utf-8'));data_start=header['fieldAndParameterDefaultValueDataOffset']
child=json.loads((out/'field_101002_child_probe.json').read_text('utf-8'))['selected_child_sections'][0]
hashes=child['container']['type_hashes'] if len(sys.argv)==1 else json.loads(Path(sys.argv[1]).read_text('utf-8'))['type_hashes'];root=json.loads((out/'type_info_candidates.json').read_text('utf-8'));keys=list(root['rows'][0]['interpreted_type_info']);assert len(keys)==23
source=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\il2cpp_data\Metadata\global-metadata.dat');rows=[];unknown=[]
with source.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
    defaults=sorted((data_start+idx,field,typ) for field,typ,idx in [struct.unpack_from('<iii',b,header['fieldDefaultValuesOffset']+i*12) for i in range(header['fieldDefaultValuesCount'])] if idx>=0);positions=[x[0] for x in defaults]
    for h in hashes:
        needle=bytes.fromhex(h)[::-1];hits=[];start=0
        while True:
            pos=b.find(needle,start)
            if pos<0:break
            hits.append(pos);start=pos+1
        candidates=[]
        for hit in hits:
            i=bisect.bisect_right(positions,hit)-1;begin,field,typ=defaults[i];end=defaults[i+1][0] if i+1<len(defaults) else None;pos=hit-24
            if end and pos>=begin and (pos-begin)%104==0 and pos+104<=end:
                vals=dict(zip(keys,struct.unpack_from('<4i3Q16i',b,pos)))
                assert f"{vals['StableTypeHash']:016x}"==h
                assert 0<=vals['SizeInChunk']<=16384 and 0<=vals['TypeSize']<=16384
                candidates.append({'provenance':'inferred','stable_hash':h,'metadata_default_field_index':field,'record_file_offset':pos,'registry_record_index':(pos-begin)//104,'default_record_offset':begin,'next_default_offset':end,'raw_hex':b[pos:pos+104].hex(),'interpreted_type_info':vals})
        if len(candidates)==1:rows.extend(candidates)
        else:unknown.append({'stable_hash':h,'raw_hash_file_offsets':hits,'candidate_count':len(candidates)})
    owners={}
    wanted={x['metadata_default_field_index'] for x in rows}
    with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as lines:
        for line in lines:
            t=json.loads(line)
            for x in t['fields']:
                if x['index'] in wanted:owners[x['index']]={'metadata_type_index':t['index'],'image':t['image'],'namespace':t['ns'],'name':t['name'],'field':x}
    for x in rows:
        owner=owners[x['metadata_default_field_index']];x['owner']=owner;assert owner['name']=='AssemblyTypeRegistry'
data={'provenance':'inferred','source':str(source),'child_guid':child['guid'],'rows':rows,'unresolved_hashes':unknown,'limitations':['Record layout supported by original TypeInfo declarations and byte bounds; component type names not fully mapped.','Registration record order is not recovered .cctor Type[] assignments.']}
(out/('field_child_type_info_candidates.json' if len(sys.argv)==1 else 'field_all_child_type_info_candidates.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'types':len(hashes),'records':len(rows),'unknown':unknown,'summary':[{'hash':x['stable_hash'],'image':x['owner']['image'],'size':x['interpreted_type_info']['SizeInChunk'],'TypeSize':x['interpreted_type_info']['TypeSize'],'recordIndex':x['registry_record_index']} for x in rows]}))
