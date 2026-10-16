import json,struct,mmap
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected'
blobs=json.loads((out/'registry_blob_hash_matches.json').read_text('utf-8'))['blobs']
fields=['TypeIndex','SizeInChunk','ElementSize','BufferCapacity','MemoryOrdering','StableTypeHash','BloomFilterMask','AlignmentInBytes','Category','EntityOffsetCount','EntityOffsetStartIndex','_HasBlobAssetRefs','_HasUnityObjectRefs','BlobAssetRefOffsetCount','BlobAssetRefOffsetStartIndex','WeakAssetRefOffsetCount','WeakAssetRefOffsetStartIndex','UnityObjectRefOffsetCount','UnityObjectRefOffsetStartIndex','WriteGroupCount','WriteGroupStartIndex','MaximumChunkCapacity','TypeSize']
fmt='<4i3Q16i';assert struct.calcsize(fmt)==104
meta=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\il2cpp_data\Metadata\global-metadata.dat')
rows=[]
with meta.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
    for blob in blobs:
        start=blob['default_record_file_offset'];end=blob['next_default_record_file_offset']
        for hit in blob['hash_matches']:
            # Only the occurrence at +24 (StableTypeHash), not the equal value at +16 (MemoryOrdering).
            pos=hit['file_offset']-24
            if pos<start or (pos-start)%104 or pos+104>end:continue
            d=dict(zip(fields,struct.unpack_from(fmt,b,pos)))
            assert f"{d['StableTypeHash']:016x}"==hit['stable_hash']
            assert 0<=d['SizeInChunk']<=16384 and 0<=d['TypeSize']<=16384 and d['AlignmentInBytes'] in {0,1,2,4,8,16}
            rows.append({'provenance':'inferred','source':str(meta),'registry_image':blob['image'],'metadata_default_field_index':blob['field']['index'],'record_file_offset':pos,'registry_record_index':(pos-start)//104,'raw_hex':b[pos:pos+104].hex(),'stable_hash':hit['stable_hash'],'interpreted_type_info':d,'component_name':None})
assert len(rows)==17 and len({x['stable_hash'] for x in rows})==17
for x in rows:
    if x['registry_image']=='Unity.Transforms.dll':
        size=x['interpreted_type_info']['TypeSize']
        x['component_name_candidate']={64:'Unity.Transforms.LocalToWorld',32:'Unity.Transforms.LocalTransform'}.get(size)
        x['candidate_basis']='Registry assembly + size matches declaration; registry type-array order/function not resolved, therefore not verified name mapping.'
all_hashes=set(json.loads((out/'field_101002.json').read_text('utf-8'))['container']['type_hashes'])
unknown=sorted(all_hashes-{x['stable_hash'] for x in rows})
data={'provenance':'inferred','record_layout':'104 bytes: 4 int32, 3 uint64, 16 int32. _HasBlobAssetRefs/_HasUnityObjectRefs stored as int32 flags, not one-byte bool. Validated hash position +24, MemoryOrdering +16, stride and size/alignment bounds.','declaration_type_index':26533,'rows':rows,'unresolved_record_hashes':unknown,'limitations':['17 hashes now bounded by registry defaults including Hybrid.HybridComponents alternate namespace. One hash remains absent from raw metadata search.','No exact component type-name mapping yet','Runtime TypeIndex is not metadata typeDefinition index','Component offsets inside chunks not derived','Do not use Transform candidate names as verified decoding']}
(out/'type_info_candidates.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'hash':x['stable_hash'],'image':x['registry_image'],'size':x['interpreted_type_info']['SizeInChunk'],'typeSize':x['interpreted_type_info']['TypeSize'],'alignment':x['interpreted_type_info']['AlignmentInBytes'],'candidate':x.get('component_name_candidate')} for x in rows],ensure_ascii=False))
