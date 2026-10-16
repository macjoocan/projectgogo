import csv, json, struct, hashlib, re
from pathlib import Path
root=Path(__file__).parent
out=root/'metadata'
header=json.loads((out/'metadata_header.json').read_text('utf-8'))
data=Path(r'D:\99.기타\out_dkbi\source\dokkaebi_Data\il2cpp_data\Metadata\global-metadata.dat').read_bytes()
targets={'PlayerInputDirectionComponent','FxPlayerInputGroundPicked','PlayerSkillInputComponent','PlayerTargetingComponent','PlayerTargetingFilterComponent','ActorTargetingComponent','ActorPreCastSkill','RConfigAutoPlay','RAutoPlayProvider','AttackPriorityPreset','AttackPriorityMoveClick','AutoPlayMessage','SemiAutoPlayMessage','NavigationMeshBuffer','NavigationMeshSurface'}
selected=[]; fb=[]; errors=[]; counts=dict(types=0,fields=0,methods=0,properties=0)
with (out/'type_index.csv').open('w',newline='',encoding='utf-8-sig') as dest:
    w=csv.writer(dest);w.writerow(['index','image','namespace','name','metadata_offset','byval_type_index','is_enum'])
    for line in (out/'metadata_types.jsonl').open(encoding='utf-8'):
        t=json.loads(line);counts['types']+=1
        w.writerow([t['index'],t['image'],t['ns'],t['name'],t['metadata_offset'],t['definition']['byvalTypeIndex'],t['is_enum']])
        for section,key in [('fields','fields'),('methods','methods'),('properties','properties')]:
            counts[section]+=len(t[key])
            for rec in t[key]:
                if not rec['name']: errors.append(['empty_name',t['index'],section,rec['index']])
                if section!='properties' and struct.unpack_from('<I',data,rec['metadata_offset'])[0]!=rec['definition']['nameIndex']: errors.append(['offset_name_mismatch',t['index'],section,rec['index']])
        if t['name'] in targets or re.search('AutoPlay|Targeting|Player.*(Move|Input)|Actor.*(Cast|Attack)',t['name']): selected.append(t)
        if t['ns']=='FlatBufferData': fb.append(t)
def write(name,v): (out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
write('requested_system_types.json',selected);write('flatbuffer_generated_types.json',fb)
write('schema_validation.json',dict(provenance='verified',source_sha256=hashlib.sha256(data).hexdigest(),counts=counts,errors=errors,requested_found=sorted(targets.intersection(t['name'] for t in selected)),requested_missing=sorted(targets.difference(t['name'] for t in selected)),flatbuffer_types=len(fb),limitations=['typeIndex is not a resolved IL2CPP type name','metadata_offset is a file offset, not instance field offset or method RVA','method bodies and FB slot numbers not decoded']))
binary=Path(r'D:\99.기타\out_dkbi\source\GameAssembly.dll').read_bytes()
pe=struct.unpack_from('<I',binary,0x3c)[0];n=struct.unpack_from('<H',binary,pe+6)[0];opt=pe+24;osize=struct.unpack_from('<H',binary,pe+20)[0];base=struct.unpack_from('<Q',binary,opt+24)[0]
sections=[]
for i in range(n):
    p=opt+osize+i*40;vs,rva,sz,raw=struct.unpack_from('<IIII',binary,p+8);sections.append(dict(name=binary[p:p+8].rstrip(b'\0').decode(errors='replace'),virtual_size=vs,rva=rva,size=sz,raw_offset=raw,flags=hex(struct.unpack_from('<I',binary,p+36)[0])))
hits=[];needle=struct.pack('<Q',header['typeDefinitionsCount']);start=0
while True:
    p=binary.find(needle,start)
    if p<0:break
    if p%8==0:
        hits.append(dict(file_offset=p,qwords=[hex(x) for x in struct.unpack_from('<'+ 'Q'*min(8,(len(binary)-p)//8),binary,p)]))
    start=p+1
write('pe_registration_candidates.json',dict(provenance='inferred',image_base=hex(base),sections=sections,type_count_hits=hits,warning='Candidates only; no registration address verified.'))
print(json.dumps(dict(counts=counts,errors=len(errors),selected=len(selected),fb_types=len(fb),pe_sections=sections,hits=len(hits)),ensure_ascii=False))
