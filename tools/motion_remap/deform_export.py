"""Sample a constrained/B-Bone rig into ordinary weighted export bones.

Linear skinning only. Segmented B-Bones use Blender's rest/pose segment matrices
and two adjacent segment weights. Preserve-volume, envelopes, shape keys and
extra mesh modifiers are rejected rather than silently flattened incorrectly.
"""
import math

import bpy
from mathutils import Matrix

from . import engine


def bake_deform_export(source,actions,*,step=1,max_samples=200000,max_vertex_samples=5000000,source_slot=None):
    engine._uniform(source)
    if not isinstance(step,int) or step<1:raise ValueError('step must be positive')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==source for m in o.modifiers)]
    if not meshes:raise ValueError('No skinned meshes for deformation export')
    for obj in meshes:
        mods=list(obj.modifiers)
        if len(mods)!=1 or mods[0].type!='ARMATURE' or mods[0].use_deform_preserve_volume or mods[0].use_bone_envelopes:
            raise ValueError('Deformation export requires a single linear vertex-group Armature modifier')
        if obj.data.shape_keys or obj.animation_data or obj.constraints:raise ValueError('Prepare meshes without shape keys/object animation/constraints first')
    old_time=bpy.context.scene.frame_current+bpy.context.scene.frame_subframe
    ad=source.animation_data;old=(ad.action,ad.action_slot,ad.use_nla) if ad else None
    basis={p.name:p.matrix_basis.copy() for p in source.pose.bones}
    collection=None;created=[]
    try:
        schedules=[];joints=sum((p.bone.bbone_segments+1 if p.bone.bbone_segments>1 else 1) for p in source.pose.bones if p.bone.use_deform)
        total=0;vertex_total=0
        for action in actions:
            start,end=action.frame_range
            if (end-start)/step*joints>max_samples:raise ValueError('Deform export budget exceeded')
            frames=sorted({float(start),float(end),*range(math.ceil(start),math.floor(end)+1,step),
                           *engine.key_times(source,action,source_slot)})
            total+=len(frames)*joints
            if total>max_samples:raise ValueError('Deform export budget exceeded')
            vertex_total+=len(frames)*sum(len(o.data.vertices) for o in meshes)
            if vertex_total>max_vertex_samples:raise ValueError('Deform vertex validation budget exceeded')
            schedules.append((action,frames))
        if not schedules:raise ValueError('No deformation actions selected')
        if not joints:raise ValueError('No deform bones selected')
        engine.bind_action(source,schedules[0][0],source_slot)
        first=schedules[0][1][0]
        bpy.context.scene.frame_set(math.floor(first),subframe=first-math.floor(first));bpy.context.view_layer.update()
        collection=bpy.data.collections.new('MotionRemap_DeformExport');bpy.context.scene.collection.children.link(collection)
        data=bpy.data.armatures.new(source.name+'__SegmentBones')
        rig=bpy.data.objects.new(source.name+'__DeformExport',data);collection.objects.link(rig)
        reference_world=source.matrix_world.copy();rig.matrix_world=reference_world
        rest={};mapping={}
        evaluated=source.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for pb in evaluated.pose.bones:
            if not pb.bone.use_deform:continue
            count=pb.bone.bbone_segments
            names=[]
            for i in range(count+1 if count>1 else 1):
                name=pb.name if count==1 else f'{pb.name}__segment_{i:02d}'
                if name in rest:raise ValueError('Generated segment bone name collision')
                names.append(name)
                rest[name]=pb.bone.matrix_local@(pb.bbone_segment_matrix(i,rest=True) if count>1 else Matrix.Identity(4))
            mapping[pb.name]=names
        bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
        for name,matrix in rest.items():
            bone=data.edit_bones.new(name);bone.head=(0,0,0);bone.tail=(0,.1,0);bone.matrix=matrix
        bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
        outputs=[]
        for obj in meshes:
            output=obj.copy();output.data=obj.data.copy();collection.objects.link(output)
            world=obj.matrix_world.copy();output.parent=rig;output.matrix_world=world
            output.modifiers[0].object=rig;output.vertex_groups.clear()
            for name in rest:output.vertex_groups.new(name=name)
            to_arm=reference_world.inverted()@obj.matrix_world
            for vertex in obj.data.vertices:
                for entry in vertex.groups:
                    group=obj.vertex_groups[entry.group].name
                    if group not in mapping:continue
                    names=mapping[group]
                    if len(names)==1:output.vertex_groups[names[0]].add([vertex.index],entry.weight,'ADD')
                    else:
                        index,weight=evaluated.pose.bones[group].bbone_segment_index(to_arm@vertex.co)
                        for name,factor in ((names[index],1-weight),(names[index+1],weight)):
                            if factor>0:output.vertex_groups[name].add([vertex.index],entry.weight*factor,'ADD')
            outputs.append(output)
        report={'clips':[],'method':'evaluated linear skin/Blender B-Bone segment matrices',
                'segment_mapping':mapping,'max_matrix_projection_error':0.,'max_skin_vertex_error_world':0.}
        for action,frames in schedules:
            engine.bind_action(source,action,source_slot)
            output_action=bpy.data.actions.new('Deform__'+action.name);output_action.use_fake_user=True;created.append(output_action)
            engine.bind_action(rig,output_action);previous={}
            for frame in frames:
                bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
                evaluated=source.evaluated_get(bpy.context.evaluated_depsgraph_get());matrices={}
                to_rig=rig.matrix_world.inverted()@evaluated.matrix_world
                for original,names in mapping.items():
                    pb=evaluated.pose.bones[original]
                    for i,name in enumerate(names):
                        segment=pb.bbone_segment_matrix(i) if len(names)>1 else Matrix.Identity(4)
                        if len(names)>1:
                            current_rest=pb.bone.matrix_local@pb.bbone_segment_matrix(i,rest=True)
                            if max(abs(current_rest[r][c]-rest[name][r][c]) for r in range(4) for c in range(4))>1e-4:
                                raise ValueError('Animated B-Bone rest shape cannot use a single bind matrix')
                        matrix=to_rig@pb.matrix@segment;loc,rot,scale=matrix.decompose()
                        projection=Matrix.LocRotScale(loc,rot,scale)
                        error=max(abs(projection[r][c]-matrix[r][c]) for r in range(4) for c in range(4))
                        report['max_matrix_projection_error']=max(report['max_matrix_projection_error'],error)
                        if error>.001:raise ValueError('Segment pose contains unsupported shear')
                        matrices[name]=matrix
                engine._assign(rig,matrices)
                for pb in rig.pose.bones:
                    pb.rotation_mode='QUATERNION'
                    if pb.name in previous and pb.rotation_quaternion.dot(previous[pb.name])<0:pb.rotation_quaternion=-pb.rotation_quaternion
                    previous[pb.name]=pb.rotation_quaternion.copy()
                    for field in ('location','rotation_quaternion','scale'):pb.keyframe_insert(field,frame=frame,group=pb.name)
                bpy.context.view_layer.update()
                # Independently compare evaluated original and exported skin every sampled frame.
                for original,output in zip(meshes,outputs):
                    dg=bpy.context.evaluated_depsgraph_get();a=original.evaluated_get(dg);b=output.evaluated_get(dg)
                    am,bm=a.to_mesh(),b.to_mesh()
                    try:
                        error=max((((a.matrix_world@av.co)-(b.matrix_world@bv.co)).length for av,bv in zip(am.vertices,bm.vertices)),default=0)
                        report['max_skin_vertex_error_world']=max(report['max_skin_vertex_error_world'],error)
                        if len(am.vertices)!=len(bm.vertices) or error>.002:raise ValueError(f'Deformation proxy vertex mismatch: {error}')
                    finally:a.to_mesh_clear();b.to_mesh_clear()
            for layer in output_action.layers:
                for strip in layer.strips:
                    bag=strip.channelbag(rig.animation_data.action_slot)
                    if bag:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:key.interpolation='LINEAR'
            report['clips'].append({'source_action':action.name,'output_action':output_action.name,
                'frame_start':frames[0],'frame_end':frames[-1],'samples':len(frames)})
        return rig,outputs,report
    except Exception:
        if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
        if collection:engine.cleanup_collection(collection)
        for action in created:bpy.data.actions.remove(action)
        raise
    finally:
        if old:
            source.animation_data.action=old[0]
            if old[0] and old[1]:source.animation_data.action_slot=old[1]
            source.animation_data.use_nla=old[2]
        elif source.animation_data:source.animation_data_clear()
        for name,matrix in basis.items():source.pose.bones[name].matrix_basis=matrix
        bpy.context.scene.frame_set(math.floor(old_time),subframe=old_time-math.floor(old_time));bpy.context.view_layer.update()
