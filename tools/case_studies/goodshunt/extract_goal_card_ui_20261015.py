from pathlib import Path
p=Path(__file__).resolve().parent;source=p/'extract_goal_fly_ui_20261015.py';s=source.read_text(encoding='utf-8')
s=s.replace("out=p/'goal_fly_ui_audit_20261015'","out=p/'goal_card_ui_audit_20261015'").replace("len(nodes)<128","len(nodes)<512")
cut=s.index(' for key,r in index.items():')
s=s[:cut]+'''
 key=('level2',29706);controller=read(key);provenance=index[key]
 targets=[('controller',key[0],controller['m_GameObject']['m_PathID'])]
 for label in ('cardPrefab','cardParticle'):
  f,gid=resolve(key[0],controller[label]);targets.append((label,f,gid))
 for label,f,gid in targets:
  go=read((f,gid));tid=next(c['component']['m_PathID'] for c in go['m_Component'] if objs[(f,c['component']['m_PathID'])].type.name in ('Transform','RectTransform'))
  roots.append(dict(label=label,file=f,root_game_object_id=str(gid),root_transform_id=str(tid),source_reference=controller.get(label)))
  walk(f,tid)
 for node in nodes:
  for c in node['components']:
   if c.get('script_class')!='GoalCard':continue
   for field in ('back','hardBack','superBack','front','hardFront','superFront'):
    ptr=c['fields'][field]
    if not ptr['m_PathID']:continue
    sk=resolve(node['file'],ptr)
    if sk in sprites:continue
    so=objs[sk];im=so.read().image;fn=f'{sk[0]}_{sk[1]}_sprite.png';im.save(out/fn)
    sprites[sk]=dict(file=sk[0],path_id=str(sk[1]),raw_sha256=hashlib.sha256(so.get_raw_data()).hexdigest(),fields=so.read_typetree(),png=dict(file=fn,size=im.size,sha256=hashlib.sha256((out/fn).read_bytes()).hexdigest(),pixel_sha256=hashlib.sha256(im.tobytes()).hexdigest()))
def enc(v):
 if isinstance(v,(bytes,bytearray)):return dict(opaque_bytes=len(v),sha256=hashlib.sha256(v).hexdigest())
 raise TypeError(type(v).__name__)
result=dict(boundary='Selected CardController29706 hierarchy, its cardPrefab/cardParticle only. Stored UI/Sprite original refs, no runtime visual or GPU parity assertion.',controller_provenance=provenance,controller_fields=controller,roots=roots,nodes=nodes,sprites=list(sprites.values()),errors=errors)
(out/'native_ui_chain.json').write_text(json.dumps(result,ensure_ascii=False,indent=1,default=enc),encoding='utf-8')
print('ROOTS',roots);print('NODES',len(nodes),'SPRITES',len(sprites),'ERRORS',len(errors));print('SETTINGS',{k:v for k,v in controller.items() if isinstance(v,float)})
for n in nodes:
 for c in n['components']:
  if c.get('script_class')=='GoalCard':print('GOALCARD',n['file'],c['path_id'],{k:v for k,v in c['fields'].items() if isinstance(v,float) or k in ('tick','_uiParticle','back','hardBack','superBack','front','hardFront','superFront')})
'''
exec(compile(s,str(source),'exec'))
