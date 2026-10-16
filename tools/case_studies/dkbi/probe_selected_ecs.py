import ast,struct,json,collections,hashlib,csv,traceback
from pathlib import Path
root=Path(__file__).parent;out=root/'ecs_selected';out.mkdir(exist_ok=True)
source=Path(r'D:\99.기타\levelscope\out\plantsonfire\finalize_dots.py')
parser_text=source.read_text('utf-8-sig')
old="ai=v('q',off);ec=v('i',off+16);cap=v('i',off+20);assert 0<=ai<ac and 0<=ec<=cap<=2040"
new="ai=v('i',off);ec=v('i',off+4);cap=None;assert 0<=ai<ac and 0<=ec<=2040"
assert parser_text.count(old)==1
module=ast.parse(parser_text.replace(old,new))
nodes=[n for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='IDS' for t in n.targets) or isinstance(n,ast.FunctionDef) and n.name=='parse']
class AdjustVersion(ast.NodeTransformer):
    def visit_Constant(self,node):
        if node.value==76:return ast.copy_location(ast.Constant(value=78),node)
        return node
safe=AdjustVersion().visit(ast.Module(body=nodes,type_ignores=[]));ast.fix_missing_locations(safe)
scope=dict(struct=struct,collections=collections);exec(compile(safe,str(source),'exec'),scope)
base=Path(r'D:\99.기타\out_dkbi');folder=base/'source/dokkaebi_Data/SP/Resource/ECS-Map-High/EntityScenes'
guids={'field_101002':'489220e256d0cee4c8e7ce6ddb38c8d4','town_100':'a4af9541f7061bb4ea93bdcfe628475f'}
relations=list(csv.DictReader((base/'analysis/ECS-Map-High_archive_relations.csv').open(encoding='utf-8-sig')))
report=[]
for label,guid in guids.items():
    file=folder/(guid+'.0.entities');b=file.read_bytes();rec=dict(provenance='verified',label=label,guid=guid,source=str(file),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),header_source=str(folder/(guid+'.entityheader')),complete_component_decode=False)
    try:
        d=scope['parse'](b);rec.update(container=d,status='container_archetypes_chunks_validated')
        chunknode=next(n for n in d['nodes'] if n['kind']=='Chunks');ids=[]
        for i,ch in enumerate(d['chunks']):
            offset=chunknode['data_offset']+i*16384;rowids=[dict(zip(['index','version'],struct.unpack_from('<ii',b,offset+64+j*8))) for j in range(ch['entities'])]
            assert all(x['index']>=0 and x['version']>0 for x in rowids);ids.extend((x['index'],x['version']) for x in rowids);ch['entity_ids']=rowids
        assert len(ids)==len(set(ids))
    except Exception as exc:rec.update(status='unresolved',error=repr(exc),traceback=traceback.format_exc())
    refs=[r for r in relations if r['relation']=='Object' and r['target_id'].startswith(guid+':')];archives=sorted({r['archive_id'] for r in refs});rec['object_archive_records']=refs;rec['archive_dependencies']=[r for r in relations if r['archive_id'] in archives and r['relation']=='Dependency']
    (out/(label+'.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8');report.append(dict(label=label,status=rec['status'],error=rec.get('error'),entities=rec.get('container',{}).get('entities'),archives=archives))
(out/'verification.json').write_text(json.dumps(dict(results=report,parser_source=str(source),parser_adaptation='Version 78: inferred int32 archetype at +0 and count at +4, consistent with metadata Chunk declarations. Capacity not decoded. Bounds, archetype totals and unique Entity IDs at +64 validated independently on both files.',limitations=['Chunk header layout inferred, original reader body unavailable','Stable hash->component name unresolved','LocalTransform/mesh/material ECS component values not decoded']),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
