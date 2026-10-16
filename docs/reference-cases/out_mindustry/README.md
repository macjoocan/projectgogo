# Mindustry 8 (159.7, Android) — 추출 데이터

입력: `Mindustry_8-official-159.7_APKPure.apk` (libGDX / Java, 오픈소스 GPL)
levelscope(Unity 전용) 범위 밖이라 libGDX/Arc 포맷 전용 추출 도구를 별도 작성.

## 산출물

| 경로 | 내용 |
|---|---|
| `Mindustry_balance.json` | **밸런스 수치** — 블록 425·유닛 61·아이템 22·액체 11·상태 23·탄환·행성·날씨. `classes.dex` 바이트코드에서 추출 |
| `Mindustry_content_catalog.json` | **콘텐츠 카탈로그** — 블록 411·유닛 60·아이템 22·액체 11·상태 20 (이름·설명·상세) |
| `Mindustry_localization.zip` | 다국어 번들 36종 (`.properties`, 평문 key=value 전문) |
| `Mindustry_maps.json` | 기본 맵 114개 메타데이터 (이름·저자·크기·규칙·생성필터·웨이브) |
| `Mindustry_schematics.json` | 스키매틱 210개 (크기·태그·사용 블록 목록·타일 수) |
| `Mindustry_sprites.zip` | 스프라이트 5,182종 PNG (Arc 아틀라스 4페이지 슬라이싱) |
| `Mindustry_audio.zip` | 효과음·음악 221종 OGG (원본 그대로) |
| `serpulo.json` | 세르풀로 행성 정의 |

## 밸런스 수치 (`Mindustry_balance.json`)

Mindustry 는 블록/유닛의 수치 스탯을 데이터 파일이 아니라 Java 코드에 하드코딩한다 —
APK 에서는 `classes.dex`(7.6MB) 바이트코드 안이다. 각 콘텐츠는 로스터 `load()` 에서
`new 블록("이름"){{ health=...; reload=...; }}` 형태의 익명 초기화 블록으로 생성되며,
이 초기화 블록의 `const`→`iput` 시퀀스를 DEX 바이트코드에서 추적해 필드값을 복원했다.

검증(알려진 값과 대조): dagger 체력 150·이동 0.5, mace 체력 550·방어 4, copper 경도 1·
비용 0.5, thorium 방사능 1.0·경도 4, duo 재장전 20·사거리 160·체력 250, water 열용량 0.4 —
모두 실제 수치와 일치.

**범위:** 각 콘텐츠가 **명시적으로 튜닝한 값**을 담는다(디자이너가 설정한 값). 상위 클래스
생성자의 기본값(예: `Router` 의 기본 체력)과 **배열형 필드(요구자원 `requirements`,
`buildCost` 등 ItemStack 배열)는 포함하지 않는다** — 각각 super 체인 추적·배열 생성 명령
해석이 필요하다. 명시 튜닝값만으로도 체력·데미지·사거리·재장전·생산량·이동속도 등 핵심
전투/생산 밸런스는 대부분 포함된다(블록 386/425, 유닛 61/61 이 스탯 보유).
정확한 원본은 오픈소스 저장소 `core/src/mindustry/content/` 에서도 확인 가능.

여기에 **콘텐츠 카탈로그 + 로컬라이즈 설명 + 스프라이트**를 더하면 전체 콘텐츠 구성·역할·
비주얼·수치까지 파악 가능하다.

## 추출 방법 (요약)

- 스키매틱 `.msch`: `msch`+버전 헤더 뒤 zlib. 해제하면 크기·태그·블록 사전·타일.
- 맵 `.msav`: zlib 직접 압축. 해제하면 `MSAV`+버전, META 영역에 맵 태그(StringMap).
- 스프라이트 `.aatls`: Arc 바이너리 아틀라스(다중 페이지). 페이지 PNG 에서 리전(x,y,w,h,
  회전)을 잘라냄 — 바이트 완전 소비로 레이아웃 검증(4페이지·5,182리전 정확).
- 로컬라이즈·오디오는 원본이 이미 평문/OGG 라 그대로 추출.
