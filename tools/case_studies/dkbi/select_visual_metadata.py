import json
from pathlib import Path
root=Path(__file__).parent
names={'SpriteRendererExtend','PropSpriteRendererExtend','AvatarController'}
rows=[]
with (root/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as f:
    for line in f:
        r=json.loads(line)
        if r.get('name') in names:
            rows.append(r)
out={'provenance':'verified','source':'metadata/metadata_types.jsonl','limitations':['Metadata declaration offsets are not runtime instance offsets or method RVA.','Method names establish candidate LUT hooks, not decoded execution order or shader equations.'], 'types':rows}
(root/'metadata/player_visual_types.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for r in rows:
    print(json.dumps({'name':r['name'],'keys':list(r),'fields':r.get('fields'), 'methods':[m.get('name') for m in r.get('methods',[])]},ensure_ascii=False))
