"""Blender 5.x bake engine: rest-relative rotations, root motion and two-bone IK.

Always creates a separate working rig and skinned mesh copies. Inputs are never
edited in Edit Mode, destructively normalized, or overwritten on disk.
"""
import math
import statistics

import bpy
from mathutils import Matrix, Quaternion, Vector

from .core import validate


def q(value):
    return Quaternion(value).normalized()


def ordered(rig):
    return sorted(rig.pose.bones, key=lambda p: len(p.parent_recursive))


def resolve_slot(rig, action, slot_name=None):
    if action and len(action.slots):
        slots = [s for s in action.slots if s.name_display == (slot_name or rig.name)]
        if not slots and len(action.slots) == 1:
            slots = list(action.slots)
        if len(slots) != 1:
            raise ValueError(f"Action {action.name}: specify an exact source_slot (multi-slot rig)")
        return slots[0]
    return None


def bind_action(rig, action, slot_name=None):
    slot = resolve_slot(rig, action, slot_name)
    rig.animation_data_create()
    rig.animation_data.use_nla = False
    rig.animation_data.action = action
    if slot: rig.animation_data.action_slot = slot


def key_times(rig, action, slot_name):
    slot = resolve_slot(rig, action, slot_name)
    if not slot: return set()
    result = set()
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(slot)
            if bag:
                for curve in bag.fcurves:
                    result.update(float(k.co.x) for k in curve.keyframe_points)
    return result


def capture_reference(rig):
    """Pose snapshot relative to the immutable data-bone rest rotation.

This is an armature-space orientation reference, not an edited bind pose.
Capture an unanimated rest-correction pose (e.g. T to A), not a moving frame.
"""
    bpy.context.view_layer.update()
    return {p.name: list((p.bone.matrix_local.to_quaternion().inverted() @
                         p.matrix.to_quaternion()).normalized()) for p in rig.pose.bones}


def _uniform(rig):
    if rig.type != 'ARMATURE':
        raise ValueError("Source and target must be armatures")
    if rig.mode != 'OBJECT':
        raise ValueError("Switch both armatures to Object Mode")
    m = rig.matrix_world.to_3x3()
    scales = [m.col[i].length for i in range(3)]
    if min(scales) <= 1e-8 or max(scales)-min(scales) > 1e-5 * max(scales):
        raise ValueError("Nonuniform/zero object scale: use a separate prepared working rig")
    if m.determinant() <= 0 or any(abs(m.col[a].dot(m.col[b])) > 1e-5*max(scales)**2
                                  for a, b in ((0, 1), (0, 2), (1, 2))):
        raise ValueError("Reflected or sheared armature object transforms are unsupported")
    return scales[0]


def validate_rigs(source, target, preset):
    if source == target:
        raise ValueError("Use distinct source and target objects (duplicate for self tests)")
    ss, ts = _uniform(source), _uniform(target)
    validate(preset, source.data.bones.keys(), target.data.bones.keys())
    proxy=preset.get('target_mode','plain')=='deform_proxy'
    if not proxy and (target.constraints or any(p.constraints for p in target.pose.bones)):
        raise ValueError("plain target mode requires a skeleton without control constraints; select deform_proxy for the control adapter")
    if not proxy and target.animation_data and target.animation_data.drivers:
        raise ValueError("Target drivers are not supported")
    if not proxy and target.data.animation_data and target.data.animation_data.drivers:
        raise ValueError("Target armature-data drivers are not supported")
    if source.data.pose_position != 'POSE':
        raise ValueError("Source armature must display Pose Position")
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and any(m.type == 'ARMATURE' and m.object == target for m in obj.modifiers):
            if obj.animation_data or obj.parent_type == 'BONE' or obj.constraints:
                raise ValueError("Animated/constrained/bone-parented target meshes need a plain export rig")
    if not proxy and any(p.bone.bbone_segments != 1 for p in target.pose.bones):
        raise ValueError("Segmented B-Bones are not supported")
    for chain in preset.get("ik_chains", []):
        u, l, e = [target.pose.bones[chain[k]] for k in ("upper", "lower", "end")]
        if l.parent != u or e.parent != l:
            raise ValueError("IK must be a direct upper -> lower -> end hierarchy")
        if preset.get("root") in (l.name, e.name):
            raise ValueError("IK lower/end cannot be the motion root")
        if (l.bone.head_local-u.bone.head_local).length < 1e-6 or (e.bone.head_local-l.bone.head_local).length < 1e-6:
            raise ValueError("IK chain contains a zero-length segment")
    pelvis=preset.get('postprocess',{}).get('pelvis',{})
    if pelvis:
        p=pelvis.get('bone',preset['root'])
        for foot in preset['postprocess'].get('feet',[]):
            chain=next(c for c in preset['ik_chains'] if c['end']==foot['end'])
            upper=target.pose.bones[chain['upper']]
            if p!=upper.name and p not in [b.name for b in upper.parent_recursive]:
                raise ValueError('Pelvis correction bone must be an ancestor of each foot upper bone')
    return ss, ts


