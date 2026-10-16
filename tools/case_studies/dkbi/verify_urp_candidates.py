import json,struct,hashlib
from pathlib import Path
r=Path(__file__).parent;out=r/'urp';data=json.loads((out/'urp_asset_schema_candidates.json').read_text('utf-8'));decl=json.loads((r/'metadata/urp_original_declarations.json').read_text('utf-8'));header=json.loads((r/'metadata/metadata_header.json').read_text('utf-8'));enums=[]
metadata=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\il2cpp_data\Metadata\global-metadata.dat')
with metadata.open('rb') as f:
    for t in decl['types']:
        if t['name'] not in {'RenderingMode','DepthPrimingMode','CopyDepthMode','IntermediateTextureMode'}:continue
        fields=[]
        for fld in t['fields']:
            if not fld.get('default_value'):continue
            offset=header['fieldAndParameterDefaultValueDataOffset']+fld['default_value']['dataIndex'];f.seek(offset);raw=f.read(1);assert raw[0]<128 and raw[0]%2==0
            fields.append({'name':fld['name'],'source_metadata_offset':offset,'raw_hex':raw.hex(),'value_candidate_compressed_i32':raw[0]>>1})
        enums.append({'name':t['name'],'fields':fields})
assert {x['name']:x['value_candidate_compressed_i32'] for e in enums if e['name']=='RenderingMode' for x in e['fields']}=={'Forward':0,'ForwardPlus':2,'Deferred':1,'DeferredPlus':3}
for asset in [data['pipeline']]+data['renderers']:
    b=bytes.fromhex(asset['raw_hex']);assert hashlib.sha256(b).hexdigest()==(asset.get('source_sha256') or asset['sha256'])
    for field in asset['fields']:
        o=field['asset_relative_offset'];size=field['byte_size'];assert b[o:o+size].hex()==field['raw_hex'];kind=field['kind_candidate'];v=field['value']
        if kind=='PPtrArray':assert struct.unpack_from('<i',b,o)[0]==len(v);assert [dict(zip(['fileID','pathID'],struct.unpack_from('<iq',b,o+4+i*12))) for i in range(len(v))]==v
        elif kind=='Int64Array':assert list(struct.unpack_from('<'+'q'*len(v),b,o+4))==v
        elif kind=='PPtr':assert dict(zip(['fileID','pathID'],struct.unpack_from('<iq',b,o)))==v
        elif kind=='bool':assert b[o]==v and v in [0,1]
        elif kind in ['Vector2','Vector3']:assert list(struct.unpack_from('<'+'f'*len(v),b,o))==v
        else:assert struct.unpack_from('<f' if kind=='float' else '<i',b,o)[0]==v
for feature in data['features']:
    b=bytes.fromhex(feature['raw_hex']);assert hashlib.sha256(b).hexdigest()==feature['sha256'];a=feature['active_field_candidate'];assert b[a['asset_relative_offset']]==a['raw_byte'] and a['raw_byte'] in [0,1]
report={'provenance':'verified source bytes and enum constant storage / field labels remain inferred','original_enum_constants':enums,'validated_pipeline':1,'validated_renderer_full_consumption':len(data['renderers']),'validated_feature_headers':len(data['features']),'original_package_version':'unknown','limitations':['Compressed-i32 constant interpretation uses v39-compatible tool source; original native method body absent.','Reference17.3.0 schema match does not establish original semver. Pipeline440-byte prefix decoded, final48 bytes opaque. GlobalSettings declaration extracted, managed reference body unresolved.']}
(out/'urp_schema_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report))
