"""Bounded synthetic integration suite for contact/control/adaptive techniques."""
import argparse
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bpy
from mathutils import Matrix,Vector
from motion_remap import core,engine,controls
from motion_remap.postprocess import ground_hit
from motion_remap.verify_blender import rig,animate,preset,near,mesh_for


def legs(name,short=False):
    data=bpy.data.armatures.new(name);obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    root=data.edit_bones.new('root');root.head=(0,0,2);root.tail=(0,0,2.3)
    for side,x in (('L',-.3),('R',.3)):
        previous=root
        heads=[(x,0,2),(x,.2,1.2 if short else 1),(x,0,.5 if short else .1),(x,-.3,.5 if short else .1)]
        for i,base in enumerate(('upper','lower','end','toe')):
            b=data.edit_bones.new(base+'.'+side);b.head=heads[i]
            b.tail=heads[i+1] if i<3 else (x,-.5,heads[i][2])
            b.parent=previous;previous=b
    bpy.ops.object.mode_set(mode='OBJECT');obj.select_set(False);return obj


def make_control_target(reference):
    obj,_,_=engine.clone_target(reference);obj.name='ControlTarget'
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for bone in list(obj.data.edit_bones):
        ctrl=obj.data.edit_bones.new('CTRL_'+bone.name)
        ctrl.head=bone.head;ctrl.tail=bone.tail;ctrl.matrix=bone.matrix;ctrl.use_deform=False
    unused=obj.data.edit_bones.new('Unused');unused.head=(3,0,0);unused.tail=(3,1,0);unused.use_deform=False
    bpy.ops.object.mode_set(mode='OBJECT');obj.select_set(False)
    for name in ['root','upper','lower','end','tip']:
        constraint=obj.pose.bones[name].constraints.new('COPY_TRANSFORMS')
        constraint.target=obj;constraint.subtarget='CTRL_'+name
    obj.pose.bones['CTRL_root']['IK_FK']=1.0
    # A real driver whose ID must be remapped to the copy (no Python script execution).
    driver=obj.pose.bones['upper'].constraints[0].driver_add('influence').driver
    driver.type='SCRIPTED';driver.expression='switch'
    variable=driver.variables.new();variable.name='switch';variable.type='SINGLE_PROP'
    variable.targets[0].id=obj;variable.targets[0].data_path='pose.bones["CTRL_root"]["IK_FK"]'
    multi=obj.pose.bones['Unused'].constraints.new('ARMATURE');entry=multi.targets.new();entry.target=obj;entry.subtarget='CTRL_root'
    obj.data['test_switch']=1.0
    driver=obj.data.bones['Unused'].driver_add('hide').driver;driver.type='SCRIPTED';driver.expression='switch'
    variable=driver.variables.new();variable.name='switch';variable.type='SINGLE_PROP'
    variable.targets[0].id_type='ARMATURE';variable.targets[0].id=obj.data;variable.targets[0].data_path='["test_switch"]'
    return obj


