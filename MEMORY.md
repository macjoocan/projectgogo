# 공유 프로젝트 메모리 — Claude Code / Codex

갱신: 2026-09-17. 이 파일은 두 도구가 읽는 공유 프로젝트 메모리다.
별도 서비스의 내장 메모리를 동기화하거나 이미 실행 중인 Claude에 메시지를 보낸 것은 아니다.
최근 작업의 빠른 요약은 이 파일, 상세 이력은 `HANDOFF.md`, 게시 증거는 아래 PUBLICATION 문서를 읽는다.

## 작업 재개 요약 — 2026-09-17 정리

- 재사용 노하우는 [ANALYSIS_KNOWHOW.md](ANALYSIS_KNOWHOW.md)에 모았다. 참조/컬렉션 식별, 바이너리 경계, 부모 TRS, 셰이더 후보와 런타임 선택, 실제 물리 소비자, 이펙트 상태 완료, 메모리 제한, 우편함 재검증을 다룬다.
- **대포 기준 Y 확인 완료:** 9/16 21:45 감사에서 CannonBase4.44와 LevelSpawnPos1은 형제라 +1 중복 금지. 저장 공 생성점 Y4.076285는 조준/애니메이션 후 불변값이 아니다. 최신 검사 당시 proto cannonFor도4.44. 해머 설계/충돌 일치 판정은 미완료.
- **볼 물리 최신 수정은 재검증 대기:** 9/16 21:18에서 directHit 제외/조건부1.2는 통과했고 표면·Bouncer·저속 차이를 발견했다. 21:29 Claude가 수정했다고 답신했으나 이후에는 대포만 검사했다. 아래 과거 실패를 현재도 남아 있다고 단정하거나, 답신만으로 통과 처리하지 않는다.
- 원작 런타임 Config 선택값, 감속/retention 소비 규칙, 유효 공 생성점/발사 계산 및 해머 동시 궤적은 남은 확인 항목. 700레벨 튜닝은 검증 근거 정리 전 보류였으며 이번 문서 정리에서 재개하지 않았다.
- 다음 검증에는 현재 함수와 해시를 다시 읽는다. `review_ball_revision_20260916.mjs`는 당시 알려진 실패도 assert하므로 수정된 코드에 그대로 돌려 나온 실패를 새 회귀로 오해하지 않는다.
- **Git 범위:** 사용자 지정 저장소 `https://github.com/macjoocan/projectgogo`에 공유 문서/정리된 노하우만 반영한다. 기존 코어·테스트·설정 수정은 별도 로컬 작업으로 보존한다. `../out_*`, 원본 패키지, 분석용 의존성/덤프/이미지/전체 증거는 Git에 포함하지 않으므로 다른 PC에서 경로만으로 재현되지는 않는다.
- 아래 기록은 각 날짜의 검사/전달 이력이다. `answered`·파일 게시가 상대의 읽음/구현/검증 완료를 뜻하지 않는다. 마지막 원작/프로토 감사는9/16이며9/17에는 문서 정리만 했다.

## 확인·전달 이력 — 날짜별 스냅샷

**Royal Smash 대포 월드Y (2026-09-16 21:45):** `../out_royalsmash/cannon_world_analysis/README.md`. 원본CannonBase62월드4.44,LevelSpawn48월드1은Arena59형제라+1중복금지. BallSpawnPos80저장월드Y4.076285/Z-25.705237,조준anchor93 Y4.009927,VFX87 Y4.246886분리. TRS3참조Matrix4교차검증. 최신proto cannonFor이미4.44;targetY8발사공startY4.930358/Z-20.100346(자체Z/포구3영향). 원작native수평속력기준탄도vsproto전체속력135차이,발사Gravitytrue/VelocityChange2확인. 낮은대포가원인이라는근거없음,해머원작런타임/완료미확정. mailbox214501→122935answered. 코드미수정/볼최신수정재검증별도.

**Royal Smash 볼 수정 재검토 (2026-09-16 21:18):** `../out_royalsmash/ball_revision_review_20260916/README.md`. 최신 웹/Sim 실제 handler+Rapier 11개 fixture묶음. directHit 제외/조건부1.2/Jar18+Tnt2전달/Impulse질량역비례/빠른접촉1회 통과. 표면만반경안 박스누락(프로토0vsUnity문서기대충격량.75),Bouncer 웹20→27vsSim20,저속impact.6 웹폭발1/Sim0 재현. decay10미소비,원작retention배열대응없음,반경cbrt(power)자체유지. 코드미수정/원작미실행/튜닝보류. mailbox211824게시·115857answered,대포Y는별도미해결.

