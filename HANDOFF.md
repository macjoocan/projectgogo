# Shared Work Handoff

## Memory and know-how publication scope (2026-09-17)

- User requested memory update and Git commit/push to `https://github.com/macjoocan/projectgogo`; repository origin already matches. Documentation-only scope: AGENTS, GUIDE link, ANALYSIS_KNOWHOW, MEMORY and this HANDOFF. Existing unrelated core/test/config/documentation edits remain in the worktree; no broad `git add .`, reset or force push.
- Consolidated reusable methods rather than copying original assets or native dumps. External `../out_*` artifacts, original packages, analysis dependencies and raw observation backlog remain local. This publication is a documentation snapshot, NOT a complete source-data/environment backup.
- Most recent original/prototype audit remains September16 cannon analysis below. Claude's21:29 ball-fix reply was received but not independently revalidated; earlier21:18 failures are historical. CannonY request has an answer, while effective runtime firing pose/hammer parity and decay rules remain open. No new game execution, CDN request or700-level tuning during this documentation task.
- Historical source-analysis constants are not required in public handoff text; retained provenance and local evidence paths instead. No code or skill configuration changes in this pass. Publication status must be confirmed from Git commit/remote hashes, not inferred from this preparation note.

## Royal Smash cannon world Y and launch origin (2026-09-16 21:45)

- Answered user's cannon/hammer question with bounded offline scene/native analysis; no prototype edits. New audit_cannon_world.py uses ObjectIndex for exact PPtr scope, verifies Controller124 payload hash and follows GO24/29 to Transforms80/93. CannonBase62 worldY4.44 and LevelSpawn48 Y1 are siblings under Arena59; adding1 to cannon is double-offset. Stored BallSpawnPos worldY4.076285/Z-25.705237; anchor4.009927; VFX4.246886. Runtime aim rotation/animation/scale can change effective pose; do not hardcode stored spawn as universally fixed runtimeY.
- verify_cannon_world.mjs independently composes three TRS chains with Three.Matrix4(maxdelta8.9e-16), executes actual Sim.fireAt3targets. Latest cannonFor already4.44 vs mail's stale5.44. targetY8 produces startY4.930358/Z-20.100346 due own z=-23.06/muzzle3. Native ResetBall reads BallSpawnPosition Transform.position; LaunchBall reads rb.position, setsgravitytrue/kinematicfalse and AddForce(mode2VelocityChange). ComputeLaunchVelocity ordinary branch uses horizontal distance/speed flight time plus gravity compensation, unlike proto total-speed135 low-arc solve. No original code port/game execution.
- cannon_world_analysis contains scene hashes/chains, protohashes/diagnostics, native_index and four bounded disassemblies. Conclude no evidence that proto cannon too low; neither proves original intended under-hammer passage nor certifies hammer. Need fixed level/aim/time and collider/pose comparison. Mailbox214501 posted replying122935 (markedanswered for cannon request); its newly claimed ball fixes were NOT revalidated in this task. Prior21:18 review is historical snapshot, notcurrentfailureclaim.

## Royal Smash ball revision review (2026-09-16 21:18)

- User requested verification of Claude ball changes. New offline `out_royalsmash/review_ball_revision_20260916.mjs` executes actual web handlers extracted into VM and Sim.contacts/blast with real Rapier bodies; injected contact-force events and visual stubs, NOT actual solver event generation or original game observation. Eleven test groups; eight source hashes stable through execution and post-check. Prototype left unchanged.
- Pass: Impulse mass inverse ratio, directHit exclusion, conditional explodes1.2, Jar18/Tnt2 physFor propagation, collider order symmetry and one-shot fast path. Reproduced surface-overlap target omission: center2.5/halfX1/radius2 gives surface distance1.5 but current velocity0, documented Unity surface model impulse.75 at force3/up0 (analytic expectation only). Unity official docs contradict Claude center-only-not-approx claim.
- Reproduced consumer mismatches: Bouncer web speed20→27 vs Sim20 because Sim lacks applyBouncer; low-impact.6 web firstContact=true/blast1 vs Sim false/0 because only Sim early-returns below wakeMinSpeed1.2. minSpeedToDecay remains unused; retention correspondence absent in web/sim search. Own power8 yields radius4 and force24, not original fixed-radius path. Stale multiplier-unused comment remains.
- Report/results under `ball_revision_review_20260916`. Mailbox to-claude211824 posted, incoming115857 markedanswered; cannon worldY request explicitly remains unresolved. No browser/original game/CDN/emulator/tuning. Recommend retaining 700-level tuning hold pending consumer parity and explosion shape/point semantics.

## Royal Smash stage144 pink bouncer initial pose (2026-09-16 20:56)

- User asked whether fallen pink columns in supplied screenshot are also normal in original. visual-qa screenshot review separated visible tilted/front columns from authored/reference proof. New audit_level144_spawn.py rereads main144sourcehash,8Bouncers identityquaternions, two originalprefabnativeTransforms/BoxColliders. No loop confusion:main108entities,moves21vsloop61withnoBouncer.
- OriginalMeshchildlocalY_3=-1.5/_4=-2 centers rawbottom-originmesh onroot; colliderscenteredroot. PrototypecatalogminY0 + mainpy h/2 introducesextra1.5/2: originalcenterY8.5/4 becomes10/6 beforecommonspawn. Currentmeshloaderalreadycentersgeometry. Evidencelevel144_spawn_audit/evidence.json contains references/components/sourcehashes/protohashes/screenshotpathhash. mainsettleSpawn runs.5s thenFixed; plausibletiltpathbutnotA-Bsimverified. Sourceauthoreduprightconfirmed;originalpostspawnruntimeunobserved. No prototypechange/game/network. Mailbox205646posted; advisefullTransformchaincorrection+0step/.5scomparison,notlevel-specificforcedrotation.

## Royal Smash ForceMode and actual configuration knobs (2026-09-16 20:46)

