import json,struct,mmap,bisect
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';h=json.loads((r/'metadata/metadata_header.json').read_text('utf-8'))
p=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\il2cpp_data\Metadata\global-metadata.dat')
data_start=h['fieldAndParameterDefaultValueDataOffset'];record_candidates=[]
with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
    defaults=[struct.unpack_from('<iii',b,h['fieldDefaultValuesOffset']+i*12) for i in range(h['fieldDefaultValuesCount'])]
    defaults=sorted((data_start+idx,field,typ) for field,typ,idx in defaults if idx>=0)
    positions=[v[0] for v in defaults]
    matches=json.loads((out/'stable_hash_raw_matches.json').read_text('utf-8'))['results'][1]['hits']
    for x in matches:
        at=x['file_offsets'][0];i=bisect.bisect_right(positions,at)-1;start,field,typ=defaults[i];end=defaults[i+1][0] if i+1<len(defaults) else None
        record_candidates.append({'stable_hash':x['stable_hash'],'source_hash_file_offsets':x['file_offsets'],'nearest_preceding_default_field_index':field,'default_type_index':typ,'default_record_offset':start,'next_default_record_offset':end,'offset_from_default':at-start})
    interfaces=[]
    wanted={x['nearest_preceding_default_field_index'] for x in record_candidates};owners=[]
    with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as lines:
        for l in lines:
            t=json.loads(l)
            relevant=[x for x in t['fields'] if x['index'] in wanted]
            if relevant:owners.append({'type_index':t['index'],'image':t['image'],'namespace':t['ns'],'name':t['name'],'fields':relevant})
            if t['image']=='Unity.Transforms.dll' and t['definition']['interfaces_count'] and t['definition']['genericContainerIndex']==-1:
                d=t['definition'];ints=list(struct.unpack_from('<'+'i'*d['interfaces_count'],b,h['interfacesOffset']+d['interfacesStart']*4))
                if any(i in {68571,68485,69275} for i in ints):interfaces.append({'metadata_index':t['index'],'name':t['ns']+'.'+t['name'],'interfaces_type_indices':ints,'field_names':[x['name'] for x in t['fields']]})
    # Exact original order candidate from directly recorded non-generic ECS interface declarations.
    registry=json.loads((out/'registration_metadata.json').read_text('utf-8'))
    reg=next(t for t in registry['types'] if t['image']=='Unity.Transforms.dll' and t['name']=='AssemblyTypeRegistry')
    start=data_start+next(x for x in reg['fields'] if x['name']=='Value0')['default_value']['dataIndex']
    end=data_start+next(x for x in reg['fields'] if x['name']=='Value1')['default_value']['dataIndex']
    records=[]
    for i,t in enumerate(interfaces):
        pos=start+i*104;assert pos+104<=end
        a=struct.unpack_from('<4i3Q16i',b,pos)
        records.append({'provenance':'inferred','registry_record_index':i,'record_file_offset':pos,'component_name_candidate':t['name'],'original_declaration':t,'TypeIndex':a[0],'SizeInChunk':a[1],'ElementSize':a[2],'BufferCapacity':a[3],'MemoryOrdering':f'{a[4]:016x}','StableTypeHash':f'{a[5]:016x}','TypeSize':a[-1],'raw_hex':b[pos:pos+104].hex()})
(out/'registry_order_candidates.json').write_text(json.dumps({'provenance':'inferred','source':str(p),'hash_default_neighbors':record_candidates,'default_owners':owners,'transform_order_candidates':records,'transform_blob_span':end-start,'limitations':['Original metadata type order plus direct non-generic ECS interface filtering, not decoded .cctor runtime Types assignments.','Generic registrations, nested traversal order or implementation version can differ; no name promoted solely from this order.','Independent stable hash recalculation failed; preserve candidate status.']},ensure_ascii=False,indent=2),encoding='utf-8')
print('Transform order',[(x['component_name_candidate'],x['StableTypeHash'],x['TypeSize']) for x in records])
print('Owners',[(x['image'],x['name'],[(z['name'],z['index']) for z in x['fields']]) for x in owners])