**Royal Smash 메인144 분홍 기둥 판정 (2026-09-16 20:56):** `../out_royalsmash/level144_spawn_audit/README.md`. 사용자발사0스크린샷검토, 원본main144해시재검증/Bouncer8모두identity회전. _3/_4 프리팹Mesh자식y=-1.5/-2,콜라이더루트중심인데프로토rawminY0+h/2로중심을1.5/2올림(원본8.5→10,4→6;공통spawn제외). 생성높이불일치확정,0.5초spawnsettle후기울어고정은유력경로/A-B미실행. 원작도눕혀저술했다는판정불가;원작런타임미관측. mailbox205646전달/프로토미수정.

**Royal Smash ForceMode/설정 배율 확인 (2026-09-16 20:46):** `../out_royalsmash/force_mode_analysis/README.md`. 원본 Ball 첫접촉 native호출 Impulse1 확정(0x382AEE4→0x7A9E990). Controller.OnEnable Config<int> first_contact_force_multiplier/ball_mass_multiplier fallback1,flags10; ELF relocation→metadata 키 확인. 원작 force만 배율·radius저장값 직접 사용. level별power/radius*cbrt(power)는 자체 유지, 원작실효Config값미확정. LighterGameplay 설정시upwards1.8배/defaultfalse 확인. 직접맞은Obstacle 제외·collider표면범위와proto중심점 차이후속. mailbox204624,요청113506answered. 코드미수정/튜닝보류.

**Royal Smash 첫 접촉 폭발 저장값 확정 (2026-09-16 20:30):** `../out_royalsmash/first_contact_verification/README.md`. APK 재판독: BallController124→Ball GO40→Core.Ball MB82. Force3/Radius2/Upwards.5/ExploderMultiplier1.2/minSpeedToDecay10; object offsets68/72/76/80/200와 raw hex 제공. Controller176/Ball204 bytes 전체 경계 및 이전FX추출값 일치. 현프로토9/2.6/.8/min3과 다름. mailbox203000 답장, 요청104933 answered. 일반 공 저장값만 확정, runtime 배율/ForceMode/전체동등성 미검증. 프로토 수정 없음,700레벨 튜닝 보류 유지.

**Royal Smash 사운드 가이드 전달 (2026-09-16 20:17):** `../out_royalsmash/sound_handoff/README.md`와 `sound_event_map.json`. 기존 원본 Feedback139종 정확 ID/참조, 기존 WAV11개 PCM 길이 검증 통과. cannon_blast WAV 약.936초 확인, SfxAsset→클립 연결·블록별 음원·gain/pitch·청음은 미확정. 이벤트 연결/중복방지/로컬 클립 추적/검수 가이드만 작성, 프로토 미수정. mailbox201738 open으로 게시(읽음 확인 아님). 기존 CDN assets ZIP 오디오 항목0은 전체 로컬 부재 판정이 아님.

**Royal Smash 파괴·대포 FX 검토 (2026-09-16 19:58):** `../out_royalsmash/destruction_fx_audit/README.md`. 원본139종 effect/ObstacleCommon PPtr·Feedback·파편,53이미터 확보/오류0. Jar18종 6색PS_Jar_* 액체/Glass 누락(프로토dust만), TNT연쇄2개detonated하지만dead/hitfalse·destroyed0·연쇄VFX누락, Pinataimpact9 pop하지만미제거. 일반Ball firstImpactVfx=null인데protoBigBallimpact2회; 대포muzzle71실제생성, animation/SFX/trail미연결. 핵심정정minMaxState3=TwoConstants/2=TwoCurves(기존반대해석). Can11종brokenpiece1은기존mesh재사용하므로“broken메시없어파괴없음”전제불가. fragment7종그룹개수불일치/8개상한/scale차이. mailbox195800 전달. 원작/브라우저실행·프로토수정없음. 실행probe는VMconsumer/Three객체,시각일치미검증. 이전물성은Claude수정중이나이번은FX범위.