- User/Claude reported MoveCount failures after source defaults and requested mode/levelPower provenance. New offline audit_force_mode.py plus force_mode_analysis outputs capture bounded native disassembly,8raw-instruction/schema checks,ELF relative relocations and metadata literal resolution; no code port or prototype edits. First-contact mode1Impulse confirmed caller0x382AEE4/call0x382AEEC→Rigidbody0x7A9E990/same-buildenum.
- BallController.OnEnable reads Config.Get<int>(first_contact_force_multiplier,1,flags10) and ball_mass_multiplier likewise. Keyslots0x82434D0/4C8→metadata literal20889/18820. Force field+0x130 consumed byBall;mass+0x134 consumed inResetBall. Realruntimeconfig unknown. Existing6configJSON no keymatches; notexhaustive. Source8rootfields/1560levelschema no power root. Prototype tuning[order].power/radius*cbrt(power) remain own policy, notsourceequivalence. Nativefunctionradiusstored unchanged.
- ConditiondirectHitvalid&m_explodes for1.2 now nativeverified; LighterGameplay.Config<bool>(lighter_gameplay_01,false,10) condition appliesupwards*1.8. Actual toggleunknown. OriginalOverlapSphere/collider surfacedistance/AddExplosionForce differfromproto bodycentercheck/applyImpulse;nativeexcludesdirectHitObstacle. Followupfixtureguidanceprovided,notimplemented/measured. OfficialUnity docsused forAPIsemantics only. No game/CDN/emulator. Mailbox204624 open/request113506answered.700tuningholdretained; reportedclearcountsnotrerun.

## Royal Smash first-contact payload verified (2026-09-16 20:30)

- User asked to resolve Claude's pending first-contact force/radius/upwards uncertainty before700-level tuning. New `../out_royalsmash/verify_first_contact_payload.py` independently rereads localAPK3SerializedFiles, follows sceneCore.BallController124 BallPrefab atobjectoffset116 tosharedassets2GO40/Core.Ball82. Fullcontroller176/176 andBall204/204 schemaends validated. Exact5valuesmatcholder destruction_fx_audit extraction.
- `first_contact_verification/payload_evidence.json` includes source/objectSHA256, fullrawhex, fieldoffsets. Force3 offset68/Radius2 offset72/Upwards.5 offset76/ExploderMultiplier1.2000000476837158 offset80/minSpeedToDecay10 offset200. Documentation clarifies serialized offsets vsIL2CPP memory offsets and fieldownershipBall notBallController.
- Currentbalance9/2.6/.8/min3 differs; currentmain multipliesforceby levelPower andradiusbycbrt(levelPower). StorednormalBall values do not certify finalruntimeforce/ForceMode/selection/consumersemantics. No prototypechange/sim/onlinegame. 700tuningremainsonholdpendingconsumerverification. Mailbox203000replyposted; request104933answered,111753FXchangesnotrevalidatedthisturn. RelatedObstacleCommonrequestalreadyansweredbyFXdataandClaudeack.

## Royal Smash sound implementation guide (2026-09-16 20:17)

- User requested a mailbox guide after asking about sound support. Guide-only scope; no prototype modifications, new extraction, original game/emulator execution, or CDN calls. Public MDN consulted for Web Audio lifecycle guidance. Used polish skill to separate gameplay transitions from presentation and centralize proposed audio policies.
- `../out_royalsmash/sound_handoff/README.md`, `build_manifest.py`, `sound_event_map.json`: existing original_effects evidence mapped to139 unique object IDs with full SfxAsset refs. Existing11WAV headers/payload frame lengths pass; cannon_blast mono16bit44.1kHz .936009sec. Existing CDN assets ZIP audio entries0, not an exhaustive all-container search. Original SfxAsset→AudioClip linkage, block clip payloads, selection/volume/pitch, listening and browser playback remain unverified.
- Guide covers shotCommitted/break/impact/TNT event separation, duplicate/voice budgets explicitly own proposals, no speculative Jar water sound, null Feedback vs missing common, local resource resolution, mute/unlock/lifecycle, and expected tests. Prior TNT/Pinata FX issues are historical dependencies to recheck, not asserted still present. Mailbox `20260916-201738-sound-implementation-guide.md` open; file delivery is not read or implementation acknowledgment.

## Royal Smash object destruction and cannon FX audit (2026-09-16 19:58)

- User added per-object break effects (jar liquid example) then cannon firing presentation. Used game-dev-team:pr-review; no implementation changes. Read current code, source139 prefab references, inline Feedback serialization and end-length validation. New audit_destruction_sources.py outputs destruction_fx_audit/original_effects.json (139objects,15hierarchies including cannon/ball/canbroken,53ParticleSystememitters,errors0). summarize_destruction_audit.py produces handoff_effect_map.json for implementation. Native material texture refs sometimesnull; runtime appearance binding notconfirmed.
- Current-consumer VM/Three tests audit_destruction_runtime.mjs seed20260916,139break calls+3contactscenarios+6actualFXpresets. TNT2detonatedbutnotdead/hit and0destroyed; chainsecondnoVFX. Pinataimpact9popbutnotbreak. Jarfragmentcounts4/6/7match but PS_Jar6colorliquid/Glass missing, common dustonly. GeneralBall originalfirstImpactVfxnull vsprotoBigBallimpact2calls. Muzzle71particles alive,7texturesexist/cleanupworks, but animFire/SFX cannon_blast/Haptic_CannonFire/trail.12+Sparkle absent. No browser/GPU/audio/originalruntime verification.
- Important enum correction localdump1218308 and Unityofficialsource: MinMaxCurve3TwoConstants,2TwoCurves; currentdump-particles/fx incorrectlycalls3missingcurves and invents scalar*.45..1. All raw/summarized evidence saved. Original Can11brokenpieces reuse intactmesh(singlebodyreplacement), so missing *_Broken_* filenames donotjustify nonbreakable. Fragmentgroupmismatch7types,perBody8dropsauthoredpieces,scale/yawtransferabsent, nativebreakparams8/2/.1or.2/3/450degvsownvalues. Report five mandatory sections and specific source lines. Mailbox195800posted, notreadack. Other open103355physicsformat request seen; previous fullJSONcoversmanyfields but not a new physicsaudit thisturn.

## Royal Smash P0 fixes verified; original prefab defaults recovered (2026-09-16 19:35)

