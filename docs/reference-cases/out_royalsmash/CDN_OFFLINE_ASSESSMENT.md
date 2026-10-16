# Royal Smash CDN 재시도 판단

> 2026-09-16 갱신: 사용자가 일반 다운로드 기록을 허용하고 인증·보호 우회는 금지하는 조건으로 변경했다. 카탈로그 원격 번들 31개를 정상 HTTPS GET으로 확보했으며 크기·내용 CRC 31개 모두 검증됐다. 최신 결과는 `CDN_PUBLIC_RESULT.md`를 읽는다. 아래는 조건 변경 전의 이력이다.

대상: Royal Smash 1.13.359 / 점검일: 2026-09-15

## 적용한 작업 조건

사용자 조건: 게임사가 작업을 알 수 있는 상황이면 중단.
이번 점검은 로컬 XAPK와 기존 dump.cs를 읽는 정적 분석만 수행했다.
게임 실행, CDN DNS 조회, HTTP 요청, 다운로드는 수행하지 않았다.
이 기록은 이번 점검의 실행 내역이며, PC 전체의 다른 프로그램이나 과거 세션의 통신을 보증하는 기록은 아니다.

## 로컬 파일에서 확인한 근거

- 원본: `C:\Users\NHN\Downloads\Royal+Smash!+-+Physics+Puzzle_1.13.359_APKPure.xapk`
- `UnityDataAssetPack.apk/assets/aa/catalog.bin`에
  `{Core.CDNAssetManagement.AddressablePathHelper.RemoteLoadPath}`가 들어 있다.
- base APK의 정상 IL2CPP metadata(version 31)에 기본 호스트 문자열
  `https://cdn.cyphergames.com`과 설정 키 `asset_cdn_base_url`이 있다.
- 같은 metadata에서 경로 형식 `/royal-smash/v1/{0}/{1}/{2}`를 확인했다.
  세 자리의 정확한 대입 순서 및 실행 시 설정값은 이번 점검에서 확정하지 않았다.
- `il2cpp_dump/dump.cs:494537`의 AddressablePathHelper는 RemoteLoadPath,
  ResolveBaseUrl, GetCDNEnvironment, GetVersion, GetPlatform 및 fallback 처리 함수를 가진다.
  따라서 단순한 고정 URL 목록이 아니라 실행 시 구성되는 경로다.
- `assets/aa/settings.json`은 로컬 catalog.bin을 사용하며
  `m_DisableCatalogUpdateOnStart`가 true다. 이것만으로 모든 원격 다운로드가 차단된다고 해석하면 안 된다.

## 이전 실패와의 구분

기존 README에는 로컬 레벨 860개 추출과 원격 배포분 31개 미확보가 기록돼 있다.
이 수치는 이전 기록에서 가져왔으며 이번에 카탈로그 전체를 다시 디코딩해 검증한 수치는 아니다.
해당 기록에는 CDN HTTP 오류 코드나 실제 다운로드 실패 응답이 제시돼 있지 않다.
물리 컴포넌트 값 미복원은 m_Script/IL2CPP 클래스 연결 문제로 기록돼 있으며,
CDN 번들을 얻는 것만으로 그 문제가 해결된다고 볼 수 없다.

## 판정 및 중단 지점

정적 자료만으로 요청 후보 경로를 더 분석할 기술적 근거는 있다.
그러나 현재 파일 존재 여부, HTTP 상태, 인증 요구, 실제 원격 배포 내용은 외부 요청 없이 확정할 수 없다.
그 요청은 상대 인프라에 IP, 요청 경로, 시각 등의 기록을 남길 수 있으므로 사용자 조건을 충족한다고 보장할 수 없다.

**실제 CDN 재시도는 요청을 보내기 전에 중단한다.**
현재 CDN 자료는 추가 확보되지 않았다. 이미 확보한 로컬 파일 분석은 별도로 가능하다.
