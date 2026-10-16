"""Actual extracted legs + deliberately shortened target fixture, source immutable."""
import argparse
import hashlib
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bpy
from mathutils import Vector
from motion_remap import core,engine
from motion_remap.batch import export_output


def main(path,out):
    path,out=Path(path),Path(out);sha=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    source=bpy.data.objects['HatKidLegs_Rig'];source.data.pose_position='POSE'
    target,meshes,_=engine.clone_target(source);target.name='ShortLegFixture'
    baseline={b.name:b.matrix_local.copy() for b in source.data.bones}
    root_height=target.data.bones['Root'].head_local.z
    bpy.context.view_layer.objects.active=target;target.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    for bone in target.data.edit_bones:
        for field in ('head','tail'):
            point=getattr(bone,field).copy()
            if point.z<root_height:point.z=root_height+(point.z-root_height)*.8
            setattr(bone,field,point)
    bpy.ops.object.mode_set(mode='OBJECT');target.select_set(False)
    for mesh in meshes:
        for vertex in mesh.data.vertices:
            if vertex.co.z<root_height:vertex.co.z=root_height+(vertex.co.z-root_height)*.8
    p=core.suggest_mapping(source.data.bones.keys(),target.data.bones.keys())
    p.update(approved=True,root='Root',source_slot=source.name)
    p['ik_chains']=[{'upper':'bip_leg'+s+'01','lower':'bip_leg'+s+'02','end':'bip_foot'+s+'01'} for s in ('L','R')]
    feet=[]
    for s in ('L','R'):
        name='bip_foot'+s+'01'
        sole=target.data.bones[name].head_local.z-target.data.bones['bip_toe'+s+'01'].head_local.z
        feet.append({'end':name,'sole_offset':sole,
                     'contact':{'mode':'auto','height':1.,'speed':8.,'min_duration':.1,'blend_frames':3}})
    p['postprocess']={'feet':feet,'ground':{'height':0},
                      'pelvis':{'bone':'Root','max_shift':8.,'axes':['Z'],'smoothness':2}}
    action=bpy.data.actions['Idle__Idle']
    output,meshes,report=engine.bake(source,target,p,[action])
    post=report['clips'][0]['postprocess']
    assert sum(len(s) for s in post['contacts'].values())>0,post
    assert post['max_contact_error_world']<.05,post
    assert post['max_pelvis_shift_world']<=8.001,post
    engine.bind_action(output,bpy.data.actions[report['clips'][0]['output_action']])
    for frame in (1,100,250,400,540):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
        for obj in meshes:
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
            assert all(math.isfinite(v) for vertex in mesh.vertices for v in vertex.co);ev.to_mesh_clear()
    for name,matrix in baseline.items():assert source.data.bones[name].matrix_local==matrix
    report['scope']='HatKid legs only; deliberately shortened 0.8 target, configured ankle-to-toe sole offset, inferred Idle contacts; not native game ground/physics'
    out.mkdir(parents=True,exist_ok=True)
    core.save(out/'preset.json',p)
    export_output(output,meshes,report,out,'hat_short_legs')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    core.save(out/'verification.json',{'passed':True,'source_sha_unchanged':sha,'postprocess':post,
                                      'skin_vertices_finite':True,'source_rest_unchanged':True,
                                      'scope':report['scope'],'export':report['export']})
    print('HAT_CONTACT_PASS',post)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);main(args.input,args.out)
