from pathlib import Path
import struct,json,hashlib
from elftools.elf.elffile import ELFFile
p=Path(__file__).resolve().parent;out=p/'drop_gauge_audit_20261015';lib=p/'ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so'
b=(p/'input_prepared/assets/bin/Data/Managed/Metadata/global-metadata.dat').read_bytes()
with lib.open('rb') as f:
 e=ELFFile(f);ss=[s for s in e.iter_segments() if s['p_type']=='PT_LOAD'];rel={r['r_offset']:r['r_addend'] for s in e.iter_sections() if s['sh_type']=='SHT_RELA' for r in s.iter_relocations() if r['r_info_type']==1027}
 def raw(a,n):
  s=next(s for s in ss if s['p_vaddr']<=a<s['p_vaddr']+s['p_filesz']);f.seek(a-s['p_vaddr']+s['p_offset']);return f.read(n)
 def ptr(a):return rel.get(a,struct.unpack('<Q',raw(a,8))[0])
 slot=0x4196ff0;usage=ptr(slot);token=struct.unpack('<Q',raw(usage,8))[0];assert token==0x80000011
 fieldrefidx=(token&0x1ffffffe)>>1;fro,frn=struct.unpack_from('<II',b,184);typeidx,localfield=struct.unpack_from('<ii',b,fro+fieldrefidx*8)
 types=ptr(0x3ff9ad0+56);typeaddr=ptr(types+typeidx*8);tdidx=struct.unpack('<Q',raw(typeaddr,8))[0]
 tdo,tdn=struct.unpack_from('<II',b,160);tdcount=struct.unpack('<Q',raw(0x3ff9ad0+80,8))[0];assert tdn//tdcount==88
 t=tdo+tdidx*88;strings=struct.unpack_from('<I',b,24)[0]
 def name(i):return b[strings+i:b.index(b'\0',strings+i)].decode()
 tn=name(struct.unpack_from('<i',b,t)[0]);assert tn=='<PrivateImplementationDetails>'
 fieldstart=struct.unpack_from('<i',b,t+32)[0];fieldidx=fieldstart+localfield;fo,fn=struct.unpack_from('<II',b,96);fieldname=name(struct.unpack_from('<i',b,fo+fieldidx*12)[0])
 do,dn=struct.unpack_from('<II',b,64);defs=[struct.unpack_from('<iii',b,do+j) for j in range(0,dn,12) if struct.unpack_from('<i',b,do+j)[0]==fieldidx];assert len(defs)==1
 dd=struct.unpack_from('<I',b,72)[0];a=dd+defs[0][2];value=b[a:a+16];assert hashlib.sha256(value).hexdigest().upper()==fieldname
 result={'grade':'original_code_and_metadata','getter_rva':'0x21f4920','field_slot':hex(slot),'rela_target':hex(usage),'token':hex(token),'fieldref_index':fieldrefidx,'fieldref':[typeidx,localfield],'type_array':hex(types),'type_address':hex(typeaddr),'typedef_index':tdidx,'type_name':tn,'field_index':fieldidx,'field_name':fieldname,'field_default_record':defs[0],'data_file_offset':a,'data_hex':value.hex(),'map_themes':list(struct.unpack('<4i',value)),'sha256_equals_field_name':True,'metadata_sha256':hashlib.sha256(b).hexdigest(),'boundary':'Static ELF relocations+metadata only. No original code execution; 4-array length from GetMapThemes disassembly.'}
 lit=raw(0xdb98e8,8);result['dda_modifiers_ctor_literal']={'rva':'0xdb98e8','raw_hex':lit.hex(),'float32':list(struct.unpack('<2f',lit))}
(out/'mart_theme_array_evidence.json').write_text(json.dumps(result,indent=1),encoding='utf-8');print(json.dumps(result))
