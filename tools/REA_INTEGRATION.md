# REA 선택 연동 — 2026-10-14

현재는 저장 Evidence 요약/모듈 페이지/JS 버전 비교, 오프라인 HAR 선택 조회,
native 함수/xrefs/trace 및 Ghidra 진단·snapshot 호출까지 연결했다.
아래의 10/13 Ghidra 미설정 기록은 당시 상태이며 최신 연결 결과가 우선한다.

기존 Unity/Addressables 에셋·레벨 추출에 별도 코드 분석 엔진을 붙이는 첫 단계다.
`tools/rea_bridge.py`는 REA CLI를 별도 프로세스로 호출하고 결과 원문을 보존한다.
기존 `levelscope run` 및 게임 플러그인 경로는 바꾸지 않았다.

## 실제 연결 범위

| 분석 대상 | 연결 명령 | 현재 검증 |
|---|---|---|
| 추출한 JS/Electron 폴더·ASAR | javascript | 합성 JS 2파일 정적 분석 통과 |
| 일반 .NET PE/CLI DLL | managed / managed-members / managed-compare | System.Runtime.dll 정적 identity 확인; member/비교 경로는 미실측 |
| 네이티브 PE | native / native-search / native-decompile / native-function / native-xrefs / native-trace | Ghidra12.1.4 연결, 자체 x64 PE 함수 판독 검증; 다른 형식/게임/나머지 연산 미실측 |
| 저장된 분석 결과 | summary / modules / compare | 합성 JS 결과 재사용·페이지·변경 버전 비교 통과 |
| 저장 네트워크 기록 | har --record N | HAR1.2 합성 기록 항목 선택 통과; 서버에 접속하지 않음 |
| 엔진 준비 상태 | capabilities | 실제 실행/JSON 저장 통과 |
| 웹 DOM·네트워크·WASM | upstream 지원 범위 확인 | 현재 어댑터에는 연결하지 않음 |

REA managed 분석은 **IL2CPP metadata 해독기가 아니다.** Unity 에셋·DOTS·PPtr·FlatBuffers는
기존 도구가 계속 담당한다. DKBI GameAssembly 본문 분석을 보강할 가능성은 있지만,
metadata v39 등록/메서드 주소 복원이 자동 해결됐다는 뜻은 아니다.
셰이더 Editor 호환성 오류를 이 연동으로 고쳤다는 주장도 하지 않는다.

## 로컬 설치 상태

- npm 배포 REA `6.4.0`, Node `24.18.0`.
- 격리 경로: `out/rea_runtime/node_modules/rea-agents`.
- 설치 명령: `npm.cmd install --prefix out/rea_runtime --ignore-scripts --omit=optional --no-audit --no-fund --save-exact rea-agents@6.4.0`.
- 설치 스크립트 및 선택 Frida 의존성 미실행. 자동 MCP setup·전역 설정·에이전트 스킬 등록 미수행.
- 재설치는 위 명령으로 할 수 있다. native helper가 필요한 기능의 준비 완료를 이 설치로 주장하지 않는다.
- upstream 검토 HEAD: `18831491cfb5cb98abbffce0cb04dae12a90fe28`.
  npm 6.4.0과 해당 HEAD 코드 전체가 같다는 주장은 하지 않는다.

## 사용

기본은 명령 계획 출력이다. `--execute`를 붙여야 실제 분석한다.