**Royal Smash 최종 재검증 + 기본 물성 신규 원본 (2026-09-16 19:35):** `../out_royalsmash/physics_recheck_20260916_1920/README.md`가 최신. 기존 P0 timestep/첫공폭발 해결, mass override1230 통과; actual ball speed135/mass1.2/radius.3283/gravity1 확인. 단, 기본값은 동일하지 않음: APK prefab139종 매칭/Obstacle133/rootRB132 확보, 실제Sim 단위fallback mass132종 전부>1%차이, df132/133·b37차이. 원본 ComputeMass=size*localScale product*density+additiveMass에1.1,최소.25;native132와교차확인. Jar1.21→proto1, Blue3.025→2.596, Cone.9075→.266. Pinataad0 44건·stabilizefalse Fixed·RAF preSpeed/wake 등잔존. mailbox193500 답장 게시, 새102817요청 answered. 원작·브라우저 실행/프로토 수정 없음. 실제원작runtime동등성false. 종전19시 P0미해결기록은 과거이력이다.

**Royal Smash 수정 후 물리 재검증 (2026-09-16 19시):** `../out_royalsmash/physics_recheck_20260916/README.md`. actualSim mass1,230건오차0(종전601해소),gravity-24/공통blast통과. 그러나실제worlddt1/60인채.0125누산기로돌아시간1.333배,첫공폭발웹/Sim식다름. ad0Pinata44건등잔존. 새원본level2BallController124 serializedInitialSpeed=135,Spin10/25,AimContactOffset.3와BallSpawnPos/BallPrefab참조확인. 실제참조공Rigidbodygravitytrue,mass1.2,rootscale.67/radius.49. speed42→135격리시험직선편차.626→.0584유닛이라사용자“원작직선느낌”에유력근거;runtime발사설정미관측. mailbox190800재검증답장게시. 프로토미수정/원작실행없음.

**Royal Smash 물리·조명 후속 및 원본 사진 검토 (2026-09-16):** `../out_royalsmash/physics_application_audit/README.md`와 `visual_reference_review/README.md`. 물리 우편함 요청 answered, 우선답장181200 게시. 원본 저장 gravity-24/fixed.0125(80Hz)/solver35·7. 실제 Rapier/Sim 진단 main1,230 override 중 mass601건 불일치, RAF당1step 시간축 문제, web/Sim blast불일치, ad0 Pinata44건미적용. 수정은 안 함. 생성자값과최종실효값구분. 사용자원본19장모두검토/그대로보존. SH27계수는 기존파일에있으며APK재독해일치(ambient_probe_verified.json); mode3Flat/실효probe선택미확정. 공통shadow수신재질기반제안·spec색값·사진별목표를별도답장181800으로전달. 두runtime verified플래그false. 프로토미수정/원작실행·CDN없음. 우편함게시≠읽음/구현확인.

**Royal Smash 마스크/대포 및 과밝음 답변 (2026-09-16):** 사용자 지정 파일 우편함 `../out_royalsmash/mailbox/README.md`로 전환. `to-claude/20260916-174416-mask-cannon-brightness.md` 답장 작성, 원본 질문 answered. Jar_Red60/Purple61의 mask는 BaseMap UV의 R을 연속 mix; Blue58에는 mask 없음. Cannon193은 Multiply Lighten의 **1+pow(sample,5.1)*7.9**, LightMap은sample*.8+.2를 곱함; wrap1, static MatCap. 26후보 해시/핵심분기 검증 통과. 원본 Toony26재질의 누락된 ramp/SColor/HColor/IndirectIntensity 등을 `shader_variant_analysis/toony_lighting_source_params.json`에 추출. 프로토 읽기 전용 확인: Blue MatCapColor 의도적 생략 및 Toony 조명 전 base를 최종 출력하는 차이. 실제 화면 개선 미검증, 프로토 미수정. 기존 릴레이는 종료되어 ENOINBOX가 보고됨; 파일 전달은 읽음/구현 확인이나 상시감시를 뜻하지 않음.

