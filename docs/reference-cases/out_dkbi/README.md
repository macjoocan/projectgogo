DKBI offline field evidence recovery - 2026-10-08

Scope: login-free local field movement/targeting/basic attack/skills. Original installation and server untouched.
Provenance: verified = saved bytes/declarations and validated joins; inferred = structurally validated interpretation; unknown = no original runtime-code evidence.

1. Field candidate: field_101002/field_summary.json
   Original district JSON explicitly stores zoneId 101002, sceneName dkb_dungeon_beginner, 71 areas, 44 monster spawn entries, four actor IDs (20101003/20101005/20101019/20102420). spawn_area_bindings.json preserves the saved spawn properties/positions and all referenced spawn areas. This does NOT establish original first-login routing or server activation.
   scene_wrapper.json preserves original native Transform/BoxCollider and scene components. Navigation configs/binary payloads are copied with separate identities; navigation binary interpretation remains unknown.
   default_pc_weapon_skill_candidates.json and spawn_monster_rows_candidates.json: raw ordinal/ID/string joins only; typed FB column meaning and gameplay units remain inferred/unknown.

2. ECS: ecs_selected/field_101002.json, town_100.json, verification.json
   Field GUID 489220e256d0cee4c8e7ce6ddb38c8d4 => 20 entities / 5 chunks.
   Town GUID a4af9541f7061bb4ea93bdcfe628475f => 74 entities.
   Native DOTSBIN version 78 node bounds, stable-hash indices, archetype totals, chunk totals, unique Entity IDs validated. Chunk int32 header positions are inferred from metadata declaration order and corroborated bytes. Capacity not decoded.
   Requested town uint GUID values map to that filename by per-word nibble reversal. Component stable-hash names/offsets, native LocalTransform, render meshes/materials and terrain scene reconstruction remain unknown. Object archive companions identified for both scenes contain lights; they are not terrain rendering proof.

3. PC visual metadata: metadata/player_visual_types.json
   Exact SpriteRendererExtend, PropSpriteRendererExtend and AvatarController declarations preserved. SpriteRendererExtend includes _baseLUT/_skinLUT/_lookupTexture/isCompressed. AvatarController includes ChangeSkinPart/ChangeDefaultSkinPart/ChangeDefaultLutTexture/SetDirection/appearance methods. These names establish schema hooks only; call order, HLSL LUT equations and runtime RVA remain unknown. Declaration byte offsets are NOT runtime field offsets.

