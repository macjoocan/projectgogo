from pathlib import Path
import json,struct,hashlib,collections,bisect
p=Path(__file__).resolve().parent;rows=[];errors=[]
def decode(d,b):
 offs=d['scale_offsets'];ts=d['tracks'];out=[];fmt=d['scale_compression'];enc=d['key_encoding'];nf=d['frames']
 if enc==2:
  if len(offs)!=len(ts):raise ValueError('per-track offset count')
  for i,t in enumerate(ts):
   a=offs[i]
   if a<0:out.append(dict(bone=t['bone'],identity=True,times=[0.],values=[[1.,1.,1.]],source_offset=a,source_key_count=0));continue
   h=struct.unpack_from('<I',b,a)[0];kf=h>>28;mask=(h>>24)&15;n=h&0xffffff;cur=a+4;assert n>0 and (mask&7)==7
   mins=[0.,0.,0.];ranges=[0.,0.,0.]
   if kf==3:
    for axis in range(3):mins[axis],ranges[axis]=struct.unpack_from('<2f',b,cur);cur+=8
   values=[]
   for j in range(n):
    if kf in (0,1):v=list(struct.unpack_from('<3f',b,cur));cur+=12
    elif kf==2:v=[x-255. for x in struct.unpack_from('<3H',b,cur)];cur+=6
    elif kf==3:
     x=struct.unpack_from('<I',b,cur)[0];cur+=4;ints=[x&1023,(x>>10)&2047,(x>>21)&2047];v=[(ints[k]/(511. if k==0 else 1023.)-1)*ranges[k]+mins[k] for k in range(3)]
    elif kf==6:v=[1.,1.,1.]
    else:raise ValueError('unsupported per-track format '+str(kf))
    values.append(v)
   cur=(cur+3)&~3;assert cur<=len(b)
   if n>1 and mask&8:
    code='H' if nf>255 else 'B';size=2 if nf>255 else 1;assert cur+size*n<=len(b);times=list(struct.unpack_from('<'+code*n,b,cur));assert times==sorted(times) and max(times)<nf
   else:times=[j*(nf-1)/max(1,n-1) for j in range(n)]
   out.append(dict(bone=t['bone'],identity=all(v==[1.,1.,1.] for v in values),times=times,values=values,source_offset=a,source_key_count=n,per_track_format=kf))
  return out
 identity_single=(fmt==6 and len(offs)==len(ts) and all(x==-1 for x in offs))
 if len(offs) not in (0,len(ts)*2) and not identity_single:raise ValueError('scale offset count does not match raw bone track count')
 for i,t in enumerate(ts):
  a,n=offs[2*i:2*i+2] if offs and not identity_single else (-1,-1)
  if a<0 or n<=0:
   out.append(dict(bone=t['bone'],identity=True,times=[0.0],values=[[1.0,1.0,1.0]],source_offset=a,source_key_count=n));continue
  if fmt not in (0,6):raise ValueError('unsupported compression '+str(fmt))
  if enc not in (0,1):raise ValueError('unsupported key encoding '+str(enc))
  if fmt==6:values=[[1.,1.,1.] for _ in range(n)];end=a
  else:
   assert a+12*n<=len(b);values=[list(struct.unpack_from('<3f',b,a+12*k)) for k in range(n)];end=(a+12*n+3)&~3
  if n==1:times=[0.0]
  elif enc==1:
   code='H' if nf>255 else 'B';size=2 if nf>255 else 1;assert end+size*n<=len(b);times=list(struct.unpack_from('<'+code*n,b,end));assert times==sorted(times) and min(times)>=0 and max(times)<nf
  else:times=[k*(nf-1)/(n-1) for k in range(n)]
  out.append(dict(bone=t['bone'],identity=all(v==[1.,1.,1.] for v in values),times=times,values=values,source_offset=a,source_key_count=n))
 return out
if __name__=='__main__':
 for f in sorted((p/'raw').rglob('*.source.json')):
  try:
   d=json.loads(f.read_text());bf=f.with_name(f.name.replace('.source.json','.compressed.bin'));b=bf.read_bytes();tracks=decode(d,b);o=f.with_name(f.name.replace('.source.json','.scale.json'));r=dict(source=str(f.relative_to(p)),compressed_sha256=hashlib.sha256(b).hexdigest(),compression=d['scale_compression'],key_encoding=d['key_encoding'],frames=d['frames'],tracks=tracks);o.write_text(json.dumps(r,separators=(',',':')),encoding='utf-8');rows.append(dict(path=str(o.relative_to(p)),nonidentity_tracks=sum(not x['identity'] for x in tracks),compression=d['scale_compression'],key_encoding=d['key_encoding'],sha256=hashlib.sha256(o.read_bytes()).hexdigest()))
  except Exception as e:errors.append(dict(path=str(f),error=str(e)))
 summary=dict(sequences=len(rows),nonidentity_sequences=sum(x['nonidentity_tracks']>0 for x in rows),nonidentity_tracks=sum(x['nonidentity_tracks'] for x in rows),formats=dict(collections.Counter(x['compression'] for x in rows)),encodings=dict(collections.Counter(x['key_encoding'] for x in rows)),errors=errors)
 (p/'scale_decoder_manifest.json').write_text(json.dumps(rows,indent=1));(p/'scale_decoder_verification.json').write_text(json.dumps(summary,indent=1));print(summary)
