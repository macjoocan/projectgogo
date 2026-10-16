from pathlib import Path
import json,zipfile
p=Path(__file__).resolve().parent
u=json.loads((p/'end_flow_audit_20261015/ui_native_nodes.json').read_text(encoding='utf-8'))
print('UI_KEYS',list(u))
for key,val in u.items():
 if isinstance(val,list) and val and isinstance(val[0],dict): print('UI_LIST',key,len(val),'SAMPLE',str(val[0])[:1900])
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
  r=json.loads(line)
  if r.get('script_class') not in ('PlayerFxComponent','PlayerComponent','StateLevelCompleteTransition'):continue
  if r.get('serialized_file') not in ('sharedassets3.assets','level2'):continue
  if not r.get('json_file'):continue
  obj=json.loads(z.read(r['json_file']))
  print('FX',r['script_class'],r['serialized_file'],r['path_id'],r['json_file'],json.dumps(obj)[:7500])
