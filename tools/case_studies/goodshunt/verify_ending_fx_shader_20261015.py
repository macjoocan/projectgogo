from pathlib import Path
import json,hashlib
from PIL import Image
p=Path(__file__).resolve().parent/'ending_fx_shader_audit_20261015'
inv=json.loads((p/'inventory.json').read_text())[0]
for seg in inv['segments']:
 for pr in seg['programs']:
  raw=(p/'ending_fx'/pr['file']).read_bytes()
  assert len(raw)==pr['code_bytes'] and hashlib.sha256(raw).hexdigest()==pr['sha256'] and pr['keyword_prefix_verified']
for pid in (1141,842):
 r=json.loads((p/f'resources_assets_{pid}.json').read_text());png=p/r['png']['file']
 assert hashlib.sha256(png.read_bytes()).hexdigest()==r['png']['sha256']
 with Image.open(png) as im:assert list(im.size)==r['png']['size'] and hashlib.sha256(im.tobytes()).hexdigest()==r['png']['pixel_sha256']
for m in json.loads((p/'materials.json').read_text()):
 vals=dict(m['fields']['m_SavedProperties']['m_Floats'])
 print(m['path_id'],{k:vals.get(k) for k in ('_blend','_Blend','_Zwrite','_ZWrite','_Ztest','_Cull','_SrcBlend','_DstBlend','_Distance')})
print('PASS compiler4 SHA/length/keywords and 2 PNG size/file/pixel SHA')
