"""World-Z contact/ground/pelvis correction on generated actions only."""
import math
import copy

import bpy
from mathutils import Matrix, Vector

from .contacts import detect_contacts, smooth_bounded, contact_weight


def set_frame(frame):
    bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame))
    bpy.context.view_layer.update()


def ground_hit(point, settings):
    """Plane or explicitly listed evaluated meshes. Never raycast the actor itself."""
    up=Vector((0,0,1));height=settings.get('height',0.0)
    objects=settings.get('objects',[])
    if not objects:return Vector((point.x,point.y,height)),up
    distance=settings.get('ray_distance',100.0);origin=point+up*distance
    candidates=[]
    for name in objects:
        obj=bpy.data.objects.get(name)
        if not obj or obj.type!='MESH':raise ValueError(f'Unknown ground mesh: {name}')
        inv=obj.matrix_world.inverted();direction=inv.to_3x3()@(-up)
        hit,location,normal,_=obj.ray_cast(inv@origin,direction.normalized(),
                                         distance=2*distance*direction.length,
                                         depsgraph=bpy.context.evaluated_depsgraph_get())
        if hit:
            world=obj.matrix_world@location
            normal=(inv.to_3x3().transposed()@normal).normalized()
            if normal.dot(up)<0:normal=-normal
            candidates.append((abs((origin-world).z),world,normal))
    if not candidates:return None
    _,point,normal=min(candidates,key=lambda x:x[0]);return point,normal


def _translate_subtree(rig,matrices,bone,delta):
    for pb in rig.pose.bones:
        if pb.name==bone or any(p.name==bone for p in pb.parent_recursive):
            matrices[pb.name].translation+=delta


def _solve_limb(rig,matrices,chain,goal,engine):
    before={n:m.copy() for n,m in matrices.items()}
    u,l,e=(chain[k] for k in ('upper','lower','end'))
    a,b,c=(matrices[n].translation.copy() for n in (u,l,e))
    pole=b-a
    if chain.get('pole_mode')=='fixed':pole=Vector(chain.get('pole',[0,0,1]))
    mid,end,clamped=engine.solve_two_bone(a,goal,pole,(b-a).length,(c-b).length)
    for name,start,old_vec,new_vec in ((u,a,b-a,mid-a),(l,mid,c-b,end-mid)):
        if old_vec.length<1e-8 or new_vec.length<1e-8:raise ValueError('Degenerate postprocess limb')
        rotation=old_vec.rotation_difference(new_vec)@matrices[name].to_quaternion()
        matrices[name]=Matrix.LocRotScale(start,rotation,matrices[name].to_scale())
    matrices[e].translation=end
    affected={u,l,e}
    for pb in engine.ordered(rig):
        if pb.name not in affected and pb.parent and pb.parent.name in affected:
            matrices[pb.name]=matrices[pb.parent.name]@before[pb.parent.name].inverted()@before[pb.name]
            affected.add(pb.name)
    return clamped


def _rotate_subtree(rig,matrices,bone,rotation):
    before=matrices[bone].copy()
    matrices[bone]=Matrix.LocRotScale(before.translation,rotation,before.to_scale())
    delta=matrices[bone]@before.inverted()
    for pb in rig.pose.bones:
        if any(p.name==bone for p in pb.parent_recursive):matrices[pb.name]=delta@matrices[pb.name]


