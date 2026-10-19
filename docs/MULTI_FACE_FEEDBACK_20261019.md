# 얼굴 사람 피드백 — 기존 얼굴을 기본으로 복원

2026-10-19, Multi 지식 동기화 `bmvejnrqv-o`. 새 독립 실험·중복 구현·추가 생성 요청이 아니다.
이 세션에서는 아래 문서/JSON을 읽었으며 모델·라이브 Blender·대시보드를 변경하거나 실행 검사를
추가로 수행하지 않았다.

## 현재 상태

- 사람은 이전 얼굴을 더 선호했다. Multi의 Idle 근접 비교에서는 새 머리 교체가 기존 코·볼·입의
  입체감과 윤곽을 바꾼 점을 확인했다고 보고했다. 이 세션이 새로 화면 비교한 결과는 아니다.
- 대시보드/단일 HTML 기본은 **기존 OriginalRetry 얼굴**. 표정 후보 비교는 **기본 OFF**.
- 검수 `study.motion-first.face-expressions@1`는 **revise**. 후보를 삭제하거나 최종 승인한 상태가 아니다.
- 기존 얼굴에서도 확대 보기가 가능하다. 다음 얼굴 방향은 **기존 형태 보존**이다.
- 모델·가중치·native 모션·atlas 파일 변경0, 추가 생성0이라는 상대 보고를 유지한다.
- 손 강한 curl/미채택 harmonic의 Idle 면적 회귀/근접 헤어 경계·특수 모션 외형은 별도 미해결이다.
  파티서빙 게이트·반복0/3도 변경하지 않았다.

## 이번 검증 범위 — 상대 QA 읽기

`validation.json`상 네 가지 조합 전환/복귀, 기본5종 **15자세 표본**의 뼈·정점finite,
기존 얼굴 확대·선택 다운로드 링크·오프라인 기본/후보/복귀와 빌드 exit0을 확인했다.
이는 이번 변경에 대한 표적 smoke 검사다. 전체278모션이나 전체 다운로드/연속시간/픽셀/외형을
재검사한 것이 아니다. `motionItems=278`을 이번에278개를 다시 검사했다는 뜻으로 읽지 않는다.

HTML 변경은 기본 선택 정책 반영이며 원본 GLB 해시가 변경됐다는 뜻이 아니다.
자동 검사 통과와 사람의 얼굴 외형 선호/최종 아트 승인을 서로 독립된 판정으로 남긴다.

## 로컬 근거

- `C:/00.SVN/Multi/web/assets/studies/motion-first-crew/source/face-feedback-20261019/human-feedback.json`
  — review id `review-1792371371785-3r67g`, decision revise, reviewer human.
- 같은 폴더 `validation.json` — 이번 표적 검사 범위와 제한.
- `C:/00.SVN/Multi/web/docs/43-character-skinning-knowhow.md`의 2026-10-19 후속.
- 사용자 안내/계획은 Multi 문서44/45. 과거 export 기술 노하우는
  [2026-10-16 기록](MULTI_EXPRESSION_EXPORT_KNOWHOW_20261016.md)에 보존한다.

이 저장소에는 원작/후보 모델·atlas·HTML·렌더 등 리소스를 포함하지 않는다.
