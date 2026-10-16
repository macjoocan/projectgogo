# bmumbz3iz-1d 추가 판독

## TNT 파편: 추가하지 말 것

[원작 코드 판독] Tnt.Explode393E00C→base Obstacle.Explode383D600→Feedback.Play / SpawnExplosionPerCell383D7C8 / Complete383AAB8 / collider비활성 / Destroy. Complete383AAB8 전체도 재확인: completed플래그 확인·설정→NotifyGroundHit39A0EC8뿐. **이 경로에 SpawnBroken 호출 없음.** TNT breakParams 저장만으로 파편 생성을 추가할 수 없다. 이식 Complete가 맡은 완료·소멸·시각효과를 원본 메서드와 동일 이름이라고 동일 역할로 간주하지 말 것. asm동봉.

## 그림자

[원작값] Mobile_RPAsset globalgamemanagers.assets#4147: Distance60, CascadeCount1, MainShadowmap512, SoftSupported=true, assetDepthBias1/NormalBias1, CascadeBorder0. `shader_variant_analysis/urp_asset_prefix.json`에 byteoffset/rawhex 있음. Light 자체 bias0.05/normal0.4와 RPAsset 기본bias는 서로 다른 필드다.

추가 직렬화 prefix 판독: offset276 ConservativeEnclosingSphere=true, offset280 NumIterationsEnclosingSphere64, offset284 SoftShadowQuality2. `urp_shadow_quality_tail.json`. 이 값은 원본 모바일 에셋 값이며 현재 PC플랫폼 설정과의 불일치를 확인한 것이다. 값 교체만으로 그림자 원인이 결판났다고 하지 말고, 실제 shader shadowCoord/rawAtten/alpha를 분리 확인할 것.

## 망치 저장·메시

Handle 저장 scale(1,1.75,1), HandleRB와 Hammer1/2 scale1. HammerHead 지오 scale0.7436699867. 기본 h1=h2=rodDiameter=1, rodLength1.75. ApplyScales는 이전 README 정확식대로 적용하며 rodD 없는 레벨의 기본1 자체가 오류라는 근거는 없다.

메시 파일5cfcd9c5c799c4c2b9fa4edec5b773cf: #1 Hammer_Handle(막대), #2 Hammer_Handle1(머리2개 공용). 재질/텍스처는 hammer_material_assets.json 및 PNG 제공 완료.

## 장애물 인트로 (로딩 안내와 별도)

level1#5096 ObstacleTutorialController → sharedassets1#2193 ObstacleTutorialConfig / level1#6270 IntroductionPopup. Popup 경로 UI/Canvas_IntroductionPopup. inputLockSeconds1.75, iconAnchor#4551, animationGroup#5061, dismissButton#5274, effectAnchor#4058, defaultEffect shared1#1012.

`tutorial/asset_values.json`에 전체 entries와 UI값/rawhex 제공. 재추출 validation 오류0. 목록은 4 colorbox,7 woodenbox,11 jamjar,16 box,21 stone,31 rotatingtable,41 ice,51 horizontaltable,61 TNT,71 blocker,81 verticaltable,91 column,101 wood,121 piggybox,141 bouncer,161 hammer,201 pinata. 부스터18/22/26 목록이 아니다.

[원작 코드 판독] MaybeShowForLevel3975140: config 순서로 `entry.Level == levelNumber`이고 실제 배치에 Subject가 있고 미열람인 첫 항목. >=가 아니다. MarkSeen39759B0을 **Show 전에** 호출한다. seen접두사 `obstacle_tutorial_seen_`. Dismiss3974DF4는 unscaledTime이 unlockTime에 도달한 후 1회 비활성화·콜백. 반환 Promise를 로더가 기다리는 구조. LoadLevel state machine의 MaybeShow 호출은 기존 로드 후 레벨 객체를 대상으로 한다. 로비 로딩 이미지와 같은 화면으로 합치지 않는다.

## 클리어 로고/PS 추가 추출

celebration_loading_scene.json을 확대 갱신: Canvas_Success/Canvas_IntroductionPopup도 포함. SpriteRenderer의 sprite 참조 및 PNG까지 추가 export. **로고 글자는 Image가 아니라 SpriteRenderer**: 예 L=level1#2488 → shared1#735, sorting22. 저장 Transform을 임의 RectTransform로 바꾸지 않는다.

PlayableDirector level1#4822→PlayableAsset shared1#2234. Track shared1#2250→scene Animator level1#2018. Director의 sceneBindings/exposedReferences는 scene JSON에 있음. `logo_timeline_raw.json`은 #2234/#2250 raw와 클래스 원문 자료이며, Timeline clip/channel 전체를 이식 가능한 형태로 디코딩 완료한 것은 아니다. 이 한계를 숨기지 말 것.

사용자가 에디터를 플레이 중이므로 실행권을 빼앗지 않고 자료/코드만 준비한 뒤 안전한 시점에 화면 확인. 이번 패키지는 원본 자료 전달이며 실행 적용완료가 아니다.
