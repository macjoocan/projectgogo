from pathlib import Path
import json,zipfile,collections,hashlib
root=Path(__file__).resolve().parent
out=root/'ingame_handoff_20261014'
out.mkdir(exist_ok=True)
selected={'PlayerComponent','PlayerFxComponent','PlayerBehavior','JoystickAdapter','CinemachineCameraController',
          'CinemachineVirtualCamera','CinemachineTransposer','CinemachineComposer','CinemachineBrain',
          'GameController','LevelController','HoleSizeUpgrade','IncomeUpgrade','PlayerUpgradeStat','UpgradesDatabase'}
records=[]
with zipfile.ZipFile(root/'results/GoodsHunt_structured_objects.zip') as z:
    with (root/'results/native_object_index.jsonl').open(encoding='utf-8') as f:
        for line in f:
            row=json.loads(line)
            if not (row.get('script_class') in selected or row['type'] in ['PhysicsManager','TimeManager']
                    or (row['type']=='Camera' and row['serialized_file']=='level3')):continue
            if not row.get('json_file'):continue
            records.append({'grade':'original_stored_value','source':row,'fields':json.loads(z.read(row['json_file']))})
(out/'component_fields.json').write_text(json.dumps(records,ensure_ascii=False,indent=1),encoding='utf-8')
hierarchy=[]
with zipfile.ZipFile(root/'results/GoodsHunt_hierarchy.zip') as z:
    for name in ['scenes/level3.json']+[n for n in z.namelist() if n.startswith('prefabs/sharedassets3.assets/')]:
        doc=json.loads(z.read(name))
        def walk(node,parent=''):
            path=parent+'/'+node.get('name','')
            comps=node.get('components',[])
            hits=[c for c in comps if c.get('script') in selected or c.get('type') in ['Camera']]
            if hits:hierarchy.append(dict(archive_entry=name,node_path=path,transform=node.get('transform'),components=hits))
            for child in node.get('children',[]):walk(child,path)
        for node in doc.get('roots',[doc.get('root')] if doc.get('root') else []):walk(node)
(out/'hierarchy_paths.json').write_text(json.dumps(hierarchy,ensure_ascii=False,indent=1),encoding='utf-8')
order=[]
for filename in ['0180_LevelDatabase.json','0181_LevelDatabase.json']:
    src=json.loads((root/'settings'/filename).read_text())
    d=src['stored_fields']
    order.append(dict(source_settings=filename,source=src['provenance'],name=d['m_Name'],loading_mode=d.get('loadingMode'),
                      level_refs=[dict(storage_index=i,**v) for i,v in enumerate(d.get('levelRefs',[]))],
                      boundary='Serialized GUID array order only; GUID-to-native asset and runtime order selection unresolved.'))
(out/'level_guid_order.json').write_text(json.dumps(order,ensure_ascii=False,indent=1),encoding='utf-8')
index=json.loads((root/'level_index.json').read_text());counts=[]
for row in index['levels']:
    if row['name'].lower().startswith(('level_001','level_002','level_003')) or len(counts)<10:
        d=json.loads((root/'levels_json'/row['file']).read_text())
        physical=collections.Counter(p['propUniqueID'] for p in d['props'])
        counts.append(dict(name=row['name'],level_file=row['file'],source=row['source'],path_id=row['path_id'],
                           targets=[dict(unique_id=k,props_record_count=physical[k]) for k in d['goalsUniqueIDs']],
                           goal_mechanic_types=d['goalMechanicTypes'],special_props_count=len(d['specialProps']),
                           grade='calculated_from_stored_records',boundary='Exact props ID equality only; runtime goal quantity, holder contents and special mechanics not verified.'))
(out/'goal_count_candidates.json').write_text(json.dumps(counts,ensure_ascii=False,indent=1),encoding='utf-8')
# Original camera/controller Transform values, not rounded hierarchy representations.
import UnityPy
env=UnityPy.load(str(root/'input_prepared/assets/bin/Data/data.unity3d'))
objects={(o.assets_file.name,o.path_id):o for o in env.objects}
trs=[]
for item in records:
    owner=item['fields'].get('m_GameObject')
    if not owner or owner['m_FileID']!=0 or not owner['m_PathID']:continue
    file=item['source']['serialized_file']
    go=objects.get((file,owner['m_PathID']))
    if go is None:continue
    d=go.read_typetree()
    transforms=[]
    for entry in d['m_Component']:
        ptr=entry['component'];o=objects.get((file,ptr['m_PathID'])) if ptr['m_FileID']==0 else None
        if o and o.type.name in ['Transform','RectTransform']:
            transforms.append(dict(file=file,path_id=o.path_id,type=o.type.name,raw_sha256=hashlib.sha256(o.get_raw_data()).hexdigest(),fields=o.read_typetree()))
    trs.append(dict(component_file=file,component_path_id=item['source']['path_id'],game_object_path_id=go.path_id,name=d['m_Name'],active=d['m_IsActive'],transforms=transforms))
(out/'component_native_transforms.json').write_text(json.dumps(trs,ensure_ascii=False,indent=1),encoding='utf-8')
print('components',len(records),'paths',len(hierarchy),'guid arrays',[(x['name'],len(x['level_refs'])) for x in order],'native transforms',len(trs))
