import json,struct,collections,hashlib
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected'
summary=json.loads((out/'field_all_children_render_summary.json').read_text('utf-8'));rows=[]
info={x['stable_hash']:x['interpreted_type_info'] for x in json.loads((out/'field_all_child_type_info_candidates.json').read_text('utf-8'))['rows']}
for section in summary['sections']:
    label=section['label'];scene=json.loads((out/(label+'.json')).read_text('utf-8'));render=json.loads((out/section['render_report']).read_text('utf-8'));layout=json.loads((out/(label+'_chunk_layout_candidates.json')).read_text('utf-8'));b=Path(scene['source']).read_bytes()
    recs=render['managed_shared_records'];payload_info=render['managed_payload_candidate'];start=payload_info['file_offset'];payload=b[start:start+payload_info['bytes']];q=0;objects=[]
    for rec_i,rec in enumerate(recs):
        assert rec['stable_hash']=='035c5b805bb5ac69';begin=q;assert payload[q]==0;q+=1;arrays=[]
        for name,stride in [('m_Materials',4),('m_Meshes',4),('m_MaterialMeshIndices',12)]:
            assert payload[q]==0;q+=1;n=struct.unpack_from('<i',payload,q)[0];q+=4;assert 0<=n<100000 and q+n*stride<=len(payload)
            a={'field_name_candidate':name,'length':n,'file_offset':start+q,'element_stride_candidate':stride}
            if stride==4:a['object_ref_indices']=list(struct.unpack_from('<'+'i'*n,payload,q))
            else:a['raw_hex']=payload[q:q+n*stride].hex()
            arrays.append(a);q+=n*stride
        assert q+16<=len(payload);h=payload[q:q+16].hex();q+=16
        objects.append({'record_index':rec_i,'serialized_shared_index':len(render['unmanaged_shared_records'])+rec_i+1,'file_offset':start+begin,'arrays':arrays,'Hash128_raw_hex':h})
    prefix_end=q;tail=[];tail_status='unresolved'
    # The trailing normal managed objects are kept separately from shared RMA.
    for i in range(payload_info['managed_component_count']):
        if q+13>len(payload):break
        h=struct.unpack_from('<Q',payload,q)[0];flag=payload[q+8];index=struct.unpack_from('<i',payload,q+9)[0]
        expected_header={'7374fd3a3060fa28':3,'82d433bd89f38e81':3,'e796be9b17f4e84d':0}
        if expected_header.get(f'{h:016x}')!=flag:break
        tail.append({'managed_component_index':i+1,'type_hash':f'{h:016x}','file_offset':start+q,'binary_header_byte':flag,'object_ref_index_candidate':index,'raw_hex':payload[q:q+13].hex()});q+=13
    if len(tail)==payload_info['managed_component_count'] and q==len(payload):tail_status='restricted_13byte_objects_full_consumption'
    shared_records=[dict(x,serialized_shared_index=i+1) for i,x in enumerate(render['unmanaged_shared_records'])]+[dict(x,serialized_shared_index=len(render['unmanaged_shared_records'])+i+1) for i,x in enumerate(recs)]
    indices=render['shared_component_indices'];cursor=0;bindings=[]
    for ch in layout['chunks']:
        # FillSharedComponentArrays emits shared types in TypeMemoryOrder order.
        shared=[x for x in ch['component_arrays'] if x['hash'] in info and info[x['hash']]['Category']==2 and not x.get('is_chunk_component',False)]
        bind=[]
        for entry in shared:
            assert cursor<len(indices);index=indices[cursor];offset=render['shared_component_indices_file_offset']+cursor*4;cursor+=1
            assert 0<=index<=len(shared_records)
            record=shared_records[index-1] if index else None
            assert record is None or record['stable_hash']==entry['hash']
            v={'hash':entry['hash'],'serialized_shared_index':index,'index_file_offset':offset,'record_file_offset':record['file_offset'] if record else None,'default_value':index==0}
            if entry['hash']=='035c5b805bb5ac69' and index:v['RenderMeshArray_candidate']=objects[index-len(render['unmanaged_shared_records'])-1]
            bind.append(v)
        render_chunk=next(c for c in render['chunks'] if c['chunk_index']==ch['chunk_index'])
        rma=next((x.get('RenderMeshArray_candidate') for x in bind if x['hash']=='035c5b805bb5ac69'),None)
        entity_bindings=[];managed_entity_bindings=[]
        for entity in render_chunk['entities']:
            for component in ch['component_arrays']:
                if component['hash'] not in {'7374fd3a3060fa28','82d433bd89f38e81','e796be9b17f4e84d'}:continue
                assert component['instance_stride']==4
                off=component['file_offset']+entity['index_in_chunk']*4;managed_index=struct.unpack_from('<i',b,off)[0]
                assert 0<=managed_index<=len(tail)
                record=tail[managed_index-1] if managed_index else None
                assert record is None or record['type_hash']==component['hash']
                managed_entity_bindings.append({'entity_identity':entity['entity_identity'],'component_hash':component['hash'],'component_index_file_offset':off,'managed_component_index':managed_index,'managed_record_candidate':record})
            mm=entity.get('material_mesh_info_candidate')
            if mm is None:continue
            v={'entity_identity':entity['entity_identity'],'material_mesh_info_candidate':mm,'shared_render_mesh_array_index':next((x['serialized_shared_index'] for x in bind if x['hash']=='035c5b805bb5ac69'),None)}
            if rma is not None:
                for field,arrindex in [('Material',0),('Mesh',1)]:
                    raw=mm[field]
                    if raw<0:
                        index=-raw-1;array=rma['arrays'][arrindex]
                        assert index<array['length']
                        v[field+'_static_array_candidate']={'array_index':index,'object_ref_index':array['object_ref_indices'][index],'array_value_file_offset':array['file_offset']+4*index}
                    else:v[field+'_runtime_id_raw']=raw
            entity_bindings.append(v)
        bindings.append({'chunk_index':ch['chunk_index'],'archetype_index':ch['archetype_index'],'entity_count':ch['entities'],'shared_bindings':bind,'render_entity_bindings':entity_bindings,'managed_entity_bindings':managed_entity_bindings})
    assert cursor==len(indices)
    data={'provenance':'inferred interpretation / verified source offsets','source':scene['source'],'source_sha256':scene['sha256'],'guid':scene['guid'],'reference_rules':'Entities1.4.3 SerializeUtility FillSharedComponentArrays/ReadManagedSharedComponents; exact original version unknown','shared_records':shared_records,'render_mesh_arrays':objects,'shared_payload_prefix_end_file_offset':start+prefix_end,'managed_tail':{'status':tail_status,'expected_count':payload_info['managed_component_count'],'parsed_count':len(tail),'remaining_bytes':len(payload)-q,'records':tail,'unknown_tail_offset':start+q},'chunks':bindings,'consumed_shared_index_count':cursor,'limitations':['Runtime Types[] identity not recovered; candidate hashes retained.','13-byte trailing Unity object wrapper interpretation requires original type and native object-table verification.','Positive MM runtime IDs and packed submeshes must not be replaced with array0. Native PPtr table supplied by Action.']}
    (out/(label+'_shared_bindings.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    rows.append({'guid':scene['guid'],'shared_indices_consumed':cursor,'shared_rma_objects':len(objects),'tail_status':tail_status,'tail_expected':payload_info['managed_component_count'],'tail_parsed':len(tail),'remaining_bytes':len(payload)-q,'tail_hash_counts':dict(collections.Counter(x['type_hash'] for x in tail))})
result={'provenance':'inferred','sections':rows,'shared_bindings_sections_pass':len(rows),'limitations':['All shared indices consumed and nonzero record hash agrees with chunk candidate; semantic names and activation unconfirmed.']}
(out/'field_all_children_shared_binding_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result))
