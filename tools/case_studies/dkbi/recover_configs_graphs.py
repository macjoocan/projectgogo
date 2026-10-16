import sys,struct,json,hashlib,csv
from pathlib import Path
sys.path.insert(0,r'D:\99.기타\bluearchive_ldplayer14')
from table_verify import Flat
root=Path(__file__).parent
records=[]
for name in ['characterconfig','combatconfig','skillconfig']:
    source=Path(r'D:\99.기타\out_dkbi\tables\raw')/('fbdata'+name+'.bytes');b=source.read_bytes();f=Flat(b)
    for ordinal,p in enumerate(f.rows()):
        fs=f.fields(p);assert len(fs)==3
        key=f.string(fs[1]);v=fs[2]+f.read(fs[2],'<I');n=f.read(v,'<I');assert n<1000
        vals=[]
        for i in range(n):
            x=v+4+i*4;vals.append(dict(value=f.string(x),pointer_offset=x,string_offset=x+f.read(x,'<I')))
        records.append(dict(provenance='verified',source=str(source),source_sha256=hashlib.sha256(b).hexdigest(),row_ordinal=ordinal,row_offset=p,key_string=key,key_pointer_offset=fs[1],slot0_uint32_view=f.read(fs[0],'<I') if fs[0] else None,values=vals,semantic_provenance='inferred',units='unknown',runtime_use='unknown'))
(root/'tables/config_string_vectors.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
keyset={'character_creation_default_weapon','character_creation_default_armor','CastingSkillGraphPath','AutoBattleGraphPath','SelectTargetMaxRange','AttackTargetMaxRange','PreCastingSkillCoolTime','AttackTargetCacheMillis'}
(root/'tables/config_focus.json').write_text(json.dumps([x for x in records if x['key_string'] in keyset],ensure_ascii=False,indent=2),encoding='utf-8')
bundle='c994222ced16276b_dd73beb0f70dfadaec8ced01e6e929bc'
folder=Path(r'D:\99.기타\out_dkbi\bundles')/bundle
wanted={'base_attack','base_attack_sword','base_attack_blade','base_attack_bow','base_attack_fan','base_attack_staff','autobattle','autobattle_server','castingskill','monsterai_field_normal'}
index={}
for line in (folder/'objects.jsonl').open(encoding='utf-8'):
    x=json.loads(line)
    if x.get('name') in wanted:index[x['path_id']]=x
graphs=root/'graphs';graphs.mkdir(exist_ok=True);report=[]
for line in (folder/'typetrees.jsonl').open(encoding='utf-8'):
    x=json.loads(line);d=x.get('data',{});name=d.get('m_Name')
    if name not in wanted or 'BinaryData' not in d:continue
    b=bytes(d['BinaryData']);(graphs/(name+'.pgrf')).write_bytes(b)
    p=12;nodes=[];edges=[];status='unknown';error=None
    def u32():
        global p
        v=struct.unpack_from('<I',b,p)[0];p+=4;return v
    def string():
        global p
        n=u32();assert n<4096 and p+n<=len(b);s=b[p:p+n].decode('utf-8');p+=n;return s
    try:
        assert b[:4]==b'PGRF';version,count=struct.unpack_from('<II',b,4)
        for _ in range(count):
            offset=p;typ=string();nid=u32();guid=b[p:p+16].hex();p+=16;enabled=b[p];p+=1;length=u32();payload=p;assert p+length<=len(b)
            nodes.append(dict(provenance='inferred',record_offset=offset,type_name=typ,id=nid,guid_hex=guid,flag_byte=enabled,payload_offset=payload,payload_size=length,payload_hex=b[p:p+length].hex()));p+=length
        count=u32()
        for _ in range(count):
            offset=p;src=u32();dst=u32();port=string();edges.append(dict(provenance='inferred',record_offset=offset,from_id=src,to_id=dst,port=port))
        assert p==len(b),(p,len(b));assert all(e['from_id'] in {n['id'] for n in nodes} and e['to_id'] in {n['id'] for n in nodes} for e in edges)
        status='layout_consistent_full_consumption'
    except Exception as exc:error=str(exc)
    entry=dict(name=name,source_object=index.get(x['path_id']),serialized_file=x['file'],path_id=x['path_id'],binary_sha256=hashlib.sha256(b).hexdigest(),binary_bytes=len(b),status=status,error=error,nodes=nodes,edges=edges,provenance='inferred',limitations=['Layout validated by bounds and full consumption, runtime parser not disassembled','Node names are stored strings; execution semantics not verified','Payload fields, timing units, node activation flag semantics and port meaning unknown'])
    (graphs/(name+'.json')).write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8');report.append(dict(name=name,nodes=len(nodes),edges=len(edges),status=status,error=error))
(graphs/'graph_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(configs=len(records),focus=[dict(key=x['key_string'],values=[v['value'] for v in x['values']]) for x in records if x['key_string'] in keyset],graphs=report),ensure_ascii=False))
