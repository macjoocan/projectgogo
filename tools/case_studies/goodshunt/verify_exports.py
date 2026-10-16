from pathlib import Path
import json,zipfile,hashlib,shutil,collections,zlib
root=Path(__file__).resolve().parent
results=root/'results'
unpacked=root/'unpacked'
unpacked.mkdir(exist_ok=True)
report={'archives':{},'input_copies':{},'limitations':[]}
archives=['GoodsHunt_sprites.zip','GoodsHunt_assets.zip','GoodsHunt_hierarchy.zip',
          'GoodsHunt_levels_decoded.zip','GoodsHunt_meshes_obj.zip',
          'GoodsHunt_native_raw.zip','GoodsHunt_structured_objects.zip']
archives += ['GoodsHunt_preload_sprites.zip','GoodsHunt_preload_assets.zip','GoodsHunt_preload_hierarchy.zip',
             'supplement/GoodsHunt_meshes_obj.zip','supplement/GoodsHunt_native_raw.zip','supplement/GoodsHunt_structured_objects.zip']
archives.append('GoodsHunt_settings.zip')
for name in archives:
    path=results/name
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    with zipfile.ZipFile(path) as z:
        entries=[i for i in z.infolist() if not i.is_dir()]
        seen=set();collisions=[]
        for i in entries:
            key=i.filename.casefold()
            if key in seen:collisions.append(i.filename)
            seen.add(key)
        bad=z.testzip()
        assert bad is None,(name,bad)
        assert not collisions,(name,collisions)
        row=dict(entries=len(entries),bytes=path.stat().st_size,sha256=h.hexdigest(),crc_ok=True,casefold_collisions=0)
        if 'native_raw' not in name and 'structured_objects' not in name:
            target=unpacked/name[:-4]
            target.mkdir(parents=True,exist_ok=True)
            for i in entries:
                p=(target/i.filename).resolve()
                assert p.is_relative_to(target.resolve()),i.filename
                p.parent.mkdir(parents=True,exist_ok=True)
                with z.open(i) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst,128*1024)
            row['disk_files']=sum(1 for p in target.rglob('*') if p.is_file())
            assert row['disk_files']==row['entries'],(name,row)
        report['archives'][name]=row
        print('verified',name,len(entries),flush=True)
for name,prefix in [('base.apk','assets/'),('abi.apk','lib/')]:
    count=0;size=0
    with zipfile.ZipFile(root/name) as z:
        for i in z.infolist():
            if not i.filename.startswith(prefix) or i.is_dir():continue
            p=root/'input_prepared'/i.filename
            crc=0;length=0
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1024*1024),b''):
                    crc=zlib.crc32(b,crc);length+=len(b)
            assert length==i.file_size and crc==i.CRC,i.filename
            count+=1;size+=length
    report['input_copies'][name]=dict(files=count,bytes=size,crc_and_sizes_match=True)
report['passed']=True
(root/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
