# 공유 프로젝트 메모리 — Claude Code / Codex



갱신: 2026-10-13. 이 파일은 두 도구가 읽는 공유 프로젝트 메모리다.

## 최신 상태 — DKBI 조사와 공통 기능 정리 (2026-10-13)

- DKBI 현재 정본은 [docs/DKBI_HISTORY.md](docs/DKBI_HISTORY.md). 마지막 확인된 실행·추출 근거는 2026-10-08이며, 오늘은 기존 보고서와 파일을 확인해 문서를 정리했다. 새 원작 실행·전체 재추출·셰이더 대조군 검사는 수행하지 않았다.
- 로그인 없는 필드 재현을 조사 중. ECS 하위16섹션의 참조·배치 후보를 연결했고 Action 측에서 메시259개·배치6,394개·텍스처137개를 검증했다. 원작 활성 렌더, 충돌·nav, 입력/공격 시간 단위, LUT 합성 본문은 미결이다. 플레이 가능한 원작 동등 재현 완료로 표현하지 않는다.
- 셰이더 초기 `supported=true` 성공 주장은 철회. 자동 import가 컴파일 데이터를 제거했고 reimport 후 unsupported. 원본 바이트를 보존한 번들5변형도 호환성 검사 실패. 다음은 실제 Shader를 포함한 정상 번들/roundtrip 대조군이며, 아직 결과가 없다. 원작 속성·텍스처·패스 기반 파생 검토 셰이더와 원본 셰이더 재사용을 구분한다.
- REA6.4.0 선택 연동은 로컬 JS 합성 표본과 capabilities 실행만 확인. Ghidra 미설정; IL2CPP metadata 자동 해독이나 DKBI 셰이더 해결 성과가 아니다. 구현·설치본은 로컬 작업이며 이번 문서 커밋에는 포함하지 않는다. 2026-10-13 회귀 검사는 512개 실행, 3개 건너뜀, 실패0.
- 앞으로 반복 기법은 공통 도구로, 게임별 구조는 설정/플러그인으로, 실패 사례는 진단/회귀 검사로 취합한다. 개별 분석 스크립트의 성과를 공통 CLI의 자동 기능으로 확대하지 않는다.
- Heroll 초기 실패 기록은 아래 날짜별 이력이다. 최종 필드 복원77,261/77,275와 표 의미 확인은 9/22 후속 기록이 정본이며, 초기450개 판독 상태를 현재 결론으로 읽지 않는다.
- 자료와 재개 경로는 로컬 전용이다. Git에는 직접 작성한 기법·상태·이력 문서만 포함하며 원본 패키지/바이너리/덤프/이미지/오디오/추출 표/셰이더 프로그램을 넣지 않는다.

별도 서비스의 내장 메모리를 동기화하거나 이미 실행 중인 Claude에 메시지를 보낸 것은 아니다.

최근 작업의 빠른 요약은 이 파일, 상세 이력은 `HANDOFF.md`, 게시 증거는 아래 PUBLICATION 문서를 읽는다.

## 새 세션 시작점 — 2026-09-27

- 최신 설치본/실행 로그 확인: 전체 추출 ZIP은 **1.004.3 기준**이며, 현재 설치본은 **1.006**이다. `post_run_installation_probe.json` 기준 파일 24,448→25,544개, 경로 추가 2,144개·제거 1,048개. 관련 해시 검사에서 관리 DLL 5개·네이티브 플러그인 1개·resources.assets·globalgamemanagers 변경, UnityPlayer.dll 동일. 실행이 업데이트를 일으켰다고 단정하지 않는다. 1.006 전체 재추출은 하지 않았다.
- 1.006 관리 어셈블리 211개 정적 검사에서도 미확인 8개 클래스의 TypeDef/TypeRef 일치 없음(파싱 오류 0, 양성 대조 성공). PlayerSettings는 836바이트 판독·재작성 일치하나 1개 필드 의미는 여전히 미확인이다. 기존 산출물은 덮어쓰지 않았다.
- 사용자가 제공한 `20260927-150552-Player.log` 검토: v1.006 시작, 새 게임 진입, 인트로 실행, 종료 절차 확인. 누락 스크립트 경고 12회는 기존 미확인 8개와 연결할 클래스명/객체 ID가 없어 동일 대상으로 확정할 수 없다. TriLib/GoogleToken/PlayerSettings 이름 및 추가 다운로드 관련 기록은 찾지 못했다. 로그 부재를 기능·다운로드 부재로 확대하지 않는다. 캐시 995개·씬 설정 6개 로드, GameBalance.LoadGameBalance 단계 기록 확인. 미확인 9건 추가 복원은 없다.
- 이번 사용자 요청은 최신 작업 기록의 커밋·푸시다. 게시 대상은 MEMORY.md와 HANDOFF.md이며 기존 AGENTS.md 변경은 제외한다. out/의 추출물·진단 스크립트·로그·원본 DLL은 게시하지 않는다. 따라서 Git 게시가 전체 분석 자료 백업을 뜻하지 않는다. 실제 푸시 결과는 Git 원격 해시로 확인한다.

- 최신 9건 후속: PlayerSettings 전체 836바이트 구조 판독·왕복 일치 성공. 엔진 원본 리더 `0x1813032d0`가 `insecureHttpOption` 뒤에 추가 1바이트(파일 offset 796, 값 0, 메모리 offset 0x266)를 읽지만 메타데이터 생성 경로는 누락한다. 원래 이름·의미는 미확인이다. `out/graveyardkeeper2/NINE_OBJECTS_STATUS.md`와 `player_settings_native_layout.json` 참조.
- 나머지 8개 MB: 관리 DLL 210개 TypeDef 35,532 / TypeRef 22,189 전수 검사에서 해당 namespace/name 없음(오류 0, 양성 대조 성공). 기존 단순 바이트 검색보다 강한 근거다. 현재 분류는 **전체 바이트 구조 확보 1건(이름 미확인 필드 1개) + 클래스 정의 부족 8건**이다. 완전한 이름 있는 스키마 미확인 수는 9 유지. `graveyardkeeper2_native_layout.zip` 추가로 총 12개 ZIP. 기존 11개 전수 검사를 반복하지 않았다.

- 추가 구조 복원: `graveyardkeeper2_structural_candidates.zip`(10항목)을 생성했다. 골격 52묶음·문자열 168개, 립싱크 15묶음·문자열 59개(빈 문자열 포함), 루트 골격 이름 3개를 배열 형태로 판독했다. 8개 MB의 익명 구조 표현은 payload 왕복 바이트 일치 확인. 원래 필드명/형식 스키마는 확보하지 못했으므로 완전 미해석 집계 9개는 유지한다. 민감 가능 문자열은 신규 후보에서 마스킹했다.
- PlayerSettings는 로컬 TPK의 Unity 6000 계열 42개 버전 항목을 대조했다. 836바이트가 맞는 6000.4 후보도 해상도/참조 위치가 어긋나 기각했다. `structural_recovery_summary.json`, `deep_remaining_evidence.json`에 근거 보존. ZIP은 이제 11개이며 이번 신규 ZIP의 CRC/JSON/중복 검사를 통과했다. 앞선 10개 ZIP 검사를 이번에 다시 수행한 것은 아니다.

- 추가 구조 복원: `graveyardkeeper2_structural_candidates.zip`(10항목)을 생성했다. 골격 52묶음·문자열 168개, 립싱크 15묶음·문자열 59개(빈 문자열 포함), 루트 골격 이름 3개를 배열 형태로 판독했다. 8개 MB의 익명 구조 표현은 payload 왕복 바이트 일치 확인. 원래 필드명/형식 스키마는 확보하지 못했으므로 완전 미해석 집계 9개는 유지한다. 민감 가능 문자열은 신규 후보에서 마스킹했다.
- PlayerSettings는 로컬 TPK의 Unity 6000 계열 42개 버전 항목을 대조했다. 836바이트가 맞는 6000.4 후보도 해상도/참조 위치가 어긋나 기각했다. `structural_recovery_summary.json`, `deep_remaining_evidence.json`에 근거 보존. ZIP은 이제 11개이며 이번 신규 ZIP의 CRC/JSON/중복 검사를 통과했다. 앞선 10개 ZIP 검사를 이번에 다시 수행한 것은 아니다.

- 최종 보완(이 절의 이전 집계보다 우선): 잔여 13개 추가 조사에서 Unity 내장 MonoScript 참조를 등록해 4개를 더 복원했다. 최신 잔여는 **MonoBehaviour 8개 + PlayerSettings 1개 = 9개**, 읽은 MonoBehaviour는 193,311/193,319개다. 완전 복원 불가를 영구적 한계로 단정하지 않는다.
- 보완 산출물: `graveyardkeeper2_builtin_recovered.zip`(복원 4개), `graveyardkeeper2_unresolved_inspection.zip`(원본·부분 판독·조사 이력). 최신 판정은 `remaining_final.json`을 우선한다. 기존 ZIP에 병합하지 않았다. 총 10개 ZIP / 1,250,594항목 CRC 검사 통과. 미해석 8개는 DLL 210개에서 해당 클래스명 바이트가 없었고 세 백엔드에서 스키마를 확보하지 못했다. PlayerSettings는 836바이트 중 832바이트 후보 판독만 가능해 참고용으로 구분했다.
- Graveyard Keeper 2 로컬 설치본의 원본 보존·변환 가능 데이터 추출 및 마무리를 완료했다. 안내는 `out/graveyardkeeper2/README.md`, 상세 검증은 같은 폴더의 `verification_20260927.json`이다. 아래 9/23의 착수·게시 준비 기록은 당시 이력이다.
- 최종 ZIP 8개: 설치 원본 24,448개를 Unity 소스 24,173개와 보조 파일 275개로 보존했다. 원본 해시 대조 불일치 0, ZIP 내부 1,250,561항목 CRC 오류 0. 전체 코드를 디컴파일했거나 시스템 분석을 완료했다는 뜻은 아니다.
- PNG 36,427개, 음원 7,246개, 독립 설정 에셋 7,473개, 장면 15개·프리팹 4,959개·노드 189,934개. 기타 객체 577,130개를 raw 및 가능한 JSON으로 보존했다.
- MonoBehaviour 추가 복원 872개는 별도 `graveyardkeeper2_managed_recovered.zip`에 있다. 기존 hierarchy/SO ZIP에 병합되지 않았다. 전체 193,319개 중 193,307개를 읽었고 12개가 미해석이다. PlayerSettings 1개도 raw만 보존했다.
- 이미지 제외 10개는 전체 Texture2D 소스 5,605개 전수 조사에서 모두 0×0 Font Texture로 확인했다. OBJ 제외 16개는 정점이 없는 메시다. 최신 근거는 `exception_evidence.json`; 최초 예외 목록에는 후속 복원분도 포함된다.
- 사용자 지시: 콘솔 창을 띄우지 않는다. 이번 마무리는 Node 도구에서 `shell:false`, `windowsHide:true`로 `pythonw.exe`를 직접 실행했다. CMD/PowerShell 경유 금지. 파일 읽기는 Node 파일 API를 사용했다. 순차 실행·낮은 우선순위·CPU affinity 1·프로세스 트리 커밋 감시 3GiB를 유지했다.
- 다음 단계는 사용자가 추출물을 확인한 뒤 요청하는 해석·보고서다. 자동 재추출·보고서 작성·Git 게시를 하지 않는다. 이번에는 README와 메모리만 정리했고 커밋/푸시는 하지 않았다. 기존 AGENTS.md 변경은 보존했다.
- 콘솔 원인 설명 정정: 사용자가 제시한 Codex Windows daemon 이슈 #48422/#48090에서 같은 현상을 확인했다. Python 실행기만의 문제라고 단정하지 않는다. 직접 실행 우회는 자식 프로세스의 콘솔 미생성만 검증한 것이다. Codex 자체 보조 프로세스까지 해결됐다고 말하지 않는다. CLI 버전·데몬 상태의 현장 확인 및 설정 변경·종료는 수행하지 않았다.
- 공용 관찰 기록의 현재 상태는 `C:/Users/macjo/.claude/skill-observations/`에서 확인한다. 9/23의 관찰 리뷰 대기 문구를 현재 상태로 재사용하지 않는다.

