exec(open(__file__.replace('validate_hatkid.py','convert_hatkid.py'),encoding='utf-8').read().split("bpy.ops.object.select_all")[0])
import bisect
def sample_scale(track,frame):
 if not track:return [1,1,1]
 ts=track['times'];vs=track['values'];i=max(0,bisect.bisect_right(ts,frame)-1)
 if i>=len(ts)-1:return vs[-1]
 a=0 if ts[i+1]==ts[i] else (frame-ts[i])/(ts[i+1]-ts[i]);return [vs[i][k]*(1-a)+vs[i+1][k]*a for k in range(3)]
bpy.ops.wm.open_mainfile(filepath=str(dest/'HatKid_five_motions.blend'))
report=json.loads((dest/'conversion_report.json').read_text());rigs=[bpy.data.objects[r['name']] for r in report['rigs']];errors=[];checks=[]
for rig in rigs:rig.animation_data.use_nla=False
for clip in report['clips']:
 path=Path(clip['source']);s=path.read_text();hier=[]
 for line in block(s,'hierarchy').splitlines():
  m=re.search(r'"(.*?)"\s+(-?\d+)\s+(\d+)\s+(\d+)',line)
  if m:hier.append((m[1],int(m[2]),int(m[3]),int(m[4])))
 base=[nums(line) for line in block(s,'baseframe').splitlines() if '(' in line];frames={int(m[1]):nums(m[2]) for m in re.finditer(r'\bframe\s+(\d+)\s*\{(.*?)\}',s,re.S)};a=bpy.data.actions[clip['action']]
 scale_path=path.with_suffix('.scale.json');scale_map={t['bone']:t for t in json.loads(scale_path.read_text())['tracks']} if scale_path.exists() else {};hi_by_name={h[0]:i for i,h in enumerate(hier)}
 for ri,rig in enumerate(rigs):rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[ri]
 for fi in sorted(set((0,clip['source_frames']//2,clip['source_frames']-1))):
  frame=1+fi*60/clip['source_fps'];bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
  for rig in rigs:
   part=rig.name.replace('_Rig','');js,_=meshread(next(sources.rglob(part+'.md5mesh')));world=[]
   for i,(name,*_) in enumerate(js):
    hi=hi_by_name[name];_,_,flags,start=hier[hi];v=base[hi][:];ci=start
    for component in range(6):
     if flags&(1<<component):v[component]=frames[fi][ci];ci+=1
    sc=sample_scale(scale_map.get(name),fi);local=mat(v[:3],quat(v[3:]))@Matrix.Diagonal(Vector((*sc,1)));parent=js[i][1];world.append(world[parent]@local if parent>=0 else local)
   delta=max(max(abs(rig.pose.bones[name].matrix[r][c]-world[i][r][c]) for r in range(4) for c in range(4)) for i,(name,*_) in enumerate(js));checks.append(dict(action=a.name,rig=rig.name,source_frame=fi,max_matrix_abs=delta))
   if delta>.002:errors.append(checks[-1])
  dg=bpy.context.evaluated_depsgraph_get()
  for ob in bpy.context.scene.objects:
   if ob.type!='MESH':continue
   ev=ob.evaluated_get(dg);me=ev.to_mesh();assert all(math.isfinite(v) for x in me.vertices for v in x.co);ev.to_mesh_clear()
for rig in rigs:rig.animation_data.action=None
assert not errors,errors
(dest/'validation.json').write_text(json.dumps(dict(sampled_matrix_checks=checks,errors=errors,skin_vertices_finite=True,method='Original exported MD5 local transforms composed with paired native mesh hierarchy versus saved Blender pose matrices; not original runtime visual parity.'),indent=1),encoding='utf-8')
print('VALIDATION_PASS',len(checks),max(x['max_matrix_abs'] for x in checks))