def apply(rig,source,preset,frames,engine):
    config=preset.get('postprocess')
    if not config:return None
    fps=bpy.context.scene.render.fps/bpy.context.scene.render.fps_base
    by_t={row['target']:row['source'] for row in preset['bones']}
    chains={c['end']:c for c in preset.get('ik_chains',[])}
    feet=config.get('feet',[]);ground=config.get('ground',{})
    samples=[];source_feet={f['end']:[] for f in feet}
    for frame in frames:
        set_frame(frame)
        samples.append({pb.name:pb.matrix.copy() for pb in rig.pose.bones})
        for foot in feet:
            source_feet[foot['end']].append(tuple(source.matrix_world@source.pose.bones[by_t[foot['end']]].matrix.translation))
    report={'contacts':{},'ground_misses':0,'ik_clamped_samples':0,
            'max_contact_error_world':0.0,'max_pelvis_shift_world':0.0,
            'max_basis_projection_error':0.0,
            'ground_space':'world Z; explicit user geometry/plane', 'samples':len(frames)}
    root=preset['root'];trajectory=config.get('trajectory',{})
    if trajectory:
        for axis in trajectory.get('axes',['X','Y']):
            index='XYZ'.index(axis)
            values=[m[root].translation[index] for m in samples]
            result=smooth_bounded(values,trajectory.get('smoothness',1),trajectory.get('max_deviation',.1))
            for mats,value,old in zip(samples,result,values):
                delta=Vector((0,0,0));delta[index]=value-old;_translate_subtree(rig,mats,root,delta)
    # Seam correction precedes locking: the later contact solve has final authority.
    loop=config.get('loop',{})
    if loop and len(samples)>1:
        blend=loop.get('blend_frames',5)
        for pb in rig.pose.bones:
            if pb.name==root and not loop.get('root',False):continue
            first,last=samples[0][pb.name],samples[-1][pb.name]
            correction=first.translation-last.translation
            delta_rotation=first.to_quaternion()@last.to_quaternion().inverted()
            for frame,mats in zip(frames,samples):
                t=max(0.0,min(1.0,(frame-(frames[-1]-blend))/blend))
                if t:
                    old=mats[pb.name]
                    rotation=old.to_quaternion().slerp(delta_rotation@old.to_quaternion(),t)
                    scale=old.to_scale().lerp(first.to_scale(),t)
                    mats[pb.name]=Matrix.LocRotScale(old.translation+correction*t,rotation,scale)
    locks={}
    for foot in feet:
        name=foot['end'];contact=foot.get('contact',{})
        points=source_feet[name]
        if contact.get('mode','auto')=='manual':
            segments=[]
            for start,end in contact['intervals']:
                indices=[i for i,f in enumerate(frames) if start<=f<=end]
                if indices:segments.append([indices[0],indices[-1]])
        else:
            floor=contact.get('floor',min(p[2] for p in points))
            segments=detect_contacts([f/fps for f in frames],points,floor=floor,
                                     height=contact.get('height',.05),speed=contact.get('speed',.1),
                                     min_duration=contact.get('min_duration',.08),max_gap=contact.get('max_gap',.04))
        report['contacts'][name]=[[frames[a],frames[b]] for a,b in segments]
        per_sample={}
        for a,b in segments:
            set_frame(frames[a])
            anchor_world=rig.matrix_world@samples[a][name].translation
            hit=ground_hit(anchor_world,ground)
            if hit:
                point,normal=hit;anchor_world.z=point.z+foot.get('sole_offset',0)
            else:report['ground_misses']+=1;normal=Vector((0,0,1))
            anchor_rotation=samples[a][name].to_quaternion()
            for i in range(a,b+1):
                weight=contact_weight(frames[i],frames[a],frames[b],contact.get('blend_frames',2))
                per_sample[i]=(anchor_world.copy(),normal.copy(),anchor_rotation.copy(),weight)
        locks[name]=per_sample
    # Ground correction applies to swings as penetration prevention; contact lock to plants.
    goals=[]
    for i,(frame,mats) in enumerate(zip(frames,samples)):
        set_frame(frame);frame_goals={}
        for foot in feet:
            name=foot['end'];world=rig.matrix_world@mats[name].translation
            rotation=mats[name].to_quaternion();weight=0.0;normal=Vector((0,0,1))
            if i in locks[name]:
                anchor,normal,locked_rot,weight=locks[name][i]
                world=world.lerp(anchor,weight)
                if foot.get('lock_rotation',True):rotation=rotation.slerp(locked_rot,weight)
            hit=ground_hit(world,ground)
            if hit:
                point,normal=hit;world.z=max(world.z,point.z+foot.get('sole_offset',0))
            elif ground.get('objects'):report['ground_misses']+=1
            if ground.get('align_feet',False):
                world_rotation=rig.matrix_world.to_quaternion()@rotation
                local_up=Vector(foot.get('up_axis',[0,0,1]))
                old_up=world_rotation@local_up
                adjustment=old_up.rotation_difference(normal)
                max_angle=math.radians(ground.get('max_tilt_degrees',45))
                if adjustment.angle>max_angle:adjustment=adjustment.slerp(type(adjustment)((1,0,0,0)),1-max_angle/adjustment.angle)
                rotation=rig.matrix_world.to_quaternion().inverted()@adjustment@world_rotation
            frame_goals[name]=(rig.matrix_world.inverted()@world,rotation,weight)
        goals.append(frame_goals)
    pelvis=config.get('pelvis',{})
    shifts=[]
    for mats,frame_goals in zip(samples,goals):
        shift=Vector((0,0,0))
        if pelvis:
            bone=pelvis.get('bone',root)
            limit=pelvis.get('max_shift',.3)/rig.matrix_world.to_scale().x
            axes=pelvis.get('axes',['X','Y','Z'])
            for _ in range(pelvis.get('iterations',12)):
                corrections=[]
                for name,(goal,_,weight) in frame_goals.items():
                    if weight<=0:continue
                    chain=chains[name];u,l,e=(chain[k] for k in ('upper','lower','end'))
                    origin=mats[u].translation+shift;vector=goal-origin
                    length=(mats[l].translation-mats[u].translation).length+(mats[e].translation-mats[l].translation).length
                    excess=vector.length-(length-1e-5)
                    if excess>0:corrections.append(vector.normalized()*excess)
                if not corrections:break
                shift+=sum(corrections,Vector((0,0,0)))/len(corrections)
                for axis in 'XYZ':
                    if axis not in axes:shift['XYZ'.index(axis)]=0
                if shift.length>limit:shift*=limit/shift.length
        shifts.append(shift)
    if pelvis and pelvis.get('smoothness',1)>0:
        for axis in range(3):
            values=smooth_bounded([s[axis] for s in shifts],pelvis.get('smoothness',1))
            for shift,value in zip(shifts,values):shift[axis]=value
    previous={}
    for i,(frame,mats,frame_goals,shift) in enumerate(zip(frames,samples,goals,shifts)):
        set_frame(frame)
        if pelvis:
            limit=pelvis.get('max_shift',.3)/rig.matrix_world.to_scale().x
            if shift.length>limit:shift*=limit/shift.length
            # Smoothing is soft; project back to reachability afterwards so it
            # cannot undo a planted foot constraint near the blend boundaries.
            for _ in range(pelvis.get('iterations',12)):
                corrections=[]
                for name,(goal,_,weight) in frame_goals.items():
                    if weight<=0:continue
                    chain=chains[name];u,l,e=(chain[k] for k in ('upper','lower','end'))
                    vector=goal-(mats[u].translation+shift)
                    reach=(mats[l].translation-mats[u].translation).length+(mats[e].translation-mats[l].translation).length-1e-4
                    if vector.length>reach:corrections.append(vector.normalized()*(vector.length-reach))
                if not corrections:break
                shift+=sum(corrections,Vector((0,0,0)))/len(corrections)
                for axis in 'XYZ':
                    if axis not in pelvis.get('axes',['X','Y','Z']):shift['XYZ'.index(axis)]=0
                if shift.length>limit:shift*=limit/shift.length
            _translate_subtree(rig,mats,pelvis.get('bone',root),shift)
        report['max_pelvis_shift_world']=max(report['max_pelvis_shift_world'],(rig.matrix_world.to_3x3()@shift).length)
        for name,(goal,rotation,weight) in frame_goals.items():
            report['ik_clamped_samples']+=int(_solve_limb(rig,mats,chains[name],goal,engine))
            _rotate_subtree(rig,mats,name,rotation)
            if weight>=.999:
                error=(rig.matrix_world.to_3x3()@(mats[name].translation-goal)).length
                report['max_contact_error_world']=max(report['max_contact_error_world'],error)
        engine._assign(rig,mats)
        for pb in engine.ordered(rig):
            pb.rotation_mode='QUATERNION'
            projected=engine._pose_from_basis(pb,pb.matrix_basis,mats[pb.parent.name] if pb.parent else None)
            error=max(abs(projected[r][c]-mats[pb.name][r][c]) for r in range(4) for c in range(4))
            report['max_basis_projection_error']=max(report['max_basis_projection_error'],error)
            if error>.005 or not all(math.isfinite(v) for row in pb.matrix_basis for v in row):
                raise ValueError(f'Postprocess produced unsupported shear/nonfinite pose at {pb.name}')
            if pb.name in previous and pb.rotation_quaternion.dot(previous[pb.name])<0:pb.rotation_quaternion=-pb.rotation_quaternion
            previous[pb.name]=pb.rotation_quaternion.copy()
            for field in ('location','rotation_quaternion','scale'):pb.keyframe_insert(field,frame=frame,group=pb.name)
        bpy.context.view_layer.update()
        for name,(goal,_,weight) in frame_goals.items():
            if weight>=.999:
                error=(rig.matrix_world.to_3x3()@(rig.pose.bones[name].matrix.translation-goal)).length
                report['max_contact_error_world']=max(report['max_contact_error_world'],error)
    report['authority']='Configured thresholds and geometry; auto segments are inferred contacts'
    report['settings']=copy.deepcopy(config)
    report['contact_satisfied']=report['max_contact_error_world']<=config.get('max_contact_error',.005)
    if config.get('strict',False) and not report['contact_satisfied']:
        raise ValueError(f"Contact error exceeds configured tolerance: {report['max_contact_error_world']}")
    return report
