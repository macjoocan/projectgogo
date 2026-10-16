from pathlib import Path
import re,json,bisect,zipfile,hashlib
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
p=Path(__file__).resolve().parent;out=p/'booster_goal_audit_20261015';out.mkdir(exist_ok=True);methods={};cur='';pending=None;want=[];decl={}
whole={'GoalCardMechanic','NormalGoalCardMechanic','HiddenGoalCardMechanic','BonusGoalCardMechanic','GoalCardMechanicFactory','PowerUpBase','GrowthPowerUp','MagnetPowerUp','HintPowerUp','ShieldPowerUp','ButtonTapSound','StateLevelCompleteTransition'}
buttons={'CompassButton','FreezeButton','GrowthButton','MagnetButton','ShieldButton','BaseInGameBoosterButton','BaseLockableButton','ConsumableButton'}
for line in (p/'code_audit_20261014/dump.cs').open(encoding='utf-8'):
 if '// TypeDefIndex:' in line and not line.startswith('\t'):cur=line.strip();pending=None
 m=re.search(r'RVA: (0x[0-9A-F]+)',line)
 if m:pending=int(m[1],16)
 elif pending and '{ }' in line:
  a=pending;pending=None;r={'class':cur,'signature':line.strip()};methods.setdefault(a,[]).append(r)
  name=re.search(r'class ([^ :]+)',cur);name=name[1] if name else ''
  selected=name in whole or (name in buttons and any(t in line for t in ('OnUseBooster(','ClearEffect(','ReactOnState(','OnClick(','UseBooster(','Start(','IsUnlock','CanUse','DecreaseQuantity('))) or (name=='GoalCard' and any(t in line for t in ('AttachMechanic(','SetHidden(','OnCardInteraction(','Reduce(','Complete(','UpdateQuantity(','ShowFront(','ShowBack('))) or (name=='BoosterManager' and any(t in line for t in ('Growth','Freeze','ExtraTime','Compass','Magnet','Shield','Lightning'))) or ('HintPowerUp.<>' in name) or ('ShieldPowerUp.<>' in name)
  selected=selected or (name in buttons and any(t in line for t in ('get_Is','PressBtn(','StartCountCoroutine(','OnCooldownDone('))) or ('BaseInGameBoosterButton.<CCountDown>' in name) or ('FreezeButton' in cur and '<OnUseBooster>' in line) or (name=='CardController' and any(t in line for t in ('ReduceCard(','PopulateCardData(','OnRemoveCard(','DoPunchCard('))) or (name=='BoosterManager' and 'ActivatePowerUp(' in line) or (name=='ClockController' and any(t in line for t in ('StartFreeze(','EndFreeze(','_Update(','Init(','_Reset(')))
  selected=selected or (name=='CardController' and 'CheckHiddenCardMechanic(' in line) or (name=='StateGame' and any(t in line for t in ('OnUsePreboosterTime(','OnUsePreboosterLightning('))) or any(t in line for t in ('<OnUsePreboosterTime>','<OnUsePreboosterLightning>'))
  selected=selected or ('StateGame' in cur and any(t in cur+line for t in ('C_PreBoosterFlyingAnim','DoExtraTimerSeq','DoLightningSeq'))) or (name=='ClockController' and any(t in line for t in ('PrepareAddTime(','AddTime(','AddExtraTime(')))
  selected=selected or ('BoosterManager' in cur and '<OnUseLightning>' in line) or ('ClockController' in cur and '<AddTime>' in line) or (name=='LightningButton' and 'Execute(' in line) or (name=='BoosterManager' and 'DoStarExplodeFx(' in line)
  selected=selected or ('LightningButton' in cur and '<Execute>' in line) or (name=='ScoreController' and 'ForceAdd(' in line)
  selected=selected or name in ('BaseUpgrade','HoleSizeUpgrade','UpgradesController') or ('PlayerBehavior.<Init>' in cur)
  if selected:want.append(a);decl.setdefault(name,[]).append(dict(r,rva=hex(a)))
lib=p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so';ks=sorted(methods);md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
with lib.open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD']
 for a in sorted(set(want)):
  end=ks[bisect.bisect_right(ks,a)];n=min(8192,end-a);s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);off=a-s['p_vaddr']+s['p_offset'];f.seek(off);raw=f.read(n)
  ls=[str(methods[a]),f'RVA={a:#x} ELF_offset={off:#x}, next_declaration={end:#x}, capped={n<end-a}, boundary not independently verified symbol size, codeSHA={hashlib.sha256(raw).hexdigest()}']
  for ins in md.disasm(raw,a):
   ann=''
   if ins.mnemonic in ['b','bl'] and ins.op_str.startswith('#0x'):ann=' ; '+str(methods.get(int(ins.op_str[1:],16),[]))
   ls.append(f'{ins.address:08x} {ins.mnemonic:8} {ins.op_str}{ann}')
  (out/f'disasm_{a:08x}.txt').write_text('\n'.join(ls),encoding='utf-8')
(out/'selected_declarations.json').write_text(json.dumps(decl,indent=1),encoding='utf-8')
stored=[]
with zipfile.ZipFile(p/'results/GoodsHunt_structured_objects.zip') as z:
 for line in (p/'results/native_object_index.jsonl').open(encoding='utf-8'):
  r=json.loads(line);c=r.get('script_class')
  if c not in whole|buttons|{'PlayerComponent','BoosterManager','CountDownClock','GoalCard','StateGame','GoalCardUI','UpgradesController','HoleSizeUpgrade','UpgradesDatabase'} or not r.get('json_file'):continue
  try:raw=z.read(r['json_file'])
  except KeyError:continue
  if len(raw)>256000:continue
  stored.append({'provenance':r,'json_sha256':hashlib.sha256(raw).hexdigest(),'fields':json.loads(raw)})
(out/'stored_components.json').write_text(json.dumps({'boundary':'Existing structured exports and native provenance, not newly executed original runtime.','records':stored},ensure_ascii=False,indent=1),encoding='utf-8')
print('selectedmethods',len(set(want)),'storedrecords',len(stored))
