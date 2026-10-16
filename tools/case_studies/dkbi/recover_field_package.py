import csv,json,hashlib,shutil,base64,struct
from pathlib import Path
root=Path(__file__).parent;out=root/'field_101002';out.mkdir(exist_ok=True)
base=Path(r'D:\99.기타\out_dkbi')
inventory=list(csv.DictReader((base/'asset_indices_by_type/TextAsset.csv').open(encoding='utf-8-sig')))
selected=[];district=None
for rec in inventory:
    if rec['name'].startswith('dkb_dungeon_beginner_navmesh') or rec['name']=='dkb_dungeon_beginner_district':
        path=base/'bundles'/rec['bundle_key']/rec['export_file'];b=path.read_bytes()
        suffix='.json' if b.lstrip().startswith(b'{') else '.bytes'
        destination=out/(rec['name']+'_'+rec['path_id']+suffix);destination.write_bytes(b)
        item=dict(provenance='verified',source=str(path),serialized_file=rec['serialized_file'],path_id=int(rec['path_id']),raw_object_pack_offset=int(rec['raw_pack_offset']),payload_sha256=hashlib.sha256(b).hexdigest(),payload_bytes=len(b),saved_file=destination.name)
        if suffix=='.json':
            t=json.loads(b);item['json_keys']=list(t)
            if rec['name']=='dkb_dungeon_beginner_district':district=t
        selected.append(item)
assert district and district['zoneId']==101002
areas={x['name']:x for x in district['areas']};spawns=[];missing=[]
for tr in district['triggers']:
    for action in tr.get('actions',[]):
        if action.get('type')=='activespawn':
            entry=dict(provenance='verified',trigger_name=tr['name'],events=tr.get('events'),action=action,spawn_area=areas.get(action['spawnArea']),monster_area=areas.get(action['monsterArea']),runtime_behavior='unknown')
            if entry['spawn_area'] is None:missing.append(action['spawnArea'])
            spawns.append(entry)
def readrows(name):return json.loads((root/'tables'/(name+'_structural_rows.json')).read_text('utf-8'))['rows']
def slot0(r):return r['slots'][0].get('inferred_numeric_views',{}).get('uint32')
actorids=sorted({x['action']['actorId'] for x in spawns})
monsters=[dict(provenance='inferred',slot0_uint32=slot0(r),row=r) for r in readrows('actormonster') if slot0(r) in actorids]
focus=dict(provenance='verified',zoneId=district['zoneId'],sceneName=district['sceneName'],zone=district['zone'],areas=len(areas),spawns=len(spawns),spawn_actor_ids=actorids,missing_spawn_areas=missing,installers=district['installers'],limitations=['Serialized field values, not server activation proof','District position/rotation are not ECS renderer Transform restoration','NPCOnly zone field interpretation unknown','FB slot0 to ActorId association inferred pending schema'],files=selected)
def save(name,obj):(out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
save('field_summary.json',focus);save('spawn_area_bindings.json',spawns);save('spawn_monster_rows_candidates.json',monsters)
save('default_pc_weapon_skill_candidates.json',dict(provenance='inferred',pc=[r for r in readrows('actorpc') if slot0(r)==10],weapon=[r for r in readrows('itemsequip') if slot0(r)==10000001],basic_sword=[r for r in readrows('skillpc') if slot0(r)==1000000],generic_basic=[r for r in readrows('skillpc') if slot0(r)==100000],limitations=['Rows contain exact asset strings and slot bytes, column names/types unresolved','Weapon->skill equip default association not verified','No inferred speed/HP/range used as original runtime rules']))
catalog=json.loads(Path(r'D:\99.기타\out_dkbi_probe\addressables_catalog.json').read_text('utf-8'));raw=base64.b64decode(catalog['m_EntryDataString']);entries=[struct.unpack_from('<7i',raw,4+i*28) for i in range(struct.unpack_from('<i',raw)[0])];bucketraw=base64.b64decode(catalog['m_BucketDataString']);p=4;buckets=[]
for _ in range(struct.unpack_from('<i',bucketraw)[0]):
    key,n=struct.unpack_from('<ii',bucketraw,p);p+=8;buckets.append(list(struct.unpack_from('<'+'i'*n,bucketraw,p)));p+=4*n
scene=[]
for i,e in enumerate(entries):
    path=catalog['m_InternalIds'][e[0]]
    if path.endswith('/seamless_chunks/dkb_dungeon_beginner/dkb_dungeon_beginner.unity'):
        deps=[dict(entry_index=j,path=catalog['m_InternalIds'][entries[j][0]],provider=catalog['m_ProviderIds'][entries[j][1]]) for j in buckets[e[2]]]
        scene.append(dict(provenance='verified',catalog_entry_index=i,path=path,dependencies=deps))
save('scene_catalog_dependencies.json',scene)
print(json.dumps(dict(zoneId=101002,assets=len(selected),areas=len(areas),spawns=len(spawns),actorIds=actorids,monster_candidate_rows=len(monsters),missing_spawn_areas=missing,scene_direct_dependencies=[len(x['dependencies']) for x in scene]),ensure_ascii=False))
