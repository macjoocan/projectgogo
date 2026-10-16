import bpy,json
from pathlib import Path
from mathutils import Matrix
p=Path(__file__).resolve().parent
for folder,name in [('preview','HatKid_five_motions'),('preview_catlady','CatLady_scale_motion')]:
 f=p/folder/(name+'.blend');bpy.ops.wm.open_mainfile(filepath=str(f))
 for ob in bpy.context.scene.objects:
  if ob.type!='ARMATURE':continue
  ob.data.pose_position='POSE';ob.animation_data.use_nla=False;ob.animation_data.action=None
  for b in ob.pose.bones:b.matrix_basis=Matrix.Identity(4)
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
 print('REST_DEFAULT_SAVED',name)
