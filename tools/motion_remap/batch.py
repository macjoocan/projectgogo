"""Run using Blender --background --python tools/motion_remap/batch.py -- ..."""
import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy
from motion_remap import core, engine


def export_output(rig, meshes, report, folder, stem='remapped'):
    """Export only output objects, with one NLA strip per generated action."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    paths = [folder/(stem+suffix) for suffix in ('.blend', '.glb', '.json')]
    if any(p.exists() for p in paths):
        raise ValueError("Output already exists; choose a new folder or stem")
    bpy.ops.object.select_all(action='DESELECT')
    for obj in [rig, *meshes]: obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.animation_data.action = None
    for clip in report['clips']:
        action = bpy.data.actions[clip['output_action']]
        track = rig.animation_data.nla_tracks.new(); track.name = action.name
        strip = track.strips.new(action.name, int(clip['frame_start']), action)
        if len(action.slots): strip.action_slot = action.slots[0]
    rig.animation_data.use_nla = True
    bpy.ops.wm.save_as_mainfile(filepath=str(paths[0]))
    bpy.ops.export_scene.gltf(filepath=str(paths[1]), export_format='GLB', use_selection=True,
                             export_animations=True, export_animation_mode='ACTIONS',
                             export_anim_single_armature=False, export_skins=True,
                             export_force_sampling=False)
    # A successful exporter call is insufficient: require actual animation and skin payloads.
    import struct
    with paths[1].open('rb') as f:
        header = f.read(20)
        if header[:4] != b'glTF': raise ValueError("Invalid GLB magic")
        data = json.loads(f.read(struct.unpack_from('<I', header, 12)[0]))
    if len(data.get('animations', [])) != len(report['clips']):
        raise ValueError("GLB animation count differs from baked actions")
    if meshes and not data.get('skins'):
        raise ValueError("GLB lost the skinned mesh")
    report['export'] = {'animations': len(data.get('animations', [])),
                        'skins': len(data.get('skins', [])),
                        'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths[:2]}}
    core.save(paths[2], report)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, help='Prepared .blend containing source/target rigs')
    parser.add_argument('--source', required=True)
    parser.add_argument('--target')
    parser.add_argument('--preset')
    parser.add_argument('--out', required=True)
    parser.add_argument('--actions', default='*', help='Exact-case glob; explicitly narrow for big libraries')
    parser.add_argument('--step', type=int, default=1)
    parser.add_argument('--max-samples', type=int, default=200000)
    parser.add_argument('--control-profile',help='Optional reviewed FK/IK profile; keeps controller copy in saved Blend')
    parser.add_argument('--deform-export-only',action='store_true',help='Bake evaluated source constraints/B-Bones to ordinary skin bones (no retarget)')
    parser.add_argument('--max-vertex-samples',type=int,default=5000000)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    if not args.deform_export_only and (not args.target or not args.preset):parser.error('--target and --preset are required for retargeting')
    if args.deform_export_only and args.control_profile:parser.error('--control-profile is a retarget option')
    path = Path(args.input).resolve()
    out = Path(args.out).resolve()
    if not path.is_file() or path.suffix.lower() != '.blend':
        raise ValueError("Input must be an existing .blend")
    if (out/'remapped.blend').resolve() == path:
        raise ValueError("Cannot overwrite input .blend")
    if any((out/('remapped'+ext)).exists() for ext in ('.blend', '.glb', '.json')):
        raise ValueError("Output exists")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    actions = [a for a in bpy.data.actions if fnmatch.fnmatchcase(a.name, args.actions)
               and not a.name.startswith('Remap__')]
    if args.deform_export_only:
        from motion_remap.deform_export import bake_deform_export
        rig,meshes,report=bake_deform_export(bpy.data.objects[args.source],actions,step=args.step,
                                            max_samples=args.max_samples,max_vertex_samples=args.max_vertex_samples)
    else:
        rig, meshes, report = engine.bake(bpy.data.objects[args.source], bpy.data.objects[args.target],
                                        core.load(args.preset), actions, step=args.step,
                                        max_samples=args.max_samples)
    report['input'] = {'path': str(path), 'sha256': before}
    if args.control_profile:
        from motion_remap.controls import bake_controls
        control_rig,_,control_report=bake_controls(rig,bpy.data.objects[args.target],report,
                                                 core.load(args.control_profile),max_samples=args.max_samples)
        report['control_rig']={'name':control_rig.name,'report':control_report}
    rig['motion_remap_report']=json.dumps(report,ensure_ascii=False)
    export_output(rig, meshes, report, out)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    print('MOTION_REMAP_PASS', json.dumps(report['export']))


if __name__ == '__main__': main()
