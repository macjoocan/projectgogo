# Stardew Valley 1.6.15.3 (Android) — 추출 데이터

입력: `Stardew-Valley-v1.6.15.3-full-apkvision.apk` (MonoGame / Xamarin .NET 8 AOT)
levelscope(Unity 전용) 범위 밖이라 XNB 전용 추출 도구를 별도 작성해 오프라인 정적 분석으로 추출.

## 산출물

| 경로 | 내용 |
|---|---|
| `data/` | **게임 데이터 125종(JSON)** — 밸런스 완본 |
| `StardewValley_sprites.zip` | 스프라이트 1,019종 PNG (원본 폴더 구조 유지) |
| `StardewValley_text.zip` | 텍스트·대사·이벤트 1,377종 JSON (12개 언어 로컬라이즈 포함) |
| `StardewValley_audio.zip` | 효과음·음악 463종 WAV (16-bit PCM) |

## data/ — 밸런스 데이터 (핵심)

`Content/Data/*.xnb` 125개를 전부 복원. 주요 파일:

- **Objects**(807) — 전 아이템: 이름·분류·판매가·식용도·버프·상점제외 플래그 등
- **Crops**(50) — 작물: 계절·성장단계일수·재성장·수확물·품질
- **BigCraftables**(182) — 대형 제작물
- **Weapons**(67) — 무기: 최소/최대뎀·넉백·속도·정밀도·방어·치명타확률/배수
- **Machines**(39) — 기계 가공 규칙(입력→출력·시간)
- **Shops**(77) — 상점 재고·가격·조건
- **Buildings**(25) · **FarmAnimals**(14) · **FruitTrees**(8) · **Tools**(37) · **Boots**(18)
  · **Fish**(74) · **Furniture**(645) · **Monsters**(51) · **CookingRecipes**(81)
  · **CraftingRecipes**(150) · **Trinkets**(8) · **Buffs**(29) · **NPCGiftTastes**(39)
  · **Quests**(66) · 던전/축제/이벤트/상점 스크립트 등

문자열 값 중 `[LocalizedText Strings\...]` 은 로컬라이즈 키(실제 표기는 `StardewValley_text.zip`).

## 추출 방법 (요약)

- XNB 는 **MonoGame LZ4 압축**(flag 0x40). 해제 후 타입리더 그래프를 따라 역직렬화.
- 커스텀 모델(ObjectData·CropData 등)의 **필드 선언 순서**는 APK 안
  `lib/arm64-v8a/libassemblies.arm64-v8a.blob.so`(XABA AssemblyStore) 에서
  `StardewValley.GameData.dll` 을 추출해 .NET 메타데이터(프로퍼티 순서·`[ContentSerializerIgnore]`)
  로 복원.
- 정확성은 **"스트림 완전 소비" 검증**으로 확인 — 125/125 전부 통과(정렬이 조금이라도
  틀리면 파싱이 끝까지 안 맞음). 표본값 대조: Parsnip 판매가 35·분류 -75, Rusty Sword
  2~5뎀 등 실제와 일치.
- 텍스처는 전부 SurfaceFormat 0(RGBA32) 무압축 → PNG. 오디오는 XACT 웨이브뱅크(.xwb)의
  MS-ADPCM 을 16-bit PCM 으로 디코드.
