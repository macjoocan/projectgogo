"""Explicit FK/IK/pole/custom-property adapter for copied Blender control rigs.

No name heuristic can infer arbitrary rig internals. A reviewed profile specifies
which controls drive which reference bones, then measured deform error decides
whether that profile works. Constraints/drivers are preserved on the rig copy.
"""
import math
import copy

import bpy
from mathutils import Matrix,Vector

from . import engine


def draft_profile(reference,target):
    """Conservative Rigify-like FK convention suggestions, never auto-approved."""
    rows=[];missing=[]
    for bone in reference.data.bones:
        stem=bone.name.removeprefix('DEF-')
        side=stem[-2:] if stem.endswith(('.L','.R')) else ''
        base=stem[:-2] if side else stem
        candidates=[base+'_fk'+side,stem] if side else [stem]
        matches=[name for name in candidates if name in target.data.bones and not target.pose.bones[name].constraints]
        if len(matches)==1:rows.append({'bone':bone.name,'control':matches[0],'location':False,'rotation':True})
        else:missing.append({'bone':bone.name,'candidates':matches})
    return {'version':1,'approved':False,'fk':rows,'ik':[],'properties':[],
            'verify_bones':[],'max_position_error':.01,'max_rotation_error_degrees':2,
            'strict':True,'unresolved':missing}


def validate(reference,target,profile):
    engine._uniform(reference);engine._uniform(target)
    if profile.get('approved') is not True:raise ValueError('Review and approve the control profile')
    used=set()
    for row in profile.get('fk',[])+profile.get('ik',[]):
        if row.get('bone') not in reference.pose.bones or row.get('control') not in target.pose.bones:
            raise ValueError('Unknown reference/control bone')
        if row['control'] in used:raise ValueError('Control driven twice')
        used.add(row['control'])
        if target.pose.bones[row['control']].constraints:raise ValueError('Driven control itself has constraints')
        if row.get('pole_control'):
            if row['pole_control'] not in target.pose.bones:raise ValueError('Unknown pole control')
            if row['pole_control'] in used:raise ValueError('Pole control driven twice')
            used.add(row['pole_control'])
            for key in ('upper','lower','end'):
                if row.get('chain',{}).get(key) not in reference.pose.bones:raise ValueError('Invalid pole reference chain')
    if not used:raise ValueError('Empty control profile')
    for row in profile.get('properties',[]):
        if row.get('bone') not in target.pose.bones or row.get('name') not in target.pose.bones[row['bone']]:
            raise ValueError('Unknown IK/FK custom property')
        if not isinstance(row.get('value'),(int,float)) or not math.isfinite(row['value']):raise ValueError('Invalid custom property value')
    if not profile.get('verify_bones'):raise ValueError('Control profile must declare deform bones to verify')
    for row in profile['verify_bones']:
        if row['reference'] not in reference.pose.bones or row['target'] not in target.pose.bones:raise ValueError('Unknown verification bone')
    for key in ('max_position_error','max_rotation_error_degrees'):
        if not isinstance(profile.get(key),(int,float)) or not math.isfinite(profile[key]) or profile[key]<0:
            raise ValueError('Control profile error tolerances are required')
    scale_tolerance=profile.get('max_scale_error',.01)
    if not isinstance(scale_tolerance,(int,float)) or not math.isfinite(scale_tolerance) or scale_tolerance<0:
        raise ValueError('Invalid scale verification tolerance')