**Royal Smash 변형 키워드/패스 매핑 후속 완료 (2026-09-16):** `../out_royalsmash/shader_variant_analysis/README.md`가 현행 정본이다. GLES287개 전부 blob 키워드↔parsed pass keyword indices 교차 검증, 재질54개 주 패스 후보 확보. 새 인덱스 `variant_keywords_mapped=true`, **`runtime_selection_verified=false` 유지**. 원본 Mobile_RPAsset은 캐스케이드1/그림자거리60/소프트 그림자 지원이며 일반 QualitySettings의 2/40과 구분한다. GameplayCamera renderShadows=true. 저장 설정 유지 및 additional/main/soft 전역 키워드 조합이라는 조건에서 ColorBox Blue Toony58, TableSquare Omni202; 실제 실행 선택 확정 아님. 이전41은 SPECULAR 없는 설명용 표본,152는 전역 광원 키워드 없는 후보. 검증 VALIDATION.json 통과. 동일 Claude에 메시지 `1c10e3db-7da9-46db-a085-dc5139ff7e10` queued(읽음/구현 확인 아님). 게임·에뮬레이터·CDN 미접속, 프로토 코드 미수정.

**Royal Smash 실제 GLSL/블록 텍스처 추가 (2026-09-16):** `../out_royalsmash/shader_program_analysis/README.md`, `../out_royalsmash/block_texture_handoff/README.md`.
원본 GLES 압축 blob에서 길이 prefix+entry 경계 검증 GLSL 텍스트 OmniShade236/Toony51개 확보(HLSL 원문 아님, 런타임 변형 매칭 미완). OmniShade 표본 MatCap은 pow(sample,contrast)×color×brightness로 중간 회색 정규화와 다름.
ColorBoxSquareBlue는 Toony, BaseColor와 별개로 TCP2_MATCAP/UseMatCap1/MatCapType1/CB_blue 참조 있음. BaseColor-only 해석 재점검 필요. 프로토51개 재질명→원본54오브젝트→텍스처 참조104/104 해석, PNG73개/오류0 및 검증ZIP 제공. 실제 화면 동일성 미검증, 게임 코드 미수정.

**Royal Smash 재질·셰이더·카메라 위치 확인 (2026-09-16):** `../out_royalsmash/visual_settings_analysis/README.md`와 근거 JSON.
원본 Material946/Shader113 + 기존 CDN Material49/Shader38 오브젝트의 값/메타데이터 저장. TableSquare의 정확한 외부 참조는 OmniShade/Standard URP + Table_Square_v02 + 2_matcap. 옛 rs_export2 `.shader`26개 모두 DummyShaderTextExporter이므로 실제 효과 구현으로 쓰면 안 된다.
원본 level2 GameplayCamera(Camera95/GO9/Transform56): 원근 FOV30°, 위치(0,8.85,-40), X회전 약+5°, near.3/far1000. level1 메뉴 MainCamera는 직교size41로 구분. 런타임 화면비/줌/흔들림 변경 미검증.
Material/Shader/Camera 읽기 오류0; MonoBehaviour 커스텀 payload1,727개는 타입트리 부족 실패를 명시하고 헤더 참조만 별도 확인. 온라인/게임 실행 및 게임 프로젝트 변경 없음.

**Royal Smash 레벨 구조 분석 완료 (2026-09-16):** `../out_royalsmash/level_structure_analysis/README.md`.
원본 APK에서 컬렉션별 1,560개 재독해/기존 감사 내용 해시 전부 일치. 오브젝트 150,648개, Entity Id 139종, Custom leaf 경로 52종.
루트 8필드, Id/Position/Quaternion/선택 Scale/Custom 구조. 원본 enum은 Normal0/Hard1/SuperHard2, PhysicsQuality High0/Medium1.
메인1–19 Normal/20 Hard 이후 및 루프 전체에서 끝자리4·7 Hard/0 SuperHard 편성이 전수 일치. Custom에 물리 설정 명시 오브젝트2,491개와 Pinata 폭발 수치88개 확인(최종 런타임 밸런스는 아님).
`ANALYSIS_VALIDATION.json` 통과. 분석용 색인·프로필·Id별 카탈로그·원본 표본을 생성했으며 완전 컬렉션 ZIP 재추출이나 게임 수정은 하지 않았다. 온라인 작업 없음.

