from pathlib import Path
import json,re,struct,subprocess
O=Path(__file__).resolve().parent;R=O.parent
d=(R/'il2cpp_dump/dump.cs').read_text('utf8')
for term in ['public static void SpawnTransient(','public enum ForceMode','public void set_Contact_Group_Calculations']:
 p=d.index(term); start=d.rfind('\npublic ',0,p) if '(' in term else p
 print(d[start:start+800])
j=json.loads((R/'destruction_fx_audit/original_effects.json').read_text('utf8'))
print('effects root',type(j), list(j)[:12] if isinstance(j,dict) else len(j))
for k,v in (j.items() if isinstance(j,dict) else enumerate(j)):
 print(str(k),type(v),str(v)[:450])
 if isinstance(v,list): print('length',len(v),'first keys',list(v[0]) if v and isinstance(v[0],dict) else '')
r=json.loads((O/'rope_saved_values.json').read_text('utf8'))
for k,v in r['references'].items():
 if v:print(k,v['file'],v['path_id'],v['data'].get('m_Name'),v.get('game_object',{}).get('data',{}).get('m_Name'))
b=(R/'static_physics/libil2cpp.so').read_bytes()
print('extra float constants',[(hex(a),struct.unpack_from('<f',b,a)[0]) for a in [0x14f3660,0x14f3670,0x14f38ac,0x14f38b0,0x14f3a84]])
tool=r'C:\Program Files\Unity\Hub\Editor\6000.0.62f1\Editor\Data\PlaybackEngines\AndroidPlayer\NDK\toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-objdump.exe'
for name,a,z in [('Vector3_SignedAngle_candidate',0x394f6d4,0x394f894),('Debug_set_Contact_Group_Calculations',0x379f378,0x379f488),('SpawnTransient',0x39466c4,0x3946784)]:
 t=subprocess.check_output([tool,'-d','--no-show-raw-insn',f'--start-address={a}',f'--stop-address={z}',str(R/'static_physics/libil2cpp.so')],encoding='utf8',errors='replace')
 (O/(name+'.asm')).write_text(t,encoding='utf8')