- Latest report `../out_royalsmash/physics_recheck_20260916_1920/README.md`. Rebound VM to actual current world initialization and ballExplosion; actual Rapier world dt .0125 in web/Sim, shared/first blast deltas0. Mass overrides1230 pass, df/b/ld currentvalues pass, ad0 Pinata44 stillfails. Ball actual speed135/mass1.2/radius.3283/gravity1/CCDtrue. quiet seconds corrected; win criterion and b.hit filter code checked. Browser/original runtime not executed. Previous19h P0 failures are superseded, not deleted.
- New offline audit_object_prefabs.py scans160 bounded serialized files,3larger skipped/errors0, root names match139catalog IDs. Core namespace inheritance important(Box/Column names collide with UIElements). Obstacle133 schema-prefix/tail fields decoded with Unity4bytealignment and ObstacleCommon pointer validation. Native rootRB132 all match statically read ComputeMass (>1% errors0): max(.25,(sizeXYZ*localScaleXYZ*density+additiveMass)*1.1). Binary call target confirms localScale; constantpool1.1. verify_prefab_mass_formula.py saves evidence/disassembly.
- compare_object_physics.mjs builds139 actualSim unit/nooverride entities. 132/132 storedrootmass differs>1%, df132/133 differs, b37differs. Not originalruntimeobserved. Family override-derived defaults are not actualprefab defaults. Native compound colliders differ from simpleprototype shapes; inertia, COM, staticfriction remainapproximate/unverified. Main entities65272,levelphys1230,nooverride64042(includesstatic/gimmicks). Full JSON rows/provenance saved. Recommend fixing defaults before700level explosiontuning.
- Read new Claude102817 request(P0fixed,stillacknowledgedunimplementedad/spawn/wake/stabilize); replied mailbox/to-claude/20260916-193500-physics-p0-pass-prefab-defaults-differ.md and markedrequestanswered. No prototype code changed. Sharedmemorywritten; mailboxposted is not read/implementation acknowledgment.

## Royal Smash revised physics recheck and cannon trajectory (2026-09-16 19h)

- User requested validation of Claude's changes, then added reference cannon appears straight versus prototype arc. New `physics_recheck_20260916/README.md`, results/trajectory/ball_controller_prefix JSON; three recheck scripts in outputroot. No prototype edits. Actual Sim1,230 overrides now0masserrors; gravity-24 and sharedgenericblast pass. Web loop and ballExplosion extracted verbatim into VM with nonphysics stubs, actualRapier; not browser E2E. Seven source hashes stable during initialtest.
- P0 remaining: world.timestep never set, stays1/60 despite80Hzaccumulator; 79steps per1s input at30/60/120Hz = solver1.316667s vs motion.9875s. FirstballExplosion still separate additive-upward formula; actualweb velocity(5.53846,1.77231,0) vs Sim(4.32481,3.45985,0). P1 frame-basedquiet/preSpeed/wake/grace,44angular-damping overrides,freeze,spawnY,missingbouncer differences. No fullphysics-pass claim.
- Fresh bounded serialized prefix from original AssetPacklevel2 MonoBehaviour124(Core.BallController) gives InitialSpeed135,Spin10/25,AimContactOffset.3. Schemaorderedpayload32 plus downstreamPPtr resolution crosscheck. BallSpawnPosition→GO24Transform80,parent93→78→62→59; BallPrefab→sharedassets2.assetsGO40. Fresh Ball Rigidbody58 gravitytrue/dynamic/mass1.2,Transform51scale.67,Collider60radius.49. This supersedes prior unknown-scene-speed and legacy-only-ball evidence, but not runtime observation.
- CurrentSimballisticlaunch isolated test atspeed42+fixeddt hasmaxchorddeviation.6261units; savedscene135+.0125dt counterfactual gives.0584units/~.15s. Explains near-straight appearance plausibly; not originalruntime match. Fixdtalone doesnotflattenarc. Do not infergravity0. Keepmass1.2 ifchangingradius. Posted `mailbox/to-claude/20260916-190800-physics-recheck-cannon-speed135.md`; no newincomingmessage to markanswered.

## Royal Smash physics priority reply and reference screenshot review (2026-09-16)

- `physics_application_audit/README.md` is the new physics report. Original native settings from baseAPK globalgamemanagers: gravity-24, fixed timestep.0125(80Hz), max.025, solver35/7. Stored settings, not observed runtime override. Rapier0.14.0 actual bundled solver/Sim/blast diagnostic:601/1230 mass overrides differ>1%; Pinata1→33.6663, cylinder4→3.14159, cone.75→.230315;44Pinataad0 overwritten. BlanketFixed despite stabilizefalse; render-dependent step scheduling; web/headless blast differ. No code fixes. Scripts audit_physics_sources.py/audit_physics_runtime.mjs; input8hashes unchanged at followup. Responded to mailbox090435 request, markedanswered; priority181200reply has constructor-vs-effective values and remainingunknowns.
- User supplied19 original screenshots, all viewed and preserved unedited under visual_reference_review/source_screenshots. README records feature-specific observations, no same-frame prototype capture/visual-pass claim. Jar labels+verticalhighlight+darkside, ColorBoxcoloredface+bevel, Ice separate. Static pictures cannot prove dynamic shadow provenance, runtimeprogram orphysicsvalues.
- Recovered SH was already present: gameplay_scene_lighting.json RenderSettings103. Fresh AssetPacklevel2 parse matches entire export; ambient_probe_verified.json holds27rawcoefficients/hashes, mode3Flat,intensity1,radiancefalse. Need actualprobe-selection/basispacking/axes/colorspace verification before treating as unity_SH uniforms. .34/.42 are own substitutes, not authentic SH coefficients. ShaderMaterial common base can reuse existing family code; actualThree r169 materialNeedsLights excludesMatcap; defaultMatcap lacksshadowchunks. Design only, notcompiledpatch. Added inspect_three_shadow_support.mjs/three_shadow_support.json and verify_lighting_followup.py. Mailbox181800 summarizes corrections. No prototype edits/game/emulator/CDN calls. Public official documentation browsed only.

## Royal Smash mailbox replies and overbrightness analysis (2026-09-16)

- User relayed Claude questions about MatCapMask and Cannon, added ColorBox/Jar overbrightness, and explicitly requested mailbox README/to-codex inspection and to-claude reply. Read rules and open question; wrote `../out_royalsmash/mailbox/to-claude/20260916-174416-mask-cannon-brightness.md`, original question marked answered. No archival until workflow completion. Future replies use files, not ended relay sessions.
- Detailed answer `shader_variant_analysis/CLAUDE_MASK_CANNON_REPLY.md`; evidence `mask_cannon_evidence.json` and `toony_lighting_source_params.json`. `verify_mask_cannon_answers.py` checked26programs: Blue4 no mask; Red4 mask/no rim; Purple4 mask+rim; Cannon14 MultiplyLighten+1. Source hashes verified, runtime_selection_verified=false. Exported26Toony source material objects with actual ramp/shadow/highlight/indirect/specular parameters absent in prototype table.
- Jar_Red candidates48/60/72/84; Purple49/61/73/85. Mask uses BaseMap-ST UV, channel0R; MatCapType1 uses weighted base/matcap mix, no0.5threshold. Cannon conditional193 (not202) has multiplier1+pow(s,C)*color*B, lightmap(sample*.8+.2), no active ambient/rim/specular, saved emissive0, wrap1, world-normal static matcap rotation.
- Read current prototype materials.js and main.js only. Jar already changing from additive to mix during inspection. Blue intentionally omits MatCapColor, both Toony paths output pre-light base without original ramp; those are concrete improvement leads, not visually measured sole causes. Current MeshMatcap path does not consume scene directional uniforms. Proposed prioritized diagnostics in reply, preserving source/GLSL/approximation labels. No prototype edits, game/emulator launch, CDN access, screenshot or runtime equivalence claim.
- Before mailbox instruction arrived, one last ephemeral relay message was queued: f1411110-e7c7-4c25-856c-9248c7e6614f. No read acknowledgment. User reports ENOINBOX replies to prior relays, consistent with ended one-shot inboxes. Do not claim live bidirectional delivery.