def scale_ratio(source, target, preset, ss, ts):
    if preset.get("scale_ratio", "auto") != "auto":
        return float(preset["scale_ratio"])
    ratios = []
    by_t = {r["target"]: r["source"] for r in preset["bones"]}
    for t, s in by_t.items():
        tb, sb = target.data.bones[t], source.data.bones[s]
        if tb.parent and sb.parent and by_t.get(tb.parent.name) == sb.parent.name:
            a = (sb.head_local-sb.parent.head_local).length*ss
            b = (tb.head_local-tb.parent.head_local).length*ts
            if a > 1e-6 and b > 1e-6:
                ratios.append(b/a)
    if not ratios:
        raise ValueError("Auto scale requires nonzero mapped parent-child segments; set scale_ratio explicitly")
    return statistics.median(ratios)


def clone_target(target, *, keep_controls=False):
    collection = bpy.data.collections.new("MotionRemap_Output")
    bpy.context.scene.collection.children.link(collection)
    try:return _clone_target_inner(target,keep_controls,collection)
    except Exception:
        cleanup_collection(collection)
        raise


def cleanup_collection(collection):
    for obj in list(collection.objects):
        data=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if data and data.users==0:
            if isinstance(data,bpy.types.Armature):bpy.data.armatures.remove(data)
            elif isinstance(data,bpy.types.Mesh):bpy.data.meshes.remove(data)
    bpy.data.collections.remove(collection)


def _clone_target_inner(target,keep_controls,collection):
    rig = target.copy(); rig.data = target.data.copy()
    rig.name = target.name + "__Remapped"
    collection.objects.link(rig)
    if keep_controls and rig.animation_data:
        rig.animation_data.action=None;rig.animation_data.use_nla=False
        for track in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(track)
    else:rig.animation_data_clear()
    if not keep_controls:
        for constraints in [rig.constraints,*[pb.constraints for pb in rig.pose.bones]]:
            for constraint in list(constraints):constraints.remove(constraint)
        rig.data.animation_data_clear()
        for bone in rig.data.bones:bone.bbone_segments=1
    rig.data.pose_position = 'POSE'
    # Preserve object placement without retaining a parent that can animate.
    world = target.matrix_world.copy(); rig.parent = None; rig.matrix_world = world
    meshes = []
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH' or not any(m.type == 'ARMATURE' and m.object == target for m in obj.modifiers):
            continue
        if obj.animation_data or obj.parent_type == 'BONE':
            raise ValueError("Animated/bone-parented target meshes need a prepared plain export rig")
        mesh = obj.copy(); mesh.data = obj.data.copy()
        collection.objects.link(mesh)
        world = obj.matrix_world.copy()
        mesh.parent = rig if obj.parent == target else None
        mesh.matrix_world = world
        for mod in mesh.modifiers:
            if mod.type == 'ARMATURE' and mod.object == target:
                mod.object = rig
        meshes.append(mesh)
    if keep_controls:
        if rig.data.animation_data:
            rig.data.animation_data.action=None;rig.data.animation_data.use_nla=False
            for track in list(rig.data.animation_data.nla_tracks):rig.data.animation_data.nla_tracks.remove(track)
        for constraints in [rig.constraints,*[pb.constraints for pb in rig.pose.bones]]:
            for constraint in constraints:
                for prop in constraint.bl_rna.properties:
                    if prop.type=='POINTER' and not prop.is_readonly:
                        if getattr(constraint,prop.identifier,None)==target:setattr(constraint,prop.identifier,rig)
                if constraint.type=='ARMATURE':
                    for entry in constraint.targets:
                        if entry.target==target:entry.target=rig
        for datablock in (rig,rig.data):
            if datablock.animation_data:
                for curve in datablock.animation_data.drivers:
                    for variable in curve.driver.variables:
                        for entry in variable.targets:
                            if entry.id==target:entry.id=rig
                            elif entry.id==target.data:entry.id=rig.data
    return rig, meshes, collection


