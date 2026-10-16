import json,ast,struct,collections,hashlib,csv
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';base=Path(r'D:\99.기타\out_dkbi');folder=base/'source/dokkaebi_Data/SP/Resource/ECS-Map-High/EntityScenes'
refs=json.loads((out/'field_101002_scene_ref_candidates.json').read_text('utf-8'))['entityheader_guid_byte_matches'];guids=sorted({x['matched_guid'] for x in refs})
inventory=[]
for g in guids:
    inventory.append({'guid':g,'source_ref':[x for x in refs if x['matched_guid']==g], 'entity_files':[{'path':str(p),'bytes':p.stat().st_size} for p in sorted(folder.glob(g+'.*.entities'))]})
source=Path(r'D:\99.기타\levelscope\out\plantsonfire\finalize_dots.py');text=source.read_text('utf-8-sig');old="ai=v('q',off);ec=v('i',off+16);cap=v('i',off+20);assert 0<=ai<ac and 0<=ec<=cap<=2040";assert text.count(old)==1
text=text.replace(old,"ai=v('i',off);ec=v('i',off+4);cap=None;assert 0<=ai<ac and 0<=ec<=2040");module=ast.parse(text)
nodes=[n for n in module.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='IDS' for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name=='parse')]
class Version(ast.NodeTransformer):
    def visit_Constant(self,n):return ast.copy_location(ast.Constant(value=78),n) if n.value==76 else n
safe=Version().visit(ast.Module(body=nodes,type_ignores=[]));ast.fix_missing_locations(safe);scope={'struct':struct,'collections':collections};exec(compile(safe,str(source),'exec'),scope)
first=refs[0]['matched_guid'];records=[]
for p in sorted(folder.glob(first+'.*.entities')):
    assert p.stat().st_size<64*1024*1024
    b=p.read_bytes();d=scope['parse'](b);records.append({'provenance':'verified','guid':first,'source':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'container':d,'limitations':['Container only; component semantic decode pending']})
archives=set();relations=[]
with (base/'analysis/ECS-Map-High_archive_relations.csv').open(encoding='utf-8-sig') as f:
    for x in csv.DictReader(f):
        if x['relation']=='Object' and x['target_id'].split(':')[0]==first:relations.append(x);archives.add(x['archive_id'])
deps=[]
with (base/'analysis/ECS-Map-High_archive_relations.csv').open(encoding='utf-8-sig') as f:
    for x in csv.DictReader(f):
        if x['archive_id'] in archives and x['relation']=='Dependency':deps.append(x)
data={'provenance':'verified','hierarchy_role':'inferred child-streamed scene from GUID byte match','field_child_inventory':inventory,'selected_child_guid':first,'selected_child_sections':records,'object_archives':relations,'archive_dependencies':deps,'limitations':['Only one of 16 field child GUIDs parsed this pass','Root 20 entities does not mean field has only 20 entities','Native scene loading semantics not disassembled']}
(out/'field_101002_child_probe.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'child_guid':first,'inventory_guids':len(guids),'inventory_sections':sum(len(x['entity_files']) for x in inventory),'selected_sections':[{'bytes':x['bytes'],'entities':x['container']['entities'],'types':len(x['container']['type_hashes']),'chunks':len(x['container']['chunks'])} for x in records],'archive_ids':sorted(archives),'dependencies':len(deps)}))
