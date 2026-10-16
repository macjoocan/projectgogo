import struct
M=(1<<64)-1
P1,P2,P3,P4,P5=11400714785074694791,14029467366897019727,1609587929392839161,9650029242287828579,2870177450012600261
def rol(x,n):return ((x<<n)|(x>>(64-n)))&M
def xx64(b):
    def rnd(v,x):return rol((v+x*P2)&M,31)*P1&M
    p=0
    if len(b)>=32:
        v=[(P1+P2)&M,P2,0,(-P1)&M]
        while p+32<=len(b):
            v=[rnd(a,x) for a,x in zip(v,struct.unpack_from('<4Q',b,p))];p+=32
        h=sum(rol(v[i],n) for i,n in enumerate([1,7,12,18]))&M
        for x in v:h=((h^rnd(0,x))*P1+P4)&M
    else:h=P5
    h=(h+len(b))&M
    while p+8<=len(b):h=(rol(h^rnd(0,struct.unpack_from('<Q',b,p)[0]),27)*P1+P4)&M;p+=8
    if p+4<=len(b):h=(rol(h^(struct.unpack_from('<I',b,p)[0]*P1&M),23)*P2+P3)&M;p+=4
    while p<len(b):h=rol(h^(b[p]*P5&M),11)*P1&M;p+=1
    h^=h>>33;h=h*P2&M;h^=h>>29;h=h*P3&M;return h^(h>>32)
def murmur(b):
    m=0xc6a4a7935bd1e995;h=len(b)*m&M;p=0
    while p+8<=len(b):
        k=struct.unpack_from('<Q',b,p)[0]*m&M;k^=k>>47;k=k*m&M;h=(h^k)*m&M;p+=8
    if p<len(b):h^=int.from_bytes(b[p:],'little');h=h*m&M
    h^=h>>47;h=h*m&M;return h^(h>>47)
if __name__=='__main__':
    for s in ['Duration','SpeedUp','AnimationKey','DamageId','Filter']:
        print(s,hex(xx64(s.encode())),hex(murmur(s.encode())))