## Royal Smash shader keyword/pass mapping and conditional variant verification (2026-09-16)

- Authoritative follow-up: `../out_royalsmash/shader_variant_analysis/README.md`, `VALIDATION.json`, `program_keyword_pass_index.json`, `material_variant_candidates.json`.
- Added scripts `map_shader_variants.py`, `inspect_render_variant_context.py`, `validate_shader_variants.py` in out_royalsmash. All287 programs pass keyword-string versus parsed keyword-index/pass/blob-ID agreement and exact GLSL length/SHA checks. 54 material objects have nonempty main-pass feature candidate sets. New index variant_keywords_mapped=true; runtime_selection_verified=false. Prior inventory is historical, with README supersession notice.
- Native GraphicsSettings and current Mobile quality reference exact Mobile_RPAsset pathID4147. Original IL2CPP schema-backed bounded serialized prefix (not native heap offsets, not full custom type recovery): cascade1, shadowDistance60, main/additional PerPixel, main shadows supported, soft support true. Legacy QualitySettings cascade2/distance40 must not override URP data. Camera additional-data122 renderShadows=true, rendererIndex=-1; scene Light104 soft,105 no shadows. Evidence includes raw offsets, object hashes and schema declarations.
- ColorBox Blue material candidates46/58/70/82; old41 lacks SPECULAR and is not a full feature match. TableSquare UniversalForward has14 candidates; old152 has no runtime lighting keywords. Exact additional/main/soft global keyword set conditionally picks Toony58 and Omni202. Saved settings, rendering path/device support, culling, shadow casters, pass activation and runtime global changes remain assumptions, NOT observed execution.
- Original texture handoff still applies. No game/emulator launch, CDN call, bypass, source APK mutation or prototype edits. Validation script passed; no core changes and no core test-suite claim.
- Existing Claude session7125873e-f716-4c4e-95ea-3879d2aebfd9/miniapp-e6 verified live; official one-shot relay accepted message1c10e3db-7da9-46db-a085-dc5139ff7e10. Receipt updated; queued is not read/implemented. No fork/restart/interrupt.
- Next safe work, if requested: use the correctly matched programs and exact texture manifest in reconstruction, retaining conditional/approximate labels; runtime certainty would require separate authorized observation, not silent scope expansion.

## Royal Smash actual GLES programs and block texture handoff (2026-09-16)

- Reports `../out_royalsmash/shader_program_analysis/README.md` and `../out_royalsmash/block_texture_handoff/README.md`. Additional user request: find further shader evidence and share block mapping images with same Claude session.
- Original OmniShade blob contains236 intact compiler-emitted VERTEX/FRAGMENT GLSL strings, Toony51. Verified exact length prefixes, blob entry containment, source/text hashes. Old UnityPy subprogram decoder misreads this layout; failed probe files preserved as `.invalid_probe.txt`, not usable shaders. These are not editable original HLSL and runtime variant mapping remains unverified.
- Omni sample gles_entry0147 uses log2(sample)*contrast→exp2 then MatCapColor/Brightness; not middle-gray normalization. Toony sample0041 selects MatCap-derived base for MatCapType>=1. ColorBoxSquareBlue indeed has BaseColor(0,.2518401,1) AND TCP2_MATCAP/UseMatCap1/MatCapType1/CB_blue; do not confuse shader families or treat stored property presence as active use.
- Current prototype51 material names matched54 source objects,104/104 nonnull texture refs resolved,73Texture2D exported PNG,0errors. Manifest includes exact source identity, slots, UV scale/offset, color_space, sampler metadata. ZIP block_textures_verified.zip includes only73PNGs+manifest+README; use manifest rather than all folder contents. HANDOFF_VALIDATION.json passes; render equivalence not tested. No game-project edits/network/game execution.

## Royal Smash original materials/shaders and gameplay camera (2026-09-16)

- User requested locating original visual settings and sharing them with the existing Claude session, then added in-game camera. Report `../out_royalsmash/visual_settings_analysis/README.md`; scripts `inspect_visual_settings.py`, `inspect_camera_links.py`.
- Original APK SHA rechecked. Exported Material946+CDN49 full saved properties, Shader113+CDN38 metadata (object counts, duplicates/fonts included), Camera3 full native data. Exact TableSquare external-file/path_id links prove OmniShade/Standard URP and MainTex Table_Square_v02, MatCapTex 2_matcap. Not a shader source recovery claim.
- Old temp rs_export2 ExportedProject/Assets/Shader has26 `.shader` files, ALL DummyShaderTextExporter. Do not use their white-fragment placeholder implementations as original game shaders.
- GameplayCamera in AssetPack assets/bin/Data/level2 Camera95/GO9/Transform56: perspective FOV30, position(0,8.85,-40), quaternion(.0436194055,0,0,.999048293) ~= X+5deg, clip.3/1000. Root transform. Distinguish level1 MainCamera orthographic41 and level0 orthographic5. Scene initial values only, runtime framing/zoom not verified.
- Script refs on GameplayCamera: UniversalAdditionalCameraData, FPSSetter, CameraShake. Header links verified against original globalgamemanagers.assets. Full MonoBehaviour custom payload1,727 failures are explicitly recorded, NOT hidden as successful reads; native Material/Shader/Camera parsing errors0.
- Game project/original archives unchanged; no network/game/emulator activity for inspection. Claude relay queue outcome stored separately in out_royalsmash/CLAUDE_RELAY_RECEIPT.json.

## Royal Smash level structure analysis completed (2026-09-16)

