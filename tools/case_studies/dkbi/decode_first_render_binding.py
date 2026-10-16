import json,struct
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';scene=json.loads((out/'field_first_child.json').read_text('utf-8'));b=Path(scene['source']).read_bytes();node=next(n for n in scene['container']['nodes'] if n['kind']=='SharedManaged');p=node['data_offset'];end=p+node['data_size']
def u32():
    global p
    val=struct.unpack_from('<I',b,p)[0];p+=4;return val
def records():
    global p
    n=u32();rows=[]
    for i in range(n):
        start=p;h,size=struct.unpack_from('<Qi',b,p);padding=b[p+12:p+16];assert padding==b'\0'*4;p+=16;rows.append({'record_index':i,'file_offset':start,'stable_hash':f'{h:016x}','component_size':size,'raw_hex':b[start:p].hex()})
    return rows
count=u32();indices=[u32() for _ in range(count)];unmanaged=records();n=u32();raw_unmanaged_start=p;raw_unmanaged=b[p:p+n];p+=n;managed=records();n=u32();managed_count=u32();payload_start=p;payload=b[p:p+n];p+=n;assert p==end
assert len(payload)==40 and managed_count==0 and len(managed)==1
# Restricted hypothesis for the one saved object: non-null root byte, three non-null array bytes,
# int32 element count followed by UnityObjectRef int32 object-table indices, then Hash128.
q=0;root_flag=payload[q];q+=1;assert root_flag==0;arrays=[]
for field in ['m_Materials','m_Meshes','m_MaterialMeshIndices']:
    flag=payload[q];q+=1;assert flag==0;length=struct.unpack_from('<i',payload,q)[0];q+=4;assert 0<=length<=2
    values=list(struct.unpack_from('<'+'i'*length,payload,q));start=q;q+=4*length
    arrays.append({'field_name_candidate':field,'null_flag':flag,'length':length,'values':values,'values_file_offset':payload_start+start})
assert q+16==len(payload)
lookup=json.loads((out/'terrain_first/MonoBehaviour_4710654306103455599.json').read_text('utf-8'))['data']['Array'];assert len(lookup)==2
for a in arrays[:2]:
    assert all(0<=i<len(lookup) for i in a['values']);a['resolved_original_pptrs']=[lookup[i] for i in a['values']]
layout=json.loads((out/'field_first_child_chunk_layout_candidates.json').read_text('utf-8'));render=layout['chunks'][1];infos=render['component_arrays'];mm=next(x for x in infos if x['hash']=='46efe2e0a2cbae6f');lt=next(x for x in infos if x['hash']=='001f79e44e197fd0');lw=next(x for x in infos if x['hash']=='8e54084ebb177ef0')
material,mesh,submesh=struct.unpack_from('<iiI',b,mm['file_offset']);assert material==-1 and mesh==-1 and submesh==0
metadata=[]
with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as f:
    for line in f:
        t=json.loads(line)
        if t['name'] in {'MaterialMeshInfo','RenderMeshArray','RenderFilterSettings','RenderBounds','WorldRenderBounds','ChunkWorldRenderBounds'} and t['image']=='Unity.Entities.Graphics.dll':metadata.append(t)
data={'provenance':'inferred','source':scene['source'],'guid':scene['guid'],'shared_managed_node':node,'shared_component_indices':indices,'unmanaged_shared_records':unmanaged,'unmanaged_shared_data_file_offset':raw_unmanaged_start,'unmanaged_shared_data_hex':raw_unmanaged.hex(),'managed_shared_records':managed,'managed_component_count':managed_count,'managed_payload_file_offset':payload_start,'managed_payload_hex':payload.hex(),'managed_array_hypothesis':arrays,'saved_hash128_raw_hex':payload[q:].hex(),'native_object_table':lookup,'render_chunk_index':1,'render_capacity_candidate':render['capacity_candidate'],'material_mesh_info_candidate':{'stable_hash':mm['hash'],'file_offset':mm['file_offset'],'raw_hex':b[mm['file_offset']:mm['file_offset']+12].hex(),'Material':material,'Mesh':mesh,'SubMesh_uint32':submesh,'array_index_candidates':{'Material':-material-1,'Mesh':-mesh-1}},'local_transform_candidate':{'file_offset':lt['file_offset'],'raw_hex':b[lt['file_offset']:lt['file_offset']+32].hex(),'Position':lt['float_values_candidates'][0][:3],'Scale':lt['float_values_candidates'][0][3],'Rotation':lt['float_values_candidates'][0][4:]},'local_to_world_candidate':{'file_offset':lw['file_offset'],'matrix_column_major':lw['float_values_candidates'][0]},'original_render_declarations':metadata,'limitations':['Object/array null-flag layout hypothesis only for this exact 40-byte payload; not a generic BinarySerialization decoder.','Managed record hash->RenderMeshArray and MaterialMeshInfo hash/type names inferred, runtime type-array assignments unavailable.','Static index -1 -> array0 is inferred until original implementation/reference independently confirmed.','World TRS candidate numeric consistency passes; renderer activation/filtering and full field replay not established.']}
(out/'field_child_render_binding_candidates.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'position':data['local_transform_candidate']['Position'],'MaterialMeshInfo':[material,mesh,submesh],'objects':lookup,'arrays':arrays,'shared_payload_consumed':q+16==len(payload)}))
