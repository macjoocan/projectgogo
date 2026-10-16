"""Sequential, bounded container parsing; does not extract renderer assets."""
import ast, json, struct, collections, hashlib
from pathlib import Path
r=Path(__file__).parent; out=r/'ecs_selected'
src=Path(r'D:\99.기타\levelscope\out\plantsonfire\finalize_dots.py')
text=src.read_text('utf-8-sig')
old="ai=v('q',off);ec=v('i',off+16);cap=v('i',off+20);assert 0<=ai<ac and 0<=ec<=cap<=2040"
assert text.count(old)==1
text=text.replace(old,"ai=v('i',off);ec=v('i',off+4);cap=None;assert 0<=ai<ac and 0<=ec<=2040")
module=ast.parse(text)
nodes=[n for n in module.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='IDS' for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name=='parse')]
class Version(ast.NodeTransformer):
    def visit_Constant(self,n): return ast.copy_location(ast.Constant(value=78),n) if n.value==76 else n
safe=Version().visit(ast.Module(body=nodes,type_ignores=[]));ast.fix_missing_locations(safe)
scope={'struct':struct,'collections':collections};exec(compile(safe,str(src),'exec'),scope)
inventory=json.loads((out/'field_101002_child_probe.json').read_text('utf-8'))['field_child_inventory']
rows=[]; hashes=set()
for child in inventory:
    for section in child['entity_files']:
        p=Path(section['path']); assert p.stat().st_size<16*1024*1024
        b=p.read_bytes(); c=scope['parse'](b); label='field_child_'+p.name.replace('.entities','').replace('.','_')
        record={'provenance':'verified','guid':child['guid'],'source':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'container':c}
        (out/(label+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        hashes.update(c['type_hashes']);rows.append({'label':label,'guid':child['guid'],'source':str(p),'bytes':len(b),'sha256':record['sha256'],'entities':c['entities'],'chunks':len(c['chunks']),'type_count':len(c['type_hashes'])})
        del b,c,record
report={'provenance':'verified','sections':rows,'type_hashes':sorted(hashes),'limitations':['Container bytes and counts only; type names, offsets and runtime semantics are separate candidates.']}
(out/'field_all_children_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'sections':len(rows),'entities':sum(x['entities'] for x in rows),'unique_hashes':len(hashes),'max_file_bytes':max(x['bytes'] for x in rows)}))