- Output `../out_royalsmash/level_structure_analysis/README.md`; profile/index/entity catalog/examples/schema declarations and `ANALYSIS_VALIDATION.json`. Scripts `analyze_level_structure.py`, `validate_level_structure.py` under out_royalsmash only; no core changes.
- Re-read 1,560 levels using verified source file+object identity and collection mapping, all semantic hashes match prior audit. Main700/loop860, entity instances150,648, distinct entity IDs139, Custom leaf paths52.
- Root8 fields complete; all entities have Id/Position/Rotation/Custom; optional Scale appears73 times. Rotation is Quaternion, no norm deviations >.001. Do not impute absent Scale/Custom keys or treat AndroidMoveCount0 as zero playable moves.
- Actual enum evidence: Difficulty Normal0/Hard1/SuperHard2; PhysicsQuality High0/Medium1. All levels match cadence: main1–19Normal/20Hard then endings4,7Hard/0SuperHard; loop uses the cadence throughout.
- Explicit Custom physical settings appear on2,491 entities; Pinata88 includes Explosion10/4/1 and KillBlast25/10/100. These are authored instance values, not validated global/runtime physics. No gameplay/win-rate/goal-count claim.
- Means: main MoveCount22.50286/entities93.24571; loop20.30698/99.27442. Exact cross-collection shared contents82; unique total1,477. Static metrics do not establish real difficulty.
- Validation independently checks saved level aggregation, entity/custom counts, all provenance hashes, cadence and enums; all pass. Existing source/export ZIPs/game project untouched; no new game-company network activity. Full collection export, prefab/collider joining, fallback/win-rule code, and preview/playtest remain possible next work.

## Royal Smash original APK level correction (2026-09-16)

- See `../out_royalsmash/LOCAL_LEVEL_FINDINGS.md` and `LOCAL_LEVEL_APK_AUDIT.json` FIRST for level counts. Original XAPK and three local APKs have matching SHA-256. Inspected 2,285 Unity files, zero read errors, 1,560 valid level JSON TextAssets.
- ResourceManager in base APK globalgamemanagers maps exact external file + path_id to `levels/rs 1/00001..00700` (main 700) and `levels/rs1 loop/00001..00860` (master/loop 860). Original main/master/included TextAssets confirm these collections.
- Existing 860-entry ZIP is MIXED: 349 same-number matches to main, 511 to loop. Do not use it as a valid main campaign. 700 collection records not independently preserved; 660 original objects have contents absent from old ZIP; deduplicating those yields 655 new contents. Total unique contents1,477; old unique822. All old contents found in originals.
- This is local APK data, not newly downloaded CDN levels. Separate RemoteLevels manifest/ZIP update classes exist but live URL/manifest/active level count not verified. Historical inference that 31 remote bundles contain ~700 levels is invalid.
- No source ZIP replaced, no game project fixed, no complete collection export performed yet. Next authorized implementation would preserve collection paths on re-extraction and validate downstream game inputs before replacing them. No online requests/game/emulator/protection bypass.
- Script `inspect_local_level_evidence.py --audit` then `--map` records source identity, semantic comparison, and mappings. Observed private-memory max272,986,112 bytes. Unicode surrogate in non-level Spine TextAsset initially prevented report write; switched JSON evidence to escaped output, reran complete audit successfully.
- User-requested CDN relay to running Claude session `7125873e-f716-4c4e-95ea-3879d2aebfd9` (`miniapp-e6`) used official ListAgents/SendMessage, no resume/fork/interrupt. Initial message queue receipt391c2d59-016a-4a04-aeeb-6224e26ae75d. Delivery/implementation acknowledgement is distinct from queue success.
- The critical local-level correction was also queued once: receipt6fd13c59-d6b7-4bcb-87af-91db15e26dec. Both receipts recorded in `../out_royalsmash/CLAUDE_RELAY_RECEIPT.json`; no read/implementation acknowledgement received before relay exit.

## Royal Smash CDN offline extraction completed (2026-09-16)

- Output: `../out_royalsmash/cdn_extracted/README.md`, `EXTRACTION_VALIDATION.json` and seven ZIPs.
- Reused existing levelscope CLI in separate stages, with 3GiB process-tree private-memory cap and an offline socket audit hook. No core edits; PyPI dependencies isolated under out_royalsmash/cdn_extraction_deps, using Blender Python 3.13 rather than broken Python312 venv.
- Images: 1,204 initial plus 267 recovered = 1,471 PNG (1,230 Sprite, 241 Texture2D). Recovery matched Atlas_UI tags and exact RenderDataKey to the original APK's shared_common_local bundle, not names alone. No source files modified; initial failure log preserved, final unresolved zero.
- Embedded component JSON: 4,684, including named subset 40. Prefabs 90 / GameObjects 7,147. Materials49 / Spine2. Mesh objects0; mesh ZIP contains only an empty manifest.
- All 31 input hashes unchanged. ZIP CRC, strict JSON and PNG integrity passed; no source/max-count truncation. Peak private memory1,094,483,968 bytes (~1.02GiB).
- TextAssets only Dart_Nigth and Dart_Nigth.atlas (Spine). No additional level JSON TextAsset found. Do not describe named UI/animation settings as 40 balance tables or claim effective runtime balance recovery.
- No visual/gameplay/reimport validation, and no AnimationClip/AnimatorController/Shader native export. Those remain in original bundles. New scripts: extract_public_cdn.py, export_cdn_components.py, recover_cdn_atlas.py, validate_cdn_extraction.py.
- Next is semantic review of extracted settings if requested. Below acquisition-stage “next extraction” note is historical and superseded by this section.

## Royal Smash public CDN acquisition (2026-09-16)

- New user boundary for this game: ordinary download logs accepted; no authentication/protection bypass. This does not authorize other games or authenticated online execution.
- Downloaded all 31 remote catalog bundles, 77,351,176 bytes, using anonymous exact HTTPS GET. All 31 returned 200 and match catalog size and decompressed CRC32. No account/cookie/token, game execution, license modification, TLS bypass or firewall change.
- Path resolved statically as `https://cdn.cyphergames.com/royal-smash/v1/prod/Android/359`. BuildParameters serialized in base APK sharedassets0.assets.split13; native argument order and literals checked. Catalog internal_id was decoded with addressablestools rather than guessed from string fragments.
- Output: `../out_royalsmash/cdn_public/bundles/`; report `../out_royalsmash/CDN_PUBLIC_RESULT.md`; machine proof `cdn_public/validation.json`; request logs retained.
- Scripts added only under out_royalsmash: inspect_cdn_local.py, download_public_cdn.py, verify_public_cdn.py. No levelscope core changes or core tests in this pass; unrelated worktree changes preserved.
- Previous 31-bundle / ~700-level claim was not demonstrated. Names indicate backgrounds, event content, loading screens and posters; new balance/level extraction is still pending.
- Next: offline asset/config extraction. Existing venv points to missing Python312; catalog pure-Python dependency was reused with Blender Python, and CRC verification used standard LZMA plus the existing bounded LZ4 decoder. Do not describe the extraction CLI as working yet.
- Prior offline runtime remains blocked at license check. No runtime re-created; original APK and historical safety/disposal reports preserved.

