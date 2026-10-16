import json
from pathlib import Path
r=Path(__file__).parent
wrapper=json.loads((r/'field_101002/scene_wrapper.json').read_text('utf-8'))
print('WRAPPER_TYPE',type(wrapper).__name__)
if isinstance(wrapper,dict):print('WRAPPER_KEYS',list(wrapper));wrapper=wrapper.get('objects',[])
for x in wrapper:
    if x.get('type')=='MonoBehaviour':
        d=x['data'];print('MB',x['path_id'],json.dumps(d,ensure_ascii=False)[:4000])
names={'LeafMeshBudget','LeafMeshVariant','LeafMeshVariantCatalog','RootPersistent','LoadedLeafMeshBudget'}
selected=[]
with (r/'metadata/metadata_types.jsonl').open(encoding='utf-8-sig') as f:
    for l in f:
        x=json.loads(l)
        if x['name'] in names:selected.append(x)
(r/'metadata/field_render_hooks.json').write_text(json.dumps({'provenance':'verified','types':selected,'limitations':['Declarations only; no method body/RVA restoration']},ensure_ascii=False,indent=2),encoding='utf-8')
for x in selected:print('TYPE',x['name'],'FIELDS',[i['name'] for i in x['fields']],'METHODS',[i['name'] for i in x['methods']])
catalog=json.loads(Path(r'D:\99.기타\out_dkbi_probe\addressables_catalog.json').read_text('utf-8'))
ids=[{'internal_id_index':i,'path':p} for i,p in enumerate(catalog['m_InternalIds']) if 'dkb_dungeon_beginner' in p.lower()]
(r/'field_101002/catalog_named_field_assets.json').write_text(json.dumps({'provenance':'verified','assets':ids},ensure_ascii=False,indent=2),encoding='utf-8')
print('CATALOG_FIELD_ASSETS',len(ids),[x['path'] for x in ids[:30]])
