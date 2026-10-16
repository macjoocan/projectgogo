"""Dependency-free mapping/preset rules for the independent motion remapper.

No Auto-Rig Pro implementation or bundled presets are used.
"""
import json
import math
import re
from pathlib import Path

VERSION = 1


def canonical(name):
    # Only namespace and punctuation normalization. No fuzzy left/right guesses.
    return re.sub(r"[^a-z0-9]", "", name.rsplit(":", 1)[-1].casefold())


def suggest_mapping(source_names, target_names):
    source_names, target_names = list(source_names), list(target_names)
    groups = {}
    for name in target_names:
        groups.setdefault(canonical(name), []).append(name)
    source_groups = {}
    for name in source_names:
        source_groups.setdefault(canonical(name), []).append(name)
    rows, unresolved, used = [], [], set()
    for name in source_names:
        candidates = ([name] if name in target_names else
                      groups.get(canonical(name), []))
        if (len(candidates) != 1 or candidates[0] in used or
                (name not in target_names and len(source_groups[canonical(name)]) != 1)):
            unresolved.append({"source": name, "candidates": candidates})
            continue
        used.add(candidates[0])
        rows.append({"source": name, "target": candidates[0]})
    return {"version": VERSION, "approved": False, "root": None,
            "scale_ratio": "auto", "alignment_wxyz": [1, 0, 0, 0],
            "in_place_axes": [], "bones": rows, "ik_chains": [],
            "unresolved": unresolved}


def vector(value, count, label):
    if (not isinstance(value, (list, tuple)) or len(value) != count or
            any(isinstance(x, bool) or not isinstance(x, (int, float)) or
                not math.isfinite(x) for x in value)):
        raise ValueError(f"{label} must contain {count} finite numbers")
    if count == 4 and sum(x*x for x in value) < 1e-12:
        raise ValueError(f"{label} cannot be a zero quaternion")
    return value


def validate(preset, source_names, target_names):
    if preset.get("version") != VERSION:
        raise ValueError("Unsupported preset version")
    if preset.get("approved") is not True:
        raise ValueError("Review the mapping and set approved=true before baking")
    sources, targets = set(source_names), set(target_names)
    rows = preset.get("bones", [])
    if not rows:
        raise ValueError("Empty bone mapping")
    seen_s, seen_t = set(), set()
    for row in rows:
        s, t = row["source"], row["target"]
        if s not in sources or t not in targets:
            raise ValueError(f"Unknown mapped bone: {s} -> {t}")
        if s in seen_s or t in seen_t:
            raise ValueError("Bone mapping must be one-to-one")
        seen_s.add(s); seen_t.add(t)
        for key in ("source_reference_wxyz", "rotation_offset_wxyz"):
            vector(row.get(key, [1, 0, 0, 0]), 4, key)
        vector(row.get("location_offset", [0, 0, 0]), 3, "location_offset")
        factor = row.get("location_multiplier", 1.0)
        if isinstance(factor, bool) or not isinstance(factor, (int, float)) or not math.isfinite(factor):
            raise ValueError("Invalid location multiplier")
        for key in ("translation", "scale"):
            if key in row and not isinstance(row[key], bool):
                raise ValueError(f"{key} must be boolean")
    if preset.get("root") not in seen_t:
        raise ValueError("root must be a mapped target bone name")
    axes = preset.get("in_place_axes", [])
    if not isinstance(axes, list) or any(x not in ("X", "Y", "Z") for x in axes):
        raise ValueError("in_place_axes must be a list of X/Y/Z")
    vector(preset.get("alignment_wxyz", [1, 0, 0, 0]), 4, "alignment_wxyz")
    ratio = preset.get("scale_ratio", "auto")
    if ratio != "auto" and (isinstance(ratio, bool) or not isinstance(ratio, (float, int)) or
                            not math.isfinite(ratio) or ratio <= 0):
        raise ValueError("scale_ratio must be auto or a positive finite number")
    ik_bones = set()
    for chain in preset.get("ik_chains", []):
        if chain.get("pole_mode", "source") not in ("source", "fixed"):
            raise ValueError("IK pole_mode must be source or fixed")
        for key in ("upper", "lower", "end"):
            if chain.get(key) not in seen_t:
                raise ValueError("IK bones must be mapped target bones")
        if len({chain[k] for k in ("upper", "lower", "end")}) != 3:
            raise ValueError("IK requires three distinct bones")
        current = {chain[k] for k in ("upper", "lower", "end")}
        if ik_bones & current:
            raise ValueError("Overlapping IK chains are not supported")
        ik_bones |= current
        vector(chain.get("pole", [0, 0, 1]), 3, "pole")
        if sum(x*x for x in chain.get("pole", [0, 0, 1])) < 1e-12:
            raise ValueError("IK pole cannot be zero")
    validate_advanced(preset,seen_t)
    return preset


