from pathlib import Path
import json,hashlib
from PIL import Image
p=Path(__file__).resolve().parent/'goal_card_ui_audit_20261015';j=json.loads((p/'native_ui_chain.json').read_text(encoding='utf-8'));assert not j['errors'];rows=[]
for r in j['sprites']:
 info=r['png'];fn=p/info['file'];assert hashlib.sha256(fn.read_bytes()).hexdigest()==info['sha256']
 with Image.open(fn) as im:assert list(im.size)==info['size'] and hashlib.sha256(im.tobytes()).hexdigest()==info['pixel_sha256']
 rows.append(dict(file=r['file'],path_id=r['path_id'],name=r['fields']['m_Name'],png=info['file'],size=info['size']))
(p/'sprite_index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1),encoding='utf-8')
for r in rows:print(r)
for n in j['nodes']:
 for c in n['components']:
  if c.get('path_id')=='6793':print('TICK',n['file'],c['fields'].get('m_Sprite'))
result=dict(nodes=len(j['nodes']),sprites=len(rows),errors=len(j['errors']),native_json_sha256=hashlib.sha256((p/'native_ui_chain.json').read_bytes()).hexdigest(),png_file_size_pixel_sha_pass=True)
(p/'verification.json').write_text(json.dumps(result,indent=1),encoding='utf-8');print('PASS',result)
