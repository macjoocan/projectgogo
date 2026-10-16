import json,hashlib,struct,math,collections
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected'
summary=json.loads((out/'field_all_children_render_summary.json').read_text('utf-8'));results=[]
for row in summary['sections']:
    d=json.loads((out/row['render_report']).read_text('utf-8'));b=Path(d['source']).read_bytes()
    assert hashlib.sha256(b).hexdigest()==d['sha256']==row['sha256']
    entities=[e for c in d['chunks'] for e in c.get('entities',[])];ids=set();parents=[];counts=collections.Counter()
    assert len(entities)==row['entities']
    for e in entities:
        ident=e['entity_identity'];key=tuple(ident['index_version'])
        assert key not in ids;ids.add(key)
        assert list(struct.unpack_from('<ii',b,ident['file_offset']))==list(key)
        for name,size,fmt,fields in [('material_mesh_info_candidate',12,'<iiI',['Material','Mesh','SubMesh_uint32'])]:
            if name in e:
                x=e[name];assert tuple(x[k] for k in fields)==struct.unpack_from(fmt,b,x['file_offset']);counts['render']+=1
        if 'local_to_world_candidate' in e:
            x=e['local_to_world_candidate'];assert list(struct.unpack_from('<16f',b,x['file_offset']))==x['matrix_column_major'];assert all(math.isfinite(v) for v in x['matrix_column_major']);assert x['affine_pass'];counts['world']+=1
        if 'local_transform_candidate' in e:
            x=e['local_transform_candidate'];assert list(struct.unpack_from('<8f',b,x['file_offset']))==x['Position']+[x['Scale']]+x['Rotation'];counts['local']+=1
        if 'parent_entity_candidate' in e:
            x=e['parent_entity_candidate'];assert list(struct.unpack_from('<ii',b,x['file_offset']))==x['index_version'];parents.append(tuple(x['index_version']))
        if 'physics_collider_candidate' in e:
            x=e['physics_collider_candidate'];assert b[x['file_offset']:x['file_offset']+8].hex()==x['raw_hex'];counts['collider']+=1
    assert counts['render']==row['render_entities'] and counts['collider']==row['physics_collider_candidates']
    results.append({'guid':d['guid'],'source_sha_and_export_offsets_pass':True,'counts':dict(counts),'unique_entity_ids':len(ids),'parent_count':len(parents),'parent_target_ids_present':sum(x in ids for x in parents),'parent_target_ids_absent':[list(x) for x in parents if x not in ids]})
report={'provenance':'verified bytes and references; semantic type binding remains inferred','sections':results,'passed_sections':len(results),'limitations':['Independent reread validates bytes, offsets, IDs and matrix consistency, not original runtime type identity or renderer activation.']}
(out/'field_all_children_export_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed_sections':len(results),'parents_present':sum(x['parent_target_ids_present'] for x in results),'parents_absent':sum(len(x['parent_target_ids_absent']) for x in results),'world_matrices':sum(x['counts'].get('world',0) for x in results)}))
