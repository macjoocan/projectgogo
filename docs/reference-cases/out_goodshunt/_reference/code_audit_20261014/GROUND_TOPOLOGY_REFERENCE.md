# Ground 原作 코드 번역 및 fixture — 2026-10-14

이 문서는 원본 ARM64 정적 판독이다. ground_reference.py와 ground_fixtures.json은 판독식을 독립 번역한 [계산] 자료이며 게임 실행에서 읽은 메시가 아니다. Android sincosf와 Python trig의 최하위 비트 일치는 미검증, PhysX 실행 없음. source disassembly SHA는 fixture 안에 보존했다.

## 범위와 원본 근거
- InitSurfaceGround 0x21CFC4C: 외곽 8개/초기 삼각형이 요청한 세 함수 이전에 만들어진다. 이것을 빼면 세 함수만으로 초기 topology를 재현할 수 없다.
- RecalculateSurface 0x21D1AD4; UpdateSurfacePosition 0x21D1E60; GroundMesh.Set 0x21D2250.
- shared generic annotation의 set_Item/AsReadOnly 이름은 잘못된 대표 alias였다. ground_aux_02a4a520.txt의 실제 body는 array[index] -> outbuffer memcpy라 get_Item이다. 0x2A4A604는 out/inbuffer에서 해당 index로 쓰는 setter, 0x2A4AFD8는 Count를 삽입 위치로 전달하는 AddRange wrapper. 즉 index0 후처리는 **inner.Add(inner[0])**이지 inner[0] 교체가 아니다.

## 정점 순서 (Y=0)
HalfSize=(hx,hz), corners=[(+hx,+hz),(-hx,+hz),(-hx,-hz),(+hx,-hz)] (X,Z).
Init oldOuterPos/정적 _outerPosBuffer 8개는 아래 순서다 (0x21CFFB8..21D015C):
[(+hx,0),(+hx,+hz),(0,+hz),(-hx,+hz),(-hx,0),(-hx,-hz),(0,-hz),(+hx,-hz)].

Init/Recalculate의 inner[i], i=0..23:
```
a = float32(float32(float32(i/24)*360)*float32(0.01745329238474369))
x = clamp(float32(center.x + float32(radius*cosf(a))), -hx, hx)
z = clamp(float32(center.z + float32(radius*sinf(a))), -hz, hz)
inner.append((x,0,z))
inner.append(inner[0]) // 별도 폐합: 총25개, 25회 sincos 아님
surfaceVertices = corners + inner + oldOuterPos // 4+25+8=37
```
sincosf의 X=cos/Z=sin은 출력 포인터 순서(0x21D1D44..1D6C)로 확인. deg2rad literal RVA0xE0A4A8. sqrt/ray-rect 교차로 outer를 새로 만드는 가정을 넣지 않는다.

## 초기 surfaceTriangles (InitSurfaceGround)
0x21D0340..21D049C: map[i]=2*floor(i/6)+(i%6!=0), i0..23; map[24]=0. outerBase=29.
```
for i=0..23:
  append(4+i,29+map[i+1],29+map[i])
  append(4+i,5+i,29+map[i+1])
```
0x21D04A0..21D0F80는 oldOuterPos를 스캔하여 각 corner의 Z경계/else-if X경계에서 가까운 두 점을 고른다. 비교는 엄격히 더 가까울 때 교체하며 동률은 먼저 나온 점 유지. 순서 TL/TR/BL/BR, 각 corner에서 if z==corner.z / else if x==corner.x. 여기 고정 8점으로 결과가 (3,4)/(1,0)/(5,4)/(7,0)이다.
추가 triangle: (1,32,33),(0,30,29),(2,34,33),(3,36,29).
총 surfaceIndices156=52triangles. 정점 중복 및 0면적 triangle도 원문에 존재하므로 fixture는 dedup/삭제하지 않았다. 중앙 사례 positive32/zero20/negative0. CalculateSurface(0x21D3B10)는 별도 로직을 포함하며 전체를 동일 함수라 취급하지 않았다.

RecalculateSurface는 oldInnerPos만 비우고 다시 만들며 oldOuterPos/기존 surfaceTriangles는 유지한다. surfaceVertices만 corners+inner+outer로 재조립. 따라서 삼각형 topology는 Init에서 확보해야 한다.

## UpdateSurfacePosition (중요)
0x21D2034..21D208C: oldInnerPos **25개 전부**에 diff를 더해 setter. sincos/clamp/outer 갱신 없음. surfaceVertices=corners+이동된 inner+oldOuterPos. surfaceTriangles 유지. radius가 바뀌었을 때의 Recalculate와 합쳐서 매번 clamp하는 구현은 원문과 다르다.
SurfaceFixedUpdate는 radius가 다르면 Recalculate; 같고 diff.sqrMagnitude>0.0001이면 UpdateSurfacePosition(diff) 후 oldCenter 갱신. 경계에서 clamp된 값을 안쪽으로 이동하면 새 중심의 원을 다시 계산한 결과와 달라지는 것을 fixture에서 확인했다. 판독 결과를 '고친' 중심 원으로 대체하지 말 것.
IsNeedToRecalculateSurface 0x21D20F8는 전달된 vertices를 정적 HashSet에 넣고 고유점 수>2를 반환한다. 이전 메시와 비교하는 변화 검사가 아니다. false이면 Set 호출을 생략한다. triangle의 0면적 여부 검사도 아니다.

