import json
from pathlib import Path
r=Path(__file__).parent
names={'UniversalRenderPipelineAsset','UniversalRendererData','UniversalRenderPipelineGlobalSettings','ScriptableRendererData','ScriptableRendererFeature','RendererType','RenderingMode','DepthPrimingMode','CopyDepthMode','IntermediateTextureMode','UniversalRenderPipeline','DebugShaderResources','ProbeVolumeResources','StencilStateData'}
rows=[]
extra=set()
if (root_path:=r/'urp/urp_asset_schema_candidates.json').exists():
    for feature in json.loads(root_path.read_text('utf-8'))['features']:
        s=feature['script_declaration'];extra.add((s['m_ClassName'],s['m_Namespace'],s['m_AssemblyName']+'.dll'))
with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as f:
    for line in f:
        t=json.loads(line)
        if (t['name'] in names and t['image']=='Unity.RenderPipelines.Universal.Runtime.dll') or (t['name'],t['ns'],t['image']) in extra:rows.append(t)
d={'provenance':'verified original metadata declarations','source':'global-metadata.dat streamed schema','types':rows,'limitations':['Definition offsets and type indices are not asset field byte offsets, native runtime instance offsets or method RVA.','Original package semver not proven by declarations or Unity engine version.']}
(r/'metadata/urp_original_declarations.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'name':t['name'],'index':t['index'],'fields':[x['name'] for x in t['fields']]} for t in rows]))
