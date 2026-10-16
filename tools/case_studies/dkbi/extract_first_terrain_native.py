import sys,json,base64,hashlib
from pathlib import Path
sys.path.insert(0,r'D:\99.기타\out_dkbi_probe\_deps')
import UnityPy
r=Path(__file__).parent;out=r/'ecs_selected/terrain_first';out.mkdir(exist_ok=True)
source=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\SP\Resource\ECS-Map-High\ContentArchives\72fd49996b09db898e4d17f42152948f')
env=UnityPy.load(str(source));records=[];external=[]
def default(x):
    if isinstance(x,(bytes,bytearray)):return {'encoding':'base64','data':base64.b64encode(x).decode()}
    raise TypeError(type(x).__name__)
for obj in env.objects:
    records.append({'path_id':obj.path_id,'type':obj.type.name,'byte_start':obj.byte_start,'byte_size':obj.byte_size})
    if not external:
        external=[{'file_id':i+1,'path':x.path,'guid':str(x.guid),'type':x.type} for i,x in enumerate(obj.assets_file.externals)]
    if obj.type.name in {'Mesh','Material','MonoBehaviour','Texture2D'}:
        t=obj.read_typetree();dest=out/(obj.type.name+'_'+str(obj.path_id)+'.json');dest.write_text(json.dumps({'provenance':'verified','source':str(source),'path_id':obj.path_id,'type':obj.type.name,'data':t},ensure_ascii=False,indent=2,default=default),encoding='utf-8')
        if obj.type.name=='Mesh':print('Mesh',t.get('m_Name'),'vertex_count',t.get('m_VertexData',{}).get('m_VertexCount'),'submeshes',t.get('m_SubMeshes'),'bounds',t.get('m_LocalAABB'))
(out/'source_manifest.json').write_text(json.dumps({'provenance':'verified','source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':records,'externals':external,'limitations':['Native Mesh typetree preserved; no OBJ axis reflection/recentering applied','Scene Transform/material slot binding not completed by mesh presence alone']},ensure_ascii=False,indent=2),encoding='utf-8')
print('externals',external)
