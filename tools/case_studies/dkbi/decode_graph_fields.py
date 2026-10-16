import json,struct,collections
from pathlib import Path
root=Path(__file__).parent
def hash64(s):
    h=14695981039346656037
    for c in s.encode('utf-16le'):h=(h^c)*1099511628211&0xffffffffffffffff
    return h
hash_names=collections.defaultdict(set);types={};schemas=[]
for line in (root/'metadata/metadata_types.jsonl').open(encoding='utf-8'):
    t=json.loads(line)
    if 'Behavior' in t['ns'] or t['index'] in [40545,40546,40547]:
        schemas.append(t);types.setdefault(t['name'],[]).append(t)
        for f in t['fields']:hash_names[hash64(f['name'])].add(f['name'])
(root/'metadata/behavior_node_schemas.json').write_text(json.dumps(schemas,ensure_ascii=False,indent=2),encoding='utf-8')
class Parser:
    def __init__(self,b):self.b=b;self.p=0
    def read(self,fmt):
        n=struct.calcsize(fmt);assert self.p+n<=len(self.b);v=struct.unpack_from(fmt,self.b,self.p)[0];self.p+=n;return v
    def string(self):
        n=self.read('<I');assert self.p+n<=len(self.b);s=self.b[self.p:self.p+n].decode('utf-8');self.p+=n;return s
    def value(self,depth=0):
        assert depth<10;offset=self.p;tag=self.read('<B')
        if tag==0:v=None
        elif tag==1:v=self.read('<B');assert v in [0,1];v=bool(v)
        elif tag==2:v=self.read('<q')
        elif tag==3:v=self.read('<d')
        elif tag==4:v=self.string()
        elif tag==5:
            n=self.read('<I');assert n<10000;v=[self.value(depth+1) for _ in range(n)]
        elif tag==6:
            n=self.read('<I');assert n<10000;v=[]
            for _ in range(n):v.append(dict(key=self.string(),value=self.value(depth+1)))
        else:raise ValueError('unknown tag '+str(tag)+' at '+str(offset))
        return dict(tag=tag,relative_offset=offset,value=v,provenance='inferred',units='unknown')
summary=[]
for file in sorted((root/'graphs').glob('*.json')):
    if file.name=='graph_validation.json' or file.name.endswith('_decoded.json'):continue
    graph=json.loads(file.read_text('utf-8'));matched=0;unknown=0;errors=[]
    for node in graph['nodes']:
        parser=Parser(bytes.fromhex(node['payload_hex']));node['fields']=[]
        try:
            count=parser.read('<I')
            for _ in range(count):
                at=parser.p;hash_=parser.read('<Q');value=parser.value();names=hash_names[hash_]
                name=next(iter(names)) if len(names)==1 else None
                node['fields'].append(dict(hash=hex(hash_),field_name=name,hash_match=name is not None,hash_algorithm='FNV1a64 UTF16LE' if name else None,source_binary_offset=node['payload_offset']+at,serialized_value=value,provenance='inferred',metadata_field_candidates=[dict(type_index=t['index'],namespace=t['ns'],field=f) for t in types.get(node['type_name'],[]) for f in t['fields'] if f['name']==name]))
                matched+=int(name is not None);unknown+=int(name is None)
            assert parser.p==len(parser.b),(parser.p,len(parser.b))
            node['payload_status']='full_consumption'
        except Exception as exc:node['payload_status']='partial';node['decode_error']=str(exc);errors.append(dict(node=node['id'],error=str(exc)))
    graph['field_decoder_limitations']='Field hashes mathematically match metadata names. Type tags inferred from consistent layout; runtime parser/code not disassembled. Timing units and gameplay semantics remain unknown.'
    (root/'graphs'/(file.stem+'_decoded.json')).write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8')
    summary.append(dict(name=file.stem,nodes=len(graph['nodes']),edges=len(graph['edges']),hash_matches=matched,unknown_hashes=unknown,errors=errors))
(root/'graphs/field_decode_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