## 이전 시작점 — 2026-09-23

- Graveyard Keeper 2의 확정 범위는 **전체 추출**이다. 사용자가 결과를 본 뒤 정리를 별도 요청하기로 했다. 지금 해석 보고서를 만들거나 특정 밸런스 분석으로 범위를 좁히지 않는다.

- 새 대상은 사용자 지정 Steam 설치 폴더 `D:\SteamLibrary\steamapps\common\Graveyard Keeper 2`다. `app.info`에서 Lazy Bear Games / Graveyard Keeper 2를 확인했다. Unity Mono 빌드이며 로컬 정적 조사에 착수했다. 출력은 `out/graveyardkeeper2/`다. 전체 추출·시스템 분석 완료로 읽지 않는다.
- Royal Match 38174 신규·복귀 케어 상세 분석은 완료했다. 최신 보고서는 `out/royalmatch_38174/care_factors/RoyalMatch_유저케어_수치와흐름_상세보고서.html`이다. 신규 안내, 복귀 티어·보상·추가 이동, 전용 풀, 이벤트 재개를 분리했다. 상세 근거와 한계는 HANDOFF.md의 9/23 기록을 본다.
- 복귀 티어의 일수 계산 경로와 서버 메시지 직접 지정 경로는 별개다. 추가 이동 25개 레벨 구간과 전용 풀 진행도도 별개다. 실패 횟수만으로 블록 확률을 낮추는 일반 DDA는 입증하지 못했다.
- LowMatch 원본 필드는 스칼라가 아닌 벡터다. 내장 레벨의 초기 배열은 비었지만 승리 상태에서 덮어쓰는 경로가 있다. 초기 비활성을 기능 전체 미사용으로 확대하지 않는다.
- 기존 검증 산출물: 정적·모델 검사 112건(경계 사례 85건 포함), 상세 HTML 검사 16건. 원작 실행·서버 실효 설정·AB 배정·운영 성과 검증은 아니다. 이번 문서 갱신에서 분석 전체를 재실행한 것도 아니다.
- 보고서는 정중하고 짧은 한국어, 표·도식·순서도 중심으로 작성한다. 사업·기획·개발 독자를 구분하고 확인 사실과 추정을 나눈다.
- 사용자 요청 관찰 기록 0001~0003의 정식 리뷰는 후속 작업으로 남아 있다. 현재 작업에 적용하는 것과 스킬 수정·리뷰 완료는 다르다.
- 이번 게시 대상은 MEMORY.md와 HANDOFF.md다. 기존 AGENTS.md·CLAUDE.md 미커밋 변경은 보존한다. 원본·추출물·HTML·덤프·의존성은 Git에 포함하지 않으므로 메모리 푸시는 전체 분석 백업이 아니다.



## 이전 작업 — Heroll 2.0.3 초기 점검 (2026-09-22, 후속 복원 전 기록)



- 사용자 다운로드 `Heroll+_+Dice+Roguelike_2.0.3_APKPure.xapk`, `com.percent.aos.rollinghero`/code115024946/한국어명 `용사님 돌았어요?`. Unity6000.2.15f1, metadata31/IL2CPP. 원본SHA256 `f197e7b5d48df6ee047a802c23c60d8423575cccfaa67134341d97ddea7dfc53` 전후 일치.

- 시작점 `out/heroll/README.md`, 표 색인 `TABLE_INDEX.md`. `Heroll_tables.zip`:164표/14,593행, 바이너리164개 메타데이터 해시 일치, 전 바이트 소비·CSV ID/일반값 일치. 완전 명명 스키마163개; ShopProductList420행의 추가4바이트는 `__unmapped_member0_bytes`로 보존. enum라벨은CSV 관찰 매핑, DateTime 원시bits/ticks 보존 및 1,216값·261빈배열 CSV 대조 통과(528 UTC,688 기본값;실행소비 미검증). 저장 표 메타데이터BundleVersion2.0.2/dev와 패키지2.0.3을 구분.

- 이미지PNG13,496개/0크기텍스처24개 제외(원본 재판독으로 확인). assets:WAV489/재질447/폰트18/TextAsset337. hierarchy:씬9/프리팹468/노드74,540; 연결MonoBehaviour77,275중450만 필드 판독,76,825 fields=null. native 백엔드3종 및 별도dumper 구조 검사 실패: dump.cs 생성/종료코드0을 성공으로 취급하지 않는다. shop_metadata_fields.json도 실패한 탐색 자료이며 스키마 근거 금지.

- 입력APK3개·13분할그룹을 `input_prepared/`에 준비. 최종Unity소스5,404/오브젝트332,361(내장소스2포함). 직접XAPK/분할미조립 survey는 중단 이력이며 최종기준 아님. `run_pipeline.py`는 기존CLI에 불변 디렉터리 색인 재사용 및 정확한파일명 우선매칭을 적용한다. 대괄호폰트번들 누락53객체를 잡아 재추출했고 `survey.json` 집계도 정정했다. 공통코어 미수정.

- 검증 `artifact_validation.json`:ZIP4개 CRC, 모든PNG/WAV프레임/엄격JSON/대소문자경로충돌/74,540노드/전체5,402비내장asset소스/모든GameObject소스/원본해시/디코더잘림등4음성검사 통과. 재질JSON2개의Infinity는명시객체로보존,원래export바이트도ZIP내보존.

- 기존BlenderPython3.13+격리의존성사용, 단계별프로세스트리5GiB상한, hierarchy피크2.107GiB/최종검증약0.353GiB. 원작실행·게임/CDN요청·원본수정·새Git게시 없음. 리소스/복구표는로컬전용. configs/heroll.yaml 추가; 기존미커밋작업보존.

- 후속 조사: `out/heroll/FOLLOWUP.md`, `datetime_validation.json`, `native/structural_diagnosis.json`. 전체필드토큰122,712중 mod16=0의30,678개만 전부 비표준; 나머지92,034정상. ELF섹션/함수표본도 미해석. Shop 추가4바이트는420행모두0이나 타입/의미 미확정. 작은표본검사 정상완료; D: HDD이나 멈춤 당시 병목은 미확인.

- 다음 후보: 패키지 내부 로더의 정적 분석으로 native/metadata 변형 복원 조사 또는 필요한 표의 게임 설계 분석. 이미 완료한 전체추출을 자동재실행하지 않는다. Sandtrix와RoyalSmash는 이전작업이력이다.

## 문서 게시 작업 — 2026-09-22



- 사용자가 기존 GitHub `macjoocan/projectgogo`에 기법·히스토리·메모리 게시를 요청했다. 이번 범위는 `ANALYSIS_KNOWHOW.md`, `EXTRACTION_HISTORY.md`, `MEMORY.md`, `HANDOFF.md` 네 문서다. 사용자의 추가 요청에 따라 Royal Smash 계층·설정값 추출 이력을 함께 정리했다.

- Sandtrix 후속 이력과 저장값/소비/도달성/실측 구분, 배열 축, UI·파티클 검증 기법을 정리했다. 원본 패키지·이미지·오디오·추출 데이터·덤프·키·인증정보는 추가하지 않는다. 기존 코드·설정·다른 문서의 미커밋 작업은 보존한다.

- 이 기록은 게시 범위와 준비 이력이다. 푸시 성공은 원격 main 해시로 별도 확인한다. 아래의 커밋/푸시 미요청·미실행은 각 과거 분석 시점의 기록이다.



## 새 세션 시작점 — 2026-09-22



- 사용자가 긴 대화의 스크롤 문제로 세션 초기화 전 메모리 정리를 요청했다. 현재 분석 작업은 마무리했으며 자동 재추출·재전송하지 않는다. 다음 요청부터 이어간다.

- 현재 대상: Sandtrix 1.8.4. 분석 저장소 `D:\99.기타\levelscope`, 산출물 `out/sandtrix/`, 개발 프로젝트 `C:\00.SVN\MiniApp`. 원본/프로토 수정 없이 로컬 정적 분석만 수행했다.

- 최신 답신: `out/sandtrix/AXIS_PARTICLE_FAKE_REPLY.md`. 축은 `flipV(transpose(raw))` 유지(소비 코드 근거), 65/65 show/color 점유 일치. J/L 이름을 표준 손대칭의 정답으로 쓰지 않는다. Q2는 1모래셀 정수 위치 보존, 변환 시 11배수 스냅 없음.

