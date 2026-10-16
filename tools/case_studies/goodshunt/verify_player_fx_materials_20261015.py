from pathlib import Path
import json,hashlib
from PIL import Image
p=Path(__file__).resolve().parent/'player_fx_material_audit_20261015';data=json.loads((p/'chains.json').read_text(encoding='utf-8'))
for rec in data['texture_records']+data['sprite_records']:
 info=rec['png'];fn=p/info['file'];assert hashlib.sha256(fn.read_bytes()).hexdigest()==info['sha256']
 with Image.open(fn) as im:
  assert list(im.size)==info['size']
  if 'pixel_sha256' in info:assert hashlib.sha256(im.tobytes()).hexdigest()==info['pixel_sha256']
for m in data['materials']:print('MATERIAL',m['file'],m['path_id'],m['shader_resolved'])
print('PASS PNG29 SHA/dimensions, texture16 pixelSHA; subtree counts',[len(g['particles']) for g in data['ps_uv_groups']])
