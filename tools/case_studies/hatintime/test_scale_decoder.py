from decode_scale_tracks import decode
import struct
def d(enc,fmt,off,nf=4):return dict(scale_offsets=off,tracks=[dict(bone='b',scale=[])],scale_compression=fmt,key_encoding=enc,frames=nf)
assert decode(d(0,6,[-1,-1]),b'')[0]['identity']
r=decode(d(0,0,[0,1]),struct.pack('<3f',1,2,3))[0];assert r['values']==[[1,2,3]]
b=struct.pack('<6f',1,1,1,2,2,2)+bytes([0,3]);r=decode(d(1,0,[0,2]),b)[0];assert r['times']==[0,3]
b=struct.pack('<6f',1,1,1,2,2,2)+struct.pack('<2H',0,769);assert decode(d(1,0,[0,2],770),b)[0]['times']==[0,769]
b=struct.pack('<I3H',0x27000001,256,256,256)+b'\0\0';r=decode(d(2,6,[0]),b)[0];assert r['values']==[[1,1,1]] and r['per_track_format']==2
b=struct.pack('<I6fI',0x37000001,1,0,2,0,3,0,0);assert decode(d(2,6,[0]),b)[0]['values']==[[1,2,3]]
try:decode(d(0,0,[4,100]),b'\0'*12)
except (AssertionError,struct.error):pass
else:raise AssertionError('out of bounds accepted')
print('7 scale decoder fixtures PASS')
