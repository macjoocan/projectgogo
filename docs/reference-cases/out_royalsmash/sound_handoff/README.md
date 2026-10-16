# Royal Smash 사운드 구현 인수인계

작성: 2026-09-16 / 대상: Claude Code의 로컬 레퍼런스 프로토.
이번 전달은 **가이드와 근거 정리만**이다. 게임 코드 수정, 신규 음원 추출, 청음, 브라우저 재생 검증은 하지 않았다.

## 1. 결론과 확보 상태

대포 → 오브젝트별 파괴 → 타격 순서로 붙일 수 있다. 먼저 음원과 이벤트를 분리하고, 같은 충돌에서 소리가 중복되는 것을 막는다. 물리 수치·파괴 임계값은 사운드 작업으로 변경하지 않는다.

- [원작값·정적 참조] `../destruction_fx_audit/original_effects.json`: 오브젝트 139종의 Feedback 참조와 대포/공 참조. 실행 시 호출 여부·믹싱 값까지 확정한 자료는 아니다.
- [로컬 파일 확인] `../RoyalSmash_assets/audio/`에 WAV 11개. PCM 헤더 및 선언된 프레임 길이를 검사했다. 청음·브라우저 디코딩은 별도 필요하다.
- `cannon_blast.wav`: mono / PCM 16-bit / 44,100 Hz / 약 0.936초. 동명 SfxAsset이 발사 Feedback에 연결되어 있다. **SfxAsset 내부 AudioClip PPtr과 이 WAV의 일대일 연결은 이번에 추가 검증하지 않았다.**
- 나머지 파일: `gameplay_music_loop`, `main_music_loop`, `level_fail`, `level_win`, `streak_moves_hit_ui`, `ui-button-click`, `ui-button-click_2`, `water_plip`, `water_splash`, `welldone_firework` (모두 `.wav`). 이름은 용도의 단서일 뿐 실제 이벤트 연결 근거는 아니다.
- 확인한 `../cdn_extracted/RoyalSmash_CDN_assets.zip`에는 WAV/OGG/MP3/FSB/AAC/FLAC 항목이 없다. **전체 로컬 컨테이너에 음원이 없다는 뜻은 아니다.**
- 아래 블록별 SfxAsset은 확보했으나 해당 클립 파일 위치·선택 방식·volume/pitch는 미확정. 파일명을 추측해 없는 URL을 구현하지 않는다.

기계 판독 자료: [sound_event_map.json](sound_event_map.json). 139개 정확한 ID마다 `hit_sfx`/`break_sfx`의 APK·파일·path_id를 담았다. `existing_wavs`에는 파일 경로·SHA256·길이·PCM 검증 상태가 있다. 재생용 manifest가 아니라 **근거용 색인**이다.

## 2. 원본 연결표

아래는 저장된 Feedback 참조이며 실제 재생 관측 결과가 아니다. `null`과 컴포넌트 부재를 구분한다.

| 대상 | 수 | hitFeedback.sfx | explodeFeedback.sfx |
|---|---:|---|---|
| Can | 11 | can_hit | can_break |
| JamJar | 18 | null | jar_break |
| Stone + Column | 20 | stone_hit | stone_break |
| BoxSquare + ColorBoxSquare + PiggyBox | 51 | box_hit | box_break |
| Ice | 10 | ice_hit | ice_break |
| BoxCylinder + Wood + Bouncer | 20 | boxCylinder_hit | boxCylinder_break |
| TNT | 2 | can_hit | tnt_explode |
| Hammer, Blocker 3종, Table 2종, Pinata | 7 | 이 common 경로로 미확인 | 이 common 경로로 미확인 |

- Bouncer에 파괴음 참조가 있어도 파괴 가능하다는 뜻은 아니다. 실제 파괴 전환 없는 상태에서는 재생하지 않는다.
- Jar의 hit SFX null은 이 Feedback 필드의 사실이다. 임의 유리 타격음은 [자체] 추가이지 원본 복원이 아니다. 액체 분출 VFX가 있다고 `water_splash`를 자동으로 연결하지 않는다.
- 대포 `shootFeedback.sfx`: `cannon_blast`, `UnityDataAssetPack.apk / assets/bin/Data/sharedassets2.assets / path_id 81`, class `SfxAsset`. 출발점은 `level2 / BallController / path_id 124`.
- 일반 Ball의 `firstImpactFeedback.sfx`와 `groundFeedback.sfx`는 null. 모든 공 충돌에 별도 폭발음을 무조건 더하지 않는다.
- HapticTimelineAsset은 음원이 아니다. 진동 참조를 WAV처럼 취급하지 않는다.

## 3. 구현 순서와 코드 연결 지점

프로토 경로: `C:\00.SVN\MiniApp\_reference\royalsmash`. 구현 전에 현재 diff를 확인할 것. 기존 FX 검토 시점의 결함이 이미 수정됐을 수 있다. 이번 `web`의 JS/HTML 검색에서는 AudioContext/new Audio/playSfx 및 대표 효과음 키 연결이 발견되지 않았다(프로젝트 전체의 오디오 부재를 증명하는 검사는 아님).

