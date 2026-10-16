from pathlib import Path
import sys,json,hashlib,collections,zipfile,shutil,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
ld=root/'ldplayer'
receipt=json.loads((ld/'capture_receipt.json').read_text())
prepared=ld/'analysis_input'
prepared.mkdir(exist_ok=True)
report={'files':[],'unity_sources':[],'json_documents':[],'duplicates_of_apk':[],'remote_configs':[], 'installed_apks':[]}
existing={}
for p in (root/'input_prepared').rglob('*'):
    if not p.is_file():continue
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    existing.setdefault(h.hexdigest(),[]).append(p.relative_to(root/'input_prepared').as_posix())
remote_dir=ld/'remote_configs'
remote_dir.mkdir(exist_ok=True)
for record in receipt['records']:
    for item in record['members']:
        if not item.get('regular_file'):continue
        p=ld/item['local_file']
        with p.open('rb') as f:head=f.read(32)
        row=dict(origin=record['label'],logical_path=item['name'],local_file=item['local_file'],bytes=item['bytes'],sha256=item['sha256'],head_hex=head[:16].hex())
        report['files'].append(row)
        if row['sha256'] in existing:
            report['duplicates_of_apk'].append(dict(**row,apk_paths=existing[row['sha256']]))
        if head.startswith((b'UnityFS\0',b'UnityRaw\0',b'UnityWeb\0')):
            dest=prepared/f"{len(report['unity_sources']):03d}_{p.name}.bundle"
            shutil.copyfile(p,dest)
            report['unity_sources'].append(dict(**row,prepared_file=dest.name))
        if item['name'].endswith('.json') and item['bytes']<4*1024*1024:
            try:
                data=json.loads(p.read_text(encoding='utf-8-sig'))
                report['json_documents'].append(dict(origin=record['label'],logical_path=item['name'],sha256=item['sha256'],keys=list(data) if isinstance(data,dict) else None))
                if 'firebase_activate.json' in item['name'] or 'firebase_defaults.json' in item['name']:
                    configs=data.get('configs_key',{})
                    prefix='activated' if 'activate' in item['name'] else 'defaults'
                    entries=[]
                    for n,(key,value) in enumerate(configs.items()):
                        decoded=value
                        if isinstance(value,str):
                            try:decoded=json.loads(value)
                            except (ValueError,TypeError):pass
                        dest=remote_dir/f'{prefix}_{n:04d}.json'
                        dest.write_text(json.dumps(dict(key=key,original_value=value,decoded_value=decoded,source=row,classification='captured SDK cache; runtime gameplay application unverified'),ensure_ascii=False,indent=1),encoding='utf-8')
                        entries.append(dict(key=key,file=dest.name,value_type=type(decoded).__name__))
                    report['remote_configs'].append(dict(kind=prefix,source=row,top_level_keys=list(data),entry_count=len(entries),entries=entries))
            except (ValueError,UnicodeError):pass
        if 'playerprefs.xml' in item['name']:
            values=[]
            for node in ET.fromstring(p.read_text(encoding='utf-8')):
                value=node.get('value',node.text or '')
                parsed=value
                if node.tag=='string':
                    try:parsed=json.loads(value)
                    except (ValueError,TypeError):pass
                values.append(dict(key=node.get('name'),type=node.tag,stored_value=value,parsed_value=parsed))
            (ld/'playerprefs_decoded.json').write_text(json.dumps(dict(source=row,entries=values,classification='local player/SDK state; not default balance'),ensure_ascii=False,indent=1),encoding='utf-8')
            report['playerprefs_count']=len(values)
for item in receipt['installed_apks']:
    p=Path(item['local'])
    with zipfile.ZipFile(p) as z:
        members=[]
        for info in z.infolist():
            if info.filename.startswith('lib/') and not info.is_dir():
                dest=ld/'installed_native'/p.stem/info.filename
                dest.parent.mkdir(parents=True,exist_ok=True)
                with z.open(info) as f,dest.open('wb') as out:shutil.copyfileobj(f,out,1024*1024)
                members.append(dict(path=info.filename,bytes=info.file_size,local_file=str(dest)))
        report['installed_apks'].append(dict(file=p.name,bytes=item['bytes'],sha256=item['sha256'],native_libraries=members))
# Preserve decoded JSON candidates independently. No server addresses are fetched.
(ld/'analysis_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=1),encoding='utf-8')
print('files',len(report['files']),'bundles',len(report['unity_sources']),'JSON',len(report['json_documents']),
      'remote',[ (x['kind'],x['entry_count']) for x in report['remote_configs'] ],'prefs',report.get('playerprefs_count'))
print('bundles',[(x['logical_path'],x['bytes']) for x in report['unity_sources']])