```powershell
python tools/rea_bridge.py capabilities --execute
python tools/rea_bridge.py javascript --input "D:/apps/extracted-game" --execute
python tools/rea_bridge.py managed --input "D:/apps/Assembly-CSharp.dll" --execute
python tools/rea_bridge.py managed-members --input "D:/apps/Assembly-CSharp.dll" --execute
python tools/rea_bridge.py summary --input "out/rea/<previous-run>/evidence.json" --execute
python tools/rea_bridge.py modules --input "out/rea/<previous-run>/evidence.json" --offset 0 --limit 20 --execute
python tools/rea_bridge.py compare --input "left-evidence.json" --other "right-evidence.json" --execute
python tools/rea_bridge.py har --input "saved.har" --record 0 --record 3 --execute
python tools/rea_bridge.py native-doctor --execute
python tools/rea_bridge.py native-function --input "sample.exe" --query "0x140001000" --cap 2.5 --execute
python tools/rea_bridge.py native --input "sample.exe" --snapshot "out/rea/sample-snapshot.json" --cap 2.5 --execute
python tools/rea_bridge.py native-search --input "D:/apps/GameAssembly.dll" --query "FindTarget" --provider ghidra
python tools/rea_bridge.py native-decompile --input "D:/apps/GameAssembly.dll" --query "0x1000" --provider ghidra
```

새 설치 경로는 `--cli .../rea-agents/scripts/rea.mjs`로 지정한다. .cmd·셸을 거치지 않고
Node와 인자 배열을 직접 실행해 경로/검색 문자열을 셸 코드로 해석하지 않는다.
입력 폴더 안에 출력 폴더를 넣으면 원본 분석 범위가 오염되므로 거부한다.

Windows 프로세스 **자손 전체 private commit**을 기존 watchdog으로 합산한다.
기본 `--cap 1.5`GB / `--timeout 240`초 / `--max-output-mb 256`MB.
이는 주기 감시 방식이며 순간 할당을 막는 OS 하드 제한은 아니다.
Node heap은 768MB로 설정; Ghidra Java 메모리는 별도 프로세스 트리 합산에 포함된다.
사용자가 따로 시작한 IDA 서버처럼 자손이 아닌 프로세스는 이 감시 범위 밖이다.
무거운 원본 DLL 전체 분석을 자동 시작하지 않는다.

각 실행은 `out/rea/rea-<unique>/`에 따로 남긴다:

- `evidence.json`: REA stdout 원문; 중단 시 불완전 원문도 보존.
- `stderr.log`: 진행 메시지/오류.
- `receipt.json`: 종료코드, 중단 이유, 시간, 최고 커밋, 원문 SHA256.
- `plan.json`: 명령, 입력 파일 SHA256, 제한. 폴더 전체 해시는 어댑터에서 만들지 않는다.

4MB보다 큰 JSON은 통째 파싱하지 않고 디스크에 남긴다.
`process_completed`는 프로세스 종료 성공만 의미한다. 원문 안의 partial/unknown/limitations,
source location, inferred/observed를 별도로 검토해야 한다. 원문을 자체 추정값으로 덮어쓰지 않는다.

summary/modules/compare는 원본 게임을 다시 열지 않고 저장 Evidence를 이용한다.
워크플로 request를 파일로 스트리밍 작성하고 upstream에 구조·출처 검증을 맡긴다.
inline Evidence128MiB, 모듈 페이지 limit1..1000의 어댑터 제한이 있다.
`compare`는 서로 다른 JS Application Evidence가 필요하며, 아무 JSON이나 비교하는 도구가 아니다.
오래된 결과 요약을 현재 원본의 재검증으로 읽지 않는다.
종료코드0이어도 구조화된 upstream error 또는 작은 stdout의 invalid JSON이면 실패 기록한다.

native snapshot은 overview 명령에만 연결했다. 원본과 동일 경로로 저장하는 것을 거부한다.
snapshot은 정확한 입력/명령/provider 조건의 관찰 재사용이며 Ghidra 데이터베이스 전체 백업이 아니다.
HAR6.4.0은 har/mitmproxy upstream 형식 중 **HAR만 이 어댑터에 연결**했다.
현재 배포본에는 SAZ가 없으므로 최신 main 문서만 보고 SAZ 지원을 주장하지 않는다.

## Ghidra 설치·연결