### 1차: 발사음과 최소 오디오 관리자

1. [자체 설계] `web/audio.js` 같은 독립 모듈에 로드/디코드 캐시, `unlock`, `play`, `setMuted`, `dispose`를 모은다. 실제 파일명은 프로젝트 규칙에 맞춘다.
2. 대포 WAV를 레퍼런스 전용 정적 에셋 경로에 등록한다. 로컬 디스크 절대 경로를 브라우저 URL로 쓰지 않는다. 현재 정적 서버의 공개 루트 기준 URL을 사용한다.
3. `web/main.js`의 `fireAt`에서 조준·탄수·발사 가능 여부를 통과하고 공 생성/탄수 차감이 확정되는 지점에 발사 이벤트 하나를 낸다. 입력 pointerdown 자체에는 발사음을 달지 않는다.
4. 머즐 FX, 반동 애니메이션과 같은 발사 이벤트를 소비하게 하되, VFX 함수 호출 횟수에 소리 재생을 종속시키지 않는다.
5. 무음 토글을 넣고 실패 시 게임은 계속 진행한다. 음원이 늦게 로드됐다고 과거 발사음을 뒤늦게 몰아 재생하지 않는다.

### 2차: 블록별 파괴와 타격

1. 아래 4절에 따라 필요한 SfxAsset의 실제 클립을 먼저 확인한다. 빠진 음원은 명시적으로 `unresolved`로 두고 무음 처리한다.
2. `breakBody` 등 **실제 살아 있음 → 파괴됨 전환**에 `objectBroken` 이벤트를 한 번 낸다. 파편마다 소리를 내지 않는다.
3. `handleContacts`의 유효 충돌 판정에서 `objectImpact`를 낸다. 초기 배치/안정화, 지속 접촉, 이미 제거된 오브젝트는 제외한다. 오디오 때문에 충돌 판정식을 바꾸지 않는다.
4. 같은 충돌/오브젝트에서 파괴가 확정되면 hit보다 break를 우선하는 정책을 적용한다. 이는 [자체] 중복 방지 정책이며 원본 믹싱 규칙 미확정이다.
5. TNT는 `detonateTnt`의 실제 최초 폭발 전환에 `tnt_explode` 하나. 같은 TNT의 일반 break 사운드와 이중 호출하지 않는다. 연쇄의 다른 TNT는 각자 고유 ID로 이벤트를 낸다.
6. Pinata 등 미확인 계열은 근거 없는 매핑을 추가하지 않는다. 필요하면 명시적인 [자체] 대체음으로 별도 승인한다.

권장 이벤트 계약 [자체]: `{ eventId, levelGeneration, entityId, kind, objectId, simulationTime, impactStrength? }`. 엔티티 ID 재사용 시 레벨 세대 값까지 중복 키에 포함한다. 음원 키는 `objectId` 정확 매핑으로 고르고 재질 이름의 부분 문자열로 추정하지 않는다. 오디오 소비자는 질량/속도/점수/파괴 여부를 변경하지 않는다. 헤드리스 테스트에서는 로그만 남기는 무음 소비자를 쓴다.

주의: 19:58 FX 검토에서 TNT는 detonated만 켜지고 제거/점수 반영이 빠지는 경로, Pinata는 pop과 break 임계값 불일치, `shockRing` 별칭은 impact FX 중복이 있었다. [이전 검토](../destruction_fx_audit/README.md)를 참고하되 최신 코드에서 재확인한다. 이를 사운드 코드의 강제 제거/임계값 변경으로 숨기지 않는다. `burst`/`shockRing` 내부에 오디오를 붙이지 말 것.

## 4. 아직 없는 클립을 찾는 방법 — 로컬만

1. `sound_event_map.json`의 SfxAsset 원본 위치부터 연다. 필요한 참조 대상만 읽고 모든 번들을 동시에 메모리에 올리지 않는다.
2. SfxAsset 타입/필드를 해석해 AudioClip 참조, 여러 클립 배열, 랜덤 선택, gain/pitch 설정 유무를 확인한다. **SfxAsset 한 개 = 단일 동명 WAV**라고 가정하지 않는다.
3. PPtr는 `(APK/컨테이너, SerializedFile, path_id)`로 해석한다. `m_FileID > 0`은 해당 파일의 externals를 따라간다. path_id만 전역 검색하지 않는다.
4. AudioClip의 스트리밍 리소스 source/offset/size를 찾아 해당 번들 내부 `.resource`부터 확인한다. 다른 CAB 리소스를 임의 대입하지 않는다.
5. 기존 levelscope 에셋 추출 경로를 재사용해 WAV로 확보하고, 실패 시 원본 FSB 및 실패 이유를 보존한다. 추출 실패와 파일 부재를 구분한다.
6. 최종 manifest에는 `audioKey`, `clipPaths`, 원본 참조, SHA256, 길이/채널/샘플레이트, 원본 gain/pitch 또는 미확정, 사용 범위를 넣는다. 같은 이름·다른 파일 충돌을 확인한다.

