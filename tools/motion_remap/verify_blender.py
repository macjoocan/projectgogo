"""Headless Blender integration tests. Outputs fixtures under a supplied output dir.

blender --background --factory-startup --python this.py -- --out <empty-dir>
"""
import argparse
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy
from mathutils import Matrix, Quaternion, Vector
from motion_remap import core, engine
from motion_remap.batch import export_output


def near(a, b, eps=5e-4):
    if isinstance(a, Matrix):
        error = max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
    else:
        error = (a-b).length
    assert error < eps, (error, a, b)
    return error


def rig(name, factor=1, rotated=False):
    data = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, data); bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    definitions = [('root', None, (0, 0, 0), (0, 1, 0)),
                   ('upper', 'root', (0, 1, 0), (.5, 2, 0)),
                   ('lower', 'upper', (.5, 2, 0), (0, 3, 0)),
                   ('end', 'lower', (0, 3, 0), (0, 3.5, 0)),
                   ('tip', 'end', (0, 3.5, 0), (0, 3.7, 0))]
    for name_, parent, head, tail in definitions:
        b = data.edit_bones.new(name_); b.head = Vector(head)*factor; b.tail = Vector(tail)*factor
        if parent: b.parent = data.edit_bones[parent]
        if rotated and name_ == 'upper': b.roll = .4
    bpy.ops.object.mode_set(mode='OBJECT'); obj.select_set(False)
    return obj


def mesh_for(obj):
    data = bpy.data.meshes.new('weighted')
    data.from_pydata([(0, 0, 0), (.2, 1, 0), (0, 3, .2)], [], [(0, 1, 2)])
    mesh = bpy.data.objects.new('weighted', data); bpy.context.collection.objects.link(mesh)
    mesh.parent = obj
    for i, name in enumerate(('root', 'upper', 'end')):
        group = mesh.vertex_groups.new(name=name); group.add([i], 1, 'REPLACE')
    mod = mesh.modifiers.new('skin', 'ARMATURE'); mod.object = obj
    return mesh


def animate(obj, name, offset=0):
    action = bpy.data.actions.new(name); engine.bind_action(obj, action)
    for frame in (1, 6, 11):
        for p in obj.pose.bones:
            p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion((0, 0, 1), (frame-1)*.02 if p.name != 'root' else 0)
            p.location = ((frame-1)*.1+offset, 0, (frame-1)*.02) if p.name == 'root' else (0, 0, 0)
            p.scale = (1, 1, 1)
            for field in ('location', 'rotation_quaternion', 'scale'):
                p.keyframe_insert(field, frame=frame)
    return action


def preset(source, target):
    p = core.suggest_mapping(source.data.bones.keys(), target.data.bones.keys())
    p.update(approved=True, root='root')
    return p


