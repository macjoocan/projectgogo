import json,math,struct
from pathlib import Path
r=Path(__file__).parent;out=r/'ecs_selected';base=Path(r'D:\99.기타\out_dkbi\bundles');reports=[]
keys={'field_101002':'0f7a9d8ebb283b65_70ac4ad581faf1b768c7695442ba659a','town_100':'3082c20a3f923203_77b276cb856605a58dce045e07f77ad1'}
for label,key in keys.items():
    trees=[json.loads(l) for l in (base/key/'typetrees.jsonl').read_text('utf-8').splitlines()]
    transforms=[x for x in trees if x['type']=='Transform'];lights=[x for x in trees if x['type']=='Light']
    layout=json.loads((out/(label+'_chunk_layout_candidates.json')).read_text('utf-8'));matches=[]
    for chunk in layout['chunks']:
        for arr in chunk.get('component_arrays',[]):
            if arr['hash']!='001f79e44e197fd0':continue
            for i,p in enumerate(arr['float_values_candidates']):
                candidates=[]
                for t in transforms:
                    d=t['data'];pos=[d['m_LocalPosition'][a] for a in 'xyz'];q=[d['m_LocalRotation'][a] for a in 'xyzw'];scale=[d['m_LocalScale'][a] for a in 'xyz']
                    pe=max(abs(p[k]-pos[k]) for k in range(3));qe=min(max(abs(p[k+4]-q[k]) for k in range(4)),max(abs(p[k+4]+q[k]) for k in range(4)));se=max(abs(p[3]-x) for x in scale)
                    if max(pe,qe,se)<1e-5:
                        go=d['m_GameObject']['m_PathID'];candidates.append({'transform':t,'lights':[x for x in lights if x['data']['m_GameObject']['m_PathID']==go],'position_max_error':pe,'quaternion_max_error_sign_invariant':qe,'scale_max_error':se,'scalar_scale_xyz_bit_exact':all(struct.pack('<f',p[3])==struct.pack('<f',v) for v in scale),'comparison_provenance':'inferredApprox' if se else 'numeric_match'})
                matches.append({'chunk_index':chunk['chunk_index'],'array_file_offset':arr['file_offset'],'instance_file_offset':arr['file_offset']+i*arr['instance_stride'],'native_local_transform_candidate':p,'unique_companion_match':len(candidates)==1,'companion_candidates':candidates})
    report={'provenance':'inferred','raw_source_provenance':'verified','comparison_mode':'Unique companion matching with tolerance 1e-5; not bit-exact XYZ-scale equality. Per-match errors and strict scalar-scale checks preserved.','label':label,'companion_source':str(base/key/'typetrees.jsonl'),'matches':matches,'limitations':['Saved TRS interpretation corroborated numerically for these four light entities only.','Scalar scale equals native X, but Y/Z can differ by up to 2.98e-7; do not claim all XYZ bit-exact.','This does not establish terrain renderer/component mapping or full runtime Types array.','Offset construction uses reference package rules; full original reader body not recovered.']}
    (out/(label+'_light_transform_crosscheck.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');reports.append({'label':label,'matches':len(matches),'unique_matches':sum(x['unique_companion_match'] for x in matches)})
print(json.dumps(reports))
