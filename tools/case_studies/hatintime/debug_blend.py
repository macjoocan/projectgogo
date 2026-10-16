import bpy
bpy.ops.wm.open_mainfile(filepath=__file__.replace('debug_blend.py','preview/HatKid_five_motions.blend'))
r=bpy.data.objects['HatKidBody_Rig'];a=bpy.data.actions['Walk__Walk'];r.animation_data.use_nla=False;r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
print('SLOTS',[(s.identifier,s.name_display,s.handle) for s in a.slots])
bag=a.layers[0].strips[0].channelbag(a.slots[0]);print('CURVES',len(bag.fcurves),[(x.data_path,x.array_index,x.evaluate(1),x.is_valid) for x in list(bag.fcurves)[:7]])
for n in ['Root','bip_spine01','bip_spine02']:
 b=r.pose.bones[n];print('BONE',n,'loc',list(b.location),'rot',list(b.rotation_quaternion),'basis',list(b.matrix_basis.translation),'world',list(b.matrix.translation),'rest',list(b.bone.matrix_local.translation))

exec(open(__file__.replace('debug_blend.py','convert_hatkid.py')).read().split("bpy.ops.object.select_all")[0]);js,_=meshread(next(sources.rglob('HatKidBody.md5mesh')));print('EXPECTED_REST',list(js[0][2]));print('ACTUAL_REST',list(r.data.bones[0].matrix_local))
