from pathlib import Path
import json,re,subprocess,time,sys,hashlib,os
p=Path(__file__).resolve().parent;game=Path('D:/SteamLibrary/steamapps/common/HatinTime/HatinTimeGame/CookedPC');exe=p/'tools/umodel_hat/umodel-hat.exe';logs=p/'logs';logs.mkdir(exist_ok=True);raw=p/'raw';raw.mkdir(exist_ok=True)
packages=sorted(x for x in game.rglob('*') if x.suffix.lower() in ('.upk','.u','.umap'))
env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8');records=[]
for i,f in enumerate(packages):
 rel=f.relative_to(game);label=str(rel).replace('\\','__').replace('/','__');log=logs/(label+'.list.log')
 cmd=[str(exe),'-list','-game=hat','-path='+str(game),str(f)]
 with log.open('w',encoding='utf-8') as out:rc=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=90).returncode
 s=log.read_text(encoding='utf-8',errors='replace');objs=[]
 for line in s.splitlines():
  m=re.match(r'\s*(\d+)\s+([0-9A-F]+)\s+([0-9A-F]+)\s+(SkeletalMesh|AnimSet|AnimSequence)\s+(.+)$',line)
  if m:objs.append(dict(export_index=int(m[1]),serial_offset=int(m[2],16),serial_size=int(m[3],16),type=m[4],name=m[5]))
 r=dict(source=str(f),relative=str(rel),bytes=f.stat().st_size,list_exit=rc,list_error=bool(re.search(r'ERROR:|Fatal error',s)),objects=objs);records.append(r)
 if any(o['type'] in ('SkeletalMesh','AnimSet') for o in objs):
  dest=raw/rel.with_suffix('');dest.mkdir(parents=True,exist_ok=True);elog=logs/(label+'.export.log');cmd=[str(exe),'-export','-game=hat','-nostat','-nomorph','-notex','-md5','-out='+str(dest),'-path='+str(game),str(f)]
  with elog.open('w',encoding='utf-8') as out:
   try:r['export_exit']=subprocess.run(cmd,stdout=out,stderr=subprocess.STDOUT,timeout=180).returncode
   except subprocess.TimeoutExpired:r['export_exit']='timeout'
  es=elog.read_text(encoding='utf-8',errors='replace');r['export_error']=bool(re.search(r'ERROR:|Fatal error',es));r['md5mesh']=len(list(dest.rglob('*.md5mesh')));r['md5anim']=len(list(dest.rglob('*.md5anim')))
  with f.open('rb') as inp:r['sha256']=hashlib.file_digest(inp,'sha256').hexdigest()
 (p/'package_inventory.json').write_text(json.dumps(records,indent=1),encoding='utf-8')
 print(f'{i+1}/{len(packages)} {rel} objects={len(objs)} mesh={r.get("md5mesh",0)} anim={r.get("md5anim",0)} err={r.get("export_error",False)}',flush=True)
print('DONE',len(records),flush=True)