- 파티클: hierarchy ZIP의 ParticleSystem InitialModule에 값 존재. sparks TwoConstants 수명 endpoints 0.5/0.2, 속도50/800, 크기1/5; flash Constant 수명0.15, 속도0, 크기700. SizeOverLifetime 곡선·원본 단위 보존, CSS 픽셀 직접 대입 금지. Fake8은 Bomb.DrawBomb에서 확인; 일반 blink는 기존 CellState 유지(Fixed도 Sand로 바꾸지 않음).

- HUD 답신 `HUD_SHAPE_BRIDGE_REPLY.md`: CanvasScaler Expand, disabled layout/image 구분, 정확한 sprite PPtr 및 9-slice border 사용. 이전 7건을 Claude가 반영했다고 보고했지만 실제 프로토 코드는 검토하지 않았다.

- 브리지 대상 Claude `27d8b6d7-5a5f-4d6e-867b-c7c47e02c8ee`. 이전 HUD 답신은 사용자 수신/작업착수 확인. 최신 bmuba92b7-1 답신은 1회 전송했고 반환 queued, 15초 내 도착 미확인. 두 메시지의 상태를 혼동하거나 중복 발신하지 않는다. 아래 이전 queued 기록은 당시 이력이다.

- 검증: 최근 native 정적 검사18/18, ASM 바이트 해시675건. 원작 실행 검증이나 프로토 R6 정합성 검증이 아니다. 남은 후보: 전체 회전/셀 단위 parity, 실제 제거 타이밍 소비·오버라이드, UIParticle 화면 배율. 24개 맵은 현행 활성 스테이지로 확정하지 않는다.

- 재개 시 AGENTS/CLAUDE → 이 절 → 최신 답신 문서 순으로 읽고 필요한 근거만 추가 조회. 원본 게임/CDN/에뮬레이터 실행·보호 우회 없음. 미커밋 사용자 변경 보존; 커밋/푸시 요청 없음. 무거운 재독은 단계 분리·프로세스 트리 커밋 상한 사용.



## 최신 작업 — Sandtrix 1.8.4 로컬 추출 (2026-09-21)



- bmuba92b7-1 후속 정적 답신 `out/sandtrix/AXIS_PARTICLE_FAKE_REPLY.md`: J/L584/588 raw 배열로 flipV(transpose) 실루엣 재현, show/color 점유65/65일치. ShapeTexture는 생성경로 확인; 표준이름 대신 소비변환 유지. 파티클 InitialModule 값 기존 ZIP에 존재(sparks lifetime endpoints.5/.2,speed50/800,size1/5;flash .15/0/700), 원본입자단위와 CSS픽셀 구분. Fake8은 Bomb.DrawBomb 경로 확인; Heap/Cell Blink는 state불변, Sand뿐 아니라 Fixed도 기존상태유지. 사용자가 이전 bridge수신/작업착수 확인; 최신프로토7건 반영 자체는 미검증.



- 전송상태 후속: 사용자 승인 후 HUD/Shape 답신을 Claude `27d8b6d7-5a5f-4d6e-867b-c7c47e02c8ee`에 cc-bridge로1회 발신. 반환 `queued`,30초 내 도착미확인. 아래 추출시점의 미전송 기록을 대체하며 수신/구현완료는 아님.



- HUD/Shape bridge 질문 bmub94rzq-3 후속: `out/sandtrix/HUD_SHAPE_BRIDGE_REPLY.md`, `hud_bridge_evidence.json`. Score 컨테이너 Layout/Fitter/Image는 원본 enabled0; Resource 부모만 Layout enabled1. HUD CanvasScaler3개는 ScreenMatchMode1=Expand, match1 높이기준 해석 취소. ui_popup_back341 border107x4; PowerUp Field416 border45/52/46/48(동명335는border0). Shape SplitParticles는 현재 integer X/Y 셀을 그대로 Sand로 변경(변환시11스냅없음); authored[a,b] -> texture[11a+u,11b+v] -> board[startX+x,H-1-y]. Rainbow direct caller ColoredBlockPowerUp.Init0x15e5c54 확인. Color/CellColor 별도이동 확인.18기존검증통과/ASM673해시, 원본HUD 재독피크1.021GiB. 원작실행/프로토수정/자동bridge전송/커밋푸시 없음; 회전전체·런타임HUD parity는 미확정.



- 맵 사용 경로 후속: `out/sandtrix/MAP_REACHABILITY.md`. 메뉴 delegate 메타데이터까지 대조: TaskGameButton2027→TryStartLevel→ExpertMode6, Endless2598→Endless4. Grid.Setup 직접6곳 모두task=null(시작3+종료3). TaskController2032 소유GO는비활성 저장. TaskState 객체/전이는남아있으므로완전삭제/전역미사용단정금지. StartScreen의 puzzle wrapper2248은같은Task버튼2027, 해금은저장10레벨이아니라Played_Once키존재. 맵24는조건부복원/실험자산, 현행활성24스테이지아님. 추가15정적검사 및원본UI5개재판독,게임실행없음. 기존미니26과분리. 공유문서갱신이며Claude수신확인/프로토수정/푸시없음.

- 추가 심층 요청 완료: `out/sandtrix/DROP_SHUFFLE_RULES.md`, `DEEP_DEVELOPMENT_FINDINGS.md`. 원본 APK2개/1,342항목 재점검 및 lib/metadata 해시 재일치. 범위제한 ASM545개+별도셔플, 핵심18/드롭13/추가11=42정적·해석 검사 통과. 추가게임컴포넌트75/엔진3개 판독·참조 검증 통과(피크1.39GiB). 아래380은 초기 핵심 배치 개수다.

- 드롭: 드래그50셀 기준/화면폭으로 pixelSize, 스와이프 .25초·15셀 조건→75+1500*t(텔레포트 아님), 좌우차단/회전별도. 착지 .15초 모래화. 설정1칸11×11/65모양 각484셀. 맵은4색 대응 Fisher–Yates/byte rejection/RNGCrypto, 항등순열 가능; 실제 재시작·맵 활성화는 미확정.

- 추가함정: Time Freeze는10초 정지가 아니라 DecreaseGameSpeed(3)로 Balance 인덱스3단계 되돌림/linesCutter 보정. BombRain7/반경22/약.2초 간격/Sand|Fixed 원형 직접Reset; TripleRocket는3개Sand시드의4방향 같은색 덩어리(일반제거8방향과 구분), 약1.2초. Continue의ClearGrid는Fixed제외, Task경로+10moves 함수 존재하나 실제 노출/감소 호출 미확정. 모래루프 clip274/volume.4/looptrue, 단발273과 구분. 저장카메라 직교5.25. 소비자·도달성·실측 구분 유지, 추가도 로컬/우회없음/프로토·커밋·푸시 없음.

- 후속 네이티브 분석 완료: `out/sandtrix/NATIVE_RULES.md`가 아래 1차 소비규칙 미검증 상태를 갱신한다. metadata31/ARM64 선언과380개 범위제한 디스어셈블리·해시,18개 정적/해석모델 검사 통과. 원본 실행 검증은 아님.

- 핵심: 모래 Y+하강/아래→왼쪽→오른쪽/옆칸도 비어야 대각선 이동;8방향 연결/Sand|Fixed 판정;제거 셀 수 점수. 속도는 Sand 수와 전체격자×0.8 기준 비율을 쓴 곱셈식. 두색 확률은 정수1..99. 입력 Activate/Deactivate는 둘 다 touch배율1이므로 해제=정지로 추정 금지.

- 24개 맵의 조건부 symbolic grid 복원 및33텍스처 wrapV=Clamp 확인. 그러나 Task/Endless/Expert 진입 경로는 task=null을 전달; TaskController.Setup 및 hardcodedSpeed 오버로드의 직접 B/BL 호출0개. 맵24/속도필드를 실제 사용 중이라고 확정하지 말 것. 간접호출/인라인 전체 배제는 아님. 자홍→Yellow enum; PNG샘플행 max(0,y-1); 무작위색은 토큰으로 유지.

- task-observer 지침에 따라 저장값/소비 함수/도달성/실측을 분리해 기록했다. 이 후속도 게임/CDN/에뮬레이터/보호우회/프로토수정/커밋푸시 없음. 미관측 랜덤시드·시청각·모든 회전/아이템 경로 및 MMF_Player1개 한계는 남는다.

- 현재 대상은 사용자 다운로드 폴더의 `Sandtrix_+ASMR+Blocks_1.8.4_APKPure.xapk`. 패키지 com.EveryDayGames.Sandtrix / code25, Unity2022.3.49f1 IL2CPP. 게임 실행·CDN 요청·보호 우회 없이 로컬 정적 추출했다. 9/17의 메모리만 저장 지시는 당시 Clash 작업의 이력이다.

- Unity 종료 후 가용 commit 약10.47GiB로 회복되어 작업 재개. 기존 `.venv` 실행기는 제거된Python3.12를 가리켜 Blender5.2 Python3.13 + 기존 `../out_royalsmash/cdn_extraction_deps` 및 `.venv/Lib/site-packages`를 사용했다. 설치/전역 설정 변경 없음. 추출 cap4GiB/5GiB, hierarchy 피크약2.09GiB.

- 결과: `out/sandtrix/README.md`. PNG490, WAV8, 머티리얼27, 폰트4, TextAsset5, 씬1/프리팹35/노드993. MonoBehaviour1251/1252 성공; MMF_Player SerializeReference1개 실패. 런타임0×0폰트텍스처5개 제외. ZIP CRC/PNG/WAV 프레임 검증 통과.

- 추가 설정135개와 nonnull PPtr 참조 검증. 생성 typetree의 m_Script135개 불일치는 독립 기본 리더와 대조해 추가 JSON에서 교정하고 원시헤더/이전값을 보존했다. 공통 코어와 hierarchy ZIP은 고치지 않았다. `gameplay_settings.json`을 참조 근거로 사용한다.

- ShapeConfig65개와 GameBalanceConfig2개의 Odin 바이너리67개를 전체 소비/노드/배열/다차원 크기 검증해 복구. `shapes_readable.json`, `balance_readable.json` 제공. BaseSpeed20, Endless5행/Expert6행. 키/확률 단위/최종속도 소비 규칙은 미검증.