## Shared memory entry point (2026-09-15)

Read `MEMORY.md` first for the consolidated current state, artifact paths, publication
receipt, validated counts and explicit limitations. `CLAUDE.md` now directs both Claude
Code and Codex to read MEMORY + HANDOFF at session start. Its obsolete Clash claim
that APK balance cannot be recovered has been corrected. Older notes below are history;
do not restart completed recovery or claim visual/runtime verification was performed.

## Latest report publication: 2026-09-15

Clash 0.46.1 content/balance analysis completed from recovered JSON.
Report: `../out_clashofcritters/content_balance_report/Clash_0.46.1_Content_Balance_Report.html`.
21 analytical content groups, 17 sections, 64-pet list, 380-root-file search.
Published to requested Dooray page 4390914232279897275 (project 2668173571253827735),
verified version 16. Added analysis before result history; original guide body preserved
exactly. HTML attachment page-file ID 4422141586733380682.
See report folder `PUBLICATION.md`, `analysis_validation.json`, `interaction_validation.json`.
Direct-key and JS DOM-mock checks passed; actual browser visual review was blocked by
local-file URL policy and was NOT bypassed. Do not claim visual/mobile QA passed.
Key caveats: ChestPR category33 sums0.93714287; UnitEvolution has27 missing Skill refs;
server overrides/final runtime formulas unverified. Element enum verified:2water,3fire,
4grass,5electric,6earth. Table row counts are not live playable-content counts.

## Latest Clash completion: 2026-09-15 Config recovery SUCCESS

This supersedes older NO CONFIGURATION PLAINTEXT notes below.
Package records: 5,327/5,327 decrypted. Config chunks: 2,670/2,670 parsed;
2,632 literal JSON exports plus 38 Graphs symbolic exports (class references
preserved, require modules NOT executed). No game launch or game/CDN requests.

- User delivery: `../out_clashofcritters/Clash_0.46.1_BALANCE_JSON.zip`.
- Read `../out_clashofcritters/balance_tables_v0461/README.md` and
  `verification_report.json` for evidence and limitations.
- All decrypted records: `../out_clashofcritters/decrypted_v0461/`.
- Repro scripts: `../android-analysis/tools/decrypt_clash_records.py`,
  `lua54_static_tables.py`, `verify_clash_delivery.py` (Blender embedded Python).
- Full technical continuation: latest section of
  `../out_clashofcritters/ANALYSIS_PROGRESS_2026-09-15.md`.
- Local package version 0.46.1 only, not latest server overrides. No original Lua
  comments/source formatting recovered. Never treat symbolic references as values.
- Preserve offline scope. No need to relaunch emulator or redo protected-code
  recovery. No whole-host isolation/undetectability guarantee.

## Historical Clash continuation: 2026-09-15 native code recovery

Read `../out_clashofcritters/ANALYSIS_PROGRESS_2026-09-15.md` latest section first.
This supersedes older notes saying igame machine code remains wholly encrypted.
At this historical checkpoint no configuration plaintext existed yet.
Do not start the game or contact game servers/CDN.

- Tools: `../android-analysis/tools/emulate_loader_transform.py` and
  `validate_loader_recovery.py`; use Blender 5.2 embedded Python. Unicorn 2.1.4 is
  installed under android-analysis/python_deps, not host Python.
- Actual caller ab4bac uses descriptor +0x88 length953440, +0x48 offset0xb8,
  arguments4/5=-1/-1. The +0x10 value336 is only header-table length, NOT transform
  length. Earlier 336-byte emulation failures are explained by that wrong input.
- `reports/loader_transform_actual_call/decoded_loader_payload.bin` contains six
  validated original program headers. Descriptor .data file offset0xa45dd0.
- `--code-body` decodes raw offset400 length10461040. Intermediate
  `reports/loader_code_actual_call/code_body_UNVERIFIED.bin` starts uint32
  unpacked11093184, packed4652428, then zlib at8. `validate_loader_recovery.py`
  independently verifies exact lengths, checksum/EOF and saves decompressed bytes.
- `reports/loader_code_validated/reconstructed_igame_ANALYSIS_ONLY.elf` is a synthetic
  scaffold for disassembly, NOT a runnable restored library. Original APK/libs untouched.
  `FileUtils_getDataFromFile`0x930388 and `igame_loadText`0x99c6b4 now disassemble
  coherently, but many helper branches in0x9e0000..0x9fa000 still need static tracing.
- Next: trace these functions through helpers to the record decryptor and validate
  against local .pkg/.jsone records. Do not claim config recovery based on code recovery.
- Only bounded pure CPU transform execution was allowed; OS/syscalls not forwarded.
  No game launch or game/CDN traffic initiated. No fresh whole-host isolation guarantee.

Claude Code와 Codex가 세션 사이의 작업 상태를 공유하는 문서다. 새 세션에서는
`CLAUDE.md`, 이 문서, `git status`, 관련 diff를 함께 확인한다. 작업을 넘기기 전에는
현재 상태에 맞게 이 문서를 짧게 갱신한다.

**Last updated:** 2026-09-14 (Asia/Seoul), Codex

## Current objective

Top Heroes 1.120.8 원본 XAPK의 `FibMatrix.Config` 바이너리 설정 묶음 디코딩은
완료됐다. 이 문서를 Claude Code와 Codex가 함께 읽는 영구 인수인계 메모리로 유지한다.

## Repository state

- Branch: `main`
- HEAD: `7a6a62b` — `analysis: Cat Gunner 밸런스 엑셀 시트·원본 데이터 추가`
- 작업 시작 전부터 있던 사용자 변경은 보존한다.
  - `levelscope/hierarchy.py`: 외톨이 서로게이트를 `backslashreplace`로 보존
  - `configs/topheroes.yaml`, `configs/wizardoflegend.yaml`: 추적되지 않은 survey 초안
