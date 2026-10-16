# Royal Smash 원본 APK 레벨 재검증 — 2026-09-16

## 결론

**추가 레벨 데이터는 CDN이 아니라 원본 APK 안에 이미 있었다.** 원본 XAPK의 세 APK와 로컬 분석용 복사본 SHA-256이 모두 일치함을 확인한 뒤, Unity 파일 2,285개를 순차 검사했다. 읽기 오류 0건, 레벨 JSON TextAsset 1,560개를 확인했다.

| 원본 컬렉션 | 리소스 경로 | 레벨 개수 | 번호 범위 |
|---|---|---:|---|
| 메인 `RS 1` | `levels/rs 1/` | 700 | 00001–00700, 누락 없음 |
| 마스터/루프 `RS1 Loop` | `levels/rs1 loop/` | 860 | 00001–00860, 누락 없음 |

두 컬렉션 합계는 1,560개 레코드이며, JSON 내용이 완전히 같은 것을 제외하면 1,477종이다. **1,560개가 연속된 메인 스테이지라는 뜻이 아니다.**

## 기존 860개 ZIP의 문제

`RoyalSmash_levels.zip`에는 00001.json–00860.json만 있다. 원본은 00001–00700 번호가 두 컬렉션에서 겹친다. 기존 ZIP을 원본 JSON과 의미상 비교하면 같은 번호 기준으로 메인 349개 + 루프 511개가 일치한다. 따라서 기존 ZIP은 메인 860개도, 루프 860개도 아닌 **컬렉션이 섞인 결과**다.

- 원본 대비 컬렉션별 레코드 700개가 기존 ZIP에 독립 항목으로 보존되지 않았다.
- 다른 번호의 동일 내용까지 고려하면, 기존 ZIP 어디에도 내용이 없는 원본 오브젝트는 660개다.
- 그 660개의 내용 중복을 다시 제외하면 **새로 확인한 고유 레벨 데이터 655종**이다.
- 기존 ZIP의 고유 내용은 822종이며, 모두 원본에서 확인됐다. 원본 고유 내용 1,477 = 기존 822 + 추가 655.

이름만으로 병합/선별되어 컬렉션 구분이 유실된 정황은 확실하지만, 과거 실행 코드와 로그를 재현하지 않았으므로 정확히 어느 코드가 덮어썼는지는 이번에 확정하지 않았다. 기존 ZIP은 증거 보존을 위해 변경하지 않았다. 기존 combined.json/밸런스 CSV가 올바른 메인 순서를 나타낸다고 가정해서도 안 된다.

## 원본에서 확인한 직접 근거

입력: `C:\Users\NHN\Downloads\Royal+Smash!+-+Physics+Puzzle_1.13.359_APKPure.xapk`.

1. base APK `assets/bin/Data/globalgamemanagers`의 `ResourceManager.m_Container`에 컬렉션 경로가 명시돼 있다. 각각의 `m_FileID`를 그 파일의 `externals[m_FileID-1]`에 대응시키고, 대상 파일 경로 + `m_PathID`로 레벨을 연결했다. 이름만으로 추정하지 않았다. 레벨 1,560개 전부 리소스 경로와 일치한다.
2. `UnityDataAssetPack.apk`의 실제 TextAsset 내용:
   - `assets/bin/Data/dcaf29c27f5974053a2b64d815aa176d`: `main` = `RS 1`.
   - `assets/bin/Data/2b275357a3aba4db596480f53ad7f2d5`: `master` = `RS1 Loop`.
   - `assets/bin/Data/da2bd601be43445fc899540e08f320ca`: `included` = `RS 1\nRS1 Loop`.
3. 기존 ZIP에 없는 실제 레벨 예:
   - `levels/rs 1/00380` → `assets/bin/Data/001075a442a7e4a0a9a448fa1729c25b`, TextAsset path_id 1, MoveCount 20, Entities 63.
   - `levels/rs 1/00641` → `assets/bin/Data/001609a6818124b859d87c86d204fc9d`, TextAsset path_id 1, MoveCount 19, Entities 152.

## 별도 원격 레벨 배포 단서

원본 metadata에서 생성된 `il2cpp_dump/dump.cs`에는 다음 구조가 있다.

- 455117행 `Core.LevelCollectionService`: MainCollection, MasterCollection, IncludedCollections.
- 455697행 `Core.LevelLoaderService`: LoadData(collection, index), Count(collection).
- 456146행 `RemoteLevels.ManifestPlan`: Url, Sha, SizeBytes.
- 456266행 `Core.RemoteLevels`: HookRemoteConfig, ReadManifestPlan, DownloadToFile, ExtractSafe, ValidateLevels, ResolveDiskRoot.

이는 Addressables 아트 번들과 별도의 레벨 묶음 갱신 경로가 있음을 뒷받침한다. **현재 서버 manifest 값, URL, 추가 레벨 수, 실제 활성화 여부는 확인하지 않았다.** 이번 로컬 700개 메인 컬렉션을 과거의 “CDN 약 700개 레벨” 추정에 끼워 맞추지 않는다. 700개는 현재 APK에 직접 존재하는 메인 컬렉션의 검증된 개수다.

## 검증 산출물과 범위

- `LOCAL_LEVEL_APK_AUDIT.json`: 세 APK 원본 일치 SHA-256, 파일별 객체 집계, 1,560개 레벨의 출처/내용 해시/기존 ZIP 대조/리소스 매핑.
- `local_level_code_evidence.json`: 관련 클래스 선언과 원본 dump.cs 행 번호.
- `local_level_catalog_inventory.json`: 기존 Addressables 카탈로그 전체 위치 목록.
- `inspect_local_level_evidence.py --audit` 후 `--map`: 재검증 절차.

실제 JSON 파싱과 내용 비교까지 수행했다. 읽은 수준을 넘어서 신규 컬렉션별 ZIP을 만들거나 게임 프로젝트를 수정하지는 않았다. 코드 스텁은 원본 메서드 구현 복원이 아니며, 모든 레벨의 실제 플레이 가능성·서버 덮어쓰기·현재 라이브 밸런스도 검증하지 않았다.

APK/게임 실행, 에뮬레이터 가동, 게임사/CDN 접속, 인증·보호 우회는 하지 않았다. 메모리는 한 소스씩 처리했으며 관측 최대 private memory는 272,986,112 bytes(약 260 MiB)였다. 무관한 Spine 바이너리의 surrogate 문자를 JSON에 기록할 때 최초 저장 실패가 있었고, ASCII JSON escape로 보존하도록 수정 후 전체 검사를 재실행해 보고서 저장을 완료했다.

다음 작업은 **컬렉션 경로를 유지한 재추출과 기존 게임 입력 데이터 교체 전 비교 검증**이다. 원본 번호만으로 다시 합치면 같은 문제가 반복된다.