def positive(value,label,zero=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<(0 if zero else 1e-12):
        raise ValueError(f'{label} must be finite and {"nonnegative" if zero else "positive"}')


def validate_advanced(preset,mapped):
    if preset.get('target_mode','plain') not in ('plain','deform_proxy'):
        raise ValueError('target_mode must be plain or deform_proxy')
    if preset.get('object_motion','reject') not in ('reject','root'):
        raise ValueError('object_motion must be reject or root')
    config=preset.get('postprocess',{})
    positive(config.get('max_contact_error',.005),'max_contact_error',True)
    ends={c['end'] for c in preset.get('ik_chains',[])}
    seen=set()
    for foot in config.get('feet',[]):
        if foot.get('end') not in ends or foot['end'] in seen:raise ValueError('Each foot needs a unique mapped IK end')
        seen.add(foot['end'])
        positive(foot.get('sole_offset',0),'sole_offset',True)
        vector(foot.get('up_axis',[0,0,1]),3,'up_axis')
        if sum(v*v for v in foot.get('up_axis',[0,0,1]))<1e-12:raise ValueError('up_axis cannot be zero')
        contact=foot.get('contact',{})
        if contact.get('mode','auto') not in ('auto','manual'):raise ValueError('Unknown contact mode')
        for k,default in (('height',.05),('speed',.1),('min_duration',.08),('max_gap',.04),('blend_frames',2)):
            positive(contact.get(k,default),k,True)
        if 'floor' in contact:vector([0,0,contact['floor']],3,'floor')
        if contact.get('mode')=='manual':
            previous=-math.inf
            for interval in contact.get('intervals',[]):
                vector(interval,2,'contact interval')
                if interval[0]>interval[1] or interval[0]<=previous:raise ValueError('Contact intervals must be ordered and disjoint')
                previous=interval[1]
    ground=config.get('ground',{})
    vector([0,0,ground.get('height',0)],3,'ground height')
    positive(ground.get('ray_distance',100),'ray_distance')
    tilt=ground.get('max_tilt_degrees',45);positive(tilt,'max tilt',True)
    if tilt>180:raise ValueError('max tilt must be <=180')
    if not isinstance(ground.get('objects',[]),list) or any(not isinstance(n,str) or not n for n in ground.get('objects',[])):
        raise ValueError('ground objects must be names')
    pelvis=config.get('pelvis',{})
    if pelvis:
        if pelvis.get('bone',preset['root']) not in mapped:raise ValueError('pelvis bone must be mapped')
        positive(pelvis.get('max_shift',.3),'max_shift',True)
        positive(pelvis.get('smoothness',1),'smoothness',True)
        iterations=pelvis.get('iterations',12)
        if not isinstance(iterations,int) or isinstance(iterations,bool) or not 1<=iterations<=100:raise ValueError('pelvis iterations must be 1..100')
    for option in ('pelvis','trajectory'):
        cfg=config.get(option,{})
        if any(a not in ('X','Y','Z') for a in cfg.get('axes',[])):raise ValueError('Invalid correction axes')
    if config.get('trajectory'):
        positive(config['trajectory'].get('smoothness',1),'smoothness',True)
        positive(config['trajectory'].get('max_deviation',.1),'max_deviation',True)
    if config.get('loop'):positive(config['loop'].get('blend_frames',5),'loop blend_frames')
    adaptive=preset.get('adaptive',{})
    if adaptive:
        for key,default in (('position_tolerance',.002),('rotation_tolerance_degrees',.5),('scale_tolerance',.002)):
            positive(adaptive.get(key,default),key)
        depth=adaptive.get('max_depth',4)
        if not isinstance(depth,int) or isinstance(depth,bool) or not 0<=depth<=10:raise ValueError('max_depth must be 0..10')


def load(path):
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+"\n",
                          encoding="utf-8")