def main(out):
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    import motion_remap
    motion_remap.register(); motion_remap.unregister()
    checks = {'ui_register_unregister': True}
    source = rig('Source'); target = rig('Target'); mesh_for(target)
    a = animate(source, 'WalkFixture'); b = animate(source, 'RunFixture', .2)
    engine.bind_action(source, a)
    bpy.context.scene.frame_set(6)
    before = {p.name: p.matrix.copy() for p in source.pose.bones}
    rests = {p.name: p.matrix_local.copy() for p in source.data.bones}
    output, meshes, report = engine.bake(source, target, preset(source, target), [a, b])
    assert source.animation_data.action == a and bpy.context.scene.frame_current == 6
    for name, mat in before.items(): near(source.pose.bones[name].matrix, mat)
    for name, mat in rests.items(): near(source.data.bones[name].matrix_local, mat, 1e-8)
    checks['source_rest_pose_action_frame_preserved'] = True
    errors = []
    for clip, action in zip(report['clips'], (a, b)):
        engine.bind_action(source, action); engine.bind_action(output, bpy.data.actions[clip['output_action']])
        for frame in (1, 3, 6, 11):
            bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
            errors += [near(p.matrix, output.pose.bones[p.name].matrix) for p in source.pose.bones]
    checks['identity_2actions_4frames_5bones_max_error'] = max(errors)
    # Fractional discontinuity-like keys would be lost by integer-only baking.
    fractional=animate(source,'FractionalFixture')
    source.pose.bones['root'].location=(2.3,0,.1)
    source.pose.bones['root'].keyframe_insert('location',frame=3.25)
    fracout,_,fracreport=engine.bake(source,target,preset(source,target),[fractional])
    engine.bind_action(source,fractional)
    engine.bind_action(fracout,bpy.data.actions[fracreport['clips'][0]['output_action']])
    bpy.context.scene.frame_set(3,subframe=.25);bpy.context.view_layer.update()
    near(source.pose.bones['root'].matrix,fracout.pose.bones['root'].matrix)
    checks['fractional_source_key_preserved']=True
    # Source scale and optional local translation must not silently disappear.
    scaleaction=animate(source,'ScaleTranslateFixture')
    for frame,scale in ((1,1.0),(6,1.15),(11,1.0)):
        source.pose.bones['upper'].scale=(scale,)*3
        source.pose.bones['upper'].keyframe_insert('scale',frame=frame)
        source.pose.bones['tip'].location=(.2,0,0)
        source.pose.bones['tip'].keyframe_insert('location',frame=frame)
    spreset=preset(source,target)
    for row in spreset['bones']:row['translation']=True
    scaleout,_,scalereport=engine.bake(source,target,spreset,[scaleaction])
    engine.bind_action(source,scaleaction)
    engine.bind_action(scaleout,bpy.data.actions[scalereport['clips'][0]['output_action']])
    bpy.context.scene.frame_set(6);bpy.context.view_layer.update()
    for pb in source.pose.bones:near(pb.matrix,scaleout.pose.bones[pb.name].matrix)
    checks['scale_and_local_translation_preserved']=True
    # A different object transform is supported when static and uniformly scaled.
    target2 = rig('LargeTarget', factor=2, rotated=True)
    target2.rotation_euler.z = .3; target2.scale = (1.5,)*3
    target2.location = (5, -2, 1); bpy.context.view_layer.update()
    p = preset(source, target2); p['in_place_axes'] = ['X']
    mapped, _, rep = engine.bake(source, target2, p, [a])
    assert abs(rep['scale_ratio_world']-3) < 1e-5
    values = []
    engine.bind_action(mapped, bpy.data.actions[rep['clips'][0]['output_action']])
    for frame in (1, 6, 11):
        bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
        values.append(mapped.pose.bones['root'].matrix.translation.copy())
    assert max(v.x for v in values)-min(v.x for v in values) < 1e-5
    assert values[-1].z > values[0].z
    source_q=source.pose.bones['upper'].matrix.to_quaternion()
    source_rest_q=source.data.bones['upper'].matrix_local.to_quaternion()
    target_q=mapped.matrix_world.to_quaternion()@mapped.pose.bones['upper'].matrix.to_quaternion()
    target_rest_q=mapped.matrix_world.to_quaternion()@mapped.data.bones['upper'].matrix_local.to_quaternion()
    angular_error=(source_q@source_rest_q.inverted()).rotation_difference(target_q@target_rest_q.inverted()).angle
    assert min(abs(angular_error),abs(2*math.pi-angular_error))<1e-3
    checks['different_rest_roll_world_ratio3_in_place_x'] = True
    # Reference snapshot aligns a posed source reference to untouched target rest.
    engine.bind_action(source, None)
    for pb in source.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    source.pose.bones['upper'].rotation_quaternion = Quaternion((1, 0, 0), .45)
    bpy.context.view_layer.update(); snapshot = engine.capture_reference(source)
    c = bpy.data.actions.new('ReferencePose'); engine.bind_action(source, c)
    for pb in source.pose.bones:
        for field in ('location', 'rotation_quaternion', 'scale'): pb.keyframe_insert(field, frame=1)
    p = preset(source, target)
    for row in p['bones']: row['source_reference_wxyz'] = snapshot[row['source']]
    refout, _, repref = engine.bake(source, target, p, [c])
    engine.bind_action(refout, bpy.data.actions[repref['clips'][0]['output_action']])
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    for pb in refout.pose.bones: near(pb.matrix, pb.bone.matrix_local)
    checks['non_destructive_reference_pose'] = True
    # IK mathematical oracle: reachable endpoint and both segment lengths.
    mid, end, clamp = engine.solve_two_bone(Vector((0,0,0)), Vector((1,1,0)), Vector((0,0,1)), 1, 1)
    near(end, Vector((1,1,0)), 1e-6)
    assert abs(mid.length-1)<1e-6 and abs((end-mid).length-1)<1e-6 and not clamp
    mid, end, clamp = engine.solve_two_bone(Vector((0,0,0)), Vector((0,9,0)), Vector((0,1,0)), 1, 1)
    assert clamp and abs(end.length-2)<1e-5 and all(math.isfinite(x) for x in mid)
    p = preset(source, target)
    p['ik_chains'] = [{'upper':'upper','lower':'lower','end':'end'}]
    ikout, _, ikreport = engine.bake(source, target, p, [a])
    engine.bind_action(source, a); engine.bind_action(ikout, bpy.data.actions[ikreport['clips'][0]['output_action']])
    for frame in (1, 6, 11):
        bpy.context.scene.frame_set(frame); bpy.context.view_layer.update()
        near(source.pose.bones['end'].matrix.translation, ikout.pose.bones['end'].matrix.translation)
        near(source.pose.bones['tip'].matrix.translation, ikout.pose.bones['tip'].matrix.translation)
    checks['ik_reachable_unreachable_singular_and_descendant'] = True
    # Reject unsupported rigs and sampling requests without leaving output objects.
    before_count=len(bpy.data.objects)
    target.scale=(1,2,1);bpy.context.view_layer.update()
    try:engine.bake(source,target,preset(source,target),[a])
    except ValueError as exc:assert 'Nonuniform' in str(exc)
    else:raise AssertionError('Nonuniform object scale was accepted')
    target.scale=(1,1,1);bpy.context.view_layer.update()
    try:engine.bake(source,target,preset(source,target),[a],max_samples=5)
    except ValueError as exc:assert 'budget' in str(exc)
    else:raise AssertionError('Sampling cap was ignored')
    assert len(bpy.data.objects)==before_count
    checks['unsupported_scale_and_budget_rejected']=True
    # Failure rollback after output allocation: animated source object transform.
    source.keyframe_insert('location', frame=1)
    source.location.x = 3; source.keyframe_insert('location', frame=11)
    object_action = source.animation_data.action
    count = len(bpy.data.objects)
    failed = False
    try: engine.bake(source, target, preset(source, target), [object_action])
    except ValueError as exc:
        assert 'object transform' in str(exc); failed = True
    assert failed and len(bpy.data.objects) == count
    checks['rollback_animated_object_rejected'] = True
    source.location = (0,0,0)
    # Serialize the identity fixture then reopen and independently check pose/weights.
    engine.bind_action(source, a)
    paths = export_output(output, meshes, report, out, 'synthetic')
    rig_name = output.name
    clip_name = report['clips'][0]['output_action']
    # Read saved file (not in-memory cached output) in the same process.
    bpy.ops.wm.open_mainfile(filepath=str(paths[0]))
    saved = bpy.data.objects[rig_name]
    engine.bind_action(saved, bpy.data.actions[clip_name])
    bpy.context.scene.frame_set(6); bpy.context.view_layer.update()
    near(saved.pose.bones['root'].matrix.translation, Vector((.5,0,.1)))
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and any(m.type == 'ARMATURE' and m.object == saved for m in obj.modifiers):
            assert all(abs(sum(g.weight for g in v.groups)-1)<1e-6 for v in obj.data.vertices)
            ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); data=ev.to_mesh()
            assert all(math.isfinite(x) for v in data.vertices for x in v.co); ev.to_mesh_clear()
    checks['saved_reopen_skin_and_root'] = True
    core.save(Path(out)/'verification.json', {'checks':checks, 'report':report, 'passed':True})
    print('BLENDER_INTEGRATION_PASS', json.dumps(checks))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--out', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:]); main(args.out)
