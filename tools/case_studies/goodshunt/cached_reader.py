from pathlib import Path
import json,zipfile,types,hashlib
from levelscope import typetree
import bounded_typetree
root=Path(__file__).resolve().parent
base=root/'input_prepared'
expected={
 'metadata_sha256':hashlib.sha256((base/'assets/bin/Data/Managed/Metadata/global-metadata.dat').read_bytes()).hexdigest(),
 'il2cpp_sha256':hashlib.sha256((base/'lib/armeabi-v7a/libil2cpp.so').read_bytes()).hexdigest(),
}
class CachedGenerator:
    def __init__(self,backend):
        self.z=zipfile.ZipFile(root/f'typetrees_{backend}.zip')
        index=json.loads(self.z.read('index.json'))
        if index['unity_version']!='2022.3.62f2' or any(index[k]!=v for k,v in expected.items()):
            raise ValueError('Typetree cache provenance mismatch')
        self.entries={(r['assembly'],r['fullname']):r['entry'] for r in index['success']}
    def get_nodes(self,assembly,fullname):
        raw=json.loads(self.z.read(self.entries[(assembly,fullname)]))
        normalized=[]
        extra_levels=[]
        for original in raw:
            n=dict(original)
            level=n['m_Level']
            while extra_levels and level <= extra_levels[-1]: extra_levels.pop()
            n['m_Level'] += len(extra_levels)
            if level == 1 and n['m_Name'] == 'm_Enabled': n['m_MetaFlag'] |= 16384
            if n['m_Type'] == 'Array' and n['m_Name'] != 'Array':
                n['m_Type']='vector'
                normalized.append(n)
                child=dict(n,m_Type='Array',m_Name='Array',m_Level=n['m_Level']+1)
                normalized.append(child)
                extra_levels.append(level)
            else: normalized.append(n)
        return [types.SimpleNamespace(**n) for n in normalized]
def cached_open(cls,input_path,cfg,unity_version,log=print,registry=None):
    gens={b:CachedGenerator(b) for b in typetree.DEFAULT_BACKENDS}
    log('[typetree] Three isolated backend caches; no native generator resident')
    return cls(gens,log=log,registry=registry)
typetree.MonoReader.open=classmethod(cached_open)
original_read=typetree.MonoReader.read
header_checks={'passed':0,'failed':0}
def checked_read(self,obj):
    data=None
    cls=None
    provided=getattr(obj.serialized_type,'node',None)
    if provided is not None:
        try:
            data=obj.read_typetree()
            ref=typetree.script_ref(obj,self.registry)
            cls=ref.cls if ref else provided.m_Type
            self.ok+=1
        except Exception:
            data=None
    if data is None:
        cls,data=original_read(self,obj)
    if data is not None:
        native=obj.read(check_read=False)
        checks=[data.get('m_Name')==native.m_Name]
        for key in ['m_Script','m_GameObject']:
            ptr=getattr(native,key)
            checks.append(data.get(key)=={'m_FileID':ptr.m_FileID,'m_PathID':ptr.m_PathID})
        if not all(checks):
            header_checks['failed']+=1
            self.ok-=1;self.failed+=1
            self.fail_classes['HEADER_MISMATCH:'+str(cls)]=self.fail_classes.get('HEADER_MISMATCH:'+str(cls),0)+1
            return cls,None
        header_checks['passed']+=1
    return cls,data
typetree.MonoReader.read=checked_read