- 이번 작업의 핵심 추가:
  - `levelscope/fibmatrix.py`: gzip 래퍼, 상수 풀, 가변 길이 행과 배열을 읽는 순수 Python 디코더
  - `tools/decode_fibmatrix.py`: APK/XAPK의 `assets/Table/**/Meta.bytes`를 찾아 JSON zip 생성
  - `levelscope/decode.py`: `fibmatrix` 코덱과 자동 시그니처 감지
  - `levelscope/cli.py`: `inspect --unity-version` 지원
  - `tests/test_fibmatrix.py`와 CLI/계층 회귀 테스트
  - 버전 `1.31.0`, README/MANUAL/CHANGELOG/CLAUDE 문서 갱신

## Top Heroes result

- 원본: `C:\Users\NHN\Downloads\Top+Heroes_+Kingdom+Saga_1.120.8_APKPure.xapk`
- 실제 메타: 중첩 base APK의 `assets/Table/1.0.40902/Meta.bytes`
- 산출물: `D:\99.기타\out_topheroes\TopHeroes_meta_decoded.zip`
- 검증 결과: 824개 테이블, 총 525,789행, raw 블록 0개
- 주요 테이블: `hero` 53행, `hero_level` 4,788행, `hero_star` 4,332행,
  `map_stage` 8,012행, `map_stage_wave` 8,092행, `citybuilding` 126행,
  `citybuilding_lvup_new` 8,032행, `shop_goods` 1,412행, `reward` 83,251행
- 기존 `configs/topheroes.yaml`이 고른 `SpineCacheConfig`는 밸런스 원본이 아니므로
  계속 survey 초안으로 취급한다.

## Validation

- FibMatrix 출력 zip의 824개 JSON을 모두 파싱하고 총 525,789행을 재확인했다.
- 실제 XAPK `detect --samples 1` 결과: `codec: ['fibmatrix']`.
- 최종 전체 테스트: 505개 통과, 4개 skip.

## Clash of Critters feasibility

- 원본 XAPK 확인: `C:\Users\NHN\Downloads\Clash+of+Critters_0.46.1_APKPure.xapk`
  (197,658,431바이트).
- `D:\99.기타\out_clashofcritters`에는 이미 에셋 1,561개, 스프라이트 7,243장,
  씬 3개·프리팹 985개의 추출 결과가 있다.
- 밸런스 원문은 `BinaryAssets.apk`의 `assets/pgame.pkg`, `*.jsone`, `*.luae`에 있고,
  `ff ff ff ff + 평문 길이 + 8바이트 패딩 본문` 구조의 블록 암호다.
- Top Heroes의 FibMatrix+gzip 포맷과 다르므로 새 FibMatrix 자동 디코더는 적용되지 않는다.
  정적 복원은 키가 없어 막혀 있으며, 키나 합법적으로 확보한 복호화 메모리 덤프가 있으면
  레코드 구조는 이미 파악돼 있어 자동 추출기를 연결할 수 있다.
- 추가 정적 시도(2026-09-14): `globalgamemanagers.assets`의 MonoScript에서
  `DecryptStream` / 빈 namespace / `Assembly-CSharp`를 확인했다. 직렬화된 컴포넌트
  인스턴스는 없어 필드값으로 키를 얻을 수는 없지만, 런타임 후킹 표적은 특정됐다.
- `pgame.pkg.bin`은 `Src/Actor/Animation.luae` 등 암호화 레코드 파일명 인덱스를
  평문으로 포함한다. 본문 복호화 뒤 레코드와 이름을 매핑하는 데 사용할 수 있다.
- 파일명·패키지명·게임 문자열 4,563개 변형으로 만든 키 후보를 DES/3DES, Blowfish,
  TEA/XTEA(양 endian)에 대입했으나 4개 `.jsone`이 함께 JSON이 되는 키는 없었다.
- 현재 PC에는 ADB, Android 에뮬레이터, Frida가 없다. 다음 경로는 USB 디버깅 가능한
  Android 기기(가능하면 루팅/Frida 가능)에서 `DecryptStream`의 출력 버퍼를 캡처하는 것이다.

## Clash of Critters offline-lab safety validation (2026-09-15)

- Game installation and launch were intentionally withheld during validation.
- ASCII runtime junction: `D:\android-analysis` -> `D:\99.기타\android-analysis`.
- Validated AVD: `ClashAsciiSafety_API30` on console/ADB ports `5614/5615`.
- QEMU was launched with metrics and crash reporting disabled and
  `-network-user-mode-options restrict=on,ipv6=off`.
- Local emulator help confirms that on API 30 and below this one option applies to both
  radio and Wi-Fi user-mode networking.
- Final verifier result: `Passed=True`, boot complete, external IP ping failed, no default
  guest route, target QEMU external host connections `0`, restricted backend present.
- Guest airplane mode was `1`; Wi-Fi, data, `wlan0`, and `eth0` were disabled/down.
- No package name containing `clash` or `critter` was installed.
- The validation AVD and its scheduled task were stopped; PID 43472 was confirmed gone.
- Reproducible launcher: `android-analysis/run_ascii_safety_scheduled.ps1`.
- Verifier: `android-analysis/verify_offline_lab.ps1` (target-AVD PID scoped).
- Next safe step, only if explicitly requested: start this isolated AVD, re-run the verifier,
  then install the XAPK without ever enabling external networking. Do not add concealment or
  anti-detection bypasses.

## Clash of Critters static recovery update (2026-09-15, later pass)

- Safety boundary remains: do not contact the game CDN or game servers; do not conceal
  rooting, hooks, or emulator traits. Current work is APK-only static analysis.
- Installed all splits and launched once in the validated x86_64 offline AVD. Frida was
  loopback-only and QEMU had zero external connections. Startup failed before Unity due
  to mixed ELF architectures: `libnesec-x86.so` is x86_64 inside the ARM64 split.
- Official ARM64 Android Emulator boot is unavailable on this x86_64 host. Direct QEMU
  diagnostics did not boot Android. No protector library was patched or replaced.
- `pgame.pkg` contains exactly 5,327 self-delimiting encrypted records; parsing reaches
  exact EOF at byte 15,770,768 with no gaps or trailing data.
- Index correction: `Pb/pgame.pbe` is at offset zero. `Src/Actor/Animation.luae` is at
  `0x29140`, with plaintext length 136 and total record length 144.
- Literal-string candidate attacks all failed: DES/3DES 15,249 keys; Blowfish 295,143
  strings; TEA/XTEA 8,072 algorithm/endian/key combinations.