def solve_two_bone(a, goal, pole, length1, length2):
    """Analytic no-stretch limb solution; deterministic pole fallback at singularity."""
    direction = goal-a
    distance = direction.length
    axis = direction.normalized() if distance > 1e-9 else Vector((0, 1, 0))
    lo, hi = abs(length1-length2)+1e-6, length1+length2-1e-6
    d = max(lo, min(hi, distance))
    perpendicular = pole-axis*pole.dot(axis)
    if perpendicular.length < 1e-8:
        seed = min((Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))),
                   key=lambda v: abs(v.dot(axis)))
        perpendicular = seed-axis*seed.dot(axis)
    perpendicular.normalize()
    along = (length1*length1-length2*length2+d*d)/(2*d)
    height = math.sqrt(max(0, length1*length1-along*along))
    return a+axis*along+perpendicular*height, a+axis*d, distance > hi or distance < lo


def _pose_from_basis(pb, basis, parent_matrix=None):
    kwargs = {}
    if pb.parent:
        kwargs = {"parent_matrix": parent_matrix,
                  "parent_matrix_local": pb.parent.bone.matrix_local}
    return pb.bone.convert_local_to_pose(basis, pb.bone.matrix_local, **kwargs)


def _assign(rig, matrices):
    for pb in ordered(rig):
        kwargs = {}
        if pb.parent:
            kwargs = {"parent_matrix": matrices[pb.parent.name],
                      "parent_matrix_local": pb.parent.bone.matrix_local}
        pb.matrix_basis = pb.bone.convert_local_to_pose(matrices[pb.name], pb.bone.matrix_local,
                                                       invert=True, **kwargs)


