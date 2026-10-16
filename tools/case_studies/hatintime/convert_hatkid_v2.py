exec(open(__file__.replace('convert_hatkid_v2.py','convert_hatkid.py'),encoding='utf-8').read().split("bpy.ops.object.select_all")[0])
import bisect
def sample_scale(track,frame):
 if not track:return [1,1,1]
 ts=track['times'];vs=track['values'];i=max(0,bisect.bisect_right(ts,frame)-1)
 if i>=len(ts)-1:return vs[-1]
 a=0 if ts[i+1]==ts[i] else (frame-ts[i])/(ts[i+1]-ts[i]);return [vs[i][k]*(1-a)+vs[i+1][k]*a for k in range(3)]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.fps=60;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
rigs=[];reports=[]
for part in ('HatKidBody','HatKidHead','HatKidLegs'):
 path=next(sources.rglob(part+'.md5mesh'));joints,chunks=meshread(path);names=[x[0] for x in joints];arm=bpy.data.armatures.new(part+'_SourceSkeleton');rig=bpy.data.objects.new(part+'_Rig',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for name,parent,m in joints:
  b=arm.edit_bones.new(name);b.head=(0,0,0);b.tail=(0,2,0);b.matrix=m
  if parent>=0:b.parent=arm.edit_bones[joints[parent][0]]
 bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True;rig.animation_data_create();rigs.append((rig,joints))
 for k,(shader,vs,ws,faces) in enumerate(chunks):
  verts=[];weights=[];uv=[]
  for i in range(len(vs)):
   vuv,start,count=vs[i];v=Vector((0,0,0));ww=[]
   for wi in range(start,start+count):
    bone,w,pos=ws[wi];v+=(joints[bone][2]@pos)*w;ww.append((bone,w))
   assert abs(sum(w for _,w in ww)-1)<.01;verts.append(v);weights.append(ww);uv.append(vuv)
  me=bpy.data.meshes.new(part+str(k));me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(part+'_'+str(k),me);bpy.context.collection.objects.link(ob);ob.parent=rig;ob.modifiers.new('Source skin weights','ARMATURE').object=rig
  for name in names:ob.vertex_groups.new(name=name)
  for vi,ww in enumerate(weights):
   for bi,w in ww:ob.vertex_groups[bi].add([vi],w,'REPLACE')
  layer=me.uv_layers.new(name='UVMap')
  for poly in me.polygons:
   for li in poly.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
  material=bpy.data.materials.get(shader) or bpy.data.materials.new(shader);material.diffuse_color=(.65,.45,.8,1);me.materials.append(material);reports.append(dict(part=part,vertices=len(verts),triangles=len(faces),source=str(path),weights_valid=True))
animbase=next(sources.rglob('HatKidV2_Anims'));attack=next(sources.rglob('HatKidV2_Attack_Anims'),animbase);choices=[]
for label,options in [('Idle',['Idle','StandingIdle','Idle_old']),('Walk',['Walk']),('Run',['RunCycle','sprint']),('Attack',['Puncha','PunchA','PunchB','StabKnife']),('Hit_Candidate',['HandHurt','Hurt1','Hurt2'])]:
 found=next((q for name in options for folder in (animbase,attack) for q in folder.glob(name+'.md5anim')),None)
 if found:choices.append((label,found))
assert len(choices)==5,choices
clipreports=[]
for label,path in choices:
 s=path.read_text();fps=float(re.search(r'frameRate\s+(\S+)',s)[1]);count=int(re.search(r'numFrames\s+(\d+)',s)[1]);hier=[]
 source_meta=path.with_suffix('.source.json')
 if source_meta.exists():
  import struct
  meta=json.loads(source_meta.read_text());f32=lambda v:struct.unpack('<f',struct.pack('<f',v))[0];fps=f32(f32(meta['frames']/f32(meta['sequence_length']))*f32(meta['rate_scale']))
 for line in block(s,'hierarchy').splitlines():
  m=re.search(r'"(.*?)"\s+(-?\d+)\s+(\d+)\s+(\d+)',line)
  if m:hier.append((m[1],int(m[2]),int(m[3]),int(m[4])))
 base=[nums(line) for line in block(s,'baseframe').splitlines() if '(' in line];frames={int(m[1]):nums(m[2]) for m in re.finditer(r'\bframe\s+(\d+)\s*\{(.*?)\}',s,re.S)};assert len(frames)==count
 scale_file=path.with_suffix('.scale.json');scale_data=json.loads(scale_file.read_text())['tracks'] if scale_file.exists() else [];scale_map={t['bone']:t for t in scale_data}
 action=bpy.data.actions.new(label+'__'+path.stem);action.use_fake_user=True;strip=action.layers.new('Source motion').strips.new(type='KEYFRAME')
 for rig,joints in rigs:
  names=[x[0] for x in joints];assert set(x[0] for x in hier)==set(names);hier_index={x[0]:i for i,x in enumerate(hier)};slot=action.slots.new(id_type='OBJECT',name=rig.name);bag=strip.channelbag(slot,ensure=True);tracks={i:[] for i in range(len(names))}
  for fi in range(count):
   vals=frames[fi];world=[]
   for i,name in enumerate(names):
    hi=hier_index[name];_,_,flags,start=hier[hi];v=base[hi][:];ci=start
    for component in range(6):
     if flags&(1<<component):v[component]=vals[ci];ci+=1
    sc=sample_scale(scale_map.get(name),fi);local=mat(v[:3],quat(v[3:]))@Matrix.Diagonal(Vector((*sc,1)));parent=joints[i][1];world.append(world[parent]@local if parent>=0 else local)
   for i,(name,parent,rest) in enumerate(joints):
    basis=rest.inverted()@(joints[parent][2]@world[parent].inverted() if parent>=0 else Matrix.Identity(4))@world[i];loc,rot,scale=basis.decompose();tracks[i].append((loc,rot,scale))
  for i,name in enumerate(names):
   previous=None
   for loc,rot,scale in tracks[i]:
    if previous is not None and rot.dot(previous)<0:rot.negate()
    previous=rot.copy()
   for prop,size,entry in [('location',3,0),('rotation_quaternion',4,1),('scale',3,2)]:
    for axis in range(size):
     fc=bag.fcurves.new('pose.bones['+json.dumps(name)+'].'+prop,index=axis);fc.keyframe_points.add(count);values=[]
     for fi,v in enumerate(tracks[i]):values.extend((1+fi*60/fps,v[entry][axis]))
     fc.keyframe_points.foreach_set('co',values)
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
     fc.update()
  for b in rig.pose.bones:b.rotation_mode='QUATERNION'
  rig.animation_data.action=action;rig.animation_data.action_slot=slot
  track=rig.animation_data.nla_tracks.new();track.name=label;ns=track.strips.new(label,1,action);ns.action_slot=slot;track.mute=False
 clipreports.append(dict(label=label,source=str(path),source_fps=fps,source_frames=count,duration=(count-1)/fps,track_bones=len(hier),source_hierarchy_placeholder=True,parent_mapping='paired mesh native bone hierarchy',action=action.name));print('ACTION',label,count,flush=True)
for rig,joints in rigs:
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
scene.frame_set(1);scene.frame_end=max(2,int(max(r['duration'] for r in clipreports)*60)+1)
bpy.ops.wm.save_as_mainfile(filepath=str(dest/'HatKid_five_motions.blend'))
bpy.ops.export_scene.gltf(filepath=str(dest/'HatKid_five_motions.glb'),export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_merge_animation='ACTION',export_anim_single_armature=False,export_force_sampling=True,export_frame_range=False,export_optimize_animation_size=False)
rep=dict(rigs=[dict(name=r.name,bones=len(j)) for r,j in rigs],parts=reports,clips=clipreports,separate_rest_poses_preserved=True,source_scale_preserved=True,preview_materials=True,source_scale_animation_support='Identity and ACF_None scale offsets with constant/variable frame times decoded into pose scale channels')
(dest/'conversion_report.json').write_text(json.dumps(rep,indent=1),encoding='utf-8');print('CONVERSION_DONE',len(rigs),len(clipreports))
