from pathlib import Path
import subprocess,json,time,hashlib,tarfile,shutil,zlib,uuid
from urllib.parse import quote
root=Path(__file__).resolve().parent
out=root/'ldplayer'
out.mkdir(exist_ok=True)
adb=r'C:\LDPlayer\LDPlayer14\adb.exe'
serial='emulator-5554'
package='and.lhhpub.goodshunt'
def call(args):return subprocess.run([adb,'-s',serial,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
identity=call(['shell','dumpsys','package',package])
(out/'installed_package.txt').write_text(identity.stdout,encoding='utf-8')
roots={'external':'/sdcard/Android/data/'+package,'private':'/data/user/0/'+package,'device_encrypted':'/data/user_de/0/'+package,'obb':'/sdcard/Android/obb/'+package}
records=[]
job=uuid.uuid4().hex[:16]
snapshot_root=out/('files_'+job)
seen_paths={}
for label,path in roots.items():
    file=out/(label+'.tar')
    before=call(['shell',f"su -c 'find {path} -type f -exec stat -c \"%s|%Y|%n\" {{}} \\;' "])
    (out/(label+'_before.txt')).write_text(before.stdout,encoding='utf-8')
    staged=f'/data/local/tmp/goodshunt_ref_{job}_{label}.tar'
    start=time.time()
    command=[adb,'-s',serial,'shell',f"su -c 'tar -C {path} -cf {staged} .; chmod 644 {staged}'"]
    run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
    remote_hash=call(['shell',f"su -c 'sha256sum {staged}'"]).stdout.strip().split()[0]
    pulled=call(['pull',staged,str(file)])
    if pulled.returncode:raise RuntimeError(pulled.stderr)
    digest=hashlib.sha256()
    with file.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    assert digest.hexdigest()==remote_hash,'ADB tar hash mismatch'
    cleaned=call(['shell',f"su -c 'rm -f {staged}'"])
    target=snapshot_root/label
    target.mkdir(parents=True,exist_ok=True)
    members=[];unsafe=[]
    with tarfile.open(file,'r:') as tar:
        for item in tar:
            row={'name':item.name,'bytes':item.size,'mtime':item.mtime,'type':item.type.decode(errors='replace')}
            if item.isfile():
                parts=[quote(x,safe='-._() ') for x in Path(item.name).parts if x not in ['.','']]
                p=(target/Path(*parts)).resolve()
                if not p.is_relative_to(target.resolve()):raise ValueError('unsafe tar path')
                key=str(p).casefold()
                if key in seen_paths and seen_paths[key] != item.name:
                    p=p.with_name(p.stem+'_'+hashlib.sha256(item.name.encode()).hexdigest()[:12]+p.suffix)
                seen_paths[str(p).casefold()]=item.name
                p.parent.mkdir(parents=True,exist_ok=True)
                h=hashlib.sha256()
                src=tar.extractfile(item)
                with src,p.open('wb') as dst:
                    for block in iter(lambda:src.read(1024*1024),b''):
                        h.update(block);dst.write(block)
                row['sha256']=h.hexdigest()
                row['regular_file']=True
                row['local_file']=p.relative_to(out).as_posix()
                assert p.stat().st_size==item.size
            elif item.issym() or item.islnk():
                row['link']=item.linkname;unsafe.append(row)
            members.append(row)
    after=call(['shell',f"su -c 'find {path} -type f -exec stat -c \"%s|%Y|%n\" {{}} \\;' "])
    (out/(label+'_after.txt')).write_text(after.stdout,encoding='utf-8')
    h=hashlib.sha256()
    with file.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    records.append(dict(label=label,remote_path=path,archive=file.name,archive_bytes=file.stat().st_size,archive_sha256=h.hexdigest(),remote_tar_sha256=remote_hash,remote_hash_match=True,temporary_staging_file_removed=cleaned.returncode==0,seconds=time.time()-start,exit_code=run.returncode,stderr=run.stderr.decode('utf-8',errors='replace'),inventory_before_exit=before.returncode,inventory_after_exit=after.returncode,inventory_unchanged=before.returncode==0 and after.returncode==0 and before.stdout==after.stdout,members=members,symlinks_not_followed=unsafe))
    print(label,'files',sum(bool(x.get('regular_file')) for x in members),'MB',round(file.stat().st_size/1e6,1),'rc',run.returncode,flush=True)
paths=call(['shell','pm','path',package]).stdout.splitlines()
installed=[]
for line in paths:
    if not line.startswith('package:'):continue
    path=line[len('package:'):];dest=out/'installed_apks'/Path(path).name;dest.parent.mkdir(exist_ok=True)
    result=call(['pull',path,str(dest)])
    h=hashlib.sha256()
    with dest.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    installed.append(dict(path=path,local=str(dest),bytes=dest.stat().st_size,sha256=h.hexdigest(),exit_code=result.returncode))
(out/'capture_receipt.json').write_text(json.dumps(dict(serial=serial,package=package,captured_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'),application_data_read_only=True,files_root=snapshot_root.relative_to(out).as_posix(),temporary_staging_outside_app_directory=True,live_snapshot_not_atomic=True,records=records,installed_apks=installed),ensure_ascii=False,indent=1),encoding='utf-8')