def bake(source, target, preset, actions, *, step=1, frame_range=None, max_samples=200000):
    """Returns (working rig, copied meshes, report). On failure removes all output.

Source action/slot/NLA/pose/time are restored even if validation or baking fails.
The sampling budget is checked before any output is created.
"""
    ss, ts = validate_rigs(source, target, preset)
    if isinstance(step, bool) or not isinstance(step, int) or step < 1:
        raise ValueError("step must be a positive integer")
    if not actions:
        raise ValueError("Select at least one action")
    schedules = []
    sample_count = 0
    for action in actions:
        start, end = frame_range or action.frame_range
        if not math.isfinite(start) or not math.isfinite(end) or end < start:
            raise ValueError("Invalid frame range")
        estimate = max(1, (math.floor(end)-math.ceil(start))//step+1)+2
        sample_count += estimate*len(target.data.bones)
        if sample_count > max_samples:
            raise ValueError("Bone-frame budget exceeded before frame allocation")
        frames = list(range(math.ceil(start), math.floor(end)+1, step))
        if not frames or abs(frames[0]-start) > 1e-6:
            frames.insert(0, float(start))
        if abs(frames[-1]-end) > 1e-6:
            frames.append(float(end))
        # Fractional source keys must survive resampling. Integer-only baking
        # can miss a sharp turn between samples even for an identical skeleton.
        frames = sorted(set(frames) | {f for f in key_times(source, action, preset.get("source_slot"))
                                      if start <= f <= end})
        schedules.append((action, frames))
    if sum(len(f)*len(target.data.bones) for _, f in schedules) > max_samples:
        raise ValueError("Bone-frame budget exceeded: select fewer actions/range or increase max_samples explicitly")
    ratio = scale_ratio(source, target, preset, ss, ts)
    scene = bpy.context.scene
    old_time = scene.frame_current+scene.frame_subframe
    ad = source.animation_data
    old = (ad.action, ad.action_slot, ad.use_nla) if ad else None
    old_pose = {p.name: p.matrix_basis.copy() for p in source.pose.bones}
    source_world = source.matrix_world.copy()
    output, meshes, collection, created = None, [], None, []
    report = {"version": 1, "method": "independent rest-relative armature-space rotation transfer",
              "scale_ratio_world": ratio, "clips": [], "warnings": [], "ik_clamped_samples": 0,
              "source_preserved": False}
    try:
        # Resolve every slot before cloning so an ambiguous batch fails atomically.
        for action, _ in schedules:
            bind_action(source, action, preset.get("source_slot"))
        output, meshes, collection = clone_target(target)
        by_t = {r["target"]: r for r in preset["bones"]}
        align = q(preset.get("alignment_wxyz", [1, 0, 0, 0]))
        bridge = output.matrix_world.to_quaternion().inverted() @ align @ source_world.to_quaternion()
        local_ratio = ratio*ss/ts
        roots = preset["root"]
        for action, frames in schedules:
            bind_action(source, action, preset.get("source_slot"))
            # Avoid channels absent from this action inheriting the preceding action's pose.
            for pb in source.pose.bones:
                pb.matrix_basis = Matrix.Identity(4)
            from .sampling import refine
            frames,adaptive_report=refine(source,frames,preset.get('adaptive',{}),
                                         [r['source'] for r in preset['bones']],
                                         max_samples//len(output.data.bones))
            if len(frames)*len(output.data.bones)+sum(c['samples']*len(output.data.bones) for c in report['clips'])>max_samples:
                raise ValueError('Adaptive total bone-frame budget exceeded')
            scene.frame_set(math.floor(frames[0]),subframe=frames[0]-math.floor(frames[0]));bpy.context.view_layer.update()
            reference_world=source.matrix_world.copy()
            if preset.get('object_motion')=='root':
                ss_reference=_uniform(source)
                clip_ratio=scale_ratio(source,target,preset,ss_reference,ts)
                local_ratio=clip_ratio*ss_reference/ts
            else:ss_reference=ss
            baked = bpy.data.actions.new("Remap__"+action.name)
            created.append(baked); baked.use_fake_user = True
            bind_action(output, baked)
            previous = {}
            first_root_delta = None
            max_projection = 0.0
            for frame in frames:
                scene.frame_set(math.floor(frame), subframe=frame-math.floor(frame))
                bpy.context.view_layer.update()
                if preset.get('object_motion','reject')=='reject' and any(abs(source.matrix_world[r][c]-source_world[r][c]) > 1e-5
                       for r in range(4) for c in range(4)):
                    raise ValueError("Animated source object transform unsupported; bake object motion into a root bone first")
                object_factor=1.0
                if preset.get('object_motion')=='root':object_factor=_uniform(source)/ss_reference
                matrices = {}
                for pb in ordered(output):
                    parent_matrix = matrices[pb.parent.name] if pb.parent else None
                    row = by_t.get(pb.name)
                    basis = Matrix.Identity(4)
                    if row and row.get("scale", True):
                        basis = Matrix.Diagonal((*source.pose.bones[row["source"]].scale, 1))
                    if pb.name==roots and object_factor!=1:
                        basis=basis@Matrix.Diagonal((object_factor,object_factor,object_factor,1))
                    base = _pose_from_basis(pb, basis, parent_matrix)
                    if row:
                        sp = source.pose.bones[row["source"]]
                        reference = sp.bone.matrix_local.to_quaternion() @ q(row.get("source_reference_wxyz", [1, 0, 0, 0]))
                        delta = sp.matrix.to_quaternion() @ reference.inverted()
                        orientation = bridge @ delta @ bridge.inverted() @ pb.bone.matrix_local.to_quaternion()
                        if preset.get('object_motion')=='root':
                            target_world_q=output.matrix_world.to_quaternion()
                            world_delta=source.matrix_world.to_quaternion()@delta@reference_world.to_quaternion().inverted()
                            orientation=target_world_q.inverted()@align@world_delta@align.inverted()@target_world_q@pb.bone.matrix_local.to_quaternion()
                        orientation = orientation @ q(row.get("rotation_offset_wxyz", [1, 0, 0, 0]))
                        position = base.translation.copy()
                        if pb.name == roots:
                            displacement = bridge @ (sp.matrix.translation-sp.bone.matrix_local.translation) * local_ratio*row.get("location_multiplier", 1.0)
                            if preset.get('object_motion')=='root':
                                world_delta=source.matrix_world@sp.matrix.translation-reference_world@sp.bone.matrix_local.translation
                                displacement=output.matrix_world.to_quaternion().inverted()@align@world_delta*(clip_ratio/ts)*row.get('location_multiplier',1.0)
                            if first_root_delta is None:
                                first_root_delta = displacement.copy()
                            for axis in preset.get("in_place_axes", []):
                                displacement["XYZ".index(axis)] = first_root_delta["XYZ".index(axis)]
                            position = pb.bone.matrix_local.translation+displacement
                        elif row.get("translation", False):
                            # Additional local translation expressed through source rest axes,
                            # then target parent pose (the same space as target basis location).
                            local = pb.bone.matrix_local.to_quaternion().inverted() @ bridge @ (
                                sp.bone.matrix_local.to_quaternion() @ sp.location)
                            translated = _pose_from_basis(pb, Matrix.Translation(local*local_ratio*row.get("location_multiplier", 1.0)), parent_matrix)
                            position += translated.translation-_pose_from_basis(pb, Matrix.Identity(4), parent_matrix).translation
                        position += Vector(row.get("location_offset", [0, 0, 0]))
                        base = Matrix.LocRotScale(position, orientation, base.to_scale())
                    matrices[pb.name] = base
                # Analytic endpoint preservation. No persistent constraints or control-rig edits.
                for chain in preset.get("ik_chains", []):
                    before = {name: matrix.copy() for name, matrix in matrices.items()}
                    u, l, e = [chain[k] for k in ("upper", "lower", "end")]
                    su, sl, se = [source.pose.bones[by_t[n]["source"]] for n in (u, l, e)]
                    source_rest_vector = se.bone.head_local-su.bone.head_local
                    source_vector = se.matrix.translation-su.matrix.translation
                    target_rest_vector = output.data.bones[e].head_local-output.data.bones[u].head_local
                    goal = matrices[u].translation+target_rest_vector+bridge@(source_vector-source_rest_vector)*local_ratio
                    pole = bridge @ (sl.matrix.translation-su.matrix.translation)
                    if preset.get('object_motion')=='root':
                        difference=source.matrix_world.to_3x3()@source_vector-reference_world.to_3x3()@source_rest_vector
                        goal=matrices[u].translation+target_rest_vector+output.matrix_world.inverted().to_3x3()@(align@difference)*clip_ratio
                        pole=output.matrix_world.inverted().to_3x3()@(align@(source.matrix_world.to_3x3()@(sl.matrix.translation-su.matrix.translation)))
                    if chain.get("pole_mode", "source") == "fixed":
                        pole = Vector(chain.get("pole", [0, 0, 1]))
                    a, b, c = [matrices[n].translation.copy() for n in (u, l, e)]
                    mid, end, clamped = solve_two_bone(a, goal, pole, (b-a).length, (c-b).length)
                    report["ik_clamped_samples"] += int(clamped)
                    for name, start, old_end, new_end in ((u, a, b, mid), (l, mid, c, end)):
                        old_vec = (b-a) if name == u else (c-b)
                        new_vec = new_end-start
                        rot = old_vec.rotation_difference(new_vec) @ matrices[name].to_quaternion()
                        matrices[name] = Matrix.LocRotScale(start, rot, matrices[name].to_scale())
                    matrices[e].translation = end
                    # Keep descendants' pre-IK relative transforms (fingers/toes etc.).
                    affected = {u, l, e}
                    for pb in ordered(output):
                        if pb.name in affected or not pb.parent or pb.parent.name not in affected:
                            continue
                        matrices[pb.name] = matrices[pb.parent.name] @ before[pb.parent.name].inverted() @ before[pb.name]
                        affected.add(pb.name)
                _assign(output, matrices)
                for pb in ordered(output):
                    pb.rotation_mode = 'QUATERNION'
                    quat = pb.rotation_quaternion.copy()
                    if pb.name in previous and quat.dot(previous[pb.name]) < 0:
                        quat.negate(); pb.rotation_quaternion = quat
                    previous[pb.name] = quat
                    # Blender basis decomposition cannot represent arbitrary shear.
                    reconstructed = _pose_from_basis(pb, pb.matrix_basis,
                                                     matrices[pb.parent.name] if pb.parent else None)
                    error = max(abs(reconstructed[r][c]-matrices[pb.name][r][c])
                                for r in range(4) for c in range(4))
                    max_projection = max(max_projection, error)
                    if error > 0.005 or not all(math.isfinite(v) for row_ in pb.matrix_basis for v in row_):
                        raise ValueError(f"Unsupported shear/nonfinite pose at {pb.name}, frame {frame}: {error}")
                    for field in ('location', 'rotation_quaternion', 'scale'):
                        pb.keyframe_insert(field, frame=frame, group=pb.name)
            for layer in baked.layers:
                for strip in layer.strips:
                    bag = strip.channelbag(output.animation_data.action_slot)
                    if bag:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:
                                key.interpolation = 'LINEAR'
            from .postprocess import apply
            post_report=apply(output,source,preset,frames,sys_engine())
            for layer in baked.layers:
                for strip in layer.strips:
                    bag=strip.channelbag(output.animation_data.action_slot)
                    if bag:
                        for curve in bag.fcurves:
                            for key in curve.keyframe_points:key.interpolation='LINEAR'
            report["clips"].append({"source_action": action.name, "output_action": baked.name,
                                    "samples": len(frames), "frame_start": frames[0], "frame_end": frames[-1],
                                    "max_basis_projection_error": max_projection,
                                    'adaptive':adaptive_report,'postprocess':post_report})
        report['target_mode']=preset.get('target_mode','plain')
        if preset.get('target_mode')=='deform_proxy':
            report['warnings'].append('Target control constraints/drivers removed on copied export skeleton only; use controls adapter for an animated control rig')
            if any(b.bbone_segments>1 for b in target.data.bones):
                report['warnings'].append('Segmented B-Bones straightened in the intermediate reference proxy; preserve final curved skin with controls adapter + deform_export')
        report["unmapped_target_bones"] = sorted(set(target.data.bones.keys())-set(by_t))
        return output, meshes, report
    except Exception:
        if collection:
            cleanup_collection(collection)
        for action in created:
            bpy.data.actions.remove(action)
        raise
    finally:
        if old:
            source.animation_data.action = old[0]
            if old[0] and old[1]: source.animation_data.action_slot = old[1]
            source.animation_data.use_nla = old[2]
        elif source.animation_data:
            source.animation_data_clear()
        for name, matrix in old_pose.items(): source.pose.bones[name].matrix_basis = matrix
        scene.frame_set(math.floor(old_time), subframe=old_time-math.floor(old_time))
        bpy.context.view_layer.update()
        report["source_preserved"] = True


def sys_engine():
    import sys
    return sys.modules[__name__]
