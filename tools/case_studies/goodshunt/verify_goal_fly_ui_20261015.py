from pathlib import Path
import json,hashlib
p=Path(__file__).resolve().parent;folder=p/'goal_fly_ui_audit_20261015';j=json.loads((folder/'native_ui_chain.json').read_text(encoding='utf-8'))
assert len(j['roots'])==1 and len(j['nodes'])==2 and not j['errors'] and not j['sprites']
for n in j['nodes']:
 print('NODE',n['path'],'TR',n['transform_id'],'GO',n['game_object_id'],'size',n['transform'].get('m_SizeDelta'),'position',n['transform']['m_LocalPosition'],'scale',n['transform']['m_LocalScale'])
 for c in n['components']:
  if c.get('script_class')=='Image':print('IMAGE',c['path_id'],'sprite',c['fields']['m_Sprite'],'color',c['fields']['m_Color'])
receipt=dict(native_ui_chain_sha256=hashlib.sha256((folder/'native_ui_chain.json').read_bytes()).hexdigest(),roots=1,nodes=2,sprites=0,errors=0,boundary='Stored Sprite null; dynamic UID icon not extracted/replaced here.')
(folder/'verification.json').write_text(json.dumps(receipt,indent=1),encoding='utf-8');print('PASS',receipt)