def bake_controls(reference,target,reference_report,profile,*,max_samples=200000):
    validate(reference,target,profile)
    scene=bpy.context.scene;old_time=scene.frame_current+scene.frame_subframe
    ad=reference.animation_data
    old=(ad.action,ad.action_slot,ad.use_nla) if ad else None
    basis={p.name:p.matrix_basis.copy() for p in reference.pose.bones}
    rig=None;collection=None;created=[];report={'clips':[],'method':'explicit copied control rig; evaluated deform verification',
                                              'profile':copy.deepcopy(profile)}
    try:
        rig,meshes,collection=engine.clone_target(target,keep_controls=True)
        report['driver_count']=len(rig.animation_data.drivers) if rig.animation_data else 0
        report['armature_data_driver_count']=len(rig.data.animation_data.drivers) if rig.data.animation_data else 0
        budget=0
        for clip in reference_report['clips']:
            action=bpy.data.actions[clip['output_action']]
            engine.bind_action(reference,action)
            frames=sorted(engine.key_times(reference,action,reference.name))
            frames=[f for f in frames if clip['frame_start']<=f<=clip['frame_end']]
            budget+=len(frames)*len(rig.data.bones)
            if budget>max_samples:raise ValueError('Control bone-frame budget exceeded')
            baked=bpy.data.actions.new('Controls__'+clip['source_action']);created.append(baked);baked.use_fake_user=True
            engine.bind_action(rig,baked)
            # Set IK/FK switches before evaluating constraints/drivers.
            for prop in profile.get('properties',[]):
                pb=rig.pose.bones[prop['bone']];pb[prop['name']]=prop['value']
                pb.keyframe_insert(data_path='["'+prop['name'].replace('"','\\"')+'"]',frame=frames[0])
            position_error=rotation_error=scale_error=0.;previous={}
            for frame in frames:
                scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
                commands={}
                for row in profile.get('fk',[])+profile.get('ik',[]):
                    bone=reference.pose.bones[row['bone']];control=rig.pose.bones[row['control']]
                    desired_world=reference.matrix_world@bone.matrix
                    if row.get('rest_offset',True):
                        desired_world=desired_world@bone.bone.matrix_local.inverted()@reference.matrix_world.inverted()@rig.matrix_world@control.bone.matrix_local
                    desired=rig.matrix_world.inverted()@desired_world
                    current=control.matrix
                    commands[control.name]=Matrix.LocRotScale(desired.translation if row.get('location',row in profile.get('ik',[])) else current.translation,
                        desired.to_quaternion() if row.get('rotation',True) else current.to_quaternion(),
                        desired.to_scale() if row.get('scale',False) else current.to_scale())
                    if row.get('pole_control'):
                        chain=row['chain'];u,l,e=(reference.pose.bones[chain[k]].matrix.translation for k in ('upper','lower','end'))
                        axis=(e-u).normalized();bend=l-u-axis*(l-u).dot(axis)
                        if bend.length<1e-6:bend=Vector(row.get('pole_fallback',[0,0,1]))
                        pole_world=reference.matrix_world@(l+bend.normalized()*row.get('pole_distance',1))
                        pole=rig.pose.bones[row['pole_control']].matrix.copy()
                        pole.translation=rig.matrix_world.inverted()@pole_world
                        commands[row['pole_control']]=pole
                for pb in engine.ordered(rig):
                    if pb.name not in commands:continue
                    pb.rotation_mode='QUATERNION';pb.matrix=commands[pb.name]
                    if pb.name in previous and pb.rotation_quaternion.dot(previous[pb.name])<0:pb.rotation_quaternion=-pb.rotation_quaternion
                    previous[pb.name]=pb.rotation_quaternion.copy()
                    for field in ('location','rotation_quaternion','scale'):pb.keyframe_insert(field,frame=frame,group=pb.name)
                    bpy.context.view_layer.update()
                bpy.context.view_layer.update()
                evaluated=rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
                for row in profile['verify_bones']:
                    expected=reference.matrix_world@reference.pose.bones[row['reference']].matrix
                    actual=evaluated.matrix_world@evaluated.pose.bones[row['target']].matrix
                    position_error=max(position_error,(expected.translation-actual.translation).length)
                    scale_error=max(scale_error,(expected.to_scale()-actual.to_scale()).length)
                    difference=expected.to_quaternion().inverted()@actual.to_quaternion()
                    angle=2*math.atan2(math.sqrt(difference.x**2+difference.y**2+difference.z**2),abs(difference.w))
                    rotation_error=max(rotation_error,math.degrees(angle))
            if profile.get('strict',True) and (position_error>profile['max_position_error'] or rotation_error>profile['max_rotation_error_degrees'] or scale_error>profile.get('max_scale_error',.01)):
                raise ValueError(f'Control profile failed deform verification: position={position_error}, rotation={rotation_error}, scale={scale_error}')
            for layer in baked.layers:
                for strip in layer.strips:
                    bag=strip.channelbag(rig.animation_data.action_slot)
                    if bag:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:key.interpolation='LINEAR'
            report['clips'].append({'source_action':clip['source_action'],'output_action':baked.name,
                'frame_start':frames[0],'frame_end':frames[-1],'samples':len(frames),
                'max_deform_position_error_world':position_error,'max_deform_rotation_error_degrees':rotation_error,
                'max_deform_scale_error':scale_error})
        verified={r['target'] for r in profile['verify_bones']}
        report['unverified_deform_bones']=[b.name for b in target.data.bones if b.use_deform and b.name not in verified]
        return rig,meshes,report
    except Exception:
        if collection:engine.cleanup_collection(collection)
        for action in created:bpy.data.actions.remove(action)
        raise
    finally:
        if old:
            reference.animation_data.action=old[0]
            if old[0] and old[1]:reference.animation_data.action_slot=old[1]
            reference.animation_data.use_nla=old[2]
        elif reference.animation_data:reference.animation_data_clear()
        for name,matrix in basis.items():reference.pose.bones[name].matrix_basis=matrix
        scene.frame_set(math.floor(old_time),subframe=old_time-math.floor(old_time));bpy.context.view_layer.update()