**Royal Smash 로컬 레벨 재검증 정정 (2026-09-16): 원본 APK에 메인 RS 1 700개 + RS1 Loop 860개, 합계 1,560개 JSON이 존재한다.**
기존 860개 ZIP은 같은 번호의 두 컬렉션이 혼합된 결과(메인 349 + 루프 511)이며 메인 순서로 쓰면 안 된다.
고유 내용 1,477종 = 기존 ZIP 822종 + 이번 확인 655종. 원본 XAPK와 APK 3개 SHA 일치, Unity 파일 2,285개 검사/읽기 오류 0, 전 레벨 ResourceManager 외부 파일+path_id 경로 매핑 완료.
근거 `../out_royalsmash/LOCAL_LEVEL_FINDINGS.md`, `LOCAL_LEVEL_APK_AUDIT.json`. 추가 데이터 확인까지 했고 컬렉션별 재추출/기존 ZIP 교체/게임 수정은 하지 않았다. 다음은 컬렉션 보존 재추출이다.
CDN의 추가 레벨 미발견과 구분한다. 별도 RemoteLevels manifest/download 코드가 있지만 실제 서버 manifest/URL/활성 레벨 수는 미확인. 게임·네트워크 실행 없음.
사용자 요청으로 Claude 세션 7125873e-f716-4c4e-95ea-3879d2aebfd9(miniapp-e6)에 공식 세션 메시지로 CDN 인수인계를 전송했다(대기열 접수 ID 391c2d59-016a-4a04-aeeb-6224e26ae75d). 공유 문서 갱신과 실제 메시지 전송은 별도 사건이다.

**Royal Smash 1.13.359 추가 성과 (2026-09-16): 일반 CDN 번들 31개 확보, 크기·비압축 CRC 31/31 일치.**
사용자가 이 게임의 일반 다운로드 기록을 허용하되 인증·보호 기능 우회는 금지했다.
정확한 카탈로그 URL에 익명 HTTPS GET만 수행했고 게임/에뮬레이터 실행·로그인·라이선스 수정은 하지 않았다.
결과: `../out_royalsmash/CDN_PUBLIC_RESULT.md`, 원본 `cdn_public/bundles/`, 검증 `cdn_public/validation.json`.
이는 새 밸런스/레벨 추출 성공이 아니며, 과거 “원격 약 700개 레벨” 추정은 미검증이다.
후속 오프라인 추출도 완료: `../out_royalsmash/cdn_extracted/README.md` 참조.
PNG 1,471개(Sprite 1,230 + Texture2D 241), 컴포넌트 JSON 4,684개, 프리팹 90개/노드 7,147개, 머티리얼 49개/Spine 2개.
최초 이미지 실패 267개는 원본 APK Atlas_UI와 RenderDataKey 일치로 모두 복구. 이름 있는 설정 40개는 전체 JSON의 부분집합이며 밸런스 테이블 40개가 아니다.
원본 31개 SHA 불변, ZIP/PNG/JSON 검증 통과, private memory 최고 약 1.02GiB. 추가 레벨 JSON TextAsset은 발견되지 않았다.
기존 Python312 venv를 전역 수정하지 않고 Blender Python 3.13 + `out_royalsmash/cdn_extraction_deps`로 실행했다. levelscope 코어 변경 없음.
남은 작업은 설정의 의미·최종 런타임 밸런스 확인, 필요하면 AnimationClip/Shader 엔진 네이티브 내보내기다.
다른 게임에는 이 온라인 허용을 확대하지 않는다. 과거 오프라인 실행은 라이선스 오류로 중단됐으며 상태 데이터 8개 경로 폐기 이력은 그대로다.

**Clash of Critters 0.46.1: 복호화 → 밸런스 JSON → 콘텐츠/시스템 HTML 보고서 → Dooray 게시 완료.**
과거 기록의 “밸런스 복구 불가/평문 없음/키가 libil2cpp에 있을 것”은 현재 결론이 아니다.

- 패키지 레코드 5,327/5,327 복호화·압축 해제.
- Config 2,670개 구문 분석: 리터럴 JSON 2,632개 + 클래스 참조를 상징적으로 보존한 Graph 38개.
- AppInfo·Config·Game·Localization 메타데이터 4개도 JSON 복구.
- 보고서: 콘텐츠 분석 묶음 21개, 분석 17개 장, 펫 64개 목록, 루트 Config 380개 검색.
- 복구한 .luae는 평문 Lua 5.4 바이트코드다. 원래 텍스트 소스·주석을 복원한 것이 아니다.

## 위치 — 프로젝트 루트 D:\99.기타 기준

