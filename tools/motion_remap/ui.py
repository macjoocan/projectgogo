"""Small UI around explicit, editable JSON mapping presets."""
import fnmatch
from pathlib import Path

import bpy
from bpy.props import IntProperty, PointerProperty, StringProperty

from . import core, engine


def armature(_, obj):
    return obj.type == 'ARMATURE'


class MR_Settings(bpy.types.PropertyGroup):
    source: PointerProperty(name="Source", type=bpy.types.Object, poll=armature)
    target: PointerProperty(name="Target", type=bpy.types.Object, poll=armature)
    preset_path: StringProperty(name="Preset JSON", subtype='FILE_PATH')
    action_pattern: StringProperty(name="Actions (glob)", default="*")
    step: IntProperty(name="Frame step", default=1, min=1, max=100)
    output_rig: PointerProperty(name="Last output",type=bpy.types.Object,poll=armature)
    control_profile: StringProperty(name="Control profile JSON",subtype='FILE_PATH')
    export_directory: StringProperty(name="New output folder",subtype='DIR_PATH')
    deform_source: PointerProperty(name='Evaluated skin source',type=bpy.types.Object,poll=armature)


def settings(context):
    st = context.scene.motion_remap
    if not st.source or not st.target:
        raise ValueError("Select source and target armatures")
    if not st.preset_path:
        raise ValueError("Set a JSON preset path")
    return st, Path(bpy.path.abspath(st.preset_path))


class MR_OT_Suggest(bpy.types.Operator):
    bl_idname = 'motion_remap.suggest'
    bl_label = 'Create mapping draft (no overwrite)'

    def execute(self, context):
        try:
            st, path = settings(context)
            if path.exists(): raise ValueError("File exists: choose a new draft path")
            preset = core.suggest_mapping(st.source.data.bones.keys(), st.target.data.bones.keys())
            path.parent.mkdir(parents=True, exist_ok=True)
            core.save(path, preset)
            bpy.data.texts.load(str(path))
            self.report({'INFO'}, "Draft created. Set root; review rows; set approved=true and save JSON.")
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc)); return {'CANCELLED'}


class MR_OT_Reference(bpy.types.Operator):
    bl_idname = 'motion_remap.reference'
    bl_label = 'Capture source correction pose'

    def execute(self, context):
        try:
            st, path = settings(context)
            preset = core.load(path)
            snapshot = engine.capture_reference(st.source)
            for row in preset['bones']:
                row['source_reference_wxyz'] = snapshot[row['source']]
            preset['approved'] = False
            # Keep the reviewed original preset; a new file must be reviewed again.
            out = path.with_name(path.stem+"_reference.json")
            if out.exists(): raise ValueError("Reference file exists; rename it before recapturing")
            core.save(out, preset); st.preset_path = str(out)
            self.report({'INFO'}, "Correction snapshot saved; review and approve the new JSON")
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc)); return {'CANCELLED'}


class MR_OT_Bake(bpy.types.Operator):
    bl_idname = 'motion_remap.bake'
    bl_label = 'Bake to copied target'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            st, path = settings(context)
            preset = core.load(path)
            actions = [a for a in bpy.data.actions if fnmatch.fnmatchcase(a.name, st.action_pattern)
                       and not a.name.startswith('Remap__')]
            rig, meshes, report = engine.bake(st.source, st.target, preset, actions, step=st.step)
            text = bpy.data.texts.new("MotionRemap_Report.json")
            import json
            text.write(json.dumps(report, ensure_ascii=False, indent=2))
            rig['motion_remap_report']=json.dumps(report,ensure_ascii=False)
            st.output_rig=rig
            self.report({'INFO'}, f"Baked {len(report['clips'])} actions to {rig.name}; inspect report")
            return {'FINISHED'}
        except Exception as exc:
            self.report({'ERROR'}, str(exc)); return {'CANCELLED'}


