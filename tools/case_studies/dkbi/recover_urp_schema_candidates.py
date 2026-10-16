import json,struct,hashlib,re,sys,importlib.util
from pathlib import Path
r=Path(__file__).parent;out=r/'urp';out.mkdir(exist_ok=True)
evidence_path=Path(r'C:\00.SVN\Action\dkbi-replica\reference\original_render_pipeline_evidence.json');evidence=json.loads(evidence_path.read_text('utf-8'))
pkg=Path(r'C:\00.SVN\Action\dkbi-replica\DKBI\Library\PackageCache\com.unity.render-pipelines.universal@40f8b5b9939e')
decl=json.loads((r/'metadata/urp_original_declarations.json').read_text('utf-8'));types={x['name']:x for x in decl['types']}
class Reader:
    def __init__(self,b):self.b=b;self.p=0;self.fields=[]
    def take(self,name,kind):
        start=self.p
        if kind=='PPtr':value=dict(zip(['fileID','pathID'],struct.unpack_from('<iq',self.b,self.p)));self.p+=12
        elif kind=='PPtrArray':
            n=struct.unpack_from('<i',self.b,self.p)[0];self.p+=4;assert 0<=n<128;value=[]
            for i in range(n):value.append(dict(zip(['fileID','pathID'],struct.unpack_from('<iq',self.b,self.p))));self.p+=12
        elif kind=='Int64Array':
            n=struct.unpack_from('<i',self.b,self.p)[0];self.p+=4;assert 0<=n<128;value=list(struct.unpack_from('<'+'q'*n,self.b,self.p));self.p+=8*n
        elif kind=='bool':
            value=self.b[self.p];assert value in [0,1];self.p+=1;self.p=(self.p+3)&~3
        elif kind in ['Vector2','Vector3']:
            n=int(kind[-1]);value=list(struct.unpack_from('<'+'f'*n,self.b,self.p));self.p+=4*n
        else:value=struct.unpack_from('<f' if kind=='float' else '<i',self.b,self.p)[0];self.p+=4
        self.fields.append({'field_name_candidate':name,'kind_candidate':kind,'asset_relative_offset':start,'byte_size':self.p-start,'raw_hex':self.b[start:self.p].hex(),'value':value});return value
    def header(self):
        n=struct.unpack_from('<i',self.b,28)[0];name=self.b[32:32+n].decode('utf-8');self.p=(32+n+3)&~3;return name
pipeline=Reader(bytes.fromhex(evidence['pipelineAsset']['nativeRawHex']));pipeline.header()
source_text=(pkg/'Runtime/Data/UniversalRenderPipelineAsset.cs').read_text('utf-8-sig')
field_types={m.group(2):m.group(1) for m in re.finditer(r'\b(\w+(?:\[\])?)\s+(m_\w+|k_AssetVersion|k_AssetPreviousVersion)\s*(?:=|;)',source_text)}
names=[x['name'] for x in types['UniversalRenderPipelineAsset']['fields']];names=names[names.index('k_AssetVersion'):names.index('m_VolumeProfile')+1]
for name in names:
    kind=field_types[name]
    if kind=='ScriptableRendererData[]':kind='PPtrArray'
    elif kind in ['ScriptableRendererData','VolumeProfile']:kind='PPtr'
    pipeline.take(name,kind)
lookup={x['field_name_candidate']:x for x in pipeline.fields};assert lookup['m_RendererDataList']['asset_relative_offset']==84 and len(lookup['m_RendererDataList']['value'])==3
assert [x['pathID'] for x in lookup['m_RendererDataList']['value']]==[16708,16711,16709]
assert 0<=lookup['m_DefaultRendererIndex']['value']<3
renderers=[];feature_ids=set()
debug=['debugReplacementPS','hdrDebugViewPS'];probes=['probeVolumeDebugShader','probeVolumeFragmentationDebugShader','probeVolumeOffsetDebugShader','probeVolumeSamplingDebugShader','probeSamplingDebugMesh','probeSamplingDebugTexture','probeVolumeBlendStatesCS']
for entry in evidence['rendererCandidates']:
    target=entry['target'];rd=Reader(bytes.fromhex(target['nativeRawHex']));name=rd.header()
    for field in debug:rd.take('debugShaders.'+field,'PPtr')
    for field in probes:rd.take('probeVolumeResources.'+field,'PPtr')
    features=rd.take('m_RendererFeatures','PPtrArray');rd.take('m_RendererFeatureMap','Int64Array');rd.take('m_UseNativeRenderPass','bool');rd.take('xrSystemData','PPtr');rd.take('postProcessData','PPtr')
    for field in ['m_AssetVersion','m_PrepassLayerMask','m_OpaqueLayerMask','m_TransparentLayerMask']:rd.take(field,'int')
    rd.take('m_DefaultStencilState.overrideStencilState','bool')
    for field in ['stencilReference','stencilCompareFunction','passOperation','failOperation','zFailOperation']:rd.take('m_DefaultStencilState.'+field,'int')
    rd.take('m_ShadowTransparentReceive','bool')
    for field in ['m_RenderingMode','m_DepthPrimingMode','m_CopyDepthMode','m_DepthAttachmentFormat','m_DepthTextureFormat']:rd.take(field,'int')
    rd.take('m_AccurateGbufferNormals','bool');rd.take('m_IntermediateTextureMode','int');assert rd.p==len(rd.b)
    feature_ids.update(x['pathID'] for x in features if x['fileID']==0 and x['pathID'])
    renderers.append({'pathID':target['pathId'],'name':name,'source_sha256':target['sha256'],'source_serialized_offset':target['sourceSerializedObjectOffset'],'raw_hex':rd.b.hex(),'fields':rd.fields,'full_consumption':rd.p==len(rd.b)})
