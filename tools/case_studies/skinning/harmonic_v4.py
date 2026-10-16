"""Isolate fitted geometry versus cross-digit weights, on copied v4 only."""
import bpy,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'v4_followup';DATA=OUT/'input'
sections=json.loads((ROOT/'hand_sections.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(DATA/'source/hand-cage-v4/candidate.blend'))
s=bpy.data.scenes['MotionFirst_OriginalRetry'];bpy.context.window.scene=s
r=bpy.data.objects['OriginalRetry_Body70'];m=bpy.data.objects['OriginalRetry_Surface'];r.animation_data.action=None;r.animation_data.use_nla=False
for t in r.animation_data.nla_tracks:t.mute=True
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
pos=np.array([v.co[:] for v in m.data.vertices]);original=np.load(ROOT/'baseline_positions.npy')
assert pos.shape==original.shape
names=list(r.data.bones.keys());groups=list(m.vertex_groups.keys());base=np.zeros((len(pos),len(names)))
for v in m.data.vertices:
    for g in v.groups:base[v.index,names.index(groups[g.group])]=g.weight
edges=np.array([e.vertices[:] for e in m.data.edges]);tris=np.array([f.vertices[:] for f in m.data.polygons if len(f.vertices)==3])
candidate=base.copy();reports=[];changed_region=np.zeros(len(pos),dtype=bool)
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
for sign,side in [(1,'L'),(-1,'R')]:
    selected=(sign*original[:,0]>23)&(original[:,2]>36)&(original[:,2]<48);ids=np.flatnonzero(selected);lookup=np.full(len(pos),-1,dtype=int);lookup[ids]=np.arange(len(ids))
    changed_region|=selected
    es=edges[selected[edges[:,0]]&selected[edges[:,1]]];a=lookup[es[:,0]];b=lookup[es[:,1]];a,b=np.r_[a,b],np.r_[b,a]
    fields=np.zeros((len(ids),6));fields[:,0]=1;fixed=np.zeros(len(ids),bool)
    fixed[sign*original[ids,0]<24.8]=True
    fingers=sorted(next(x for x in sections[str(sign)] if x['cut']==29)['components'],key=lambda x:-x['mean'][1])
    thumb=min(next(x for x in sections[str(sign)] if x['cut']==27)['components'],key=lambda x:x['mean'][1])
    for digitno,comp in enumerate(fingers+[thumb],1):
        seed=lookup[np.array(comp['ids'])];seed=seed[seed>=0];fields[seed]=0;fields[seed,digitno]=1;fixed[seed]=True
    count=np.bincount(a,minlength=len(ids));movable=~fixed&(count>0)
    for iteration in range(600):
        accum=np.zeros_like(fields);np.add.at(accum,a,fields[b]);new=fields.copy();new[movable]=accum[movable]/count[movable,None]
        error=float(np.max(np.abs(new-fields)));fields=new
        if error<1e-7:break
    weights=np.zeros((len(ids),70));weights[:,names.index(f'bip_hand{side}_base')]=fields[:,0]
    for digitno,digit in enumerate(['pinky','ring','middle','index','thumb'],1):
        first=np.array(r.data.bones[f'bip_hand{side}_{digit}01'].head_local);second=np.array(r.data.bones[f'bip_hand{side}_{digit}02'].head_local)
        axis=second-first;t=(pos[ids]-first)@axis/np.dot(axis,axis);blend=smooth((t-.55)/.9)
        weights[:,names.index(f'bip_hand{side}_{digit}01')]=fields[:,digitno]*(1-blend)
        weights[:,names.index(f'bip_hand{side}_{digit}02')]=fields[:,digitno]*blend
    gate=smooth((sign*original[ids,0]-24.8)/1.5);candidate[ids]=base[ids]*(1-gate[:,None])+weights*gate[:,None]
    reports.append({'side':side,'vertices':len(ids),'iterations':iteration+1,'last_delta':error,'method':'topological harmonic ownership with fixed distal seeds, palm boundary; derived weights only'})
chosen=np.argpartition(candidate[changed_region],-4,axis=1)[:,-4:];limited=np.zeros_like(candidate[changed_region]);np.put_along_axis(limited,chosen,np.take_along_axis(candidate[changed_region],chosen,axis=1),axis=1);candidate[changed_region]=limited/limited.sum(1)[:,None]
assert np.array_equal(candidate[~changed_region],base[~changed_region])
def write(weights):
    for g in list(m.vertex_groups):m.vertex_groups.remove(g)
    for name in names:m.vertex_groups.new(name=name)
    for i,row in enumerate(weights):
        for j in np.flatnonzero(row>1e-8):m.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
    m.data.update();bpy.context.view_layer.update()
def positions():
    ob=m.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ob.to_mesh();p=np.array([v.co[:] for v in data.vertices]);ob.to_mesh_clear();return p
actions=[a for a in bpy.data.actions if a.name.startswith('OriginalRetryNative__')];assert len(actions)==5
def action_slot(a):return next(slot for slot in a.slots if slot.target_id_type=='OBJECT')
hand=(np.abs(original[:,0])>24)&(original[:,2]>36)&(original[:,2]<48);arm=(np.abs(original[:,0])>7)&(np.abs(original[:,0])<25)&(original[:,2]>37)&(original[:,2]<47)
hm=hand[edges[:,0]]&hand[edges[:,1]];am=arm[edges[:,0]]&arm[edges[:,1]];ht=np.all(hand[tris],axis=1);length=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)
def areas(p):q=p[tris[ht]];return np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)*.5
restarea=areas(pos);valid=restarea>1e-6
cd=bpy.data.cameras.new('HarmonicStudyCamera');cam=bpy.data.objects.new('HarmonicStudyCamera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=.34
s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.6,.67,.73);s.display.shading.show_cavity=True
s.render.resolution_x=800;s.render.resolution_y=700;s.render.resolution_percentage=100
for ob in s.objects:ob.hide_render=ob not in (m,cam)
result={'fields':reports,'geometry_unchanged':True,'outside_hand_weights_exact_in_memory':True,'adopted':False,'variants':{}}
for label,w in [('v4_baseline',base),('harmonic_ownership',candidate)]:
    write(w);summary={'finite':True,'samples':125,'max_arm_edge_m':0.,'max_hand_edge_m':0.,'min_hand_triangle_area_ratio':1.,'clips':[]}
    for a in actions:
        r.animation_data.action=a;r.animation_data.action_slot=action_slot(a)
        clip={'action':a.name,'max_hand_edge_m':0.,'min_triangle_area_ratio':1.}
        for frame in np.linspace(float(a.frame_range[0]),float(a.frame_range[1]),25):
            s.frame_set(math.floor(frame),subframe=frame%1);q=positions();summary['finite']&=bool(np.isfinite(q).all());delta=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)-length
            summary['max_arm_edge_m']=max(summary['max_arm_edge_m'],float(delta[am].max())*r.scale.x);summary['max_hand_edge_m']=max(summary['max_hand_edge_m'],float(delta[hm].max())*r.scale.x)
            summary['min_hand_triangle_area_ratio']=min(summary['min_hand_triangle_area_ratio'],float((areas(q)[valid]/restarea[valid]).min()))
            clip['max_hand_edge_m']=max(clip['max_hand_edge_m'],float(delta[hm].max())*r.scale.x);clip['min_triangle_area_ratio']=min(clip['min_triangle_area_ratio'],float((areas(q)[valid]/restarea[valid]).min()))
        summary['clips'].append(clip)
    r.animation_data.action=None
    for pb in r.pose.bones:pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    for pose in ['rest','curl']:
        if pose=='curl':
            for side in ['L','R']:
                for digit in ['pinky','ring','middle','index','thumb']:
                    one=r.pose.bones[f'bip_hand{side}_{digit}01'];two=r.pose.bones[f'bip_hand{side}_{digit}02'];axis=(two.head-one.head).cross(Vector((0,0,1))).normalized()
                    for pb,angle in [(one,65),(two,80)]:
                        h=pb.head.copy();pb.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-h)@pb.matrix;bpy.context.view_layer.update()
        center=r.matrix_world@Vector((27,-1.5,42));cam.location=center+Vector((.12,-.5,.25));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        q=positions();summary[pose+'_min_hand_triangle_area_ratio']=float((areas(q)[valid]/restarea[valid]).min())
        s.render.filepath=str(OUT/f'{label}_{pose}.png');bpy.ops.render.render(write_still=True)
    result['variants'][label]=summary
    if label=='harmonic_ownership':
        for pb in r.pose.bones:pb.matrix_basis.identity()
        for a in actions:
            if not any(strip.action==a for t in r.animation_data.nla_tracks for strip in t.strips):
                t=r.animation_data.nla_tracks.new();t.mute=True;strip=t.strips.new(a.name,1,a);strip.action_slot=action_slot(a)
        bpy.data.libraries.write(str(OUT/'harmonic-candidate.blend'),{s,*actions},fake_user=True,compress=True)
(OUT/'comparison.json').write_bytes(json.dumps(result,indent=2).encode('utf-8'));print('HARMONIC',json.dumps(result))