- 목표50개를 연속50스테이지로 합치지 말 것: GameData 미니목표26(시작18+일반8, `Level_01`~26, 맵null)와 TaskController 맵목표24(시작14+일반10, `Level 01`~24)는 다른 자산이다. `tasks_readable.json`, `task_collections.json` 및 맵별 sourceID/PNG 해시를 가진 `map_texture_index.json` 참조. 배열 좌표/맵색 변환과 실행시 선택은 미확정.

- 새 게임설정 `configs/sandtrix.yaml`, 후속 스크립트와 산출물은 `out/sandtrix/`. 원본/산출물 Git게시·커밋·푸시 없음, 기존 코어 변경 보존. RoyalSmash 물리 재검토는 사용자 대상 전환으로 미완료 상태이며 답신 완료로 취급하지 않는다. 이 공유 파일 저장은 Claude의 수신/내장 메모리 동기화가 아니다.



## 이전 작업 — Clash of Critters LDPlayer / 메모리만 저장 (2026-09-17)



- 사용자 최신 지시: **일단 메모리 기록만**. 추가 분석·추출·설정 변경·커밋·푸시는 진행하지 않는다. 아래 이전 Git 요청을 현재 작업 권한으로 해석하지 않는다.

- 사용자가 LDPlayer에서 게임과 CDN을 다운로드했다고 알렸고 USB 디버깅을 활성화했다. 이후 `emulator-5554 device` 연결과 `uid=2000(shell)`을 확인했다. 설치 위치 `C:\LDPlayer\LDPlayer14`, 인스턴스 0, CLI 14.0.25.2. 루트는 활성화하지 않았다.

- 패키지 `com.farlightgames.pgame.gp` 설치 버전은 **0.47.1 / 4242**. 기존 로컬 분석은 **0.46.1 / 4097**, Config 2,670개 청크 복구 이력이 있으므로 기존 분석 전체를 실패로 취급하지 않는다.

- 외부 저장소 `/sdcard/Android/data/com.farlightgames.pgame.gp`는 10,708 KiB, 대부분 `files/il2cpp`(10,392 KiB). `global-metadata.dat` 9,967,284 bytes 및 DLL 리소스 등이 보였다. OBB 디렉터리는 비어 있다. 작은 SDK/계정 관련 캐시·로그의 내용은 읽거나 복사하지 않았다.

- 내부 `files`·`cache`(`/data/user/0/com.farlightgames.pgame.gp/…`)는 **Permission denied**. **CDN 캐시 위치·내용·완전성은 미확인**이며, 접근 거부를 다운로드 부재로 해석하지 않는다. 인증·보호 기능·파일 접근 권한 우회 없이 중단했다.

- 설치된 base / BinaryAssets / UnityDataAssetPack / arm64 split APK 경로는 읽을 수 있었다. **아직 pull·추출·분석하지 않았으며 설치 APK가 CDN 확보 증거는 아니다.** 재개 시 0.47.1 설치 패키지의 오프라인 정적 비교가 후보일 뿐, 이번에는 착수하지 않는다.

- 사용자는 ADB를 로컬 전용으로 설정했다고 알렸으나 관측된 리스너는 adb 서버 `127.0.0.1:5037`, LD VM `0.0.0.0:5555`, `0.0.0.0:2222`였다. wildcard 바인딩만으로 외부 접근 가능/불가능을 판정하지 않는다. 방화벽·외부 도달성은 미검증, 연결은 로컬로만 수행했고 설정은 바꾸지 않았다.

- 게임은 이미 실행 중이었고 직접 실행하거나 CDN 요청을 보내지 않았다. 기존 에뮬레이터/게임 통신을 차단하거나 전체 통신 안전성을 검증한 것은 아니다. 상세 근거: `../out_clashofcritters/LDPLAYER_CHECK_2026-09-17.md`. 공유 파일 저장은 Claude 내장 메모리 동기화나 읽음 확인을 뜻하지 않는다.



## 작업 재개 요약 — 2026-09-17 정리



- 재사용 노하우는 [ANALYSIS_KNOWHOW.md](ANALYSIS_KNOWHOW.md)에 모았다. 참조/컬렉션 식별, 바이너리 경계, 부모 TRS, 셰이더 후보와 런타임 선택, 실제 물리 소비자, 이펙트 상태 완료, 메모리 제한, 우편함 재검증을 다룬다.

- **대포 기준 Y 확인 완료:** 9/16 21:45 감사에서 CannonBase4.44와 LevelSpawnPos1은 형제라 +1 중복 금지. 저장 공 생성점 Y4.076285는 조준/애니메이션 후 불변값이 아니다. 최신 검사 당시 proto cannonFor도4.44. 해머 설계/충돌 일치 판정은 미완료.

- **볼 물리 최신 수정은 재검증 대기:** 9/16 21:18에서 directHit 제외/조건부1.2는 통과했고 표면·Bouncer·저속 차이를 발견했다. 21:29 Claude가 수정했다고 답신했으나 이후에는 대포만 검사했다. 아래 과거 실패를 현재도 남아 있다고 단정하거나, 답신만으로 통과 처리하지 않는다.

- 원작 런타임 Config 선택값, 감속/retention 소비 규칙, 유효 공 생성점/발사 계산 및 해머 동시 궤적은 남은 확인 항목. 700레벨 튜닝은 검증 근거 정리 전 보류였으며 이번 문서 정리에서 재개하지 않았다.

- 다음 검증에는 현재 함수와 해시를 다시 읽는다. `review_ball_revision_20260916.mjs`는 당시 알려진 실패도 assert하므로 수정된 코드에 그대로 돌려 나온 실패를 새 회귀로 오해하지 않는다.

- **Git 범위:** 사용자 지정 저장소 `https://github.com/macjoocan/projectgogo`에 공유 문서/정리된 노하우만 반영한다. 기존 코어·테스트·설정 수정은 별도 로컬 작업으로 보존한다. `../out_*`, 원본 패키지, 분석용 의존성/덤프/이미지/전체 증거는 Git에 포함하지 않으므로 다른 PC에서 경로만으로 재현되지는 않는다.

- 아래 기록은 각 날짜의 검사/전달 이력이다. `answered`·파일 게시가 상대의 읽음/구현/검증 완료를 뜻하지 않는다. 9/17에는 문서 정리 이후 Royal Smash 층/파괴 정적 분석과 Clash of Critters LDPlayer 연결 점검도 수행했다. 최신 프로토 수정의 원작 런타임 동등성을 검증한 것은 아니다.



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


### Heroll native progress 2026-09-22 (newer than prior blocked status)
Verified static AG code decompression for libloader (1,519,396 bytes) and libil2cpp (115,968,172 bytes), with complete zlib streams and saved hashes. Metadata is still unresolved; do not report hierarchy custom fields as recovered. Resume from out/heroll/native/RECOVERY_PROGRESS.md: mmap wrapper 0xf0fac -> generic transform 0xf06e8 -> descriptor parser 0xef000. All original files and existing export ZIPs preserved.


### Heroll metadata recovery breakthrough 2026-09-22
Native code AND metadata restored statically; all122,712 field-token checks pass. Local sidecar filename equals SHA256(level0) first32; observed AES-CBC+zlib decoder restores metadata. All164 table types/fields and59 observed enums checked against native declarations. ShopProductList extra member resolved as ProductType, PercentProductType int32, all420 values Consumable(0). Heroll_tables.zip updated, original CSV/binary preserved. Full hierarchy rerun uses cached typetrees from separately executed backends to stay under5GiB; see out/heroll/native/RECOVERY_PROGRESS.md and final validation reports. Earlier native-unresolved statements are superseded.





## Heroll 최종 완료 — 2026-09-22



