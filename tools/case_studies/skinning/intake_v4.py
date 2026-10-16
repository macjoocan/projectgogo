from pathlib import Path
import shutil,hashlib,json
ROOT=Path(__file__).resolve().parent/'v4_followup';ROOT.mkdir(exist_ok=True)
source=Path('C:/00.SVN/Multi/web/assets/studies/motion-first-crew');rows=[]
for rel in ['final/original-retry-native.blend','source/hand-cage-v4/candidate.blend','source/hand-cage-v4/validation.json','source/hand-cage-v4/proportion-diagnosis.json','source/hand-cage-v4/native-reopen-validation.json','source/hand-cage-v4/README.md']:
    p=source/rel;dest=ROOT/'input'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    rows.append({'source':str(p),'copy':str(dest),'sha256':h(p),'copy_sha256':h(dest)})
(ROOT/'intake.json').write_bytes(json.dumps(rows,indent=2).encode('utf-8'));print('V4_INTAKE',len(rows))
