# 설정창 세로 레이아웃·공 크기 보충

2026-09-29. 원본 저장값 재판독. 기존 C: 적용 결과는 Claude 보고이며 아래 보충본의 런타임 적용은 아직 미검증.

## VerticalLayoutGroup

`vertical_layout_groups.json`: level1의 8개, 각 레코드 바이트 소비 일치. 요청 대상은 **level1#6151**, `UI/Canvas_GameplaySettings/Buttons`.

| 필드 | 원본값 |
|---|---:|
| padding L/R/T/B | 모두0 |
| childAlignment | 4 / MiddleCenter |
| spacing | 183.5500030517578 |
| childForceExpandWidth / Height | false / false |
| childControlWidth / Height | false / false |
| childScaleWidth / Height | false / false |
| reverseArrangement | false |

원본 RectTransform/버튼 크기와 함께 적용한다. 화면 픽셀 단위로 변환한 임시 간격이 아니다. 로비 Left/Right 버튼 그룹은 paddingTop22/spacing45 등 다른 값이므로 전체 그룹에 한 값을 복제하지 않는다.

## 공 메시를 콜라이더에 맞춰 자동 정규화하지 않기

확인 결과 **원본에 이미 geo scale=1.38이 저장**돼 있다. 보고한 계산 배율1.377은 가깝지만 원본 정합성은 아래 TRS를 보존하는 방식으로 맞춘다. `ball_scale_sources.json`은 기존 prefab_components에서 관련 원문을 분리한 것이다.

| 원본 필드 | Ball | BigBall |
|---|---:|---:|
| root localScale xyz | 0.6700000763 | 1.5 |
| geo localScale xyz | 1.3799999952 | 1.3799999952 |
| geo/shadow localScale xyz | 1.5 | 1.5 |
| SphereCollider radius (local) | 0.4900000095 | 0.4900000095 |
| Rigidbody mass | 1.2000000477 | 30 |

상위 scale=1 가정 [자체 계산]: 일반 공 콜라이더 지름 약0.6566, 큰 공1.47. **0.98은 root scale 적용 전 로컬 지름**이다. Bullet_Ball native bounds 약0.711에 geo1.38과 root0.67을 곱한 렌더 크기가 일반공 크기다. 콜라이더 지름을 월드값으로 오해해 두 번 확대하지 않는다.

BigBall root의 저장 position=(0,0.41,-7.7649998665)은 프리팹 저장 배치다. 발사에서는 ReplaceLoadedBall/발사 위치 계약을 따라 장전 위치에 놓아야 하며 이 position을 BallSpawnPos에 다시 더하지 않는다. 회전/scale·자식 로컬값과 spawn 위치를 구분한다.

BigBall의 대포 scale1.5와 **공 프리팹 root scale1.5는 다른 필드**다. 대포확대배수를 공에 추가로 곱하지 않는다. 큰공 질량30은 저장값이며 일반공1.2에1.5만 곱하는 방식과 다르다. 런타임 BallMassMultiplier 등은 별도 경로이므로 저장 질량이 모든 상황의 최종 질량이라는 뜻은 아니다.

shadow 자식은 원본 별도 노드다. 런타임 투영/변형까지 이 TRS 표만으로 검증됐다고 쓰지 않는다. 기존 메시/재질 슬롯과 Ball 동작을 결합하고 외형을 확인한다.

## 완료 범위

+15/레이아웃14개/공 텍스처가 기본 Sphere 프리팹 때문에 빠졌다는 실측 보고를 기록한다. 발사 VFX·사운드·큰공 아이템·구매창 퇴장·Spine·정밀 settle 및 오프라인 이벤트는 보고대로 아직 진행할 항목이다. 데이터 전달과 실제 적용 완료를 분리한다.
