# Normal MapTheme 필드 입력 확인 (bmv8zgaos-v)

[원작 코드 판독] factory0x21F429C의 입력을 **Level.backgroundTheme(+28)라고 확인할 수 없다**. 오히려 이 함수 안에서 확인되는 정확한 데이터 흐름은 다음과 같다.

`GameModeMechanicFactory.InjectGameMode(GameModeType type)`0x21F3A2C:
- 0x21F3A3C `mov w20,w0`: 함수 인자 type를 보존.
- w20은0x21F3B0C/3B18에서 dispatch에 읽힌다.
- 이 함수의 나머지 구간에서 w20에 다시 대입하는 명령은 없다.
- Normal/fallback 분기의0x21F429C `str w20,[x19,#0x10]`: 보존된 **함수 입력값**을 GModeNormal.MapTheme 필드에 저장.
- 이 경로에는 Level 인스턴스+28을 읽는 명령이 없다.

따라서 metadata 필드명만으로 `Normal.MapTheme=Level.backgroundTheme`를 확정하는 것은 안 된다. getter0x21F48B8는 필드0이면Grass1, 그외 저장값 그대로이며 그 자체는 확인됐다.

현재 읽힌 factory 서명과 본문만 보면 입력이0인 Normal 분기는 field0→Grass1이다. 다만 실제 상위 호출에서 어떤 값을 전달하는지/다른 경로가 필드를 쓰는지는 별도 문제다. 원본39맵의 backgroundTheme 명시값을 무시해야 한다거나 우선 적용해야 한다는 전체 런타임 계약을 이 한 함수로 단정하지 않는다.

호출 상위를 더 좁히려고 원본 .text의 직접 B/BL target0x21F3A2C 검색도 했으나0건이었다. `normal_theme_factory_calls.json`에 보존. 이는 인라인/간접 호출이 없거나 함수가 사용되지 않는다는 뜻이 아니다. 해당 작업 peak commit0.701GB/1.61초, 원작 코드 실행 없음. 이 한계로 상위 연결 미확정을 유지한다.

정본 근거: mode_theme_disasm_021f3a2c.txt 및 mode_theme_disasm_021f48b8.txt. 구현에서 Level.backgroundTheme를 우선 쓰기로 선택하면 현재까지는 별도 웹 정책으로 표시하고, factory를 근거로 원작과 같은 우선순위라고 주장하지 않는다.
