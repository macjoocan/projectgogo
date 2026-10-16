"""Local Hat in Time evidence fixture; no extracted assets shipped with the tool."""
import argparse
import hashlib
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy
from mathutils import Vector
from motion_remap import core, engine
from motion_remap.batch import export_output


def main(path, out):
    path, out = Path(path), Path(out)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    source = bpy.data.objects['HatKidBody_Rig']
    source.data.pose_position='POSE'
    target, _, _ = engine.clone_target(source)
    target.name = 'HatKidBody_Target'
    p = core.suggest_mapping(source.data.bones.keys(), target.data.bones.keys())
    p.update(approved=True, root=next(b.name for b in target.data.bones if not b.parent),
             source_slot=source.name)
    for row in p['bones']: row['translation'] = True
    actions = [a for a in bpy.data.actions if not a.name.startswith('Remap__')]
    rest = {b.name: b.matrix_local.copy() for b in source.data.bones}
    output, meshes, report = engine.bake(source, target, p, actions)
    checks = []
    for clip, action in zip(report['clips'], actions):
        engine.bind_action(source, action, source.name)
        engine.bind_action(output, bpy.data.actions[clip['output_action']])
        for frame in (clip['frame_start'], (clip['frame_start']+clip['frame_end'])/2, clip['frame_end']):
            bpy.context.scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
            bpy.context.view_layer.update()
            err = max(abs(pb.matrix[r][c]-output.pose.bones[pb.name].matrix[r][c])
                      for pb in source.pose.bones for r in range(4) for c in range(4))
            bone_errors=sorted(((max(abs(pb.matrix[r][c]-output.pose.bones[pb.name].matrix[r][c])
                                    for r in range(4) for c in range(4)),pb.name) for pb in source.pose.bones),reverse=True)
            checks.append({'action':action.name,'frame':frame,'max_matrix_abs':err,'worst_bones':bone_errors[:3]})
    worst = max(c['max_matrix_abs'] for c in checks)
    core.save(out.parent/'hat_diagnostic.json',checks)
    assert worst < .005, worst
    for name, matrix in rest.items():
        assert matrix == source.data.bones[name].matrix_local
    report['identity_checks'] = checks
    report['input_sha256'] = before
    report['scope'] = 'HatKid body part, 70 bones, five source clips; separate head/legs rigs are not merged'
    out.mkdir(parents=True, exist_ok=True)
    core.save(out/'hatkid_identity_preset.json', p)
    paths = export_output(output, meshes, report, out, 'hatkid_body_identity')
    # The saved output must reproduce sampled source matrices, not just have F-curves.
    name = output.name
    expected = {}
    for clip in report['clips']:
        engine.bind_action(output, bpy.data.actions[clip['output_action']])
        frame=(clip['frame_start']+clip['frame_end'])/2
        bpy.context.scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
        bpy.context.view_layer.update()
        expected[clip['output_action']] = (frame, {pb.name:pb.matrix.copy() for pb in output.pose.bones})
    bpy.ops.wm.open_mainfile(filepath=str(paths[0])); output=bpy.data.objects[name]
    reload_error=0
    for action_name, (frame, matrices) in expected.items():
        engine.bind_action(output, bpy.data.actions[action_name])
        bpy.context.scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
        bpy.context.view_layer.update()
        reload_error=max(reload_error, max(abs(output.pose.bones[n].matrix[r][c]-m[r][c])
                                           for n,m in matrices.items() for r in range(4) for c in range(4)))
        for obj in bpy.context.scene.objects:
            if obj.type!='MESH' or not any(m.type=='ARMATURE' and m.object==output for m in obj.modifiers): continue
            evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get()); data=evaluated.to_mesh()
            assert all(math.isfinite(v) for x in data.vertices for v in x.co)
            evaluated.to_mesh_clear()
    assert reload_error<.005
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    core.save(out/'verification.json', {'passed':True, 'source_sha_unchanged':before,
                                      'identity_max_matrix_abs':worst,'saved_reload_max_matrix_abs':reload_error,
                                      'matrix_samples':len(checks)*70, 'clips':len(actions),
                                      'glb':report['export'], 'source_rest_unchanged':True,
                                      'deformed_vertices_finite':True})
    print('HAT_REMAP_PASS',worst,reload_error,len(actions))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);main(args.input,args.out)
