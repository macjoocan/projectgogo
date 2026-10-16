# Goods Hunt 1.9.1 추출 정본 — 2026-10-14

## 1. 결과와 시작점

- 사용자 지시: 다운로드 XAPK 최대 추출 + LD플레이어에 내려받은 추가 데이터 전량 보존·분석.
- 결과 폴더: D:/99.기타/out_goodshunt. HTML은 상위 GoodsHunt_추출보고서.html.
- 패키지 and.lhhpub.goodshunt / versionCode98 / Unity2022.3.62f2 / IL2CPP metadata31.
- APK 정본 results/, 압축 푼 파일 unpacked/, 설정 객체 settings/, 레벨 원문 levels_json/.
- LD 정본 ldplayer/capture_receipt.json → analysis_inventory.json → final_summary.json.
- 검증: verification.json / ldplayer/final_summary.json.archive_verification. 초기 실패·정정 전 결과는 superseded_header 및 invalid_execout에 분리. 이 폴더의 ZIP을 정본과 섞지 않는다.

## 2. APK 로컬 추출 기준치

| 항목 | 결과 |
|---|---:|
| 레벨 에셋 | 1,126 |
| 저장 물품 배치 | 1,511,737 |
| 레벨 디코딩 실패 | 0 |
| 이미지 파일 | 5,658 |
| 0×0 런타임 폰트 텍스처 | 4건 제외 |
| 일반 자산 파일 | 1,175 |
| 메시 객체/OBJ | 1,427 |
| 애니메이션 클립 | 41 |
| 파티클 시스템 | 1,786 |
| Shader 객체 | 240 |
| 씬 / 프리팹 / 노드 | 4 / 1,322 / 17,506 |
| 분리한 설정 객체 | 333 |
| 전체 MB 필드 | 17,393/17,468 |
| MB 미복원 | 75 (원시 바이트 보존) |

레벨 1,126은 로컬 레벨 에셋 수이며 실제 진행도 1~1,126, 고유 플레이맵 전체, 라이브 콘텐츠 전체를 뜻하지 않는다. 난이도/게임모드는 코드값을 그대로 남겼으며 enum명·런타임 분기를 임의로 부여하지 않았다. 제한 시간 저장값50~345초. 난이도0:893 / 1:111 / 2:106 / 3:16.

## 3. LD플레이어 추가 추출

- 장치 emulator-5554, LDPlayer14. 설치본 역시1.9.1/98. 앱 폴더만 복사했으며 다른 앱/계정 폴더를 수집하지 않았다.
- 앱/외부/디바이스 보호/OBB tar4개를 adb pull로 가져와 장치 tar SHA와 일치 확인. 임시 tar는 앱 외부 /data/local/tmp에 만들고 제거했다. 앱 원문은 수정하지 않았다.
- 확보 파일 441개, 실제 새 Unity 번들4개: LevelLoop / holiday_offer_easter_2026_midautumn / fontstackbundle / profilecosmeticcatalog_midautumn.
- LD 컴포넌트18/18 복원, header PPtr/이름 독립 대조18pass/0fail, 미복원0. 원본이 가진 native TypeTree를 우선 읽고 캐시로 폴백한다.
- 레벨 루프 편성 1300행: 기본 참조600, Ocean/SerenityGarden/BrickToys/Beach/Disco/Museum/RetroGames 각100. 별도 LevelLoop_decoded.json / LevelLoop_entries.csv. 이것은 신규 맵1,300개나 초기 진행순서가 아니다. 현재 해당 테마 맵 번들이 실제 캐시에 있었다는 근거도 아니다.
- Firebase 활성화 캐시109 / 기본값80 / 공유 키61 중 다른 값47 / 활성화에만48 / 기본값에만19. remote_configs/ 원문·해독 JSON 및 remote_config_comparison.json. 서버 값을 새로 요청하지 않았다. 클라이언트가 각 값을 실제 게임에 적용하는 호출 경로는 미검증.
- 활성화 DDA: level_start30, timer_speeds=[90,95,100,103,107], bomb_drags=[5,2,1,1,1], score_thresholds=[10,20,40,60], recent_games_weight10. APK/기본캐시와 다름. 단위/산식은 코드 판독 전 확정하지 않는다.
- PlayerPrefs95개 항목, 이벤트 JSON3개 원문 보존. 개인·SDK 상태를 기본 밸런스 수치로 쓰지 않는다.
- 폰트 원문5종: Lalezar-Regular, NotoSansThai-Black, NotoSansJP-Black, NotoSans-Black, NotoSansKR-Black. fontData를 TTF로 복원하고 원시 객체 바이트 안의 동일 구간 및 SHA를 확인했다. fonts/ 및 GoodsHunt_LD_fonts.zip.
- 설치 APK의 ARM64 libil2cpp.so73,706,096B 추가 보존. 원래 XAPK는 armeabi-v7a만 있었음. installed_apks/ 및 installed_native/. 바이너리를 실행하거나 메서드 본문을 복원한 것은 아님.
- 외부 파일은 캡처 전후 size/mtime 동일. 내부는 실행 중 SDK 파일 변경이 있어 전체 스냅샷이 원자적이라고 주장하지 않는다. snapshot_changes.json 참조. 분석 완료 뒤 LD 연결이 끊겨 마지막 재조회는 미검증; 현재 완료 범위는 검증된 캡처 시점까지이다.

