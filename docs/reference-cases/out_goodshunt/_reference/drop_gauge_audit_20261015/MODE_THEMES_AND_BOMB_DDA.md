# モード主题 / 폭탄 DDA 좁은 원문 판독 (bmv8z2n00-r / bmv8z5l2i-t)

기존 로컬 ARM64 ELF와 metadata만 정적으로 읽음. 신규 번들/픽셀 추출, 원작 실행, 구현 변경 없음. 선택 함수 `mode_theme_disasm_*.txt`에 RVA/ELFoffset/코드SHA 보존. 최종 배열 재현 검증 peak0.088GB.

## GetMapTheme 반환 [원작 코드 판독]

| GameMode | 반환 MapTheme | GetMapTheme RVA |
|---|---|---|
| Normal0 | 필드 MapTheme(+10)가0이면 Grass1, 그외 그 값 | 0x21F48B8 |
| Desert4 | Desert5 | 0x21F47F8 |
| Mart5 | Mart6 (index0) | 0x21F4990 |
| Mart2=6 | Mart2=7 (index1) | 0x21F4990 |
| Mart4=8 | Mart4=9 (index3) | 0x21F4990 |
| Box9 | Box10 | 0x21F4798 |
| Vegetables11 | Vegetables11 | 0x1DE3084 |
| FastFood13 | FastFood13 | 0x1DE2E7C |
| Toy14 | Toy14 | 0x1DE301C |
| MeatAndSeaFood15 | MeatAndSeaFood15 | 0x1DE2EE4 |
| Stationaries16 | Stationaries16 | 0x1DE2FB4 |
| Cosmetics17 | Cosmetics17 | 0x1DE2DAC |

추가 판독된 상수: Bonus1→Bonus2(0x21F4540), Ice2→Ice3(0x21F4858), Water3→Water4(0x21F4A20), Sea12→Sea12(0x1DE2F4C), Drink18→Drink18(0x1DE2E14). Mart3=7은 index2→MapTheme8. enum전범위를 구현했다는 의미는 아님.

Normal은 `ldr w8,[this+10];cmp0;csinc w0,w8,wzr,ne;ret`: field!=0이면 그대로, field==0이면1. 이 getter만으로 field가 항상 Level.backgroundTheme라고 확정하지 않는다. Factory0x21F429C는 해당 필드 대입도 수행하므로 실제 호출 경로를 함께 대조해야 한다.

Mart .ctor(index)0x21F448C는 ChosenMode=5+index, _index=index. GetMapTheme0x21F4990는 MapThemes[_index]. get_MapThemes0x21F4920는 4원소 배열을 RuntimeHelpers.InitializeArray로 채운다.

**배열 [6,7,8,9]는 추정이 아니다.** `mart_theme_array_evidence.json` 및 재현스크립트 resolve_mart_theme_array_20261015.py:
getter가 읽는 fieldslot0x4196FF0 → ELF RELA target0x43B0DE0 → usage token0x80000011 → fieldRef8=(type27114,field0) → MetadataRegistration.types[27114]→TypeDef4422 `<PrivateImplementationDetails>` → field21588 → fieldDefault dataIndex21848 → metadata 파일offset11134064의16B `06000000070000000800000009000000`. 해당16B SHA256이 원본 필드명0EDB...AD73F와 일치함을 assert했다. 매핑 숫자를 GameMode와 단순 등치하지 않았다.

## ShouldActivateBomb [원작 코드 판독]
0x1EBACA4, `mode_theme_disasm_01ebaca4.txt`:
```
if (!DDAManager.IsEnable || DDAManager.I == null || IsBonusLevel)
    return true;
return I._currentModifiers.CurrentBombZone >= placement.ddaZone;
```
0x1EBAD84에서 instance+30을 읽고 signed cmp/cset ge. DDAManager._currentModifiers는 instance+20, DDAModifiers.CurrentBombZone struct+10이므로 +30과 일치. 단순 zone equality나 무작위확률이 아니다.

DDAZoneLevel: VeryChill0 / Chill1 / Normal2 / Hard3 / VeryHard4. 저장 0~4와 연결. IsEnable0x1EBA338: testLevel cheat disableflag가false, remote IsEnabled=true, GameRefManager가존재, CurrentLevel>=DDAConfig.level_start 조건. config null이면 그 경로의 임계0 fallback. 원문 IsBonusLevel0x1EBA44C도 보존했으나 nullable/generic type 연결이 있으므로 모든 보너스 정의를 이번 자료로 확대하지 않음.

`settings/0029_DDARemoteConfigSO.json`(sharedassets1#8): enabledtrue/level_start30, timer_speeds[90,95,100,105,110], bomb_drags[8,5,3,2,1], score_thresholds[30,45,75,85], recent_games_weight25. 저장 기본값과 실제 원격 override/플레이 이력 계산 상태는 구분.

DDAModifiers .ctor(bool isDefault)0x1EBB1AC는 IsDefault=인자, TimerGlobalMultiplier1/BombDrag0, CurrentTimerZone2/CurrentBombZone2, TimerScore50/BombScore50을 초기화. float1/0은 raw literal0xDB98E8, zone둘다2는 `movi v0.2s,#2` 저장. **생성자 기본값이 실제 활성 세션의 최종 zone2라는 증명은 아니다.** 웹에서 이 원작 생성자 기본값을 로컬 시작 상태로 채택한다면 해당 선택과 이력 갱신 미이식을 명시할 것.

[상대집계 기반 계산] 보고된 zone분포0:5329/1:5/2:55/3:5/4:1에서, DDA활성·nonBonus·instance존재·currentBombZone2라는 조건이면 활성5389/비활성6. DDA비활성이거나instance없음/Bonus라면5395전부true. 이는 조건부 산술이고 원작 실행 관찰값이 아니다. 모든5395를항상활성 또는특수66전부비활성으로고정할 근거없음.