class MR_OT_ControlDraft(bpy.types.Operator):
    bl_idname='motion_remap.control_draft'
    bl_label='Create control profile draft'

    def execute(self,context):
        try:
            from .controls import draft_profile
            st=context.scene.motion_remap
            if not st.output_rig or not st.target or not st.control_profile:raise ValueError('Set output rig/target/control profile path')
            path=Path(bpy.path.abspath(st.control_profile))
            if path.exists():raise ValueError('Profile file exists')
            path.parent.mkdir(parents=True,exist_ok=True)
            core.save(path,draft_profile(st.output_rig,st.target))
            self.report({'INFO'},'Review FK/IK/pole/switches and verify_bones, then approve JSON')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class MR_OT_Controls(bpy.types.Operator):
    bl_idname='motion_remap.controls'
    bl_label='Bake copied control rig'
    bl_options={'REGISTER','UNDO'}

    def execute(self,context):
        try:
            import json
            from .controls import bake_controls
            st=context.scene.motion_remap
            if not st.output_rig or not st.target or not st.control_profile:raise ValueError('Set output rig/target/control profile path')
            report=json.loads(st.output_rig['motion_remap_report'])
            rig,_,control_report=bake_controls(st.output_rig,st.target,report,core.load(bpy.path.abspath(st.control_profile)))
            rig['motion_remap_report']=json.dumps(control_report,ensure_ascii=False)
            text=bpy.data.texts.new('MotionRemap_ControlReport.json');text.write(json.dumps(control_report,indent=2))
            self.report({'INFO'},'Control copy baked and deform verification checked; export plain reference rig for GLB')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class MR_OT_Export(bpy.types.Operator):
    bl_idname='motion_remap.export'
    bl_label='Export last plain output (Blend/GLB)'

    def execute(self,context):
        try:
            import json
            from .batch import export_output
            st=context.scene.motion_remap;rig=st.output_rig
            if not rig or not st.export_directory:raise ValueError('Set output rig and a new export directory')
            meshes=[o for o in context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers)]
            export_output(rig,meshes,json.loads(rig['motion_remap_report']),bpy.path.abspath(st.export_directory))
            self.report({'INFO'},'Saved Blend/GLB and export report')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class MR_OT_Deform(bpy.types.Operator):
    bl_idname='motion_remap.deform'
    bl_label='Bake evaluated skin / B-Bones'
    bl_options={'REGISTER','UNDO'}

    def execute(self,context):
        try:
            import json
            from .deform_export import bake_deform_export
            st=context.scene.motion_remap;source=st.deform_source or st.source
            if not source:raise ValueError('Set evaluated skin source')
            actions=[a for a in bpy.data.actions if fnmatch.fnmatchcase(a.name,st.action_pattern)]
            rig,_,report=bake_deform_export(source,actions,step=st.step)
            rig['motion_remap_report']=json.dumps(report);st.output_rig=rig
            self.report({'INFO'},'Ordinary skin proxy baked; per-sample evaluated vertex error checked')
            return {'FINISHED'}
        except Exception as exc:self.report({'ERROR'},str(exc));return {'CANCELLED'}


class MR_PT_Panel(bpy.types.Panel):
    bl_label = 'Levelscope Motion Remap'
    bl_idname = 'MR_PT_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Motion Remap'

    def draw(self, context):
        layout = self.layout; st = context.scene.motion_remap
        for field in ('source', 'target', 'preset_path', 'action_pattern', 'step'):
            layout.prop(st, field)
        layout.operator('motion_remap.suggest')
        layout.label(text='Review JSON: root / approved / IK chains')
        layout.operator('motion_remap.reference')
        layout.operator('motion_remap.bake')
        layout.label(text='Contact / terrain / pelvis / adaptive: preset JSON')
        layout.prop(st,'output_rig');layout.prop(st,'control_profile')
        layout.operator('motion_remap.control_draft');layout.operator('motion_remap.controls')
        layout.prop(st,'deform_source');layout.operator('motion_remap.deform')
        layout.prop(st,'export_directory');layout.operator('motion_remap.export')
        layout.label(text='Inputs preserved; output is a separate rig')


CLASSES = (MR_Settings, MR_OT_Suggest, MR_OT_Reference, MR_OT_Bake,MR_OT_ControlDraft,MR_OT_Controls,MR_OT_Export,MR_OT_Deform, MR_PT_Panel)


def register():
    for cls in CLASSES: bpy.utils.register_class(cls)
    bpy.types.Scene.motion_remap = PointerProperty(type=MR_Settings)


def unregister():
    del bpy.types.Scene.motion_remap
    for cls in reversed(CLASSES): bpy.utils.unregister_class(cls)
