import json,struct,hashlib
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';folder=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\SP\Resource\ECS-Map-High\EntityScenes')
reports=[]
for label in ['field_101002','town_100']:
    layout=json.loads((out/(label+'_chunk_layout_candidates.json')).read_text('utf-8'));b=Path(layout['source']).read_bytes();matches=[];arrays=[]
    for ch in layout['chunks']:
        for arr in ch.get('component_arrays',[]):
            size=arr['size']
            if arr['hash']=='implicit Entity' or size<=0:continue
            rows=[]
            for i in range(ch['entities']):
                pos=arr['file_offset']+i*size;raw=b[pos:pos+size];rows.append({'instance_index':i,'file_offset':pos,'raw_hex':raw.hex()})
                for j in range(0,size-15,4):
                    ints=struct.unpack_from('<4I',raw,j)
                    for variant,guid in [('word_nibble_reverse',''.join(f'{v:08x}'[::-1] for v in ints)),('raw_bytes',raw[j:j+16].hex())]:
                        p=folder/(guid+'.entityheader')
                        if p.exists():matches.append({'provenance':'verified','chunk_index':ch['chunk_index'],'component_hash':arr['hash'],'instance_index':i,'file_offset':pos+j,'component_byte_offset':j,'encoding_candidate':variant,'uint_values':ints,'matched_guid':guid,'entityheader_source':str(p),'entityheader_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
            arrays.append({'chunk_index':ch['chunk_index'],'component_hash':arr['hash'],'stride':size,'instances':rows})
    result={'provenance':'inferred','source':layout['source'],'arrays':arrays,'entityheader_guid_byte_matches':matches,'limitations':['GUID byte match establishes candidate source reference, not original loader semantics.','Chunk offsets based on previously corroborated reference layout.','Full runtime component names remain unresolved.']}
    (out/(label+'_scene_ref_candidates.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');reports.append({'label':label,'guid_matches':len(matches),'unique_targets':len({x['matched_guid'] for x in matches}),'matches':matches[:3]})
print(json.dumps(reports))