## GroundMesh.Set
```
n = inputVertices.Count
points = inputVertices + [v + (0,-10,0) for v in inputVertices]
indices = inputTriangles.copy()
for (a,b,c) in inputTriangles:
  indices += (a+n,c+n,b+n) // 바닥 reverse winding
for i=0..n-1:
  prev = (n-1 if i==0 else i-1)
  indices += (prev,prev+n,i+n, prev,i+n,i)
mesh.Clear(); SetVertices(points); SetTriangles(indices,submesh0); MarkModified()
meshFilter.mesh=mesh; meshCollider.sharedMesh=mesh
```
측면은 **모든 입력 정점 배열**의 prev->i 순서이며 ring만 따로 구분한 extrusion이 아니다. corners/폐합 inner/outer 그룹 사이 연결도 원문대로 유지. 37입력 ->74정점, 534indices=178triangles. 원작에는 이 함수의 RecalculateNormals 호출이 없다.

웹 convex-prism adapter는 파생이다. 특히 native 0면적/중복 triangle을 처리할 경우 원문 topology는 따로 보존하고 adapter 필터·사유를 기록해야 한다. 모든 측면/바닥을 무작정 물리 prism 생성 대상으로 삼으면 임의의 추가 지지면이 생길 수 있다. 원본 메시와 prism 접촉 동등성은 미검증.

## halfSize/bounds 생성
RecalculateBounds0x21CF938 -> level static pointer0x417B2C8 -> static+0x20의 LevelBounds(minX,maxX,minY,maxY)를 읽는다. get_LevelBounds0x21D57A4도 같은 pointer/4floats. relocation -> encodedtype0x200135AF -> MetadataRegistration types[39639] -> Il2CppType.data4337=LevelBehavior로 독립 대조. Vector3 type pointer0x4175438 -> runtimeTypes[50767] -> data9861=Vector3, static+0xC는 oneVector.
```
M=max(abs(minX),abs(maxX),abs(minY),abs(maxY))
halfSize = Vector3.one.xy * (M*2.5) // 양축 동일, 독립적인 width/2,height/2 아님
```
0x21CFA08..44의 순서를 유지. fixture halfSize(20,20)는 요청한 **가상 입력**이며 원작 Level5의 저장 default라는 뜻은 아니다. 원점 대칭의 넓은 충돌 지면이고 LevelCenter를 더하지 않는다.
LevelBehavior 초기화0x21D5C0C는 GroundBehavior.Init(5). Init0x21CF900에서 holeResolution=max(input,4) 저장 후 Bounds/CreateTrigger/InitSurface, 다만 이 surface circle은 명시 24표본이다. 저장 holeResolution=5를 circle segment수로 쓰지 말 것.
Bounds 상위 생성은 추가 ground_aux_021dc248.txt에 원문 보존: InitProp compiler MoveNext의 minPos/maxPos에서 center=(min+max)*0.5(0x21DDC0C..64), size=max-min(0x21DDC6C..AC). PlayerSpawnPosition을 Vector3.zero로 두고 min/max를 spawn.x,z를 포함하도록 확장(0x21DDD04..21DDF98), static LevelBounds+0x20/+0x24/+0x28/+0x2C에 minX/maxX/minZ/maxZ 저장(0x21DDFF0..F8). 하지만 min/max 누적 대상 전 분기/빈 레벨 처리 및 런타임bounds 재호출 순서는 아직 완전 번역·검산하지 않았다. 이 범위를 'all renderer.bounds union' 또는 prefab extents 포함이라고 단정하지 않는다. aux의 next-method bound는 공유함수 때문에 실제 함수 끝보다 길 수 있으니 주소 범위로 읽는다.

## fixture 및 검산
python ground_reference.py -> ground_fixtures.json. center(0,0,0), edge(19.5,0,0), corner(19.5,0,19.5), outside(20.5,0,0), 경계clamp 후 diff(-1,0,0) 이동 비교 5개.
정점/인덱스 수·범위/closure/아래10유닛 검산 통과. 중앙 signed top area1596.894171477884 = 40*40 - 24각형 면적, 독립 면적식 대조 통과. 경계 sample의 음수·0면적도 diagnostics에 보존했다. 이 극단 입력이 실제 플레이에서 reachable인지는 미검증. 원작 runtime 메시 bit-exact 판정 아님.
