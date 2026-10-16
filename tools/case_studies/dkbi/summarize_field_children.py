"""Preserve bounded ECS candidates; never substitute meshes or gameplay rules."""
import json,struct,csv,collections,math
from pathlib import Path
r=Path(__file__).parent; out=r/'ecs_selected'
inventory=json.loads((out/'field_all_children_inventory.json').read_text('utf-8'))
relations=collections.defaultdict(list)
with (r.parent/'analysis/ECS-Map-High_archive_relations.csv').open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row['relation']=='Object': relations[row['target_id'].split(':')[0]].append(row)
summary=[]
for section in inventory['sections']:
    label=section['label']; scene=json.loads((out/(label+'.json')).read_text('utf-8'))
    layout=json.loads((out/(label+'_chunk_layout_candidates.json')).read_text('utf-8'))
    b=Path(scene['source']).read_bytes(); node=next(n for n in scene['container']['nodes'] if n['kind']=='SharedManaged')
    p=node['data_offset']; end=p+node['data_size']
    def uint():
        global p
        assert p+4<=end
        v=struct.unpack_from('<I',b,p)[0];p+=4;return v
    def records():
        global p
        n=uint();assert n<10000;rows=[]
        for i in range(n):
            assert p+16<=end
            h,size=struct.unpack_from('<Qi',b,p);assert b[p+12:p+16]==bytes(4)
            rows.append({'stable_hash':f'{h:016x}','size':size,'file_offset':p,'raw_hex':b[p:p+16].hex()});p+=16
        return rows
    n=uint();assert n<10000;indices_offset=p;indices=[uint() for _ in range(n)]
    unmanaged=records();n=uint();unmanaged_start=p;unmanaged_hex=b[p:p+n].hex();p+=n
    managed=records();n=uint();managed_count=uint();payload_start=p;payload=b[p:p+n];p+=n;assert p==end
    managed_candidate={'status':'unresolved','file_offset':payload_start,'bytes':len(payload),'sha256':__import__('hashlib').sha256(payload).hexdigest(),'managed_component_count':managed_count}
    if all(x['stable_hash']=='035c5b805bb5ac69' for x in managed) and managed_count==0:
        q=0;objs=[]
        try:
            for index,record in enumerate(managed):
                start=q;assert payload[q]==0;q+=1;arrays=[]
                for field,stride in [('m_Materials',4),('m_Meshes',4),('m_MaterialMeshIndices',12)]:
                    assert payload[q]==0;q+=1
                    count=struct.unpack_from('<i',payload,q)[0];q+=4;assert 0<=count<100000 and q+count*stride<=len(payload)
                    entry={'field_name_candidate':field,'length':count,'file_offset':payload_start+q,'element_stride_candidate':stride}
                    if stride==4:entry['object_ref_index_candidates']=list(struct.unpack_from('<'+'i'*count,payload,q))
                    else:entry['raw_hex']=payload[q:q+count*stride].hex()
                    arrays.append(entry);q+=count*stride
                assert q+16<=len(payload);h=payload[q:q+16].hex();q+=16
                objs.append({'managed_record_index':index,'payload_file_offset':payload_start+start,'arrays':arrays,'hash128_raw_hex':h})
            assert q==len(payload)
            managed_candidate.update(status='restricted_hypothesis_full_consumption',objects=objs)
        except (AssertionError,IndexError,struct.error) as e:
            managed_candidate.update(status='restricted_hypothesis_failed',partial_consumed_bytes=q,error=type(e).__name__)
    chunks=[];render_count=0;parent_count=0;physics_count=0;affine_bad=0;local_world_different=0
    for chunk in layout['chunks']:
        if 'component_arrays' not in chunk:
            chunks.append(chunk);continue
        arrays={x['hash']:x for x in chunk['component_arrays'] if not x.get('is_chunk_component',False)}
        mm=arrays.get('46efe2e0a2cbae6f');lt=arrays.get('001f79e44e197fd0');lw=arrays.get('8e54084ebb177ef0');parent=arrays.get('c65e2a652658b400');collider=arrays.get('a047018c0f8c5400')
        if parent:parent_count+=chunk['entities']
        if collider:physics_count+=chunk['entities']
        entities=[];identity=arrays['implicit Entity']
        for i in range(chunk['entities']):
            identity_offset=identity['file_offset']+i*identity['instance_stride']
            item={'index_in_chunk':i,'entity_identity':{'file_offset':identity_offset,'index_version':list(struct.unpack_from('<ii',b,identity_offset))}}
            if mm:
                off=mm['file_offset']+i*mm['instance_stride'];a,m,s=struct.unpack_from('<iiI',b,off)
                item['material_mesh_info_candidate']={'file_offset':off,'Material':a,'Mesh':m,'SubMesh_uint32':s,'raw_hex':b[off:off+12].hex()};render_count+=1
            if lt:
                vals=lt['float_values_candidates'][i];item['local_transform_candidate']={'file_offset':lt['file_offset']+i*lt['instance_stride'],'Position':vals[:3],'Scale':vals[3],'Rotation':vals[4:]}
            if lw:
                matrix=lw['float_values_candidates'][i];affine=all(abs(matrix[k])<1e-5 for k in [3,7,11]) and abs(matrix[15]-1)<1e-5
                item['local_to_world_candidate']={'file_offset':lw['file_offset']+i*lw['instance_stride'],'matrix_column_major':matrix,'translation':matrix[12:15],'affine_pass':affine,'finite_pass':all(math.isfinite(v) for v in matrix)}
                affine_bad+=not affine
                if lt:
                    error=max(abs(vals[k]-matrix[12+k]) for k in range(3));item['local_world_translation_error']=error
                    local_world_different+=error>1e-4
            if parent:
                off=parent['file_offset']+i*parent['instance_stride'];item['parent_entity_candidate']={'file_offset':off,'index_version':list(struct.unpack_from('<ii',b,off))}
            if collider:
                off=collider['file_offset']+i*collider['instance_stride'];item['physics_collider_candidate']={'file_offset':off,'raw_hex':b[off:off+8].hex(),'blob_interpretation':'unknown'}
            entities.append(item)
        chunks.append({'chunk_index':chunk['chunk_index'],'archetype_index':chunk['archetype_index'],'entity_count':chunk['entities'],'capacity_candidate':chunk['capacity_candidate'],'entities':entities})
    report={'provenance':'inferred','source':scene['source'],'sha256':scene['sha256'],'guid':scene['guid'],'object_archive_relations':relations[scene['guid']],'shared_component_indices':indices,'shared_component_indices_file_offset':indices_offset,'unmanaged_shared_records':unmanaged,'unmanaged_shared_data_file_offset':unmanaged_start,'unmanaged_shared_data_hex':unmanaged_hex,'managed_shared_records':managed,'managed_payload_candidate':managed_candidate,'chunks':chunks,'limitations':['Type identity and offsets inferred from raw TypeInfo and compatible official source, not recovered native Types[] body.','Shared-component index to archetype memory order and native object table resolution still pending for these expanded scenes.','Parent makes local position differ from world; divergence alone is not a layout failure.','MaterialMeshInfo indices are saved values; positive runtime indices and packed SubMesh interpretation not reconstructed.','Collider raw data retained; collision shape and nav not decoded. Renderer activation and runtime equivalence unknown.']}
    (out/(label+'_render_candidates.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary.append(dict(section,render_entities=render_count,parent_entities=parent_count,physics_collider_candidates=physics_count,matrix_affine_failures=affine_bad,local_world_translation_differences=local_world_different,managed_payload_status=managed_candidate['status'],managed_objects=len(managed_candidate.get('objects',[])),render_report=label+'_render_candidates.json'))
result={'provenance':'inferred','sections':summary,'totals':{k:sum(x[k] for x in summary) for k in ['entities','chunks','render_entities','parent_entities','physics_collider_candidates','matrix_affine_failures','local_world_translation_differences','managed_objects']},'limitations':['16 saved child sections, not proof they are all runtime active. No mesh extraction, terrain collision or navigation implementation.']}
(out/'field_all_children_render_summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'totals':result['totals'],'managed_status_counts':dict(collections.Counter(x['managed_payload_status'] for x in summary))}))
