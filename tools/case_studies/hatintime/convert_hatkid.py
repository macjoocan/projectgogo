import bpy,sys,re,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parent;dest=p/'preview';dest.mkdir(exist_ok=True);sources=p/'raw/Startup/Startup'
if not sources.exists():sources=p/'pilot/Startup'
def block(s,key):return re.search(r'\b'+re.escape(key)+r'\s*\{(.*?)\}',s,re.S).group(1)
def nums(s):return [float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',s)]
def quat(v):return Quaternion((-math.sqrt(max(0,1-sum(x*x for x in v))),*v))
def mat(pos,q):return Matrix.Translation(Vector(pos))@q.to_matrix().to_4x4()
def meshread(path):
 s=path.read_text();j=[]
 for line in block(s,'joints').splitlines():
  m=re.search(r'"(.*?)"\s+(-?\d+)\s+\((.*?)\)\s+\((.*?)\)',line)
  if m:j.append((m[1],int(m[2]),mat(nums(m[3]),quat(nums(m[4])))))
 chunks=[]
 for b in re.findall(r'\bmesh\s*\{(.*?)\}',s,re.S):
  vs={};ws={};faces=[];shader=re.search(r'shader\s+"(.*?)"',b)[1]
  for line in b.splitlines():
   t=line.strip().split()
   if not t:continue
   if t[0]=='vert':
    a=nums(line);vs[int(a[0])]=(a[1:3],int(a[3]),int(a[4]))
   if t[0]=='tri':a=nums(line);faces.append(tuple(int(x) for x in a[1:4]))
   if t[0]=='weight':a=nums(line);ws[int(a[0])]=(int(a[1]),a[2],Vector(a[3:6]))
  chunks.append((shader,vs,ws,faces))
 return j,chunks
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
body=next(sources.rglob('HatKidBody.md5mesh'));joints,_=meshread(body);names=[x[0] for x in joints];arm=bpy.data.armatures.new('HatKid_SourceSkeleton');rig=bpy.data.objects.new('HatKid',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,parent,m in joints:
 b=arm.edit_bones.new(name);b.matrix=m;b.length=2
 if parent>=0:b.parent=arm.edit_bones[joints[parent][0]]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True;meshes=[];reports=[]
for part in ('HatKidBody','HatKidHead','HatKidLegs'):
 path=next(sources.rglob(part+'.md5mesh'));js,chunks=meshread(path);assert [x[0] for x in js]==names;assert max(max(abs(js[i][2][a][b]-joints[i][2][a][b]) for a in range(4) for b in range(4)) for i in range(len(js)))<.001
 for k,(shader,vs,ws,faces) in enumerate(chunks):
  verts=[];weights=[];uv=[]
  for i in range(len(vs)):
   vuv,start,count=vs[i];v=Vector((0,0,0));ww=[]
   for wi in range(start,start+count):
    bone,w,pos=ws[wi];v+=(js[bone][2]@pos)*w;ww.append((bone,w))
   assert abs(sum(w for _,w in ww)-1)<.01;verts.append(v);weights.append(ww);uv.append(vuv)
  me=bpy.data.meshes.new(part+str(k));me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(part+'_'+str(k),me);bpy.context.collection.objects.link(ob);ob.parent=rig;mod=ob.modifiers.new('Source skin weights','ARMATURE');mod.object=rig
  for name in names:ob.vertex_groups.new(name=name)
  for vi,ww in enumerate(weights):
   for bi,w in ww:ob.vertex_groups[bi].add([vi],w,'REPLACE')
  layer=me.uv_layers.new(name='UVMap')
  for poly in me.polygons:
   for li in poly.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
  material=bpy.data.materials.get(shader) or bpy.data.materials.new(shader);material.diffuse_color=(.65,.45,.8,1);me.materials.append(material);meshes.append(ob);reports.append(dict(part=part,vertices=len(verts),triangles=len(faces),source=str(path),weights_valid=True))
scene=bpy.context.scene;scene.render.fps=60;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
animbase=next(sources.rglob('HatKidV2_Anims'));attack=next(sources.rglob('HatKidV2_Attack_Anims'),animbase);choices=[]
for label,options in [('Idle',['Idle','StandingIdle','Idle_old']),('Walk',['Walk']),('Run',['RunCycle','sprint']),('Attack',['Puncha','PunchA','PunchB','StabKnife']),('Hit',['Hurt1','Hurt2','HandHurt'])]:
 found=next((q for name in options for folder in (animbase,attack) for q in folder.glob(name+'.md5anim')),None)
 if found:choices.append((label,found))
assert len(choices)==5,choices
clipreports=[]
for label,path in choices:
 s=path.read_text();fps=float(re.search(r'frameRate\s+(\S+)',s)[1]);count=int(re.search(r'numFrames\s+(\d+)',s)[1]);hier=[]
 for line in block(s,'hierarchy').splitlines():
  m=re.search(r'"(.*?)"\s+(-?\d+)\s+(\d+)\s+(\d+)',line)
  if m:hier.append((m[1],int(m[2]),int(m[3]),int(m[4])))
 assert [x[0] for x in hier]==names
 base=[nums(line) for line in block(s,'baseframe').splitlines() if '(' in line];frames={int(m[1]):nums(m[2]) for m in re.finditer(r'\bframe\s+(\d+)\s*\{(.*?)\}',s,re.S)};assert len(frames)==count
 action=bpy.data.actions.new(label+'__'+path.stem);action.use_fake_user=True;slot=action.slots.new(id_type='OBJECT',name=rig.name);strip=action.layers.new('Source motion').strips.new(type='KEYFRAME');bag=strip.channelbag(slot,ensure=True);tracks={i:[] for i in range(len(names))}
 for fi in range(count):
  vals=frames[fi];world=[]
  for i,(_,_,flags,start) in enumerate(hier):
   v=base[i][:];ci=start
   for component in range(6):
    if flags&(1<<component):v[component]=vals[ci];ci+=1
   local=mat(v[:3],quat(v[3:]));parent=joints[i][1];world.append(world[parent]@local if parent>=0 else local)
  for i,(name,parent,rest) in enumerate(joints):
   basis=rest.inverted()@(joints[parent][2]@world[parent].inverted() if parent>=0 else Matrix.Identity(4))@world[i];loc,rot,scale=basis.decompose();tracks[i].append((loc,rot,scale))
 for i,name in enumerate(names):
  previous=None
  for loc,rot,scale in tracks[i]:
   if previous is not None and rot.dot(previous)<0:rot.negate()
   previous=rot.copy()
  for prop,size,entry in [('location',3,0),('rotation_quaternion',4,1)]:
   for axis in range(size):
    fc=bag.fcurves.new('pose.bones['+json.dumps(name)+'].'+prop,index=axis);fc.keyframe_points.add(count);values=[]
    for fi,v in enumerate(tracks[i]):values.extend((1+fi*60/fps,v[entry][axis]))
    fc.keyframe_points.foreach_set('co',values)
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 for b in rig.pose.bones:b.rotation_mode='QUATERNION'
 rig.animation_data_create();rig.animation_data.action=action;rig.animation_data.action_slot=slot;clipreports.append(dict(label=label,source=str(path),source_fps=fps,source_frames=count,duration=(count-1)/fps,track_bones=len(hier),source_hierarchy_placeholder=True,parent_mapping='paired mesh native bone hierarchy',action=action.name))
rig.animation_data.action=None;scene.frame_set(1);scene.frame_end=max(2,int(max(r['duration'] for r in clipreports)*60)+1)
# Native MD5 units preserved. Materials are a neutral preview, not source shader parity.
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.ops.wm.save_as_mainfile(filepath=str(dest/'HatKid_five_motions.blend'))
bpy.ops.export_scene.gltf(filepath=str(dest/'HatKid_five_motions.glb'),export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_optimize_animation_size=False)
rep=dict(bones=len(joints),parts=reports,clips=clipreports,source_scale_preserved=True,preview_materials=True,source_scale_animation_not_supported_by_exporter=True)
(dest/'conversion_report.json').write_text(json.dumps(rep,indent=1),encoding='utf-8');print('CONVERSION_DONE',len(joints),len(clipreports))
