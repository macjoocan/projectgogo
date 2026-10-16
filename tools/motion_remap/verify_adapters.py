"""Real Blender IK-controller and segmented B-Bone skin adapter fixtures."""
import argparse
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import bpy
from motion_remap import core,engine,controls
from motion_remap.deform_export import bake_deform_export
from motion_remap.batch import export_output
from motion_remap.verify_blender import rig,animate,preset


def main(out):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    source=rig('IKSource');target=rig('IKTarget')
    action=animate(source,'IKMotion')
    # Keep parent upper anchored; rotate only lower so endpoint stays within reach.
    for frame in (1,6,11):
        source.pose.bones['root'].location=(0,0,0);source.pose.bones['root'].keyframe_insert('location',frame=frame)
        source.pose.bones['upper'].rotation_quaternion=(1,0,0,0);source.pose.bones['upper'].keyframe_insert('rotation_quaternion',frame=frame)
    reference,_,refreport=engine.bake(source,target,preset(source,target),[action])
    control_target=rig('IKControls')
    bpy.context.view_layer.objects.active=control_target;control_target.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    e=control_target.data.edit_bones.new('FootIK');e.head=(0,3,0);e.tail=(0,3.5,0);e.use_deform=False
    bpy.ops.object.mode_set(mode='OBJECT');control_target.select_set(False)
    ik=control_target.pose.bones['lower'].constraints.new('IK');ik.target=control_target;ik.subtarget='FootIK';ik.chain_count=2
    # Copy end orientation independently; IK target location is the ankle/head.
    rot=control_target.pose.bones['end'].constraints.new('COPY_ROTATION');rot.target=control_target;rot.subtarget='FootIK'
    profile={'approved':True,'ik':[{'bone':'end','control':'FootIK','location':True,'rotation':True,'rest_offset':False}],
             'verify_bones':[{'reference':'end','target':'end'}],
             'max_position_error':.02,'max_rotation_error_degrees':.2,'strict':True}
    _,_,ikreport=controls.bake_controls(reference,control_target,refreport,profile)
    # Segmented B-Bone skin with animated bend offsets (not only a static skeleton).
    data=bpy.data.armatures.new('Bendy');bendy=bpy.data.objects.new('Bendy',data);bpy.context.collection.objects.link(bendy)
    bpy.context.view_layer.objects.active=bendy;bendy.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    bone=data.edit_bones.new('Ribbon');bone.head=(0,0,0);bone.tail=(0,4,0)
    bpy.ops.object.mode_set(mode='OBJECT');bendy.select_set(False);data.bones['Ribbon'].bbone_segments=4
    mesh_data=bpy.data.meshes.new('RibbonMesh')
    verts=[(x,i*.5,0) for i in range(9) for x in (-.15,.15)]
    faces=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(8)]
    mesh_data.from_pydata(verts,[],faces)
    mesh=bpy.data.objects.new('RibbonMesh',mesh_data);bpy.context.collection.objects.link(mesh)
    group=mesh.vertex_groups.new(name='Ribbon');group.add(list(range(len(verts))),1.,'REPLACE')
    mod=mesh.modifiers.new('Skin','ARMATURE');mod.object=bendy
    motion=bpy.data.actions.new('BendMotion');engine.bind_action(bendy,motion)
    for frame,value in ((1,0),(6,.5),(11,-.4)):
        pb=bendy.pose.bones['Ribbon'];pb.bbone_curveinx=value;pb.bbone_curveoutx=-value*.5
        pb.keyframe_insert('bbone_curveinx',frame=frame);pb.keyframe_insert('bbone_curveoutx',frame=frame)
    before=[v.co.copy() for v in mesh.data.vertices]
    original_segments=data.bones['Ribbon'].bbone_segments
    proxy,meshes,report=bake_deform_export(bendy,[motion])
    assert len(proxy.data.bones)==5 and report['max_skin_vertex_error_world']<.002
    assert data.bones['Ribbon'].bbone_segments==original_segments
    assert all(v.co==before[i] for i,v in enumerate(mesh.data.vertices))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    export_output(proxy,meshes,report,out,'bendy_export')
    core.save(out/'verification.json',{'passed':True,'ik_control':ikreport,'segmented_deform_export':report,
                                      'source_vertices_and_segments_unchanged':True})
    print('ADAPTERS_PASS',ikreport,report['max_skin_vertex_error_world'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);main(args.out)