4. Earlier recovered evidence:
   metadata/schema_validation.json: metadata39 names/record bounds validated, 41864 types/191128 fields/317481 methods. Full DLL dumper did NOT succeed despite exit0: registration zero and loader ERROR. No method-RVA dump claimed.
   tables/config_string_vectors.json: 146 config string-vector records. default weapon stored 10000001; default armor 11100001. Named range/cooldown values are preserved as strings; units unconfirmed.
   graphs/*_decoded.json + field_decode_validation.json: 10 PGRF graphs, 626 field hashes uniquely matched against metadata field names by FNV-1a64 of UTF-16LE. Binary structure/tag meanings remain inferred, original reader body unavailable. Do not assume Delay.Duration270 means seconds or milliseconds without runtime proof.

Memory: sequential bounded subprocesses, 1536MB process commit cap, RSS stop 1280MB, minimum available RAM safeguards. Latest ECS probe peak 50,884,608 bytes; PC metadata stream 20,455,424 bytes. Metadata JSONL must be streamed, not loaded as one JSON document.

Remaining priorities: ECS component identity/layout and ground render linkage; generated FB getters/typed fields; original input/move/attack timing units and code; LUT shader equation. No placeholder rules asserted as original.

Additional ECS registration probe:
 ecs_selected/stable_hash_raw_matches.json: 17/18 selected stable hashes occur in original metadata; zero occurrences in on-disk GameAssembly.dll. This does not imply registration absent at runtime.
 registry_blob_hash_matches.json ties those byte positions to metadata AssemblyTypeRegistry.Value defaults, preserving indices/offsets.
 registration_metadata.json preserves original registry and TypeInfo declarations. type_info_candidates.json interprets 15 records within known blob bounds at 104-byte stride (4 int32 + 3 uint64 + 16 int32). _HasBlobAssetRefs/_HasUnityObjectRefs are int32 flags. All selected size/alignment bounds pass.
 Hash 001f79e44e197fd0 => Unity.Transforms assembly, 32-byte size: LocalTransform candidate. Hash 8e54084ebb177ef0 => same assembly, 64-byte size: LocalToWorld candidate. Names are inferred from declaration/size; runtime type-array mapping and chunk component offsets NOT verified. Three hashes remain without validated record interpretation.
 field_101002/catalog_named_field_assets.json lists 23 exact logical paths; metadata/field_render_hooks.json preserves leaf-mesh/streaming declarations. These are leads, not completed terrain reconstruction.
Latest registration scan peak RSS 93,106,176 bytes; sequential guarded execution. No native DLL loading.

Latest update (supersedes 15-record status above):
 TypeInfo now 17 records / one raw-unmatched hash, after locating Hybrid.HybridComponents alternate-namespace registry. No exact full runtime Types array recovered.
 registry_order_candidates.json: six Transform declarations align with six saved registry records, still inferred. transform_hash_verification.json retains failed independent hash recalculations; never use these failures as positive name proof.
 *_chunk_layout_candidates.json: reference-source capacity, cacheline and flags/memory-order calculations. Important: encoded archetype bit29 creates chunk components with zero size in regular entity arrays. Ignoring it produced a failed terrain offset test; preserving this branch produces valid quaternion/matrix/position consistency.
 *_light_transform_crosscheck.json: four unique original companion TRS matches under tolerance, NOT all scale XYZ bit-exact. Scalar matches native X but Y/Z differ up to 2.98e-7. Inferred approximate comparison explicitly preserved.
 field_101002_scene_ref_candidates.json and town_100_scene_ref_candidates.json: 40-byte component hash16391158ac9a7b85 starts with GUID words that match 16 field / 70 town actual entityheaders. Initial 20/74 entities are root scenes, not total terrain entity counts.
 field_101002_child_probe.json: complete 16-child file inventory; first child de37d78410919f54dae1d39138dc8780 independently parsed (104352 bytes, 3 entities, 3 chunks, 20 type hashes), archive72fd49996b09db898e4d17f42152948f.
 field_child_type_info_candidates.json: 19/20 child hashes resolved to bounded TypeInfo constants, one unmatched hash. field_first_child_chunk_layout_candidates.json: terrain transform candidate Position(192,0,192), scale1, identity rotation, affine matrix/position checks pass, capacity68.
 field_child_render_binding_candidates.json: original SharedManaged records/payload offsets, restricted 40-byte object/array interpretation, native object-table material9074642373532751974 and mesh7267955958797348298. MaterialMeshInfo candidate raw(-1,-1,0), array-index candidates(0,0). Still inferred pending generic reader/type-array/body confirmation.
 terrain_first/ caches one native original mesh/material/texture typetree and ordered externals (785 vertices, 3960 indices); subsequent native asset/shader ownership belongs to Action session. No further duplicate texture or shader investigation here.
 Snapshot investigation delegated to Action: 41-byte editor capturebounds payload, excluded as terrain source.
 Remaining: exact runtime Types assignments, generic managed decoder validation, renderer activation/filtering, whole-field navigation/collision/replay, and LUT body. No complete playable field claimed.

16-child expansion (2026-10-08):
 ecs_selected/field_all_children_inventory.json: all 16 saved sections, 6897 entities, 261 chunks, 33 unique hashes. Largest input 1001060 bytes. Container source SHA preserved independently.
 field_all_child_type_info_candidates.json: 32 bounded TypeInfo records / one unknown hash6f02124d960c5b29. Type names/order remain inferred.
 field_all_children_render_summary.json and field_child_<GUID>_0_render_candidates.json: 6394 MaterialMeshInfo candidates, 349 PhysicsCollider hash candidates, 160 Parent candidates. Every entity identity/index/version and source offset is retained.
 All extracted LocalToWorld candidate matrices are affine; 160 local/world position divergences coincide with parent-bearing entities, so local/world equality is not a valid universal layout test. Hierarchy semantics still require independent validation.
 Twelve restricted managed payload interpretations consume all bytes; four other payloads remain unresolved and preserved by offset/size/hash. Expanded shared-index-to-chunk binding and native object-table resolution remain pending. No invented material fallback.
 Collision blob bytes/offsets are preserved, not decoded collision shapes or nav. This package does not establish active renderer status or field playability.
 Guarded expansion runs peak RSS <= 73187328 bytes, process commit cap1536MB. Original files, installed game and Unity project were not modified.

Shared binding completion (supersedes four-unresolved payload description above):
 field_all_children_shared_binding_summary.json and field_child_<GUID>_0_shared_bindings.json: 16/16 saved RMA prefixes parsed, shared indices681 completely consumed. Nonzero serialized index record hashes match each chunk shared-type candidate. Zero remains default, never shifted to array0.
 Each of6394 render entities now has its chunk RMA serialized shared index and negative Material/Mesh -> static array index candidate -> original object-ref table index -> source value offset. This selected scope has6394 negative Material and6394 negative Mesh values; nonnegative runtime IDs were not observed here, do not generalize to all scenes.
 The four remaining payloads were not unexplained RMA variants: shared RMA prefix is followed by normal managed components count36/162/12/327. Exactly537 bounded13-byte records remain: hash7374fd3a3060fa28/header3/count179, hash82d433bd89f38e81/header3/count179, hashe796be9b17f4e84d/header0/count179. Preserve header bytes, do not call3 a null flag.
 Every managed record is connected to an original chunk4-byte managed index and entity identity; hash equality and raw offsets pass. Exact runtime class bindings and semantic meaning remain inferred/unknown. Native object-table PPtr resolution stays with Action asset investigation.
 field_all_children_shared_binding_validation.json: independent original reread passes16/16, shared681/render6394/managed537; source hashes and array indices/record hash consistency validated. All16 payloads consumed exactly under the restricted hypotheses, not a generic serializer success claim.
 Official cached Entities1.4.3 SerializeUtility FillSharedComponentArrays/ReadManagedSharedComponents supports shared memory-order and trailing hash/object structure; original exact package version and runtime Types[] body are still unknown. No playable-field or activation confirmation.

URP original schema reference:
 metadata/urp_original_declarations.json and urp/HANDOFF.txt / urp_asset_schema_candidates.json / urp_schema_validation.json.
 Original declaration fields plus local compatible17.3.0 source support an inferred488B asset prefix schema (440B decoded,48B opaque), three full RendererData schemas568/496/552B and37 feature object headers. Raw source SHA/offsets and original compressed enum constants independently checked. Default renderer candidate0; saved renderer list16708/16711/16709; all three RenderingMode candidate2=ForwardPlus (original enum constants0/2/1/3).
 Exact original URP package semver and GlobalSettings managed body remain unknown. Current17.3.0 is only a reference, not asserted original version. No Unity installation or project mutation performed.

Action cross-validation update (bridge bmuz7rrpx-y):
 Reviewed C:/00.SVN/Action/dkbi-replica/reference/field_all_children_asset_join_evidence.json summary: native PPtr targets for tail hash7374fd3a3060fa28/header3 are ParticleSystem179; hash82d433bd89f38e81/header3 are ParticleSystemRenderer179; hashe796be9b17f4e84d/header0 are GameObject179. GameObject header0 is not null. This is Action's native reference validation, not a new original runtime Types[] extraction here.
 Native reference tables16/shared bindings681/render candidates6394/managed tail537 joined. Earlier four-unresolved status remains historical; current report managedUnresolvedChildren is empty. Source payload labels/order and runtime Types identity remain inferred, renderer activation remains unknown.
 Action reports Unity compilation0 errors,6897 entity/160 parent lookup revalidated and Python71 tests pass. These are reference/Core checks, not playable field confirmation. Physics/nav/input timing and renderer feature bodies still unknown.

Shader-source availability follow-up:
 shader_source/HANDOFF.txt and shader_source_availability.json. Scoped source-file suffix scan24640 installed files found0 source files;2657 TextAsset names found0 source-style leads. Two catalog .shader logical IDs are UI-only and do not prove editable files.
 Shader index430 rows all lack names: zero name hits must not be interpreted as zero custom shaders. Exact TerrainLit pathID998575624410370492 raw1666636B SHA8f1de537... matches existing native report. D3D11 compiled blob preserved, original HLSL/ShaderGraph source not discovered in this scope.
 Native Editor import/load/render remains Action isolated-test ownership and unknown. No new nav/input/LUT body result asserted. No duplicated shader/texture extraction or project changes.

Shader compatibility correction (2026-10-08, supersedes prior isolated-import unknown):
 Action reports NativeFormatImporter removed original compiled GPU data; initial supported=true was transient cache, reimport unsupported. Five raw-preserving bundle adapters fail actual compatibility guard. shader_source/COMPATIBILITY_FOLLOWUP.txt and shader_compatibility_container_audit.json preserve this correction and independent small-file comparison. Both original/control SF22/platform19/TypeTree=true, but successful control only contains TextAsset, not Shader. Next useful test is a real Shader bundle control and roundtrip/schema comparison; no version-string retry or guaranteed exact-editor fix. Derived review renderer may continue, original GPU fidelity unverified. Guarded reread peak RSS82591744B; no source/project mutation.
