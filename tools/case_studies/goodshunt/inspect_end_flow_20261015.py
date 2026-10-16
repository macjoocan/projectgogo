from pathlib import Path
import re,json,bisect,hashlib,zipfile
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent;out=p/'end_flow_audit_20261015';out.mkdir(exist_ok=True)
whole={'StateCompliment','StateFail','StateTimeUp','StateOutOfBox','StateLevelCompleteTransition'}
manager_tokens=('OnGoalPropsRemoved','OnLevelEndAllAnimComplete','OnAllPropInLevelCollected','OnAfterClockCleared','C_WaitForGoalCard','OnClearLevel','OnTimeUp','OnBombTriggering','OnChangeGameState','OnQuitGameplay','OnRetry','OnRestart','PlayNext','OnPlayClicked')
methods={};cur='';pending=None;want=[]
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
 if '// TypeDefIndex:' in line and not line.startswith('\t'):cur=line.strip();pending=None
 m=re.search(r'RVA: (0x[0-9A-F]+)',line)
 if m:pending=int(m[1],16)
 elif pending and '{ }' in line:
  a=pending;pending=None;name=re.search(r'class ([^ :]+)',cur);name=name[1] if name else '';r={'class':cur,'name':name,'signature':line.strip()};methods.setdefault(a,[]).append(r)
  selected=any(name==x or name.startswith(x+'.') for x in whole)
  selected=selected or ('GameRefManager' in cur and any(t in cur+line for t in manager_tokens)) or ('CardController' in cur and any(t in cur+line for t in ('ReduceCard','OnRemoveCard','OnAll','Complete','Clear','RemoveDoneCard')))
  selected=selected or (name=='ClockController' and any(t in line for t in ('OnTimeUp','Clear','End','PauseClock','StopClock')))
  selected=selected or (name in ('GameModeBase','GModeNormal') and any(t in line for t in ('OnClearLevel','OnLevelTimeOut','GetCompletePopupID'))) or (name=='StateGame' and 'PlayWinFireworks(' in line)
  if selected:want.append(a)
ks=sorted(methods);md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN);decl=[]
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
 for a in sorted(set(want)):
  end=ks[bisect.bisect_right(ks,a)];n=min(12288,end-a);s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-s['p_vaddr']+s['p_offset'];f.seek(off);raw=f.read(n)
  rec={'rva':hex(a),'ELF_offset':hex(off),'next_declaration':hex(end),'capped':n<end-a,'code_sha256':hashlib.sha256(raw).hexdigest(),'declarations':methods[a]};decl.append(rec)
  lines=[json.dumps(rec),'Boundary=next declaration, not independently verified symbol size. Generic annotations may alias.']
  for i in md.disasm(raw,a):
   ann=''
   if i.mnemonic in ('b','bl') and i.op_str.startswith('#0x'):ann=' ; '+str(methods.get(int(i.op_str[1:],16),[]))
   lines.append(f'{i.address:08x} {i.mnemonic:8} {i.op_str}{ann}')
  (out/f'disasm_{a:08x}.txt').write_text('\n'.join(lines),encoding='utf-8')
(out/'declarations.json').write_text(json.dumps(decl,indent=1),encoding='utf-8')
stored=[]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
  r=json.loads(line)
  if r.get('script_class') not in whole|{'PopupManager','GameViewManager','CardController'} or not r.get('json_file'):continue
  raw=z.read(r['json_file']);stored.append({'provenance':r,'json_sha256':hashlib.sha256(raw).hexdigest(),'fields':json.loads(raw)})
(out/'stored_ui_components.json').write_text(json.dumps(stored,ensure_ascii=False,indent=1),encoding='utf-8');print('methods',len(decl),'capped',sum(r['capped'] for r in decl),'UIrecords',len(stored))
