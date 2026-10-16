import json,struct,hashlib,collections
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';inventory=json.loads((out/'field_all_children_inventory.json').read_text('utf-8'));results=[]
totals=collections.Counter()
for s in inventory['sections']:
    d=json.loads((out/(s['label']+'_shared_bindings.json')).read_text('utf-8'));b=Path(d['source']).read_bytes();assert hashlib.sha256(b).hexdigest()==d['source_sha256']
    records={x['serialized_shared_index']:x for x in d['shared_records']};counts=collections.Counter()
    for obj in d['render_mesh_arrays']:
        for a in obj['arrays']:
            if 'object_ref_indices' in a:assert list(struct.unpack_from('<'+'i'*a['length'],b,a['file_offset']))==a['object_ref_indices']
            else:assert b[a['file_offset']:a['file_offset']+a['length']*a['element_stride_candidate']].hex()==a['raw_hex']
    for ch in d['chunks']:
        rmas={x['serialized_shared_index']:x['RenderMeshArray_candidate'] for x in ch['shared_bindings'] if 'RenderMeshArray_candidate' in x}
        for bind in ch['shared_bindings']:
            idx=struct.unpack_from('<I',b,bind['index_file_offset'])[0];assert idx==bind['serialized_shared_index'];counts['shared_indices']+=1
            if idx:assert records[idx]['stable_hash']==bind['hash']
        for entity in ch['render_entity_bindings']:
            mm=entity['material_mesh_info_candidate'];assert tuple(mm[k] for k in ['Material','Mesh','SubMesh_uint32'])==struct.unpack_from('<iiI',b,mm['file_offset']);counts['render_entities']+=1
            for field,ai in [('Material',0),('Mesh',1)]:
                if field+'_static_array_candidate' in entity:
                    x=entity[field+'_static_array_candidate'];arr=rmas[entity['shared_render_mesh_array_index']]['arrays'][ai]
                    assert x['array_index']==-mm[field]-1;assert x['object_ref_index']==arr['object_ref_indices'][x['array_index']];assert x['object_ref_index']==struct.unpack_from('<i',b,x['array_value_file_offset'])[0];counts['static_'+field]+=1
                else:counts['runtime_nonnegative_'+field]+=1
        for bind in ch['managed_entity_bindings']:
            idx=struct.unpack_from('<i',b,bind['component_index_file_offset'])[0];assert idx==bind['managed_component_index'];rec=bind['managed_record_candidate']
            if rec:assert rec['type_hash']==bind['component_hash'];assert b[rec['file_offset']:rec['file_offset']+13].hex()==rec['raw_hex'];counts['managed_entity_bindings']+=1
    tail=d['managed_tail'];assert tail['parsed_count']==tail['expected_count'] and tail['remaining_bytes']==0
    counts['managed_records']=tail['parsed_count'];assert counts['shared_indices']==d['consumed_shared_index_count'];totals.update(counts)
    results.append({'guid':d['guid'],'source_bytes_and_mapping_checks_pass':True,'counts':dict(counts)})
report={'provenance':'verified original bytes and internal hash/reference consistency; semantic decoder candidates remain inferred','sections':results,'totals':dict(totals),'limitations':['No native PPtr asset-table resolution or original runtime activation validation. Static negative-index interpretation is compatible hypothesis, not original body recovery.']}
(out/'field_all_children_shared_binding_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed_sections':len(results),'totals':dict(totals)}))
