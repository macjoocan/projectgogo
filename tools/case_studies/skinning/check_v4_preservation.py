import bpy,json,hashlib,struct
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'v4_followup'
def read(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['OriginalRetry_Body70'];m=bpy.data.objects['OriginalRetry_Surface']
    rest=[(b.name,b.parent.name if b.parent else None,[list(row) for row in b.matrix_local]) for b in r.data.bones]
    curves={};counts=[0,0]
    for a in bpy.data.actions:
        if not a.name.startswith('OriginalRetryNative__'):continue
        h=hashlib.sha256()
        for layer in a.layers:
            for strip in layer.strips:
                for slot in a.slots:
                    bag=strip.channelbag(slot)
                    if not bag:continue
                    for f in bag.fcurves:
                        counts[0]+=1;counts[1]+=len(f.keyframe_points);h.update(f.data_path.encode());h.update(struct.pack('<I',f.array_index))
                        for k in f.keyframe_points:h.update(struct.pack('<6f',*k.co,*k.handle_left,*k.handle_right));h.update(k.interpolation.encode())
        curves[a.name]=h.hexdigest()
    p=np.array([v.co[:] for v in m.data.vertices]);polys=[list(f.vertices) for f in m.data.polygons]
    uv=np.array([x.uv[:] for x in m.data.uv_layers.active.data]);names=list(m.vertex_groups.keys());weights=[[(names[g.group],g.weight) for g in v.groups] for v in m.data.vertices]
    return rest,curves,counts,p,polys,uv,weights
a=read(ROOT/'input/source/hand-cage-v4/candidate.blend');b=read(ROOT/'harmonic-candidate.blend')
original=np.load(ROOT.parent/'baseline_positions.npy');mask=(np.abs(original[:,0])>23)&(original[:,2]>36)&(original[:,2]<48)
outside=all(dict(a[6][i])==dict(b[6][i]) for i in np.flatnonzero(~mask))
intake=json.loads((ROOT/'intake.json').read_text());source=[]
for item in intake:source.append({'path':item['source'],'unchanged':hashlib.sha256(Path(item['source']).read_bytes()).hexdigest()==item['sha256']})
result={'rest_hierarchy_exact':a[0]==b[0],'native_action_hashes_exact':a[1]==b[1],'native_actions':len(b[1]),'curve_count':b[2][0],'key_count':b[2][1],
        'geometry_exact':np.array_equal(a[3],b[3]),'triangles_exact':a[4]==b[4],'uv_exact':np.array_equal(a[5],b[5]),'outside_hand_weights_exact_after_reload':outside,'max_weights':max(len(row) for row in b[6]),'source_files':source}
result['preservation_pass']=all(result[k] for k in ['rest_hierarchy_exact','native_action_hashes_exact','geometry_exact','triangles_exact','uv_exact','outside_hand_weights_exact_after_reload']) and len(b[1])==5 and all(x['unchanged'] for x in source)
(ROOT/'preservation.json').write_bytes(json.dumps(result,indent=2).encode());print(json.dumps(result))