- `global-metadata.dat` has the `HTPX` marker and the package includes
  `libNetHTProtect.so`; this is protected IL2CPP metadata.
- The HTPX size field equals the exact metadata file size (9,960,028 bytes).
- `libunity.so` resolves 101 mass-renamed ordinary IL2CPP APIs with `HTP...` names;
  they are not three special protection entry points. A 234-entry resolver-table alignment
  mapped all 101/101 obfuscated entries. The three names previously highlighted map to
  `il2cpp_class_get_namespace`, `il2cpp_class_get_static_field_data`, and
  `il2cpp_class_get_type` respectively.
- Mapping report: `android-analysis/reports/il2cpp_api_table_mapping.json`. It aligns
  against the locally available Unity 6000.0.62f1 header; the game reports 2022.3.62f3,
  so five plaintext-name differences remain version-sensitive.
- Reports are in `android-analysis/reports/`; user-facing status is
  `out_clashofcritters/ANALYSIS_PROGRESS_2026-09-15.md`.
- Latest breakthrough: index is a uint32 output-size prefix plus raw LZ4 at byte 4,
  not a custom path trie. Decoding yields exactly 294,258 bytes. All 5,327 unique names
  map to consecutive package records and exact EOF, with every header/length validated.
- Directory counts: Config 2,670; Src 2,615; Tolua 41; Pb 1. Names and offsets are saved
  in `android-analysis/reports/index_recovery/pgame_named_records.json`.
- Deliverable: `out_clashofcritters/Clash_Config_2670_ENCRYPTED.zip`, containing original
  encrypted Config records and manifest. This is NOT plaintext balance data. Four decoder
  tests and ZIP CRC checks pass. Decoder: `android-analysis/tools/decode_pgame_index.py`.
- Runtime correction: the existing crash occurs in `MyApplication.attachBaseContext`,
  before the game activity. A post-IL2CPP-load dump is not known to be reachable on this
  AVD. No new runtime launch occurred in the index-recovery pass.
- Next safe work: use complete filename mapping for ciphertext/loader analysis. The
  decryption key and plaintext balance values remain unresolved.

### Content decryption follow-up (2026-09-15)

- No configuration plaintext has been recovered. Never describe the encrypted ZIP as
  decoded tables. No game was launched or game/CDN contacted in this follow-up.
- `probe_compressed_cipher_candidates.js` adds bounded LZ4/gzip/zlib and strict JSON
  validation across four jsone files. Final expanded run: 315,825 tests, zero hits.
  Report: `android-analysis/reports/compressed_cipher_recovered_seeds.json`.
- `probe_symbol_xor.py` recovered an IL2CPP dynstr periodic XOR constant; the raw constant is retained only in local analysis evidence, not this published handoff.
  `recover_il2cpp_strings.py` saved 2,512 name records (2,370 decoded and 142 original),
  and independently matched all 234 Unity resolver names, including all 101 HTP names.
  Files: `android-analysis/reports/il2cpp_string_recovery/symbols.json` and
  `recovery_summary.json`. Treat symbol addresses/sizes as protected, not ready to call.
- Applying this key to other code/data regions did not reveal target strings; using it
  or recovered names as configuration key candidates yielded no validated plaintext.
- `libigame.so` uses a different string/code protection; simple periodic XOR failed.
  Its DT_INIT_ARRAY uses RELA entries at file offset `0x9fca80`, with initializers
  `0xab1534`, `0xab15e4`, `0xab1d38`; the first calls `0xab9160`. Static observations
  only: no loader hooks, patched APK, or concealment were used.
- Remaining work: reconstruct the protected decryptor statically or obtain a compatible
  isolated ARM64 runtime. Existing log shows early attachBaseContext architecture crash.
- Host CIM process query was denied in this sandbox; no fresh claim of zero external
  QEMU connections can be made for this follow-up. No new runtime was started.

## Next steps

### Additional static loader reconstruction (2026-09-15)

- Authoritative new reports: `android-analysis/reports/il2cpp_symbol_fields.json` and
  `igame_symbol_fields.json`; generated by `tools/recover_il2cpp_symbol_fields.py`.
- Observed IL2CPP loader at VA `0x377b45c`, call at `0x37e8bc0`, reads descriptor fields
  at `.data+0x90`: flag=0, first=188, end=2558, dynstr length=111584. It applies fixed
  XOR `0x56312342` to names, then XORs nonzero symbol values with `first+0x151=0x20d`
  and sizes with `first+0x15b=0x217`. 2,370 field records decoded; zero function
  alignment failures. Example: il2cpp_init VA `0x154fb88`, size44.
- Observed igame loader at VA `0xab56e8` uses the same initial string key but increments
  it by the current byte offset AFTER each 32-bit word. `--evolving-string-key` recovers
  all 2,962 nonempty names (2,963 symbol records). Descriptor: first58/end2963,
  string length128976, value XOR0x18b, size XOR0x195. 2,905 fields decoded; zero
  function alignment failures. Previous periodic-XOR failure is explained by this schedule.
- Useful igame targets: `FileUtils_getDataFromFile` VA0x930388 size132;
  `FileUtils_getDataFromFileByOffsetAndLength` VA0x93040c size168;
  `igame_loadText` VA0x99c6b4 size152; `igame_loadTextByOffset` VA0x99c74c size260;
  `tolua_loadbuffer` VA0x91c6c4 size12; `luaL_loadbufferx` VA0x4beab4 size84.
- These are reconstructed symbol metadata, not decrypted code or runtime addresses.
  On-disk code at the mapped targets is still protected. No configuration plaintext yet.
  No game launch, networking, APK modification, or online detection concealment performed.
- Next: reconstruct code-region protection using the loader descriptors. `.data+0xb0`
  XOR0xd7 yields the first plausible ELF program header; later bytes do not all fit that
  transform, so do not assume a full header/table decode. Keep this as an unverified lead.

- 임시 역공학 폴더 `out/_scratch`는 제거했다.
- 후속 분석은 영웅 성장(`hero*`), 스테이지/전투(`map_stage*`), 건물 경제
  (`citybuilding*`), 상점·보상(`shop_goods`, `reward`) 중 목적에 맞춰 진행한다.
- Claude Code는 새 세션에서 이 문서의 `Top Heroes result`를 기준으로 이어서 작업한다.
- Clash of Critters는 리소스·계층 분석은 즉시 가능하지만, 밸런스 테이블은 위 암호화 제한을
  전제로 범위를 잡는다.
