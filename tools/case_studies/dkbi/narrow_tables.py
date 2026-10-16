import sys,struct,json,hashlib,csv,base64
from pathlib import Path
sys.path.insert(0,r'D:\99.기타\bluearchive_ldplayer14')
from table_verify import Flat
root=Path(__file__).parent; tables=root/'tables';tables.mkdir(exist_ok=True)
names=['characterconfig','combatconfig','skillconfig','skillpc','skilldamage','skillanimationclip','skillmonster','actorpc','itemsequip','actormonster','zone','zonedistrict','zoneconfig']
summary=[]
for name in names:
    source=Path(r'D:\99.기타\out_dkbi\tables\raw')/('fbdata'+name+'.bytes');b=source.read_bytes();f=Flat(b);rows=[];strings=[]
    for number,p in enumerate(f.rows()):
        fields=f.fields(p);vt=p-f.read(p,'<i');size=f.read(vt+2,'<H');present=sorted(x for x in fields if x)
        slots=[]
        for i,x in enumerate(fields):
            if x is None:slots.append(dict(slot=i,present=False));continue
            end=next((y for y in present if y>x),p+size)
            cell=dict(slot=i,present=True,source_offset=x,raw_span_hex=b[x:end].hex(),provenance='verified',semantic_name=None,type=None,unit=None)
            if end-x>=4:
                cell['inferred_numeric_views']=dict(uint32=struct.unpack_from('<I',b,x)[0],int32=struct.unpack_from('<i',b,x)[0])
                a=x+struct.unpack_from('<I',b,x)[0]
                if x<a<=len(b)-4:
                    n=struct.unpack_from('<I',b,a)[0]
                    if 0<n<=2048 and a+4+n<len(b) and b[a+4+n]==0:
                        try:
                            s=b[a+4:a+4+n].decode('utf-8')
                            if all(c.isprintable() or c in '\r\n\t' for c in s):
                                cell['inferred_string_view']=dict(value=s,target_offset=a,provenance='inferred');strings.append(dict(row=number,slot=i,value=s,source_offset=x,target_offset=a))
                        except UnicodeDecodeError:pass
            slots.append(cell)
        rows.append(dict(row_ordinal=number,table_offset=p,slots=slots))
    output=dict(source=str(source),sha256=hashlib.sha256(b).hexdigest(),provenance='verified',rows=rows,limitations='Only structural slots verified. Numeric/string views are interpretations, not field types. No slot-to-property mapping or real ID join verified.')
    (tables/(name+'_structural_rows.json')).write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    summary.append(dict(name=name,rows=len(rows),strings=strings))
(tables/'narrow_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
catalog=json.loads(Path(r'D:\99.기타\out_dkbi_probe\addressables_catalog.json').read_text('utf-8'));ids=catalog['m_InternalIds']
paths=[x for x in ids if '/actions/' in x and any(k in x.lower() for k in ['basic','normal','default','pc_','player','attack'])]
(root/'action_path_candidates.json').write_text(json.dumps(dict(provenance='verified',source='out_dkbi_probe/addressables_catalog.json',paths=paths,limitations='Logical path only. ActorID and actual runtime use unknown.'),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(tables=[dict(name=x['name'],rows=x['rows'],strings=len(x['strings'])) for x in summary],action_candidates=len(paths),first_paths=paths[:6]),ensure_ascii=False))
