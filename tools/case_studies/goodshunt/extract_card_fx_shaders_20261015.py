import json,struct,re,hashlib,gc
from pathlib import Path
import UnityPy
from UnityPy.helpers import CompressionHelper
p=Path(__file__).resolve().parent;out=p/'card_fx_asset_audit_20261015';out.mkdir(exist_ok=True)
env=UnityPy.load(str(p/'input_prepared/assets/bin/Data/data.unity3d'));objs={(o.assets_file.name,o.path_id):o for o in env.objects};result=[]
for label,file,pid in [('uiadditive','globalgamemanagers.assets',9),('softadditive','sharedassets2.assets',591),('lineardodge','resources.assets',1235),('uiaura','sharedassets0.assets',35)]:
 dest=out/label;dest.mkdir(exist_ok=True);o=objs[(file,pid)];t=o.read_typetree();blob=bytes(t['compressedBlob']);rec={'label':label,'file':file,'path_id':pid,'raw_sha256':hashlib.sha256(o.get_raw_data()).hexdigest(),'name':t['m_ParsedForm']['m_Name'],'platforms':t['platforms'],'segments':[]}
 (dest/'parsed_form.json').write_text(json.dumps(t['m_ParsedForm'],ensure_ascii=False,indent=1),encoding='utf-8')
 for pi,platform in enumerate(t['platforms']):
  if platform!=9:continue
  oo,ll,ss=[t[k][pi] for k in ['offsets','compressedLengths','decompressedLengths']]
  if isinstance(oo,int):oo,ll,ss=[oo],[ll],[ss]
  for si,(offset,length,size) in enumerate(zip(oo,ll,ss)):
   assert 0<size<64*1024*1024
   data=CompressionHelper.decompress_lz4(blob[offset:offset+length],size);assert len(data)==size
   count=struct.unpack_from('<I',data)[0];assert 0<count<20000
   entries=[(i,*struct.unpack_from('<3I',data,4+12*i)) for i in range(count)];assert all(4+12*count<=a and a+n<=len(data) and n>0 for i,a,n,s in entries)
   programs=[]
   for match in re.finditer(rb'[\x09\x0a\x0d\x20-\x7e]{100,}',data):
    code=match.group()
    if b'#version' not in code[:100] or b'void main' not in code:continue
    a=match.start();n=struct.unpack_from('<I',data,a-4)[0]
    if not 0<n<=len(code):continue
    owners=[e for e in entries if e[1]<=a-4 and a+n<=e[1]+e[2]]
    if len(owners)!=1:continue
    code=data[a:a+n];i,entryoff,entrysize,eseg=owners[0];name=f'p{platform}_s{si}_entry{i:04d}.glsl';(dest/name).write_bytes(code);kw=[];cur=entryoff+24;count_kw=struct.unpack_from('<I',data,cur)[0];cur+=4
    kw_ok=0<=count_kw<256
    if kw_ok:
     for _ in range(count_kw):
      length_kw=struct.unpack_from('<I',data,cur)[0];cur+=4
      if not 0<length_kw<256:kw_ok=False;break
      kw.append(data[cur:cur+length_kw].decode('ascii').rstrip('\0'));cur=(cur+length_kw+3)&~3
    kw_ok=kw_ok and cur==a-4
    programs.append({'keywords':kw if kw_ok else None,'keyword_prefix_verified':kw_ok,'program_header_words':struct.unpack_from('<6I',data,entryoff),'file':name,'blob_entry':i,'entry_offset':entryoff,'entry_bytes':entrysize,'code_offset':a,'code_bytes':n,'sha256':hashlib.sha256(code).hexdigest(),'length_and_entry_bounds_verified':True})
   rec['segments'].append({'platform':platform,'segment':si,'decompressed_bytes':size,'blob_entry_count':count,'programs':programs,'boundary':'Compiler text extracted, material-to-variant keyword matching and rendering parity not yet verified.'})
   del data;gc.collect()
 print(label,'programs',sum(len(s['programs']) for s in rec['segments']),flush=True);result.append(rec);del t,blob;gc.collect()
(out/'inventory.json').write_text(json.dumps(result,indent=1),encoding='utf-8')
