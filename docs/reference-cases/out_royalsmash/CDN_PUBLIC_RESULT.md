# Royal Smash 일반 CDN 다운로드 결과

> 후속 갱신: 받은 31개 번들의 오프라인 추출까지 완료했다. PNG 1,471개, 컴포넌트 JSON 4,684개, 프리팹 90개. 최신 산출물·검증·제한은 `cdn_extracted/README.md` 참조. 아래는 다운로드 단계의 결과와 당시 다음 작업 기록이다.

2026-09-16 / APK 1.13.359 / CDN build 359.

## 결과

카탈로그 원격 번들 **31/31개**, **77,351,176 bytes** 다운로드 및 검증 완료.
각 파일의 HTTP 200 응답, Content-Length, UnityFS 내부 크기, 카탈로그 크기가 일치했다.
오프라인 압축 해제 후 내용 CRC32도 카탈로그 기대값과 **31/31개 일치**했다.
SHA-256은 저장한 파일의 재현·변경 확인용으로 기록했다. 카탈로그 Hash128을 SHA-256과 비교한 것은 아니다.

## 사용자가 변경한 조건

일반적인 다운로드 요청 기록은 허용한다. 인증 우회·보호 기능 우회는 하지 않는다.
이번에는 계정·쿠키·인증 토큰 없이 카탈로그에 명시된 파일에만 HTTPS GET을 보냈다.
User-Agent는 `RoyalSmash-AssetDownload/1.0`으로 작업 종류를 표시했다.
게임 클라이언트 위장, 로그인, 인증 응답 조작, 인증서 검사 해제, URL 열거, 리디렉션 추적을 하지 않았다.
게임/에뮬레이터를 실행하거나 방화벽을 변경하지 않았다. 라이선스 오류를 수정한 결과가 아니다.
이 조건 변경은 Royal Smash의 이번 다운로드 작업에 적용되며 다른 게임 작업의 접속 권한으로 확대하지 않는다.

## 주소를 확정한 근거

- IL2CPP `AddressablePathHelper.get_RemoteLoadPath` RVA `0x397f468`의 호출·인자 순서: 환경 / 플랫폼 / 빌드번호.
- ELF 재배치와 정상 metadata 문자열 대조: `https://cdn.cyphergames.com`, `/royal-smash/v1/{0}/{1}/{2}`, `Android`.
- base APK `assets/bin/Data/sharedassets0.assets.split13`의 BuildParameters: `359`, `prod`.
- 로컬 `addressablestools` 1.0.0으로 카탈로그 객체를 해석: 전체 번들 83개, RemoteLoadPath 대상 31개.
- 실제 요청 기본 경로: `https://cdn.cyphergames.com/royal-smash/v1/prod/Android/359`.
- 단순 문자열 검색에 보이는 해시 포함 이름은 실제 internal_id와 달랐다. 다운로드에는 정식으로 해석한 internal_id만 사용했다.

## 파일과 실행 기록

- 원본 다운로드: `cdn_public/bundles/` (하위 경로 유지).
- 대상·카탈로그 크기/CRC: `cdn_public/request_plan.json`.
- 최초 샌드박스 요청: `requests_20260916T044923Z.json` — 로컬 WinError 10013, HTTP 응답 없음. 서버가 거부했다고 해석하지 않는다.
- 승인 후 첫 정상 GET: `requests_20260916T045209Z.json` — 1개.
- 후속 다운로드: `requests_20260916T045233Z.json` — 기존 파일 1개 재사용, 나머지 30개 정상 GET.
- 전체 독립 로컬 재검사: `cdn_public/validation.json`.
- 도구: `inspect_cdn_local.py`, `download_public_cdn.py`, `verify_public_cdn.py`.

검증은 파일을 하나씩 처리하며 압축 해제 상한을 적용했다. LZMA/LZ4 해제는 일반 압축 처리이며 실행·복호화·보호 제거가 아니다.
CRC 검사 기준은 [Unity 공식 설명](https://docs.unity3d.com/cn/2023.1/Manual/AssetBundles-Integrity.html)의 비압축 내용 기준과 맞췄다.

## 제한 및 다음 작업

파일명 기준 분류: 게임 배경 2개, 이벤트 10개, 로딩 화면 5개, 메인 메뉴 포스터 14개.
기존 README의 “원격 번들 약 700개 레벨” 추정은 입증되지 않았으며 현재 성과로 인용하지 않는다.
이번 완료 범위는 원본 번들 확보와 무결성 검증이다. 새 밸런스 테이블, 추가 레벨, 최종 플레이 수치를 복원했다는 뜻이 아니다.
다음 단계는 확보한 파일의 오프라인 에셋/설정 분석이다. 현재 levelscope venv의 Python312 실행 경로가 사라져 있으므로 일반 추출 CLI를 실행하기 전 환경 점검이 필요하다.
`FINAL_OFFLINE_CONCLUSION.md`는 이전 전면 오프라인 조건에서의 이력으로 보존한다.
