"""Source-file/catalog audit only; no shader extraction/decompilation/engine load."""
import json,csv,hashlib
from pathlib import Path
r=Path(__file__).parent;out=r/'shader_source';out.mkdir(exist_ok=True)
install=Path(r'C:\Kakaogames\DKBI\client');extensions={'.shader','.shadergraph','.shadersubgraph','.hlsl','.cginc','.compute'}
actual=[];files_scanned=0
for p in install.rglob('*'):
    if not p.is_file():continue
    files_scanned+=1
    if p.suffix.lower() in extensions:actual.append({'path':str(p),'bytes':p.stat().st_size})
catalog_path=Path(r'D:\99.기타\out_dkbi_probe\addressables_catalog.json');catalog=json.loads(catalog_path.read_text('utf-8'));logical=[]
for i,path in enumerate(catalog['m_InternalIds']):
    if Path(path).suffix.lower() in extensions or 'terrainlit' in path.lower():logical.append({'internal_id_index':i,'logical_id':path,'interpretation':'catalog logical source-style name, not source-file content evidence'})
text_index=Path(r'D:\99.기타\out_dkbi\asset_indices_by_type\TextAsset.csv');text_leads=[];text_rows=0
with text_index.open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        text_rows+=1;name=row.get('name','')
        if Path(name).suffix.lower() in extensions or any(x in name.lower() for x in ['terrainlit','shadergraph','shadersubgraph','hlsl','cginc']):text_leads.append(row)
shader_index=Path(r'D:\99.기타\out_dkbi\asset_indices_by_type\Shader.csv');shader_leads=[];shader_rows=0;shader_blank_names=0;terrain_rows=[]
with shader_index.open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        shader_rows+=1;shader_blank_names+=not bool(row.get('name'))
        if row.get('path_id')=='998575624410370492':terrain_rows.append(row)
        if row.get('name','').startswith('SUPERCAT/Dokkaebi/') or row.get('name')=='SUPERCAT/Dokkaebi/TerrainLit':shader_leads.append(row)
evidence_path=Path(r'C:\00.SVN\Action\dkbi-replica\reference\field_material_reconstruction_evidence.json');evidence=json.loads(evidence_path.read_text('utf-8'))
native={k:evidence.get(k) for k in ['shaderName','shaderPathId','shaderNativeBytesSha256','shaderNativeBytesVerified','nativeShaderBaked','platforms','stageCounts','compiledBlobBytes','compiledBlobSha256','originalSerializedUnityVersion']}
d={'provenance':'verified scoped file/catalog/index scan; Action native shader evidence attributed','install_root':str(install),'install_file_count':files_scanned,'source_extensions_checked':sorted(extensions),'actual_source_files':actual,'catalog_source':str(catalog_path),'logical_source_style_ids':logical,'text_asset_index_source':str(text_index),'text_asset_rows_scanned':text_rows,'named_text_asset_leads':text_leads,'custom_native_shader_index_rows':shader_leads,'terrain_native_evidence_source':str(evidence_path),'terrain_native_evidence':native,'limitations':['No filenames found does not prove absent embedded text inside every binary archive. TextAsset payloads were not exhaustively content-scanned.','Catalog .shader/.shadergraph logical IDs may designate baked native Shader objects, not editable source.','Native compiled variants/ShaderLab parsed state do not establish original HLSL/ShaderGraph content.','Editor isolated native-file import/load/render success remains Action test ownership; cannot infer success from UnityFS or DXBC existence.','No new input/movement/nav/LUT native body or RVA recovered this pass.']}
d.update(shader_index_rows_scanned=shader_rows,shader_index_blank_names=shader_blank_names,terrain_pathid_index_rows=terrain_rows,action_evidence_generated_at=evidence.get('generatedAtUtc'))
d['limitations'].append('Shader index names are unavailable for blank-name rows; zero name matches is NOT proof native custom shader absence. Terrain exact pathID rows are independently listed. Historical Action project readiness statements are not reused as current facts.')
(out/'shader_source_availability.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'install_files':files_scanned,'actual_source_files':len(actual),'catalog_source_style_ids':len(logical),'text_asset_rows':text_rows,'named_text_asset_leads':len(text_leads),'native_custom_shader_rows':len(shader_leads),'native_terrain':native}))