# Only original native feature objects requested here; no texture/shader extraction.
sys.path.insert(0,r'D:\99.기타\out_dkbi_probe\_deps')
tool=Path(r'C:\00.SVN\Action\dkbi-replica\tools\recover_original_render_pipeline.py')
spec=importlib.util.spec_from_file_location('bounded_pipeline_reader',tool);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
source=mod.SourceRanges(Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\data.unity3d'));assets,asset_meta=source.metadata('globalgamemanagers.assets')
from UnityPy.streams import EndianBinaryReader
from UnityPy.helpers.TypeTreeHelper import read_typetree
features=[]
for pathid in sorted(feature_ids):
    obj=assets.objects[pathid];raw=source.read('globalgamemanagers.assets',obj.byte_start,obj.byte_size);assert len(raw)<64*1024
    fid,scriptid=struct.unpack_from('<iq',raw,16);assert fid==0;script=assets.objects[scriptid];sraw=source.read('globalgamemanagers.assets',script.byte_start,script.byte_size)
    tree=read_typetree(script._get_typetree_node(),EndianBinaryReader(sraw,endian=assets.header.endian),byte_size=len(sraw),check_read=True)
    n=struct.unpack_from('<i',raw,28)[0];body=(32+n+3)&~3
    features.append({'pathID':pathid,'type':obj.type.name,'source_serialized_offset':obj.byte_start,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex(),'name':raw[32:32+n].decode('utf-8'),'script_pathID':scriptid,'script_declaration':tree,'script_sha256':hashlib.sha256(sraw).hexdigest(),'active_field_candidate':{'asset_relative_offset':body,'raw_byte':raw[body],'semantic':'ScriptableRendererFeature.m_Active candidate, not original custom typetree'}})
d={'provenance':'verified source bytes and metadata / inferred asset field schema','source_evidence':str(evidence_path),'original_engine_version':source.engine,'original_package_version':{'status':'unknown','reason':'Engine/version13 schema is not package semver proof'},'reference_package':{'path':str(pkg),'version':json.loads((pkg/'package.json').read_text('utf-8'))['version'],'role':'Local compatible reference, NOT original package version'},'pipeline':{'pathID':16707,'sha256':evidence['pipelineAsset']['sha256'],'raw_hex':pipeline.b.hex(),'fields':pipeline.fields,'decoded_prefix_bytes':pipeline.p,'uninterpreted_tail_offset':pipeline.p,'uninterpreted_tail_hex':pipeline.b[pipeline.p:].hex()},'renderers':renderers,'features':features,'source_metadata':asset_meta,'limitations':['Original custom MonoBehaviour typetree absent. Field labels/order inferred from original declarations plus local17.3.0 source; offsets/raw bytes independently verified.','Renderer features are saved list membership, not proof executed/active under runtime camera routing.','Original method RVA/native bodies and package semver unknown; GlobalSettings managed reference schema not completely decoded.']}
(out/'urp_asset_schema_candidates.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pipeline_prefix_consumed':pipeline.p,'pipeline_bytes':len(pipeline.b),'default_renderer_candidate':lookup['m_DefaultRendererIndex']['value'],'renderers':[(x['pathID'],len(next(f['value'] for f in x['fields'] if f['field_name_candidate']=='m_RendererFeatures'))) for x in renderers],'feature_classes':[(x['pathID'],x['script_declaration']['m_ClassName']) for x in features]}))
