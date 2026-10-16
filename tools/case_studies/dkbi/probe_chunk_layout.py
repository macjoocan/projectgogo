import json,struct,math,hashlib,sys
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected'
info={x['stable_hash']:x['interpreted_type_info'] for x in json.loads((out/'type_info_candidates.json').read_text('utf-8'))['rows']}
if (out/'field_child_type_info_candidates.json').exists():info.update({x['stable_hash']:x['interpreted_type_info'] for x in json.loads((out/'field_child_type_info_candidates.json').read_text('utf-8'))['rows']})
if (out/'field_all_child_type_info_candidates.json').exists():info.update({x['stable_hash']:x['interpreted_type_info'] for x in json.loads((out/'field_all_child_type_info_candidates.json').read_text('utf-8'))['rows']})
def align(x):return (x+63)//64*64
results=[]
for label in (sys.argv[1:] or ['field_101002','town_100']):
    d=json.loads((out/(label+'.json')).read_text('utf-8'));container=d['container'];b=Path(d['source']).read_bytes();node=next(n for n in container['nodes'] if n['kind']=='Chunks');chunks=[]
    for ci,ch in enumerate(container['chunks']):
        arch=container['archetypes'][ch['archetype']];hashes=[container['type_hashes'][x&0xffffff] for x in arch['type_indices_with_flags']]
        missing=[h for h in hashes if h not in info]
        if missing:chunks.append({'chunk_index':ci,'status':'unresolved','missing_hashes':missing});continue
        types=[{'hash':'implicit Entity','size':8,'flags':0,'memory_order':0,'max_cap':128}]
        for h,encoded in zip(hashes,arch['type_indices_with_flags']):
            x=info[h];is_chunk_component=bool(encoded&(1<<29));flags=x['TypeIndex']&~8191
            if is_chunk_component:flags|=(1<<29)|(1<<30)
            types.append({'hash':h,'size':0 if is_chunk_component else x['SizeInChunk'],'flags':flags,'memory_order':x['MemoryOrdering'],'max_cap':x['MaximumChunkCapacity'],'encoded_archetype_type_index':encoded,'is_chunk_component':is_chunk_component})
        maxcap=min(x['max_cap'] for x in types);cap=min(maxcap,16320//sum(x['size'] for x in types))
        while sum(align(x['size']*cap) for x in types)>16320:cap-=1
        assert cap>=ch['entities'] and cap>0
        types=[types[0]]+sorted(types[1:],key=lambda x:(x['flags'],x['memory_order']))
        offset=0;rows=[];base=node['data_offset']+ci*16384+64
        for x in types:
            size=x['size'];entry=dict(x,component_array_buffer_offset=offset,file_offset=base+offset,capacity=cap,instance_stride=size)
            raw=b[base+offset:base+offset+size*ch['entities']];entry['active_array_sha256']=hashlib.sha256(raw).hexdigest()
            if x['hash'] in {'001f79e44e197fd0','8e54084ebb177ef0'}:
                entry['float_values_candidates']=[list(struct.unpack_from('<'+'f'*(size//4),b,base+offset+i*size)) for i in range(ch['entities'])]
            rows.append(entry);offset+=align(size*cap)
        lt=next((x for x in rows if x['hash']=='001f79e44e197fd0'),None);lw=next((x for x in rows if x['hash']=='8e54084ebb177ef0'),None)
        checks=[]
        if lt and lw:
            for p,m in zip(lt['float_values_candidates'],lw['float_values_candidates']):
                qnorm=sum(x*x for x in p[4:8]);affine=all(abs(m[k])<1e-5 for k in [3,7,11]) and abs(m[15]-1)<1e-5;error=max(abs(p[i]-m[12+i]) for i in range(3))
                checks.append({'quaternion_norm_squared':qnorm,'scale':p[3],'matrix_affine':affine,'local_world_position_error':error,'pass':abs(qnorm-1)<1e-4 and p[3]>0 and affine and error<1e-4})
        chunks.append({'chunk_index':ci,'archetype_index':ch['archetype'],'entities':ch['entities'],'capacity_candidate':cap,'component_arrays':rows,'transform_cross_checks':checks,'status':'inferred_layout_crosschecked' if checks and all(x['pass'] for x in checks) else 'inferred_layout_unconfirmed'})
    report={'provenance':'inferred','source':d['source'],'reference_source':'tools/entities_reference_1.4.3/EntityComponentStore.cs','rules':{'chunk_bytes':16384,'buffer_offset':64,'buffer_bytes':16320,'cacheline':64,'max_capacity':128,'clear_flags_mask':8191},'chunks':chunks,'limitations':['Official source version compatibility inferred, not exact original code body','Transform type names remain candidates; hash recalculation failed','Checks validate numeric layout consistency, not full scene rendering or all component semantics']}
    (out/(label+'_chunk_layout_candidates.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    results.append({'label':label,'chunks':[(x['chunk_index'],x['status'],x.get('capacity_candidate'),x.get('transform_cross_checks')) for x in chunks]})
print(json.dumps(results))
