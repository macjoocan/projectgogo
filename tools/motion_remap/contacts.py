"""Pure Python contact segmentation and bounded trajectory filtering.

Thresholds are user retarget settings in world units/seconds, not game values.
"""
import math


def detect_contacts(times, points, *, floor, height, speed, min_duration=0.08,
                    max_gap=0.04):
    if len(times) != len(points) or not times:
        raise ValueError('Contact samples must be nonempty and paired')
    if any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Contact times must be finite and strictly increasing')
    if any(len(p) != 3 or any(not math.isfinite(v) for v in p) for p in points):
        raise ValueError('Contact positions must be finite triples')
    flags = []
    for i, p in enumerate(points):
        velocities=[]
        for a,b in ((i-1,i),(i,i+1)):
            if 0 <= a < b < len(points):
                velocities.append(math.dist(points[a],points[b])/(times[b]-times[a]))
        # Both sides must be slow: do not mark a landing/takeoff impulse as planted.
        flags.append(p[2] <= floor+height and max(velocities,default=0) <= speed)
    segments=[];i=0
    while i<len(flags):
        if not flags[i]:i+=1;continue
        start=i
        while i+1<len(flags) and flags[i+1]:i+=1
        segments.append([start,i]);i+=1
    merged=[]
    for a,b in segments:
        if merged and times[a]-times[merged[-1][1]] <= max_gap:
            merged[-1][1]=b
        else:merged.append([a,b])
    return [[a,b] for a,b in merged if times[b]-times[a] >= min_duration]


def smooth_bounded(values, strength=1.0, max_deviation=math.inf, fixed=None):
    """Solve sum(x-y)^2 + strength*sum(diff(x)^2), then bound displacement.

Exact Dirichlet samples split the tridiagonal solve; no dependency on scipy/numpy.
The first/last samples are fixed by default to preserve clip boundaries.
"""
    if not values:return []
    if strength < 0 or not math.isfinite(strength) or max_deviation < 0:
        raise ValueError('Invalid smoothing settings')
    n=len(values);fixed=dict(fixed or {})
    fixed.setdefault(0,values[0]);fixed.setdefault(n-1,values[-1])
    lower=[-strength]*n;upper=[-strength]*n
    diag=[1+strength*((i>0)+(i<n-1)) for i in range(n)]
    rhs=list(values)
    for i,value in fixed.items():
        if not 0<=i<n:raise ValueError('Invalid fixed sample index')
        if i>0:rhs[i-1]-=upper[i-1]*value;upper[i-1]=0
        if i+1<n:rhs[i+1]-=lower[i+1]*value;lower[i+1]=0
        lower[i]=upper[i]=0;diag[i]=1;rhs[i]=value
    for i in range(1,n):
        factor=lower[i]/diag[i-1];diag[i]-=factor*upper[i-1];rhs[i]-=factor*rhs[i-1]
    result=[0.0]*n;result[-1]=rhs[-1]/diag[-1]
    for i in range(n-2,-1,-1):result[i]=(rhs[i]-upper[i]*result[i+1])/diag[i]
    return [fixed[i] if i in fixed else max(y-max_deviation,min(y+max_deviation,x))
            for i,(x,y) in enumerate(zip(result,values))]


def contact_weight(frame,start,end,blend_frames):
    if frame<start or frame>end:return 0.0
    if blend_frames<=0:return 1.0
    t=min(1.0,(frame-start)/blend_frames,(end-frame)/blend_frames)
    return max(0.0,t*t*(3-2*t))