- 현재 진입점: `out/heroll/README.md`, 재현 순서 `out/heroll/FOLLOWUP.md`. 초기 실패 상태는 native/*before_native*로 보존했다.

- 코드와 별도 메타데이터 복원, 122,712개 필드 토큰 검증, 테이블 164개/14,593행 모두 이름·타입 확인. ShopProductList.ProductType 계산 속성과 실제 serializer 순서 확인; CSV/바이너리 원본 보존. 관찰 enum 59종과 날짜 1,216개/빈 배열 261개 대조 통과.

- 최종 계층: 씬 9 / 프리팹 468 / 노드 74,540 / 전체 컴포넌트 160,575 / MonoBehaviour 77,275 중 77,261 필드 복원(99.9819%). 기존450에서 증가. 이전 계층과 topology·개수 일치, GameObject 소스294개 전부 포함. 최종 ZIP SHA256 f8833b19232783d52b23af66519a4b25984e06b0bfd52dacd06f195cd392994c.

- 미복원14개는 원본 script pointer0인32바이트 객체13개 + Ddangddang.CustomScreenShot.CustomScreenShot184바이트1개. 전체31,843타입 정의에 해당 클래스 없음. native/unresolved_objects.zip에 raw·해시·출처 보존; fields:null 유지. 현재 패키지에서 확인할 근거 없는 이름을 추측하지 않는다.

- 파일을 bytes로 로드할 때 임의 이름이 붙어 외부 참조가 틀리던 문제는 canonical filename + registry 우선으로 해결. 타입트리 m_Enabled 정렬, 이름 있는 Array를 vector/Array로 정규화. VInspector Dictionary 정의는131후보 필드의 네이티브 제네릭 타입을 대조해 Unity.Rendering 동명 타입과 구분.

- 중간 잘못된 배열 판독 작업에서 약9GB 증가 관찰 후 자체 프로세스 종료. C 확장 대신 bounded Python reader + 별도 프로세스5GiB 감시. 최종174초/외부 측정1.587GiB/exit0. HDD 고장 여부나 과거 모든 멈춤 원인으로 확대 해석하지 않는다.

- 최종4개 ZIP 해시 확인, tables/hierarchy CRC·엄격JSON 재검사, assets/sprites 이전 내용 검증은 해시 일치로 유지. 원작 실행·게임/CDN 요청 없음. 공통 코어 기존 dirty 변경은 건드리지 않음. 공개 대상은 ANALYSIS_KNOWHOW.md / EXTRACTION_HISTORY.md 직접 작성 기법·이력만.


Heroll 공개 이력 반영 완료: 2026-09-22 commit 4a40d59 (ANALYSIS_KNOWHOW.md / EXTRACTION_HISTORY.md 2개 문서, 55줄 추가), origin main push 성공. 원본·복원 바이너리·타입트리·리소스·테이블·로컬 스크립트는 게시하지 않았다. 기존 Royal Smash/Sandtrix 공개 이력 commit 87f0ac8 위에 추가했다.







## Plants on Fire 정적 추출 최종 정리 — 2026-09-22

- 진입점 out/plantsonfire/README.md, FINAL_VALIDATION.json. ZIP7개 최종 검증 통과, 입력 SHA256 변동 없음.

- CSV54개/5,649행, 씬2/프리팹594/노드2,358, 부착MB2,661 및 독립219 포함 전체2,880 모두 필드 판독.

- DOTS152개 컨테이너/archetype/chunk 수량 대조 통과, 파일별 엔티티 레코드 합614; 보조3개 보존. 컴포넌트별 모든 필드 의미 복원은 미완료이며 전체 디코딩100%로 표현하지 않음.

- PNG기본1,086개, 게임Mesh21개/기본13개. FrameAnimationAuthoring57, 일반Clip1은UI. 기존캐릭터리그 재사용 미검증.

- 머티리얼 비유한수 표준JSON 태그 변환 및 원문TXT 보존. CSV열불일치4개/카탈로그 미존재6경로 유지. 리소스는 로컬만.

- 사용자가 추출 마무리를 우선 요청. 캐릭터1개 외형 변경 테스트는 그 이후 작업이며 아직 실행하지 않음.





### Plants DOTS 추가 해석 (이전 정리 이후)

152파일의 Entity ID614, 외부버퍼303 분리/경계검증. 타입92종 중73종 해시 exact match, 미일치19종 null. 타입이름debugsection없음. 원인단정/값오프셋추정 금지. Entity외 필드값 전체해석은 아직 미완료. 상세 out/plantsonfire/DOTS_REMAINING.md 및 PlantsOnFire_dots_details.zip. 총8 ZIP 재검증통과. 3D 테스트 계속보류.


### Plants 캐릭터 외형 테스트 2026-09-22
Role_AK/Role2D 머티리얼/16x16 atlas 연결 확인. character_test에 신규Blender 로봇17메시, Run_F28~33/10FPS 신규동작, RGBA128PNG6장, 통합GLB클립, 비교HTML 저장. GLB재임포트17메시/애니메이션객체5 확인. 기존리그재사용/원본동작복원/APK적용 아님. 원본프레임방향은셰이더대조미완료. 진입점 out/plantsonfire/character_test/README.md.


2026-09-22 Dooray 게시 완료: 부모4390914232279897275 아래 자식4427340531635271673 생성. Blender 외형 히스토리/대표이미지1+달리기6장/신규산출물ZIP 첨부. 원작atlas·추출리소스 제외. API재조회에서부모관계·이미지태그7·첨부8·미치환표식0 확인. https://nhncorp.dooray.com/wiki/2668173571253827735/4427340531635271673


## Royal Match 스크린샷 보드 식별 — 2026-09-28
- 사용자 실제 복귀 스크린샷: reactivation-405 / 00405v01_RA. 복귀90개 전체 기존 FlatBuffers 해독기와 configs/royalmatch.yaml 이름 지도 사용. 수동 전사한 고정 장애물67칸 좌표와 목표4종 유일 일치. 9×11, IceCrusher5/Bush6/Hat3/Pink18. 일반405와 다른 판.
- 기본Move27, 화면42로 +15 차이. 적용 원인과 405 선택 이유는 미확인; 이전1005/901 단정 철회. 기존 시뮬레이터의 StartReactivationProgress 상태 분기 누락은 발견됐지만 해당 사례 원인으로 단정하지 않는다. 설명용 시뮬레이터를 확정 예측기로 사용하지 않는다.
- 결과: D:\99.기타\out_royalmatch\returning_user_report\LIVE_DISCREPANCY.md, screenshot_match_verification.json, match_screenshot_board.py, reactivation_405_structure.svg, reactivation_decoded/90 JSON. 보드 식별만 검증; 랜덤 색·부스터 제외. 코어/기존 dirty 파일 보존. 게임 실행/서버 접근/새 게시 없음.





## Royal Match 이미지 레벨 뷰어 개선 — 2026-09-28

- 사용자 지정 ../out_royalmatch/RoyalMatch_viewer.html 갱신. 기존 파일은 RoyalMatch_viewer_이미지개선전_20260928_171603.html로 보존. 일반14,300 + 복귀90 =14,390개; 일반/복귀 필터·정확한 번호/범위 검색·일반405↔복귀405·일반1115↔복귀405 비교·24개 페이지·SVG 저장.

- 이미지90개 연결, 사용타입227종 표현 / 미연결146종 번호·이름 유지. 이름·형태 확인한 스프라이트와 목표/대표 이미지 구분. 꽃밭 사각형·얼음 연속칸 합치기, 받침 부품 조립, 사슬 연결점 오매핑 정정. 주머니/우편함/쿠키는 Spine3.8 공식 파서+삼각형 렌더로 대표 포즈 복원. 게임 실행/서버 연결/외부 데이터 전송 없음.

- 일반맵·이미지는 기존112233.xapk 추출본, 복귀맵은제공38174. 버전동일성/실시간난수/시작부스터/추가이동/런타임상태 재현 아님. 기본R칸과 선택 가능한 색블록예시 구분.

- 검증: 전체14,390개 격자·3,057,905 그리기요소, 복귀405 꽃밭6/얼음기둥5/받침5/모자3 일치, Node DOM대역 초기화·페이지·검색·비교 검사 통과. 공유scene명령 오프라인PNG로1115/405 시각확인. Playwright연결 및 로컬URL정책 제한으로 실제 브라우저 레이아웃/E2E 미검증. 코어변경 없음.

- 재현/후속: ../out_royalmatch/viewer_upgrade/README.md, build_viewer.py, viewer.js, art_mapping.json, installation.json. HTML 28.8MB→11.1MB. Bush/flower Spine atlas크기불일치, clipping필요포즈 임의복원 금지. 리소스·뷰어는로컬만, Git게시 없음.



## Royal Smash 런타임 콜라이더 재생성 판독 — 2026-09-28
- Claude 요청 bmul578gg-8 / 보충 bmul5xmrj-a / Pinata 적용 bmul5fhtq-9 회신 완료 파일: ../out_royalsmash/mailbox/to-claude/20260928-runtime-collider-generators-bmul578gg-8.md. 세션 7125873e-f716-4c4e-95ea-3879d2aebfd9 전송 요청, 최초 30초 확인 상태 queued. 실제 수신/이식 완료와 구분.
- 160종 APK 재판독 vs collider_hierarchy 저장 TRS/형상 차이0, PrefabInstance0. 문제9종은 BeveledBoxCollider Awake/WarmUp 재생성 미이식으로 설명됨. authoring variant/base/m_Modifications는 복구 못함. Size=(1,N,1), Bevel=.08, Build RVA0x391E788 → X/Z-.01, Y-1%, 각13박스.
- ../out_royalsmash/variant_collider_audit_20260928/README.md 진입점. 9종 보충본 + procedural142종 normal/low JSON, 저장원문·PPtr·오프셋·native ASM·파라미터·C# 참고코드 제공. 생성 host 자식만 교체. normal1478/low1354개 생성박스이며 보존된 외부 콜라이더는 미포함. C# Unity6000.0.62f1 참조 컴파일 확인, 대상 Unity 프로젝트 수정/700레벨 시뮬 미수행.
- 원통12종(Ice/Stone/WoodCylinder_2~5)의 layer0 루트 Facet48개는 원본에도 active/enabled로 존재. 생성기 host 밖이라 RebuildFacets가 제거하지 않음. 후속 런타임 처리 미확인; 임의삭제 금지.
- 관성은 원본 생성기 Size*abs(lossyScale), solidTensor*.45, Inverse(obstacle.rotation)*source.rotation. 렌더 AABB와 다름. Can2Square_2가 현 object-physics에 직접항목 없어 원본물성/ai 보충JSON 제공.
- Pinata 이식93종 성공·경고0은 Claude 실행측 보고로 수신. 원본 실제정점 같은좌표(Pole제외): 렌더(2.485543,3.353960,3.055073), 충돌(2.485554,3.353981,3.055070). 렌더localAABB 모서리를 회전하면(3.182276,3.353960,3.712201)로 기존 차이재현. 누락으로 단정할 근거없음; 모든표면일치/분리거동/라이브PhysX검증과 구분.


## Royal Smash 원통 관성·품질 선택 판독 — 2026-09-28
- bmul6ws1s-c / bmul7c31y-d 회신: ../out_royalsmash/mailbox/to-claude/20260928-cylinder-inertia-quality-bmul6ws1s-c.md. 증거·코드 진입점 ../out_royalsmash/quality_inertia_audit_20260928/README.md. 전달 상태는 해당 폴더 delivery_receipt.json 확인.
- Cylinder SolidInertiaTensor RVA0x391F8C8: 저장 Radius*max(abs(lossyScale.x,z)), Height*abs(y). side=m/12*(h²+3r²), roll=m*.5*r², 엔티티별 Vector3배율을 성분별 곱한 반환값에 Obstacle이 .45 적용. 형상 축소보정/NumBoxes/품질은 관성 입력 아님. 59종 배율(1,.5,1), BigWood_1만(.5,1,3). source Transform 회전 유지.
- LowColliderQuality 쓰기: Level.Awake 0x3827AB8, LevelSerializer.Build 0x3829404. Override High(1)/Medium(2) 우선, 그 다음 Config.TryGet<bool>(enforce_level_medium_physics_quality) true, 그 다음 레벨 품질. LevelPhysicsQuality High0/Medium1, effective==1이 low. Build는 엔티티 생성 전에 설정. 현재 라이브 Config 값은 미캡처.
- APK ResourceManager levels/rs 1/ 메인700 재판독, 현재 Unity physicsQuality700/700일치. OverrideNone/enforce없음·false일 때175/223/362만low. 세레벨 원통0이지만 베벨자식 layer14차이 있음. 예전 RoyalSmash_levels_combined860은 main/loop혼합이라 검증소스 사용금지.
- 60 payload 대조, 분기18조합, 자체 비균등/음수scale검산2건, 참고C# Unity6000참조컴파일 통과. 프로젝트 수정/직접물리시뮬 없음.
- Claude bmul7c31y-d 수신: 기존 보충 적용후700레벨 미달233→23, >10m붕괴143→0, 에러0/누락0. 관성미반영 시점의 상대보고이며 원작동일성검증 아님. 남은23은 파고듦만8, lv110낙하1, 중간이동14. 이전전달 queued와달리 후속보고가적용확인증거.


## Royal Smash 잔여 물리 원인 조사·인게임 아트 전달 — 2026-09-28
- 사용자 명시 승인: 퇴근 후 추가 수락 없이 Claude 세션과 직접 조율하며 진행. 대상 7125873e-f716-4c4e-95ea-3879d2aebfd9. 발신 01a0c7d5-8f06-7060-a3cc-d1e5b168b17d. C: Unity 프로젝트는 이쪽에서 수정하지 않고 D: 소스 근거·자료를 전달.
- 잔여 물리 진입점 ../out_royalsmash/mailbox/to-claude/20260928-residual-stability-leads.md, residual_stability_audit_20260928. 149종 루트 Rigidbody 저장 플래그·COM·tensor, 4레벨 원문 좌표·회전 A/B 보충본 제공. 관성 수동값/COM 누락, Start 랜덤 yaw, 회전 받침·Hammer의 FixedUpdate를 실행하지 않는 편집 모드 검사 범위가 후보. 원인 확정/고쳐서 안정화 완료 아님. lv478 drift4.3959지만 낙하0, lv110 drift3.1307/낙하1. 파고듦만 8개 전부 <0.1이라는 요약은 틀리고 lv405/544는 >0.1. 중간11개도 원작과 동등함을 검증하지 않음.
- 아트 진입점 ../out_royalsmash/ingame_art_audit_20260928/README.md. 답신 part1-materials / part2-shaders / part34-environment / part5-hud가 mailbox/to-claude/20260928-ingame-art-*-bmul94s75-f.md에 있음.
- 머티리얼 실객체43, 저장 키워드19조합, 실제 GLSL287(Omni236/Toony51). 동명 재질3쌍을 file#pathID로 구분, 노드/슬롯 배선138프리팹 제공. Phong·MatCap·색/채도·Toony 식 근거 포함. Claude bmulabprq-j에서 적용 보고 수신. shader는 런타임 모든 키워드조합 실측이 아니라 저장 조합/대표 컴파일 프로그램 판독.
- 배경 ReferenceFor0x399A4C4: 유효 index 우선, 나머지 difficulty2 Western/1 Water/그 외 Forest. fallback Forest와 기본선택을 구분. Claude의 bg=-1 전부 Forest 단정을 정정했고 bmulb53o7-o에서 수정 수락. Forest는2048² Sprite 한 장(흙/나무/길 포함); Water 별도 동적 수면은 실행 복원 미완료.
- Ground SG_Ground는 그림자 합성면. 고정 pass Blend SrcAlpha OneMinusSrcAlpha / ZTestAlways / ZWriteOn이 재질 저장 float와 다름. alpha=(1-shadow)*0.6, RGB 단순검정 아님. 원작 GLSL·native mesh7·환경에셋50·카메라/광원 원문 제공. 카메라q X약5도,FOV30은저장초기값,autoFit true/margin.01/max35. 두 광원 회전/ambientFlat/reflection0/fogfalse 전달. PlayerSettings colorSpace1(Linear), generic schema 소비864/868bytes 차이로 전체완전판독 주장은 안함.
- HUD: hud_layout.json 노드491(원래UI부모포함)/컴포넌트1028/난이도팔레트10/폰트참조3. hud_assets/manifest.json 에셋137=Sprite85+Material39+Texture13. Atlas_UI+정확RenderDataKey로 참조복원, 원본rect/pivot/border/PPU와AtlasUV변환/잘림위치·nativeSprite메시 보존. croppedPNG에 원래pivot만 적용하면 크기틀림. 폰트전체glyph테이블·Spine/파티클 실행재현은 미완료.
- 상시HUD 부스터2개 InfiniteBalls/BigBall; Canvas1125x2436 matchHeight1. InfiniteBalls progress는시간표시. Canvas_LevelNumber 자식0이며 상시전체진행도/레벨번호 근거없음. 사용자스크린샷 하단가로선+원형점은 영상오버레이가능성[자체]이나 정체미확인: 조준선으로임의추가금지. Popup 레벨텍스트와상시번호구별.
- 정적검증 JSON23개/PNG128개 해시·크기/메시인덱스·참조오류0. Infinity4곳 문자열화+nonfinite_values.json 위치보존. 자료검증과 Unity실기/화면동등성 별도. validate_ingame_art_handoff_20260928.py로 재검증 가능.
- 최종HUD/환경답신 메시지 bmulbs08j-p 전송 성공(도착확인대기안함). 수신/최종HUD적용완료는 아직 미확인. 영수증 ../out_royalsmash/mailbox/to-claude/20260928-ingame-art-delivery-bmulbs08j-p.json. 다음엔 이 답신과 Claude 회신을 먼저 읽고 중복추출하지 말 것. 로컬 리소스 Git공개게시 안함.


## Royal Smash 카메라·Ground·ColorBox GPU 색상 — 2026-09-29
- 진입점 ../out_royalsmash/camera_ground_audit_20260929/README.md 및 mailbox/to-claude/20260929-camera-ground-colorbox-followup.md. C: 프로젝트 수정 없이 참고자료/진단probe를 Claude로 전달. 사용자 최신 관찰: 전체가 아닌 ColorBox 같은 일부만 어두움.
- FOV native Fit0x399E858/ViewportSpan0x399F830/WidthFits0x399F9A8 판독: includeInactive Table.SurfaceRenderer 중 renderer.enabled=true 월드AABB합집합8모서리, minZ>0/minX>=margin/maxX<=1-margin, 세로·nearclip판정없음. base캐시/매번복원, base30~max35 24회이분탐색 high. CameraFovReference.cs 참조컴파일 경고0/수학7건검산, Unity레벨실행은Claude예정.
- Ground SG_Ground4개Forward 모두 저장Zgradient안읽음. fixed diffuse(.0361055769,.144683689,.00716756145)+SH9+directspec+probe, alpha=(1-rawStrengthShadow)*.6에거리fade없음/RGB별도fade. Blend RGB SrcAlpha/OneMinusSrcAlpha, alpha One/OneMinusSrcAlpha;ZTestAlways/ZWriteOn/CullBack. GroundReference.hlsl 대수식 참고. Scene nodes[].transform에TRS존재; worldy=.0493623614, m_SortingOrder=-3(MeshRenderer96). Claude순서누락수정/HUD적용보고 bmum024ii-t.
- Toony 원본 MatCapColor/SpecularColor flags16HDR가 이식본 일반Color였음. ColorBox9+대조3 저장색숫자는1e-7내같아도 GPU다름. Claude bmum024ii-t의 'GPU변환없음'은 GetVector CPU조회였다고 지적, 제공 ColorPropertyProbe로 실제RTreadback 요구. bmum06q51-v에서정정/확인: Unity6000.0.62f1 D3D11 Linear 1x1ARGBFloat, raw(.6,.34117642,.23759998)→PlainGPU(.318547,.095307,.046052), HDR/Vector는raw그대로. SetColor/SetVector CPU는동일. 실행측GPU보고이며이쪽은C#참조컴파일과sRGB식1e-6검산. 공식최신문서API설명보다해당버전실측우선.
- HDR누락은 ColorBox선택적어두움기여확인. MatCapColor white인JamJarBlue는변환영향없음. ClaudeHDR선언+MatCap/spec분기함께반영완료보고, 화면A/B기여도분리/단독원인확정은보류. Toony26종기능표동봉: MatCap(use,type)=(1,1)14/(0,0)8/(1,0)4. off8종은원래type0이라 albedo대체가아닌불필요가산오류였음. white mask1은무마스크ColorBox식과동일;defaultblack만바꾸지말것.
- JamJarOrange/Purple는원본rim실제있음(candidate49/61/73/85). 대표Blue의rim없음을일반화하면안됨. entry61의662–697/775–808: smoothstep(.5,1,1-max(NV,0))*RimColor*(각광원ramp*atten*lightRGB합),albedo/HColor/SColor곱없음. RST_RimLightMasked 참고함수+원문제공.
- Forward+ 별도미결: savedPC품질RendererMode2, RS셰이더additionalifdef만있고FP대응없음. 설치URP가FP에서_ADDITIONAL_LIGHTS끔. 실제실행pipeline로그/Forward0-only/보조광onoff A/B는Claude후속. 원본대조화면/MatCap GLES→D3D UV/Ground·FOV·rim최종적용은미확인. HUD/그림자순서수정은Claude보고.


## Royal Smash 재질 복원 보강 51객체 — 2026-09-29

- 자료: ../out_royalsmash/material_recovery_20260929/README.md. 핵심43재질 Forward186후보의 사용 속성·텍스처·pass 비교 + 보조8재질/24슬롯 추가. material_catalog.html 및 auxiliary_material_catalog.html.
- 실제 동명 MatCap 충돌: fan_mat/Pinata는98a9236…#1인데 target PNG는1126081…#1. 원본 RGBA 해시로 구분. 보조 fan_mat_02 1도 첫 원본 사용. asset_key를 파일명/GUID까지 유지해야 함.
- 추가 누락 근거: Ice MATCAP off, fan/Cannon multiply-lighten direct*(1+M), 대비3개, Omni rim6, SpecularMap2(R강도/Alpha Phong지수), Cannon Lightmap, Toony AG normal3(AlphaX/GreenY), Cull23. HLSL/원본GLSL/값 제공. 스냅샷 비교이며 이후 Claude 수정분에 그대로 적용하지 않음.
- 핵심 실제 사용 고유텍스처63: sRGB60/linear normal3; mip1=61, Stone normal2만mip11. PNG픽셀 일치와 GPU압축/화면 동등성 구분.
- 보조8: Spiral_mat, fan_mat_02, fan_mat_02 1, M_BlobShadow, lambert8/9/11, WreckingBall_Rope. 원본 APK 재판독8/8 일치. Omni/Toony/URP Lit/URP Unlit 4종 배선 필요. BlobShadow queue2999/Unlit투명은 SG_Ground와 별개. Blocker L/M/S 슬롯 순서 차이 보존. 보조PNG6장 해시 검증.
- JSON/HTML 참조/대수7건 정적검증. Unity 렌더/보조 전체variant 검증 아님. C: 수정 없음. Claude session7125873e-f716-4c4e-95ea-3879d2aebfd9에 최종 bmum211a2-1 전송 완료(도착/반영 미확인), delivery_receipt.json.


## Royal Smash 로비·기본 시스템·UI/승패 연출 — 2026-09-29
- 진입점 ../out_royalsmash/systems_audit_20260929/README.md 및 IMPLEMENTATION_CHECKLIST.md. system_values56 + ui_animation_values65(커브13) = 고유121에셋, 수집134전부 bytes소비검증. code883메서드는 전체판독완료가 아닌 근거탐색집합. C: 수정 안함.
- 시작 코인1500/하트5/하트충전900 원본저장. life configfallback max5/regen30분/enabledtrue, 서버실값아님. 부스터1개가격 Big700 Infinite1500 Barrage500, 초기보유3.
- Continue가격900/1900/3900은 시도내 코인구매횟수. 제공량5/10/15은 currentLevelFailCount+1 경계1~3/4~7/8+. 시작하트선차감없음; 최종실패/포기1회차감. 안정대기min.5/hold.5/max2 및 받침상대앵커판정, 단순속도임계아님.
- 연승+3은 fallback0x39A61D4 및 animator0x380C994 둘다확인, 로그+5 틀림. RawWinStreak는 승리마다+1, firstTry는 attemptNumber==1 별도. +moves용 WinStreakCount는 SuccessPopup.OnEnable에서 feature && currentLevel>=36이면 min(old+1,5): 정상순서35클리어부터. 이어하기0회조건없음. 팝업재활성중복가드는이식측필요.
- 클리어기본15/40/50 즉시지급/레벨증가. .75후로고, 로고기준input.5/confetti.8/autoexit2.55. runId로스킵후콜백무효화. Success텍스트LastReward즉시설정, 기본0부터카운트업근거없음. Spine Enter/Idle/Exit 정확이름과RVA전달. 커브/팝업별Tween/TRS자료제공.
- 미결: 다음레벨라우팅임계, 서버/광고/IAP전체, 강제종료정책, 안정판정회전helper, 보상배수카운트업전체, 모든사운드/파티클. Unity검증은Claude측.
- Claude bmum3kax7-4로 중간값 C:반영보고 받음. 최종자료 bmum3tqpk-5 전송완료(도착대기안함), systems_audit_20260929/delivery_receipt.json. 사용자 UI/클리어/실패연출추가구현과자율전달허용.


## Royal Smash 아이템·오프라인 이벤트·대포공/VFX — 2026-09-29
- 사용자 서버통신없는 교체용, 정식데이터없어도 자체규칙허용. 점심중 사용자에게 추가확인없이 Claude와진행명시. 자료만D:작성, C:편집없음.
- 진입점 ../out_royalsmash/items_events_handoff_20260929/README.md. ITEMS/EVENTS/INTEGRATION + offline_catalog.json. 아이템3종 소비/취소/복구계약(미판독정책자체), 이벤트6종(연승사다리/수집/생존/단기레이스/리그/일일미션) 전부 자체교체용수치. 지갑+claim원자저장, 결정적모의상대, 시도/보상중복가드. config/산술10건검증, Unity실행아님.
- cannon_ball_vfx_20260929/README.md: APK재추출41노드82컴포넌트21자산 native메시7 PNG7 WAV1 검증/export오류0. 일반공geo+shadow M_CannonBall sharedassets1#3→Main/Spec#191 Standart_BulletBall, 큰공geo#4→#166 Big_BulletBall, 큰공shadow일반#3. Bullet_Ball nativeUV보존.
- 발사VFX sharedassets2#38 PS_Cannon 6PS. spawn level2Transform87 TRS체인. 원본 LaunchCurrentBall0x3990E24의Aim/Firetrigger/SpawnTransient/Feedback이일반·아이템분기앞; 읽은 RsCannon스냅샷엔호출없음. SpawnTransient0x39466C4 lifetime1, Spawn은positive lifetime그대로DestroyAfterAsync. root looptrue/length5라도1초회수. URPParticlesUnlit additive5/1, trail5/10.
- cannon_blast.wav 0.936초 mono44100, Sfx#81 volume1/var.1/pitch1/var.15/cooldown.05, Haptic#80raw만. BallController추가확인 postInfiniteLockout.5/autoshootCooldown.2/scaletween.2. 아이템명세/JSON에반영.
- Claude bmum43s4q-6 기본시스템실측보고: 시작하트미차감/continue축분리/연승분리/실패순번+1교정완료. 상대좌표settle간소화, 물리pause미구현, 연출미구현은완료처리안함. 신규최종인계 bmum4qbcr-8 전송완료(도착대기안함), mailbox/to-claude/20260929-items-events-cannon-vfx-handoff.md 및 delivery_receipt.


## UI 추가보충 bmum55rwa-9 — 2026-09-29
- Claude타임라인/runId/물리Scriptpause실측보고받음. Spine/구매퇴장연출/상대받침settle은미완료.
- ../out_royalsmash/ui_followup_20260929/README.md. HLayout14개 전체payload확인: Success BottomButtons spacing0/MiddleCenter/ForceExpand둘true/ControlScale둘false. RewardsLayout spacing-212.21 원본.
- AddMoves15_icon sharedassets1#591 실제존재/추출. 5#564 10#350 20#551 25#439 30#486 포함6Sprite 확보. 15단계10배지대체제거전달.
- Tween52개 Target→component→GO해석 모두sameGO. 보고된31self fallback은노드오류로판정안함; Graphic/CanvasGroup컴포넌트정합은별도. UnityPy숫자임시파일명은실행마다변할수있어logicalfile/pathID/rawSHA매칭사용.
- 최종 bmum5at8c-a 전송완료(도착대기안함), ui_followup delivery_receipt.

- bmum5q8ke-b 추가회신: ui_followup_20260929/REPLY_bmum5q8ke-b.md, vertical_layout_groups.json8개전체해독. GameplaySettings/Buttons level1#6151 spacing183.55/MiddleCenter/padding0/ExpandControlScale전부false. Ball 원본root.67/geo1.38/shadow1.5, localcolliderradius.49/mass1.2; BigBallroot1.5/geo1.38/mass30. 계산1.377대신원본TRS사용전달. Claude공기본Sphere원인실측해결보고수신; VFX아이템이벤트아직미완료.

- bmum6e13b-f 발사VFX/SFX/1초회수실측수신, Animator/Trail미구현. REPLY_bmum6e13b-f.md 보충: 원본Animator level2#102/101/100→sharedassets2controller26/24/25→clip22/20/21 이미animation_dependencies보유. PSroot looptrue보존+1초회수(강제loopfalse원본근거없음). 생략Noise/Trail/Collision/Sub모듈6PS전부enabledfalse확인. BallTrail#59enabledtrue/.12초/minDistance.1, BigBallTrail#1306enabledfalse. 사용자추가승인없이후속진행회신.

## DKBI 필드 복원·셰이더 호환성 정정 및 작업 종료 — 2026-10-08

- 사용자 요청: 오늘 작업 종료, 다음 세션을 위해 메모리 저장. 대형 추출/Unity 실행을 추가로 시작하지 않고 여기서 중단. RAM 주의 및 기존 자료 보존 유지.
- 원본: C:/Kakaogames/DKBI/client, 제품 도깨비의세계 / supercat / 26.102.018, Unity6000.3.24f1, metadata39. 목표는 로그인/실서버 없이 로컬 필드 이동·타겟팅·기본공격·스킬 재현. 설치/원본 수정/실서버 조작 요청 없음.
- 협업 대상 Action Codex: 01a1161c-9898-76c3-8c9e-cffb43af0863, C:/00.SVN/Action/dkbi-replica, 실제 Unity 프로젝트 하위 DKBI. 현재 Editor6000.3.15f1 / URP17.3.0 / Direct3D12 / RTX5060. 이쪽은 D: 근거 추출, Action은 Unity·렌더 자산 반영 담당. 중복 전체 추출 금지.
- 작업 진입점: ../out_dkbi/systems_recovery_20261008/README.txt. 작은 입력 순차 실행 run_limited.py: 프로세스 commit cap1536MB, RSS stop1280MB, free RAM 시작6GiB/중단4GiB, timeout240초. exit0만으로 성공 판단 금지, 로그·실제 산출물 확인.
- ECS field101002: 원본 관계71areas/44spawns/4actorIDs 확보. 초기 진입 필드/서버 활성/단위는 unknown. 루트20Entity와 하위16섹션을 구분. 16child6897entities/261chunks/33hash, TypeInfo32+unknown1, Parent160, PhysicsCollider349 raw후보. shared681/render6394/managed537 연결 및 소스 바이트 검증. managed tail은 Action native PPtr로 PS179/PSRenderer179/GameObject179 확인; header0 GameObject를 null로 취급하지 말 것.
- ECS 명칭/배열/레이아웃은 일부 호환 Entities1.4.3 규칙에 의한 inferred. bit29 chunkcomponent는 일반 entity stride0. LT와 LTW는 Parent160 때문에 동일하지 않음. 스칼라 scale과 XYZ TRS의 근접 비교를 bit-exact로 확대 금지. 활성 렌더·충돌 형태·nav·원작 입력/공격 timing단위·LUT 합성 body는 unknown 유지.
- Action 보고 자산 구현 검증: nativeMesh259, 위치후보6394, 원본 텍스처137 SHA/mips/colorspace, rawMaterial126 확보. 이것은 playable 및 원작 GPU 화면 동등성을 뜻하지 않음. Scene/worldTRS·native mesh검증과 렌더/게임규칙 검증을 구분.
- 원작 URP: urp/HANDOFF.txt 및 metadata/urp_original_declarations.json. asset488B prefix440해석/48opaque, renderer3개 저장 mode2=ForwardPlus를 원본 enum으로 확인. renderer features37. 정확한 원작 패키지 semver/일부 managed body는 unknown; 로컬17.3.0을 원작 버전이라 단정 금지.

### 최중요 정정: 원본 Shader Editor import 성공 주장은 철회
- shader_source/HANDOFF.txt 및 shader_source_availability.json: 설치24640파일 suffix 검사 편집 가능한 source0, TextAsset2657 이름 lead0. 이름 범위 검사이며 모든 payload를 뒤진 부재 증명 아님. catalog UI .shader 두 logical ID는 실제 editable source 아님. Shader.csv430 blank names는 custom shader 부재 근거로 사용 금지.
- TerrainLit 원본 archive25f33c4faf67b7e10e7411fad9fab6fd, Shader class48/pathID998575624410370492, raw1666636B SHA8f1de53774528894dfa0daa75c303e937ef749c73b475e28ff4e3a5fb2a70c55. baked compressedBlob1614745B SHA4c67f81a730c15f9554e6dc0d22a28aafd323ce96bd67c15f4fadcdf81a79892 보존.
- Action bmuzb1l8q-13 / bmuzb5wf4-15: NativeFormatImporter가 native파일1743004B SHA8712c644...를 derived YAML226108B SHAd4b80ae2...로 변경, compressedBlob/platform/stageCounts 제거. 첫 supported=true는 임시 캐시 상태; reimport 후 unsupported. 처음 pre/post unchanged는 이미 변환된 구간이라 원본 보존 검증이 아님. 초기 실메모리 객체를 proxy라고 단정하지도 말 것. raw/immutable bytes는 보존.
- class142 wrapper nativeBundle adapters5개 source/outerversion/SFversion/templateflags/CABnames 모두 raw/blob/typehash 보존하지만 실제 AssetBundle load compatibilityguard 실패. 문자열만 바꿔 재시도하는 해결책은 이미 실패했으므로 반복 금지. TextAsset 정상 bundle 및 UnityPy unmodified resave 실제 load 성공은 Shader load 성공을 의미하지 않음.
- 이쪽 독립 소범위 재판독: shader_source/shader_compatibility_container_audit.json, inspect_shader_compatibility.py. 원본과 정상 TextAsset control 모두 SF22/platform19/TypeTree=true. 정상 control에는 class142+class49만 있고 class48 Shader 없음. 원본 typehash57f0dd2d4ef24437b4655529a673a936. script tree dump hash는 별도 writer방식이므로 adapter canonical hash와 같다고 해석 금지. peak RSS82591744B, cap1536MB, 성공 산출물 확인. 초기 dump_blob API mismatch 실패로그도 보존.
- 다음 실험 지침: shader_source/COMPATIBILITY_FOLLOWUP.txt. Action이 현재 .3.15에서 실제 Shader+Material bundle 생성→load/isSupported/작은 GPU검사→같은 Shader bundle UnityPy unmodified roundtrip 재검사→class48 TypeTree field/type/version/metaFlags 원본 비교. 이후 control 통과 시 작은 원본 fallback shader부터 rawblob 보존 wrapper로 분리검사. D3D12는 실제 환경이지만 현재 loadguard의 원인이라 확정 금지; D3D11 검사는 load통과 뒤 GPU backend 비교로 분리. .3.24 정확 Editor격리시험은 이후 후보, 설치/마이그레이션 없음, 해결 보장 없음.
- 구현은 원본47props/TexEnv/pass/compiled instruction을 근거로 명시 derived REVIEWTerrainLit 검토 셰이더 계속 진행 가능. HLSL 복원은 파생 코드이며 원본 editable source 회수라 표현 금지. 원작 외관 동일성 판단 보류.
- 마지막 MCP 인계: Action session으로 COMPATIBILITY_FOLLOWUP 경로와 위 Shader대조군 실험 전달. 15초 도착 확인 실패, 마지막 상태 queued(도착·반영으로 표시하지 말 것). 바로 전 사용자 최종 답변에도 전달 대기라고 알림. 다음 세션은 Action 새 회신/대조군 결과부터 확인하고 중복 전송·중복 추출하지 말 것.

## REA 선택 연동 — 2026-10-13
- 사용자 morluto/rea 기능 취합 요청. 기존 dirty core/README/MANUAL 변경 보존, 공통 CLI 변경 없이 tools/rea_bridge.py + tests/test_rea_bridge.py + tools/REA_INTEGRATION.md 신규.
- npm REA6.4.0을 out/rea_runtime에만 고정 설치(143패키지), ignore-scripts/omit optional, Node24.18.0. MCP setup/전역 등록/Frida 설치/게임 실행/서버 접속 미수행. upstream HEAD18831491cfb5cb98abbffce0cb04dae12a90fe28 검토; npm과HEAD 동일성 단정 없음.
- bridge: JS/Electron 정적 분석, 일반managed PE/CLI inspect/members, native analyze/search/decompile 호출 및 capabilities. 기본 계획 출력; --execute 필요. Node CLI direct argv, Windows 기존 watchdog 자손 private commit 합산 cap1.5GB/timeout240s/출력256MB 주기감시. OS hardlimit 아님. 대형 JSON 통째 로딩 안 함. 고유 out/rea 실행폴더에 원문/로그/receipt/plan 보존; exit0=process_completed이며 의미완전복원 아님.
- 실제 합성JS2파일 분석: out/rea/rea-hwy2rnkm/evidence.json, parsed2/failure0/import-export 후보 source-range 보존, commit0.369GB/4.53초. capabilities out/rea/rea-pim4l2_c/evidence.json commit0.907GB/4.02초. Ghidra not_configured. Native실분석/managed실DLL/웹관찰/WASM/MCP등록은 아직 미검증 또는 미연결.
- REA managed는 IL2CPP metadata 해독기 아님. 기존 Unity/DOTS/PPtr/FlatBuffers 유지. DKBI metadata39/등록/RVA/셰이더호환을 자동 해결했다는 주장 금지. Native는 엔진 준비 후 작은 함수부터.
- 최종 python -m unittest discover -s tests -t .:512 tests OK, skipped3. 추가테스트7개(인자, SHA, 실패기록, timeout). 초기 .3초 timeout샘플은 Windows interpreter시작 전에 종료돼 partial본문검사 실패; 2초 여유로 수정해 전체 통과. 실제 게임 검증 아님.
- 다음: tools/REA_INTEGRATION.md 사용법. Python tools/rea_bridge.py capabilities --execute 또는 javascript --input <추출JS폴더> --execute. 자동GUI/배치 통합 및 native Ghidra 환경 연결은 후속. 커밋/푸시 없음.


## 2026-10-14 종료 인계 — 기능 강화 게시 및 DKBI 마을 진행

- REA 선택형 정적 분석 어댑터 `tools/rea_bridge.py` 및 `tools/REA_INTEGRATION.md`를 게시 대상으로 정리했다. JS/managed/native, 저장 결과 summary/modules/compare, HAR 항목 선택, native snapshot을 연결했다. REA6.4.0 격리 설치 및 Ghidra12.1.4/JDK21 연결은 로컬 `out/` 설정으로 보존하며 설치물은 Git에 넣지 않는다. 기본 계획 출력, `--execute` 실행, 프로세스 트리 메모리/시간/출력 상한을 유지한다.
- 자체 JS/HAR 및 1KB PE의 정적 실측 통과. native 함수 MOV/RET와 return0x2a 복원, 원본 실행 없음. 같은 native overview snapshot 재사용 36.86초→3.95초, normalized_result 동일. 이것은 DKBI 메서드/RVA/게임 규칙 해결이나 원작 셰이더 호환성 해결을 뜻하지 않는다.
- FibMatrix 디코더/추출 도구, inspect --unity-version, 계층 JSON 외톨이 surrogate 보존 처리를 함께 게시한다. 검증 전 survey 설정 초안, 백업 메모리, 게임 원본 리소스, 추출 결과, 외부 도구 설치물은 게시하지 않는다.
- Action 측 최신 셰이더 control 보고: 현재 Unity6000.3.15 Shader+Material baseline 및 UnityPy1.25.4 unmodified roundtrip 모두 actual bundle load/support/64px GPU green 대조 통과. class48 DFS-normalized2306fields/typeHash 일치. 정본 `C:/00.SVN/Action/dkbi-replica/reference/shader_control_validation.json`. 원작 TerrainLit 재사용은 여전히 미해결이며 파생 검토 셰이더와 구분한다.
- Action 사용자 요청으로 DKBI 마을 복원도 오늘 중단. 최종 회신 bmv7nv11t-1t의 보고: Town70child/76396 native MeshMaterial pairs/mesh1334/material535/texture490 원본 추출 완료. Unity mesh1333/texture490 readback PASS; material39 validated/40files created/496pending. 이전 재질 검증 중이라는 표현을 전체535 검증 완료로 읽지 않는다. 전체 Town 씬/GPU 미완료.
- 최초 NPC 표본은 원문105objects/75sprites/10clips/2textures와 sourceShaderSHA 일치 근거 보존. PNG/Unity NPC 실행 없음. npc_00_0002의 _baseLUT==_lookupTexture256x1/skinLUTnull은 Action 신규 표본이며, PC base45+skin15를 복제하지 않는다. LUT 합성 body/autoGen/MPB/NPC 실제 활성/카메라/nav/입력/전투 동등성 unknown 유지.
- Action 재개 정본: `C:/00.SVN/Action/docs/DKBI_TOWN_RESUME_20261014.md`. 우리 기존 연구 진입점은 `../out_dkbi/systems_recovery_20261008/README.txt`. 양쪽 신규 추출/실험은 오늘 시작하지 않는다.
- 브리지 회신 queued만으로 도착이라 주장하지 않는다. 재전송 MCP에서 delivered 확인 후 Action bmv7nmb8s-1s 및 bmv7nv11t-1t로 1q/1r 수신 확인 완료. 작업 중 ack 지연이었으며 전달 실패로 확정하지 않는다.
- 게시에는 원격 main의 Hades/Graveyard Keeper/DKBI 문서를 보존한 별도 worktree `../levelscope-publish-20261014`를 사용한다. 원래 로컬 작업 폴더의 미커밋 변경/백업은 그대로 남긴다. 최신 기능 사용은 원격 main 또는 게시 worktree를 기준으로 한다.

- 게시 worktree 검증: `python -m unittest discover -s tests -t .` 541개 실행 / 3개 skipped / 실패0 (8.645초). 기존 원격 테스트까지 합친 범위이며 앞선 로컬517개와 구분한다.
