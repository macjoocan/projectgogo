# Goods Hunt 1.9.1 부스터·목표·오디오 판독 인계

2026-10-15. 구현 소스는 C:/00.SVN/Goodhunt 세션 소유이며 이 조사에서는 수정하지 않았다. 원작 실행·DLL 로딩·서버 접속 없이 기존 ARM64 ELF/metadata/원본 저장 객체만 읽었다. 최신 추가 판독 peak commit 0.342GB, guard 2.5GB, 정상 종료. 원작 PhysX/웹 프레임·렌더 동등성은 별도 미검증.

- `POWERUPS.md`: 공통 상태, 저장값, 자석/보호막/힌트 구현 계약. **자석 중 Shield.pushForce=80+88=168**, 종료100. 기존 힘100+88이라는 해석은 폐기.
- `GOALS_AND_AUDIO.md`: Hidden/Bonus 경계, 실제 오디오 호출 문자열/주소.
- `PREBOOSTERS.md`: ExtraTime 실제+60, Lightning 버튼 인자2와 ForceScore 경로. 선언 상수10을 이 버튼에 적용하지 않는다.
- `LIGHTNING_UPGRADE_STATE.md`: 같은 HoleSize 자산의 UpgradeLevel과 플레이어 nextEnergyStage를 구분. ForceAdd는 후자만 증가시키며 반복 NextStage.Price가 자동 상승하지 않는다.
- `stored_components.json`: 기존 구조화 저장값과 source/file/pathID/rawSHA.
- `native_ui_button_chains.json`: 실제 5버튼 부모 TRS. 좌→우 Growth/Compass/Magnet/Freeze/Shield.
- `followup_native_evidence.json`: 폭탄 GO/TagManager, 문자열 토큰·metadata offset, 오디오 호출 직전 문맥. `audio_call_candidates`는 선형 레지스터 후보이며 문서에서 검토한 호출과 구분.
- `literal_audio_evidence.json`: 초기 부스터 문자열/상수, **기존 ZIP 내부 오디오146개** 경로·크기·SHA. 오디오 원본 ZIP은 `../results/GoodsHunt_assets.zip`. 느슨한 WAV 추출을 새로 했다는 뜻이 아님.
- `selected_declarations.json`, `disasm_*.txt`: 선언/RVA, ELF offset, 읽은 바이트 SHA, 원문 명령어. 메서드 경계는 다음 선언 기준이며 심볼 크기 독립 검증은 아님. generic 공유 메서드 주석 이름보다 레지스터/인자/원문을 우선한다.

원본: `../ldplayer/installed_native/split_config.arm64_v8a/lib/arm64-v8a/libil2cpp.so`, `../input_prepared/assets/bin/Data/Managed/Metadata/global-metadata.dat`, `../input_prepared/assets/bin/Data/data.unity3d`. 폭탄 prefab은 `../input_prepared/assets/aa/Android/props_assets_all_8cfb9dc23d45f5ca0c92cd5f38151ff7.bundle`.

표기: [원작값] 저장 객체/상수, [원작 코드 판독] 정적 본문, [계산/조인] 기본 초기화·테이블 대응, [미확정] 실행/전체 분기 증거 부족. 로컬 무료 재고/구매·광고 미배선 정책은 구현 세션의 자체 정책이다.