이번 전달은 추출 지침이다. 추가 추출은 아직 실행하지 않았다. 게임 실행, CDN 추가 요청, 로그인, 인증·보호 기능 우회는 필요 작업에 포함하지 않는다.

## 5. 웹 재생 및 믹싱 정책

- 사용자 제스처에서 AudioContext를 생성/재개하고 상태·실패를 처리한다. 짧은 효과음은 미리 디코딩한 버퍼를 재사용하고 무음/볼륨 컨트롤을 제공한다. [MDN Web Audio 권장 사항](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Best_practices)
- AudioBuffer는 공유할 수 있지만 AudioBufferSourceNode는 한 번만 start할 수 있다. 재생마다 새 소스 노드를 만들고 종료 시 활성 목록/연결을 정리한다. [MDN AudioBufferSourceNode](https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode)
- [자체] 초기에는 2D SFX로 시작한다. 3D 거리 감쇠·팬·pitch 랜덤화는 원본 근거가 나오거나 별도 연출 조정할 때 추가한다.
- [자체·초기 제안값] 동시 SFX 상한 8개, 동일 오브젝트 타격 cooldown 80ms. 발사·폭발·파괴를 타격보다 우선한다. 이 값들은 원본에서 추출한 값이 아니며 청음 후 조정한다.
- [자체] 채널 예산 초과 시 조용한/낮은 우선순위 타격부터 생략한다. 연쇄 TNT는 이벤트 수와 실제 voice 수를 따로 기록한다. 단순히 모든 소리를 풀볼륨 합산하지 않는다.
- [자체] masterGain 초기값 0.5에서 청음 시작. 파일별 loudness가 다르므로 이것이 안전한 최종 믹스나 원본 음량이라는 뜻은 아니다. gain/voice/cooldown 정책은 하나의 설정 파일에서 관리한다.
- [자체] 숨김/일시정지 시 재생 중 효과음을 정리하고 과거 이벤트 큐를 버린다. 복귀해도 사용자 무음 설정을 유지한다. 레벨 재시작 시 중복 키·오디오 세션을 정리한다.
- [자체] 음원 미확보, 404, 디코드 실패, autoplay 차단은 개발 로그에 구분하고 게임 로직은 멈추지 않는다. 오디오 RNG가 게임의 결정적 RNG를 소비하지 않게 한다.
- BGM/승패/UI는 2차 이후. 기존 WAV 이름만 보고 루프 경계·전환 타이밍·원본 사용 상황을 확정하지 않는다. 특히 `water_splash`를 Jar에 임의 연결하지 않는다.

## 6. 완료 판정과 답장 요청

아래는 앞으로 수행할 테스트이며 이번 전달에서 통과했다고 주장하지 않는다.

| 검증 | 기대 결과 |
|---|---|
| 유효 발사 1회 / 무효 입력 | cannon 이벤트 1 / 0 |
| 한 오브젝트 파괴, 파편 여러 개 | break 이벤트 1, 파편 수만큼 중복 없음 |
| 동일 접촉 지속 | 프레임마다 반복 재생하지 않음 |
| hit와 break 동시 발생 | 정책대로 break 우선, 중복 키 로그 확인 |
| TNT 2개 연쇄 | 서로 다른 explosion 이벤트 2, 중복 0; 제거/점수 검증은 별도 |
| Jar | 확인된 jar_break만 연결; 근거 없는 hit/water 사운드 없음 |
| 미확인/미확보 음원 | 무음 + 식별 가능한 개발 로그, 물리 정상 |
| 무음/탭 전환/레벨 재시작 | 무음 유지, 이전 레벨 소리 지연 재생 없음 |
| 동시 충돌 스트레스 | 설정 voice 상한 준수, 종료 후 활성 voice 0 |
| 브라우저/모바일 | 실제 대상 브라우저의 첫 제스처·디코딩·음소거·복귀 확인 |
| 최종 청음 | 발사/충돌 영상과 동기, 찢어짐/과한 반복/상대 음량을 사람이 승인 |

참조 음원은 `_reference` 범위에 격리하고 배포 빌드에 자동 포함하지 않는다. 배포용은 사용 권한이 확인된 음원으로 교체하며, 파일 확보 자체를 배포 허가로 간주하지 않는다.

Claude 답장에는 ① 변경 파일 ② 실제 연결한 이벤트/오브젝트 목록 ③ 미확보 클립 ④ 자동 검증 결과 ⑤ 청음/브라우저 검증 여부를 구분해 남겨 주세요. 우편함에 이 문서가 있다는 사실과 실제 구현·읽음 확인은 별개다.
