from pathlib import Path
import json,subprocess,re,hashlib,time
p=Path(__file__).resolve().parent;inv=json.loads((p/'package_inventory.json').read_text());exe=p/'tools/source/UEViewer-master/umodel.exe';game=Path('D:/SteamLibrary/steamapps/common/HatinTime/HatinTimeGame/CookedPC');result=[]
for r in inv:
 if not any(x['type']=='AnimSet' for x in r['objects']):continue
 rel=Path(r['relative']);dest=p/'raw'/rel.with_suffix('');log=p/'logs'/(str(rel).replace('\\','__')+'.enhance.log');cmd=[str(exe),'-export','-game=hat','-nostat','-nomesh','-nomorph','-notex','-md5','-nooverwrite','-out='+str(dest),'-path='+str(game),r['source']]
 with log.open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
 text=log.read_text(errors='replace');count=len(list(dest.rglob('*.source.json')));result.append(dict(package=r['relative'],exit_code=rc,errors=bool(re.search('ERROR:|Fatal error',text)),sidecars=count,exe_sha256=hashlib.sha256(exe.read_bytes()).hexdigest()));(p/'enhancement_runs.json').write_text(json.dumps(result,indent=1));print(len(result),r['relative'],count,flush=True)
print('DONE',flush=True)
