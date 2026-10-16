## Well Done fireworks runtime check — 2026-09-29

Inspected current read-only Unity implementation and Gameplay.unity.

- RsGameplayView: ShowWellDone activates Success then calls PlaySuccessFx. That method skips any ParticleSystem whose GameObject is not activeInHierarchy; active systems are Clear(true)+Play(true).
- Parsed serialized GameObjects/transforms: 154 ParticleSystem components overall, split as 24 Logo + 130 Success. In Success/Fireworks there are 84 systems. With Canvas_Success active and descendant activeSelf preserved, 36/84 are active and 48/84 are skipped. The 12 cluster parents each have 7 PS descendants; base and _01 variants are inactive (0 active descendants), while _02/_03 have 6 active descendants each. Inactive child PS_Atrail states also exist. Do not blindly activate all 84 or trails.
- Success child Animator controllers are only on AdButton, ContinueButton, Reward, RewardDartNight; none binds FireworkCluster activation.
- The source celebration-Canvas_Success.json has 130 systems. Need separate authored-disabled variants from missing activation logic before changing. Next diagnostic: log each cluster/emitter activeSelf/activeInHierarchy/playOnAwake/isPlaying/isEmitting/particleCount and renderer enabled/material/sorting; capture WellDone once at 3.3s.
- Bridge report sent to Claude, message bmumhkxs8-1m. No Unity runtime capture was available, so this is a code/serialized-state diagnosis, not a verified visual fix.
