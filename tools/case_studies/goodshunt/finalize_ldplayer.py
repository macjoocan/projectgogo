from pathlib import Path
import json,zipfile,hashlib,base64,csv,collections,shutil
root=Path(__file__).resolve().parent
ld=root/'ldplayer'
results=ld/'results'
inventory=json.loads((ld/'analysis_inventory.json').read_text())
capture=json.loads((ld/'capture_receipt.json').read_text())
summary=json.loads((ld/'native_export_summary.json').read_text())
fonts=[]
font_dir=ld/'fonts'
font_dir.mkdir(exist_ok=True)
with zipfile.ZipFile(results/'GoodsHunt_structured_objects.zip') as z, zipfile.ZipFile(results/'GoodsHunt_native_raw.zip') as rawz:
    for line in (results/'native_object_index.jsonl').read_text().splitlines():
        row=json.loads(line)
        if row.get('script_class')!='UniTextFont' or not row.get('json_file'):continue
        d=json.loads(z.read(row['json_file']))
        value=d['fontData']
        content=base64.b64decode(value['__bytes_base64__']) if isinstance(value,dict) else bytes(value)
        assert content.startswith((b'\x00\x01\x00\x00',b'OTTO',b'ttcf')),row['name']
        raw=rawz.read(row['raw_file'])
        offset=raw.find(content)
        assert offset>=0,'font bytes absent from source object'
        filename=row['name']+('.otf' if content.startswith(b'OTTO') else '.ttf')
        (font_dir/filename).write_bytes(content)
        fonts.append(dict(name=row['name'],file=filename,bytes=len(content),sha256=hashlib.sha256(content).hexdigest(),source=row,object_byte_offset=offset,stored_font_hash=d.get('fontDataHash')))
(ld/'fonts_manifest.json').write_text(json.dumps(fonts,ensure_ascii=False,indent=1),encoding='utf-8')
with zipfile.ZipFile(results/'GoodsHunt_LD_fonts.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('manifest.json',json.dumps(fonts,ensure_ascii=False))
    for item in fonts:z.write(font_dir/item['file'],item['file'])
configs={}
for group in inventory['remote_configs']:
    configs[group['kind']]={x['key']:json.loads((ld/'remote_configs'/x['file']).read_text())['decoded_value'] for x in group['entries']}
a=configs['activated'];b=configs['defaults']
comparison=dict(activated_count=len(a),defaults_count=len(b),shared_count=len(a.keys()&b.keys()),
                changed_keys=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]),
                activated_only=sorted(a.keys()-b.keys()),defaults_only=sorted(b.keys()-a.keys()),
                dda_activated=a.get('DDAConfig'),dda_defaults=b.get('DDAConfig'),
                caveat='SDK activated-cache snapshot; runtime method application and gameplay units are not verified.')
(ld/'remote_config_comparison.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=1),encoding='utf-8')
with zipfile.ZipFile(results/'GoodsHunt_LD_remote_configs.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.write(ld/'remote_config_comparison.json','comparison.json')
    for p in sorted((ld/'remote_configs').glob('*.json')):z.write(p,p.name)
loop=json.loads((ld/'LevelLoop_decoded.json').read_text())
entries=loop['stored_fields']['entries']
with (ld/'LevelLoop_entries.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['storage_index','actualLevelId','packId','packLevelIdx','basePackLevelId']);w.writeheader()
    for i,item in enumerate(entries):w.writerow(dict(storage_index=i,**item))
loop_summary=dict(entries=len(entries),pack_counts=dict(collections.Counter(x['packId'] for x in entries)),
                  boundary='Ordered loop references, not 1300 new map assets or initial level order; runtime selection formula unverified.')
verified={}
unpacked=ld/'unpacked'
for p in sorted(results.rglob('*.zip')):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    with zipfile.ZipFile(p) as z:
        names=[i.filename for i in z.infolist() if not i.is_dir()]
        assert z.testzip() is None
        assert len(names)==len(set(n.casefold() for n in names)),p.name
        target=unpacked/p.stem
        target.mkdir(parents=True,exist_ok=True)
        if p.name not in ['GoodsHunt_structured_objects.zip','GoodsHunt_native_raw.zip']:
            for name in names:
                dest=(target/name).resolve();assert dest.is_relative_to(target.resolve())
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(name) as f,dest.open('wb') as out:shutil.copyfileobj(f,out,128*1024)
            disk=sum(p.is_file() for p in target.rglob('*'));assert disk==len(names)
        else:disk=None
        verified[p.name]=dict(entries=len(names),bytes=p.stat().st_size,sha256=h.hexdigest(),crc_ok=True,disk_files=disk)
changes={}
for rec in capture['records']:
    def rows(text):
        return {s.split('|',2)[2]:s.split('|',2)[:2] for s in text.splitlines() if len(s.split('|',2))==3}
    pre=rows((ld/(rec['label']+'_before.txt')).read_text());post=rows((ld/(rec['label']+'_after.txt')).read_text())
    changes[rec['label']]=sorted(k for k in pre.keys()|post.keys() if pre.get(k)!=post.get(k))
(ld/'snapshot_changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=1),encoding='utf-8')
extra=dict(captured_files=len(inventory['files']),new_bundles=len(inventory['unity_sources']),loop=loop_summary,
           activated_configs=len(a),default_configs=len(b),changed_config_keys=len(comparison['changed_keys']),
           playerprefs=inventory.get('playerprefs_count'),font_files=len(fonts),font_names=[x['name'] for x in fonts],
           native_types=summary['types'],decoded_types=summary['decoded_types'],header_checks=summary['header_checks'],unresolved=len(summary['failures']),
           archive_verification=verified,snapshot_non_atomic=True,private_changed_paths=len(changes['private']),
           archives_match_remote_sha=all(x['remote_hash_match'] for x in capture['records']))
(ld/'final_summary.json').write_text(json.dumps(extra,ensure_ascii=False,indent=2),encoding='utf-8')
print('LD complete',dict(fonts=len(fonts),configs=len(a),loop=len(entries),bundles=4,unresolved=extra['unresolved']))