- 공식 Ghidra12.1.4를 `D:/99.기타/analysis-tools/ghidra/ghidra_12.1.4_PUBLIC`에 격리 설치.
- 공식 release digest와 다운로드 SHA256 일치 확인. 영수증은 설치 상위폴더 installation.json.
- 기존 full JDK21 사용. 전역 PATH/JAVA_HOME/MCP 설정을 변경하지 않았다.
- `out/rea_runtime/bridge-settings.json`에 프로젝트별 ghidra_dir만 기록.
  `--ghidra-dir`가 우선하며 다른 경로는 `--settings`로 지정한다.
- native 함수 실측은1.54GB로 기본1.5GB보다 컸으므로 작은 native 검사에는 `--cap 2.5`를 지정한다.
  대형 게임 DLL의 성공이나 전체게임 분석 메모리를 이 값으로 보장하지 않는다.

## 검증 기록

합성 샘플 `out/rea_fixture/main.js`, `reward.js`: 두 파일 모두 파싱, parse failure0,
import와 export 후보 관계 및 source-range 보존. 대상 JS 실행하지 않음.
실제 결과 `out/rea/rea-hwy2rnkm/evidence.json`, 최고 트리 커밋0.369GB,4.53초.
capabilities 실제 결과 `out/rea/rea-pim4l2_c/evidence.json`, 최고0.907GB,4.02초.
10/13 당시 Ghidra는 `not_configured`였다. 아래10/14 실측이 현재 상태다.

10/14: summary0.307GB/3.19초, modules0.307GB/3.06초,
JS version compare0.328GB/3.56초(unchanged1/changed1/added5/removed5 후보),
HAR 선택0.353GB/4.06초. 모두 저장 결과/자체 표본이며 실제 게임 동작 판정이 아니다.
System.Runtime.dll의 일반 managed identity를 정적으로 읽었으며0.304GB/3.22초, DLL 실행없음.
Ghidra doctor 준비 확인 뒤1KB 자체 PE 함수에서 `MOV EAX,0x2a; RET`와 `return 0x2a` 복원.
전체 함수6바이트/주소0x140001000/원본 SHA 검증,43.23초/최고1.543GB/상한2.5GB.
Native fixture 및 어떤 원작 프로그램도 실행하지 않았다.

## 다음 단계

1. 현재 기능을 사용할 때 실제 보유 JS/일반 managed DLL 한 개부터 표본 검증.
2. Ghidra 연결과 작은 자체 PE를 넘어, 실제 승인된 DLL의 함수 하나부터 표본 검증.
3. MCP가 필요하면 REA 자체 서버 등록을 별도 진행. 현재 세션에는 등록하지 않았다.
4. 웹 분석은 브라우저 관찰 기능을 별도 연결; 실제 게임 플레이와 정적 JS 분석을 구별.

## 라이선스·근거

REA 자체는 MIT이며 관련 저작권·라이선스 고지는 설치 패키지에 보존했다.
전체 소스를 복사해 우리 코어에 편입하지 않고 외부 CLI로 호출한다.
Ghidra/Hopper/IDA 및 다른 의존성의 라이선스는 각각 적용된다.

- [저장소/기능](https://github.com/morluto/rea)
- [CLI·출력·IL2CPP 제한](https://github.com/morluto/rea/blob/main/docs/cli.md)
- [Windows Ghidra](https://github.com/morluto/rea/blob/main/docs/windows-ghidra-p0.md)
- [MIT](https://github.com/morluto/rea/blob/main/LICENSE)

기능 목록은 upstream 문서, 실측은 위 로컬 샘플 결과에 근거한다.

10/13 회귀 검사:512개 실행/3개 skipped/실패0.
10/14 최종 회귀 검사:517개 실행/3개 skipped/실패0. 어댑터 테스트12개.


스냅샷 실제검증: 자체 PE overview 첫36.86초/1.545GB → 동일query재사용3.95초/0.929GB. normalized_result동일,원본SHA변화없음. out/rea/upgrade_validation_20261014.json passed=true(8내용대조). 다른query/전체게임의성능보장아님.
