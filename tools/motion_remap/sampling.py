"""Bounded midpoint refinement of the evaluated source; not a continuous proof."""
import math

import bpy


def refine(source,frames,config,names,limit):
    if not config:return frames,{'enabled':False}
    cache={};max_depth=config.get('max_depth',4);unresolved=[]
    tolerances=(config.get('position_tolerance',.002),math.radians(config.get('rotation_tolerance_degrees',.5)),config.get('scale_tolerance',.002))
    def sample(frame):
        if frame not in cache:
            if len(cache)>=limit:raise ValueError('Adaptive sample budget exceeded')
            bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
            # World matrices include animated object motion and source constraints.
            cache[frame]=[(source.matrix_world@source.pose.bones[n].matrix).decompose() for n in names]
        return cache[frame]
    result=set(frames)
    def visit(a,b,depth):
        if b-a<1e-5:return
        mid=(a+b)/2;left,right,actual=sample(a),sample(b),sample(mid)
        errors=[0.,0.,0.]
        for (pa,qa,sa),(pb,qb,sb),(pm,qm,sm) in zip(left,right,actual):
            errors[0]=max(errors[0],(pa.lerp(pb,.5)-pm).length)
            predicted=qa.slerp(qb,.5)
            difference=predicted.inverted()@qm
            errors[1]=max(errors[1],2*math.atan2(math.sqrt(difference.x**2+difference.y**2+difference.z**2),abs(difference.w)))
            errors[2]=max(errors[2],(sa.lerp(sb,.5)-sm).length)
        if any(e>t for e,t in zip(errors,tolerances)):
            if depth>=max_depth:unresolved.append({'start':a,'end':b,'errors':errors})
            else:
                result.add(mid);visit(a,mid,depth+1);visit(mid,b,depth+1)
    for a,b in zip(frames,frames[1:]):visit(a,b,0)
    if unresolved and config.get('strict',False):raise ValueError(f'Adaptive tolerance unresolved in {len(unresolved)} intervals')
    return sorted(result),{'enabled':True,'input_samples':len(frames),'output_samples':len(result),
                           'evaluated_samples':len(cache),'unresolved_intervals':unresolved,
                           'method':'evaluated source world-space midpoint checks; not continuous-time certification'}
