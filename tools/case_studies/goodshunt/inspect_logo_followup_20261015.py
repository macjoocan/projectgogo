from pathlib import Path
import json, struct
from elftools.elf.elffile import ELFFile
p = Path(__file__).resolve().parent
rows = []
with (p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so').open('rb') as f:
    elf = ELFFile(f)
    loads = [s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
    for address, label in [(0xe0a994,'Logo scale first multiplier'),(0xe0a5f0,'Logo hold interval'),(0xe0a5e4,'Logo scale final multiplier')]:
        s = next(s for s in loads if s['p_vaddr'] <= address < s['p_vaddr']+s['p_filesz'])
        offset = address-s['p_vaddr']+s['p_offset']
        f.seek(offset)
        raw=f.read(4)
        rows.append(dict(label=label,address=hex(address),ELF_offset=hex(offset),hex=raw.hex(),value=struct.unpack('<f',raw)[0]))
result=dict(track_entry=dict(type_def_index=17159,trackTime_offset='0x94',timeScale_offset='0xa4',write_rva='0x1d984b4',bits='0x3fd33333',value=struct.unpack('<f',struct.pack('<I',0x3fd33333))[0]),ease=dict(type_def_index=18200,name='DG.Tweening.Ease.OutBack',value=27,call_rvas=['0x1d985a4','0x1d98628']),literals=rows)
(p/'end_flow_audit_20261015/logo_followup_values.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
