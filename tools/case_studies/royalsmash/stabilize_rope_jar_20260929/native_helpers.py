from pathlib import Path
import struct,re,json,bisect
import numpy as np
R=Path(__file__).resolve().parent.parent; O=Path(__file__).resolve().parent
b=(R/'static_physics/libil2cpp.so').read_bytes()
phoff=struct.unpack_from('<Q',b,32)[0]; ents,num=struct.unpack_from('<HH',b,54)
segs=[struct.unpack_from('<IIQQQQQQ',b,phoff+i*ents) for i in range(num)]
def off(va):
    for t,f,o,v,p,fs,ms,a in segs:
        if t==1 and v<=va<v+fs:return o+va-v
    raise ValueError(hex(va))
const={hex(a):{'file_offset':hex(off(a)),'float32':struct.unpack_from('<f',b,off(a))[0],'hex':b[off(a):off(a)+4].hex()} for a in [0x14f3a38,0x14f38a8,0x14f3a10,0x14f3aa4,0x14f36cc,0x14f388c,0x14f3aac,0x14f3720]}
(O/'constants.json').write_text(json.dumps(const,indent=2));print(json.dumps(const,indent=2))
dump=(R/'il2cpp_dump/dump.cs').read_text('utf8')
methods={int(a,16):s.strip() for a,s in re.findall(r'// RVA: 0x([0-9a-fA-F]+)[^\n]*\n\s*([^\n]+)',dump)}
addrs=sorted(methods)
targets=[0x383b030,0x393f7dc,0x383ca00,0x383d7c8,0x39466c4]
refs={hex(t):[] for t in targets}
for typ,flags,o,v,p,fs,ms,align in segs:
    if typ!=1 or not flags&1:continue
    words=np.frombuffer(b,dtype='<u4',count=fs//4,offset=o)
    ix=np.flatnonzero((words&0x7c000000)==0x14000000)
    ws=words[ix]; disp=(ws&0x3ffffff).astype(np.int64);disp=np.where(disp&(1<<25),disp-(1<<26),disp)
    va=ix*4+v;dest=va+disp*4
    for t in targets:
        for j in np.flatnonzero(dest==t):
            src=int(va[j]);idx=bisect.bisect_right(addrs,src)-1
            refs[hex(t)].append({'callsite':hex(src),'function_start':hex(addrs[idx]),'signature':methods[addrs[idx]]})
(O/'direct_xrefs.json').write_text(json.dumps(refs,indent=2));print(json.dumps(refs,indent=2))
