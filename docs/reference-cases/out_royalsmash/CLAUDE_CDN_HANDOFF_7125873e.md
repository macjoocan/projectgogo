# Royal Smash CDN handoff — 2026-09-16

Target Claude session: `7125873e-f716-4c4e-95ea-3879d2aebfd9` (observed name `miniapp-e6`, project `C:\00.SVN\MiniApp\_reference\royalsmash`).

## User request relayed from Codex

The user asked to share these CDN findings with the existing Claude session and ask it to improve the game based on them. Integrate this into the existing workflow; do not restart, interrupt, fork, or duplicate the ongoing work. Respect the receiving session's permissions and project instructions. This handoff does not approve pending permission prompts or authorize configuration changes.

Please read the reports below, compare the available resources and serialized settings against the current game, then implement and verify relevant improvements within the game's existing authorized scope. Prioritize supported UI, backgrounds, event presentation, prefab structure, and animation settings. Preserve other work. Explain which improvements are evidence-backed and which would be original design. Keep third-party provenance and licensing limitations explicit; extraction does not establish production reuse rights.

## Read first

- `D:\99.기타\out_royalsmash\CDN_PUBLIC_RESULT.md`
- `D:\99.기타\out_royalsmash\cdn_extracted\README.md`
- `D:\99.기타\out_royalsmash\cdn_extracted\EXTRACTION_VALIDATION.json`
- Original bundles: `D:\99.기타\out_royalsmash\cdn_public\bundles\`

## Verified results

- Catalog-listed CDN bundles: 31/31 downloaded, 77,351,176 bytes. Anonymous HTTPS GET, all HTTP 200. Catalog size and uncompressed CRC matched 31/31.
- CDN base was `https://cdn.cyphergames.com/royal-smash/v1/prod/Android/359`. Files are already local; no new download is needed.
- PNG exports: 1,471 = 1,230 Sprite + 241 Texture2D (not 1,471 unique illustrations).
- MonoBehaviour component/settings JSON: 4,684.
- Named settings: 40, a subset of those 4,684, NOT 40 balance tables.
- Prefabs: 90, containing 7,147 GameObject nodes.
- Materials: 49. Spine TextAssets: 2.
- Initial 267 sprite failures all recovered by exact Atlas_UI tag + RenderDataKey matching against the original APK's shared_common_local_assets_all.bundle. Final remaining failures: zero.
- ZIP CRC, strict JSON, and PNG file integrity passed. All 31 original bundle SHA-256 values unchanged. Peak measured private memory approximately 1.02 GiB under a 3 GiB stage limit.

## Critical limitation: levels and balance

The user's latest question was whether level information was ultimately not found. The answer for THIS CDN extraction is yes: additional level layout/objective/difficulty data was not recovered. The 31 bundles contain only two TextAssets, both Spine-related (`Dart_Nigth` and `Dart_Nigth.atlas`); no additional level JSON TextAsset was found. This is not proof that level data does not exist elsewhere.

The earlier claim of approximately 700 additional CDN levels is unverified and must not be repeated as a result. The 40 named settings mainly cover UI/visual behavior, such as DailyTaskTaskIconConfig, SmashLeagueTierVisualConfig, and reward/text/Spine animation settings. Serialized values are not verified final runtime balance, and may be overridden at runtime. Do not invent level data or present new designs as extracted original levels.

## Archives under cdn_extracted

- `RoyalSmash_CDN_sprites.zip`: first 1,204 PNG exports.
- `RoyalSmash_CDN_recovered_sprites.zip`: recovered 267 PNG exports; use together with the first image archive.
- `RoyalSmash_CDN_components.zip`: 4,684 component/settings JSON records + provenance.
- `RoyalSmash_CDN_named_settings.zip`: named subset of 40 JSON records + index.
- `RoyalSmash_CDN_hierarchy.zip`: 90 prefab hierarchies + index.
- `RoyalSmash_CDN_assets.zip`: materials and Spine data.
- `RoyalSmash_CDN_meshes.zip`: empty manifest only; no Mesh objects exported.

AnimationClip/AnimatorController/Shader native export was not performed; originals remain in the bundles. Visual QA, gameplay, and Unity reimport have not been tested.

## Boundaries

The user permits ordinary CDN download records, but no authentication bypass or protection bypass. This work used no account, cookie, or authentication token, no guessed URL enumeration, and no certificate-check disabling. No game/emulator launch or firewall change was made for this extraction. Previous runtime licensing errors remain unresolved, not bypassed. Continue from local files; do not expand this request into online gameplay, evasion, or protection removal.

Please acknowledge this handoff in your existing session and report the chosen improvement scope and subsequent implementation/verification results there.