- 원본: `C:\Users\NHN\Downloads\Clash+of+Critters_0.46.1_APKPure.xapk`
- 복호화 전체: `out_clashofcritters/decrypted_v0461/`
- 밸런스 JSON: `out_clashofcritters/balance_tables_v0461/`
- 전달 ZIP: `out_clashofcritters/Clash_0.46.1_BALANCE_JSON.zip`
- HTML: `out_clashofcritters/content_balance_report/Clash_0.46.1_Content_Balance_Report.html`
- 분석 근거: 같은 폴더의 `table_profile.json`, `measurements.json`, `content_catalog.json`, `source_manifest.json`.
- 검증·게시: 같은 폴더의 `analysis_validation.json`, `interaction_validation.json`, `PUBLICATION.md`.
- 기술 이력: `out_clashofcritters/ANALYSIS_PROGRESS_2026-09-15.md` 최신 섹션.

## Dooray 게시 결과 — 마지막으로 확인한 상태

- URL: https://nhnent.dooray.com/wiki/2668173571253827735/4390914232279897275
- 원래 제목: 게임 개발 하네스&오케스트라.
- 버전 15→16. 기존 결과물 히스토리 앞에 분석 섹션과 HTML 다운로드 링크를 추가했다.
- 재조회 때 새 섹션을 제거한 본문이 수정 전 본문과 정확히 일치함을 확인했다.
- HTML page-file ID: `4422141586733380682`, 크기 127,373 bytes.
- HTML SHA-256: `7a7a186051b732161ebc03139c9354efe231407b7ca03a931078aefdb54e65a6`.
- 후속 수정 전에는 반드시 다시 읽는다. 버전 16은 게시 직후 확인값이지 미래 현재값 보장이 아니다.
- 기존 가이드 본문을 분석 보고서로 통째 교체하거나 중복 섹션/첨부를 추가하지 않는다.

## 분석상 중요한 사실

- Pet 64개는 모두 Unit에 연결되고 Enable=true. Unit 204행 전체가 수집 펫은 아니다.
- Stage 6,400행은 80개 챕터 참조. StageChapter 120행 전체가 사용되지는 않는다.
- BossTower 500행 = 5개 그룹 × 100층.
- UnitLevel 11,840행 = 2,400레벨과 Progress 0~4의 복합키. 행 수와 레벨 수를 구분한다.
- ScheduleOpen 52행 중 IsEnable=true 46행. 실제 동시 개최 수가 아니다.
- 속성 enum: 2=물, 3=불, 4=풀, 5=전기, 6=땅. UnitElement의 아이콘/배지로 확인했다.
- _official/_oversea/_cbt 변형은 기본 테이블과 합산하지 않는다.
- ChestPR Category 33의 PR 합계는 0.93714287. 의미 확인 전 정규화·실효 확률 단정 금지.
- UnitEvolution.BattleSkill 27행이 기본 Skill과 미연결: 100101×20, 0×7. 즉시 버그로 단정 금지.

## 검증과 남은 제한

- 통과: 복호화 파일 해시, Config 재해석 대조, ZIP CRC, 핵심 키 직접 집계·참조·필드 누락 검사.
- 통과: JavaScript 문법 및 DOM 모형 검색/필터/페이지 이동 기능검사 11개.
- **미완료: 브라우저 실제 화면/모바일 검수.** 로컬 HTML URL 보안 정책으로 차단되어 우회하지 않았다.
- **미확인:** 최신 서버 덮어쓰기, 현재 콘텐츠 공개 여부, 최종 런타임 수식·반올림·확률 분모.
- 승률·게임성·경제 지속가능성·매출·LTV를 측정하거나 검증한 보고서가 아니다.

## 재현·이어서 할 때

도구는 `android-analysis/tools/`에 있다. 이미 완료한 복호화를 이유 없이 반복하지 않는다.

- 복구: `decrypt_clash_records.py` → `lua54_static_tables.py` → `verify_clash_delivery.py`.
- 분석: `profile_balance_report.py` → `measure_balance_report.py` → `build_content_balance_report.py`.
- 기능검사: Node `test_report_interactions.cjs`.
- Python: `C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe`.
- 보호 코드 복구와 데이터 디코딩은 별도 도구로 수행했다. levelscope 일반 CLI에 통합됐다고 주장하지 않는다.
- 다음 작업 후보는 화면 검수, 로컬 코드 기반 최종 수식·확률 의미 확인이다. 추가 요청 없이 실행하지 않는다.
- 게임 실행·게임사 서버/CDN 접속·온라인 탐지 회피는 수행하지 않는다. “절대 안 들킨다”는 보장도 하지 않는다.
- Top Heroes는 별도 과제다. 기존 HANDOFF의 Top Heroes result를 보존하며 Clash 성과와 섞지 않는다.