## 4. 파일과 검증

- results/GoodsHunt_summary.xlsx: 자동 필드 요약. 파일 ID를 플레이 스테이지 번호로 읽지 않는다.
- results/GoodsHunt_levels_decoded.zip / level_catalog.csv / level_index.json: 이름·번들·SerializedFile·pathID·SHA·배치.
- results/GoodsHunt_sprites.zip + GoodsHunt_preload_sprites.zip: 선로딩 보충본을 함께 사용.
- results/GoodsHunt_assets.zip + GoodsHunt_preload_assets.zip: 사운드·재질·폰트·Spine·텍스트.
- results/GoodsHunt_meshes_obj.zip + supplement/GoodsHunt_meshes_obj.zip: OBJ는 UnityPy 축/감기 규약을 적용한 파생물. 원작 좌표 정합성을 OBJ만으로 주장하지 않는다.
- results/GoodsHunt_native_raw.zip / GoodsHunt_structured_objects.zip / supplement/: 원시 바이트와 타입 필드. native_object_index.jsonl이 원본 소스·파일·pathID·SHA를 연결한다.
- serialized_file_references.jsonl: 원본 fileID 외부 참조표. pathID만으로 번들 전체에서 검색하지 않는다.
- Shader는 compiled blob·프로퍼티 확보까지. 편집 가능한 원작 HLSL이나 Editor/GPU 호환성 확보 주장은 하지 않는다.
- primary/preload/설정/LD ZIP CRC 및 casefold 충돌0 확인. 압축을 푼 대상은 ZIP 항목수=실제 파일수 확인. 대형 native raw/structured ZIP은 CRC·SHA로 검사하고 디스크 전체 해제는 하지 않았다.
- input_prepared는 원본 base/ABI APK의 파일 크기·CRC와 대조됨. 실행 명령/종료코드/시간/메모리는 *_receipt.json에 보존.

## 5. 제한과 재개

- APK의 MB75개(주로 UniText56, 참조없음11, 기타8)와 바이너리 Addressables 주소 매핑은 미결. 원시 바이트는 있다. 전체 native 미복원76에는 catalog TextAsset1도 포함되므로 MB 실패와 혼동하지 않는다.
- MB 재구성은 full-byte 소비만 검사하면 부족하다. m_Enabled 정렬/Array→vector 소비표현을 보정하고 원래 Unity 헤더의 name/m_Script/m_GameObject PPtr를 대조했다. 캐시는 동일metadata/libSHA/Unity버전과 연결한다.
- 초기 메모리 감시2.5GB가 넘는 경로를 중단했다. 주기 감시라 한 차례8.19GB 순간 할당이 관측됐다. 이후 배열 할당 전 길이 검사와 엔진별 별도 캐시로 수정했고, 성공 단계 피크는 대략0.02~1.54GB였다. OS 하드 메모리 제한으로 오해하지 않는다.
- 게임 실행/라이브 통신 재현/보호조치 우회/원작 화면 동일성/Unity 이식은 수행하지 않았다.
- 사내 리서치 범위이며 리소스·앱 상태·서버 캐시는 Git이나 외부 공유에 올리지 않는다. 공개 가능한 재사용 기법만 별도로 정리한다.
- 추가 작업은 combined_baseline.json, ldplayer/final_summary.json, settings_index.json부터 시작한다. 외부 맵팩 주소가 있다고 이미 내려받은 맵이라 세지 않는다.