def main(out):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.render.fps=30;checks={}
    source=legs('ContactSource');target=legs('ShortLegTarget',True)
    action=bpy.data.actions.new('BiasedStand');action.use_fake_user=True;engine.bind_action(source,action)
    for frame in range(1,32):
        source.pose.bones['root'].location=(.04*math.sin((frame-1)/30*math.pi*2),0,0)
        source.pose.bones['root'].keyframe_insert('location',frame=frame)
    p=preset(source,target);p['ik_chains']=[{'upper':'upper.'+s,'lower':'lower.'+s,'end':'end.'+s} for s in ('L','R')]
    p['postprocess']={'feet':[{'end':'end.'+s,'contact':{'speed':.4,'height':.03,'blend_frames':2}} for s in ('L','R')],
                      'ground':{'height':0},'pelvis':{'bone':'root','max_shift':.8,'axes':['Z'],'smoothness':1},
                      'trajectory':{'axes':['X'],'smoothness':1,'max_deviation':.01}}
    output,_,report=engine.bake(source,target,p,[action]);post=report['clips'][0]['postprocess']
    assert len(post['contacts']['end.L'])==1 and post['contacts']['end.L'][0]==[1.,31.],post
    assert 0.1<post['max_pelvis_shift_world']<=.80001,post
    engine.bind_action(output,bpy.data.actions[report['clips'][0]['output_action']])
    positions=[]
    for frame in range(4,29):
        scene.frame_set(frame);bpy.context.view_layer.update()
        position=output.pose.bones['end.L'].matrix.translation.copy();positions.append(position)
        assert position.z>=-.005,(frame,position,post)
    drift=max((a-positions[0]).length for a in positions)
    assert drift<.01,(drift,post)
    checks['automatic_stance_lock_short_limbs_pelvis']={'drift_world':drift,'report':post}
    import copy
    impossible=copy.deepcopy(p);impossible['postprocess']['pelvis']['max_shift']=0;impossible['postprocess']['strict']=True
    before_count=len(bpy.data.objects)
    try:engine.bake(source,target,impossible,[action])
    except ValueError as exc:assert 'Contact error' in str(exc)
    else:raise AssertionError('Impossible strict contact silently accepted')
    assert len(bpy.data.objects)==before_count
    checks['impossible_contact_strict_rollback']=True
    # Explicit manual contact intervals + toe/swing trajectory and seam before contact.
    p['postprocess']['feet'][0]['contact']={'mode':'manual','intervals':[[1,12]],'blend_frames':0}
    p['postprocess']['feet'][1]['contact']={'mode':'manual','intervals':[[20,31]],'blend_frames':0}
    p['postprocess']['loop']={'blend_frames':5,'root':True}
    _,_,manual=engine.bake(source,target,p,[action])
    assert manual['clips'][0]['postprocess']['contacts']['end.L']==[[1.,12.]]
    checks['manual_intervals_and_loop']=True
    # Evaluated mesh raycast with transformed ground object, not only a flat plane.
    data=bpy.data.meshes.new('slope');data.from_pydata([(-4,-4,-.4),(4,-4,.4),(4,4,.4),(-4,4,-.4)],[],[(0,1,2,3)])
    ground=bpy.data.objects.new('Slope',data);bpy.context.collection.objects.link(ground)
    ground.location.z=.2;ground.scale=(2,2,1);bpy.context.view_layer.update()
    point,normal=ground_hit(Vector((2,0,1)),{'objects':['Slope'],'ray_distance':10})
    assert abs(point.z-.3)<1e-5 and normal.z>.99,(point,normal)
    p['postprocess']['ground']={'objects':['Slope'],'ray_distance':10,'align_feet':True,'max_tilt_degrees':30}
    _,_,slope=engine.bake(source,target,p,[action])
    assert slope['clips'][0]['postprocess']['ground_misses']==0
    checks['mesh_ground_raycast_and_alignment']=True
    # Adaptively detect a nonlinear source curve between sparse regular samples.
    simple=rig('CurveSource');simple_target=rig('CurveTarget');mesh_for(simple_target)
    curve=animate(simple,'Curve')
    slot=simple.animation_data.action_slot
    for layer in curve.layers:
        for strip in layer.strips:
            bag=strip.channelbag(slot)
            for fc in bag.fcurves:
                if fc.data_path=='pose.bones["root"].location' and fc.array_index==0:
                    for key in fc.keyframe_points:key.interpolation='BEZIER';key.handle_left_type='FREE';key.handle_right_type='FREE'
                    fc.keyframe_points[0].handle_right=(2,3)
    p=preset(simple,simple_target);p['adaptive']={'position_tolerance':.005,'rotation_tolerance_degrees':1,'max_depth':8}
    adaptive_out,_,adaptive_report=engine.bake(simple,simple_target,p,[curve],step=5)
    ar=adaptive_report['clips'][0]['adaptive']
    assert ar['output_samples']>ar['input_samples'] and not ar['unresolved_intervals'],ar
    engine.bind_action(simple,curve);engine.bind_action(adaptive_out,bpy.data.actions[adaptive_report['clips'][0]['output_action']])
    dense_error=0
    for i in range(81):
        frame=1+i*.125;scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
        dense_error=max(dense_error,max((pb.matrix.translation-adaptive_out.pose.bones[pb.name].matrix.translation).length for pb in simple.pose.bones))
    assert dense_error<.01,dense_error
    ar['independent_81_sample_max_position_error']=dense_error
    checks['adaptive_nonlinear_curve']=ar
    # Actual animated object translation is folded into root only when opted in.
    simple.keyframe_insert('location',frame=1);simple.location.x=2;simple.keyframe_insert('location',frame=11)
    simple.rotation_euler=(0,0,0);simple.scale=(1,1,1)
    simple.keyframe_insert('rotation_euler',frame=1);simple.keyframe_insert('scale',frame=1)
    simple.rotation_euler.z=.35;simple.scale=(1.2,)*3
    simple.keyframe_insert('rotation_euler',frame=11);simple.keyframe_insert('scale',frame=11)
    scene.frame_set(1);bpy.context.view_layer.update()
    p=preset(simple,simple_target);p['object_motion']='root'
    objout,_,objreport=engine.bake(simple,simple_target,p,[curve])
    engine.bind_action(objout,bpy.data.actions[objreport['clips'][0]['output_action']])
    scene.frame_set(11);bpy.context.view_layer.update()
    object_matrix_error=max(abs((simple.matrix_world@pb.matrix)[r][c]-objout.pose.bones[pb.name].matrix[r][c])
                            for pb in simple.pose.bones for r in range(4) for c in range(4))
    assert object_matrix_error<.001,object_matrix_error
    checks['animated_object_translation_rotation_scale_to_root']={'max_matrix_abs':object_matrix_error}
    # Explicit control rig path retains original constraints + remaps copied driver IDs.
    # Reference is the already baked adaptive result; no source object animation ambiguity.
    control_target=make_control_target(simple_target)
    profile={'approved':True,'fk':[{'bone':b,'control':'CTRL_'+b,'location':True,'rotation':True,'scale':True}
                                  for b in ['root','upper','lower','end','tip']],
             'properties':[{'bone':'CTRL_root','name':'IK_FK','value':1}],
             'verify_bones':[{'reference':b,'target':b} for b in ['root','upper','lower','end','tip']],
             'max_position_error':.002,'max_rotation_error_degrees':.2,'strict':True}
    control_count=len(control_target.pose.bones['upper'].constraints)
    working,_,control_report=controls.bake_controls(adaptive_out,control_target,adaptive_report,profile)
    assert control_report['driver_count']==1
    assert len(control_target.pose.bones['upper'].constraints)==control_count
    assert working.pose.bones['upper'].constraints[0].target==working
    variable=working.animation_data.drivers[0].driver.variables[0]
    assert variable.targets[0].id==working
    assert working.pose.bones['Unused'].constraints[0].targets[0].target==working
    assert working.data.animation_data.drivers[0].driver.variables[0].targets[0].id==working.data
    checks['fk_control_copy_constraints_driver_and_deform_verification']=control_report
    # A constrained target can also be explicitly reduced to a plain export proxy.
    p=preset(simple_target,control_target);p['bones']=[r for r in p['bones'] if not r['target'].startswith('CTRL_')]
    p['target_mode']='deform_proxy';p['root']='root'
    proxy,_,proxy_report=engine.bake(simple_target,control_target,p,[bpy.data.actions[adaptive_report['clips'][0]['output_action']]])
    assert not any(pb.constraints for pb in proxy.pose.bones)
    assert len(control_target.pose.bones['upper'].constraints)==control_count
    checks['explicit_plain_export_proxy']=True
    # Wrong profile must fail and clean its temporary rig/meshes/actions.
    broken=dict(profile);broken['fk']=[{'bone':'root','control':'CTRL_upper','location':True}]
    count=len(bpy.data.objects)
    try:controls.bake_controls(adaptive_out,control_target,adaptive_report,broken)
    except ValueError as exc:assert 'verification' in str(exc)
    else:raise AssertionError('Broken control profile accepted')
    assert len(bpy.data.objects)==count
    checks['bad_control_profile_rollback']=True
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    core.save(out/'verification.json',{'passed':True,'checks':checks})
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'advanced_fixtures.blend'))
    print('ADVANCED_REMAP_PASS',list(checks))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);main(args.out)
