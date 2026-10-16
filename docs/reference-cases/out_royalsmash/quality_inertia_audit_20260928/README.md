# Royal Smash 원통 관성 / 품질 선택 판독 — 2026-09-28

완료 회신: [Cylinder 관성식과 LowColliderQuality](../mailbox/to-claude/20260928-cylinder-inertia-quality-bmul6ws1s-c.md).

- Cylinder 관성은 저장 Radius/Height에 생성기 lossyScale을 적용. X/Z 최대 절댓값으로 반지름을 스케일하며, 형상 생성의 축소 보정은 관성에 쓰지 않음.
- 원통식의 Vector3 배율은 59종 `(1,0.5,1)`, BigWood_1 `(0.5,1,3)`. 반환 후 Obstacle이 0.45를 곱하고 관성축 회전을 적용.
- 품질 선택은 Override High/Medium → enforce config → 레벨 저장값 순. LowColliderQuality는 최종 품질이 Medium(1)일 때 true.
- Override None, enforce 없음/false일 때 메인 175/223/362만 low. APK 메인 700개와 현재 Unity 품질 값 700/700 일치. 이 세 레벨에는 원통 인스턴스 없음.
- 참고 C# 컴파일 및 데이터/분기 검산 완료. Unity 물리 실행은 하지 않았고, 라이브 Config 값은 미캡처.

## 재현

상위 폴더의 `audit_quality_inertia_20260928.py` → `audit_main_level_quality_20260928.py` → `finalize_quality_inertia_20260928.py`.

Python 3.13은 Blender 5.2 bundled Python을 사용했고, UnityPy는 상위 `cdn_extraction_deps`를 PYTHONPATH에 추가했다. CP312 패키지 폴더를 함께 넣지 않는다.

`artifact_manifest.json`은 산출물 해시이며 `delivery_receipt.json`은 전달 도구의 상태이다. 실제 상대 적용 완료와 분석 완료를 구분한다.
