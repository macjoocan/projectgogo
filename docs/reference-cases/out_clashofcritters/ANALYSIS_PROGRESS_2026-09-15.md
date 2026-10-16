# Clash of Critters balance-data recovery progress

## Latest: package decrypted and Config exported (2026-09-15)

SUCCESS: this section supersedes all older NO CONFIGURATION PLAINTEXT statements.
All 5,327 package records decrypted and decompressed; all 2,670 Config Lua 5.4
chunks parsed. 2,632 exported as literal JSON; 38 Graphs configs exported with
explicit symbolic class references, without executing their require calls.

- Deliverable: `Clash_0.46.1_BALANCE_JSON.zip`; contents in `balance_tables_v0461/`.
- Verification passed: all record hashes and Config re-evaluation comparisons;
  malformed chunk/external CALL rejection and archive CRC test. Archive 3,994,127
  bytes, SHA256 `6c0d2e6db8495d185b8b23b6e3078b597d3994808bc612efeea262eef01be51d`.
- AppInfo, Config, Game and Localization .jsone also decoded to valid JSON;
  saved separately under `decrypted_v0461/Metadata/` (not part of balance ZIP).
- Decrypted bytecode and Pb payload: `decrypted_v0461/`; per-record SHA-256 in
  `decode_report.json`. These .luae files now contain plaintext Lua bytecode,
  not original textual source code.
- Native decoder 0x882bf4: 8-byte outer header, little-endian-word Blowfish ECB,
  inner prefix length and metadata, then size-prefixed raw LZ4. Initialization
  at 0x8829d0 supplies a 32-byte ASCII key recovered from a native literal.
- Original loader RELA entries resolve on-disk zero vtable slots; literal decoder
  0x9252f8 uses the global XOR word at VA 0xa9ad90 (file 0xa92d90).
- Tools: `inspect_recovered_native.py`, `recover_native_literals.py`,
  `decrypt_clash_records.py`, `lua54_static_tables.py`, `verify_clash_delivery.py`
  under `../android-analysis/tools/`. Use Blender 5.2 embedded Python.
- Read delivery README for key preservation, graph limitations, version scope
  and verification methodology. Server overrides/latest live balance are not claimed.
- No game launch, game-server/CDN request, or online concealment was performed.
  This is not a fresh whole-host network audit or a guarantee of undetectability.

## Historical: native loader payload recovered (2026-09-15)

This update supersedes older statements that all igame code bodies remain encrypted.
At this historical checkpoint configuration plaintext had not yet been recovered.

- Traced actual caller `0xab4bac`: stored loader payload length is descriptor `+0x88`
  (953,440), not header-table length `+0x10` (336); transform arguments 4/5 are -1/-1.
- Isolated Unicorn 2.1.4 execution of ONLY `0xab3314..0xab3ebc`, with memory-only
  memcpy/memset/strlen stubs and prohibited guest interrupts/syscalls, recovered the
  payload. All six original program headers pass type/flags/file-range/size/alignment
  checks. No game process or game/CDN request was initiated by this work.
- Code transform input: file offset 400, length 10,461,040, same -1/-1 arguments.
  Result contains a size-prefixed zlib stream: 4,652,428 compressed bytes become
  11,093,184 bytes, with exact input consumption, output size and zlib EOF/checksum.
- Added an ANALYSIS-ONLY synthetic ELF header/section scaffold; this is not a runnable
  restored APK/library. Native disassembly at FileUtils_getDataFromFile `0x930388`
  and igame_loadText `0x99c6b4` now shows coherent ARM64 function bodies. Numerous
  branch helper stubs remain; no claim that all obfuscation or relocations are resolved.
- Artifacts: `android-analysis/reports/loader_transform_actual_call/`,
  `loader_code_actual_call/`, `loader_code_validated/` (all under reports).
  Validated payload SHA256: `900106a0c83c7ab5828ba20f2f41a0a7e5bd5fbdbeb358021186aad05bcacb49`.
- Next: statically trace the recovered file/text load functions and their helper stubs
  to identify the package record decryptor; then validate on local records only.
- Unicorn was installed from PyPI with approval into workspace python_deps. No game
  network activity was added. Historical emulator isolation is NOT a fresh host audit.

Date: 2026-09-15
Source: `Clash+of+Critters_0.46.1_APKPure.xapk`
Package: `com.farlightgames.pgame.gp` (0.46.1 / versionCode 4097)

## Safety boundary

- No game server or game CDN request was made.
- The only runtime launch used the validated network-restricted emulator.
- QEMU showed zero external connections during the launch attempt.
- No root/hook/emulator concealment or anti-detection bypass was used.
- Current recovery work is static and reads only files bundled in the XAPK.

## Confirmed findings

- Balance/script data is stored in `BinaryAssets.apk/assets/pgame.pkg` plus a compact
  path index, `pgame.pkg.bin`.
- Each package record uses this boundary format: marker `ff ff ff ff`, plaintext
  length as unsigned 32-bit little-endian, then ciphertext padded to an 8-byte boundary.
- A sequential scan from offset zero recovers **5,327 records** and lands at the exact
  file size, **15,770,768 bytes**, with zero trailing bytes.
- The complete index is now decoded: a uint32 decompressed-size prefix followed by raw
  LZ4 at byte 4. The result is exactly 294,258 bytes, containing package size, entry count,
  then repeated UTF-8 filename length/name, record size and record offset fields.
- `Pb/pgame.pbe` starts at offset zero; `Src/Actor/Animation.luae` starts at `0x29140`.
  All 5,327 names match consecutive package records and their declared lengths, with
  exact EOF coverage and no duplicate names. The former offset attribution was incorrect.
- Entries comprise 2,670 `Config`, 2,615 `Src`, 41 `Tolua`, and one `Pb` record.
- `Clash_Config_2670_ENCRYPTED.zip` preserves all 2,670 named Config records with their
  headers and ciphertext. It includes a manifest and is NOT a decoded balance-table export.
- Repeated 8-byte ciphertext blocks occur across many records, confirming a
  deterministic 8-byte-block transform (ECB-like behavior or equivalent custom logic).
- The four standalone `.jsone` files share their second ciphertext block, providing
  a strong cross-file oracle for future algorithm tests.
- `global-metadata.dat` starts with `HTPX`, and `libNetHTProtect.so` is bundled.
- Its HTPX header stores the exact protected file size in bytes 4-7 (`9,960,028`).
- `libunity.so` dynamically resolves **101 mass-renamed ordinary IL2CPP APIs** whose
  exported names begin with `HTP`; these are not three special decryption entry points.
- Sequence alignment against Unity's IL2CPP API declaration table mapped all 101/101
  obfuscated entries. For example, `HTPx6Ys2roy5OUJqbiX3VEeS9p` maps to
  `il2cpp_class_get_namespace`, `HTPX9gTLcUYHKGqQdDO7A` maps to
  `il2cpp_class_get_type`, and `HTPxQAVmlRSTN7BcYdwOhspGD8Ez45Uig1` maps to
  `il2cpp_class_get_static_field_data`.
- The package reports Unity `2022.3.62f3`; the available local declaration table is
  Unity 6000.0.62f1, so five plaintext alignment differences remain version-sensitive,
  while the 101-name obfuscated run is fully positionally mapped.

## Unsuccessful algorithm/key candidate tests

- DES/3DES ECB: 15,249 keys derived from 6,690 native-library strings; no candidate.
- Blowfish ECB: all 295,143 printable native-library strings of valid key length;
  no candidate.
- TEA/XTEA: 8,072 algorithm/endian/key combinations from exact 16-byte and relevant
  MD5-derived native strings; no candidate.
- Earlier filename-derived DES/3DES, Blowfish, TEA/XTEA and repeating-XOR attempts also
  produced no valid JSON.

These tests exclude only the tested algorithm/key combinations. They do not rule out those
algorithms in general or prove the source of the key. Non-printable and derived keys remain
possible, along with other transforms.

## Runtime result

- The x86_64 offline emulator installed all APK splits, obtained root ADB, and ran a
  loopback-only Frida server.
- The game stopped before Unity initialization because `libnesec-x86.so`, located in
  the ARM64 split, is actually an x86_64 ELF and was loaded into an ARM64-translated process.
- No telemetry response or server-side block was involved.
- The protector library was not patched or replaced because that would cross into
  concealment/bypass behavior.

## Reproducible outputs

- `android-analysis/reports/pgame_records.json` — all 5,327 record boundaries
- `android-analysis/reports/cipher_candidate_hits.json` — DES/3DES report
- `android-analysis/reports/blowfish_candidate_hits.json` — Blowfish report
- `android-analysis/reports/tea_candidate_hits.json` — TEA/XTEA report
- `android-analysis/reports/global_metadata_xrefs_pure.json` — metadata string scan
- `android-analysis/reports/libunity_htpx_slot_12f0260_xrefs.json` — HTPX API-slot scan
- `android-analysis/reports/il2cpp_api_table_mapping.json` — 234-entry resolver table,
  including 101/101 obfuscated-name mappings
- `android-analysis/tools/scan_pgame_records.py` — package boundary scanner
- `android-analysis/tools/test_dotnet_cipher_candidates.ps1` — DES/3DES tester
- `android-analysis/tools/test_blowfish_candidates.js` — Blowfish tester
- `android-analysis/tools/test_tea_candidates.js` — TEA/XTEA tester

## Next safe path

1. Use the recovered names to classify ciphertext blocks and identify bundled loader code.
2. Runtime logs place the failure in `MyApplication.attachBaseContext`, before the game
   activity starts. A post-IL2CPP-load dump is not established as reachable on this AVD;
   the previous proposal assumed a later crash than the log supports.
3. A compatible, network-isolated ARM64 runtime remains a possible source of decrypted
   data. No new game launch was performed during the index-recovery pass.

## Index recovery outputs and validation

- `android-analysis/reports/index_recovery/pgame_named_records.json`: full name/offset map.
- `android-analysis/reports/index_recovery/balance_name_candidates.json`: 3,160 keyword
  matches across configuration and source filenames; these are candidates, not verified tables.
- `android-analysis/tools/decode_pgame_index.py`: bounded decoder, package validation,
  and encrypted Config archive writer.
- Four decoder tests pass, including overlap, extended lengths and malformed-input rejection.
- ZIP CRC validation passes for all 2,672 members (2,670 records plus README and manifest).
- LZ4 format reference: https://github.com/lz4/lz4/blob/dev/doc/lz4_Block_format.md

## Content-decryption follow-up

Latest addition: loader code now confirms the exact symbol-name, address and size
transforms for both native libraries. IL2CPP has 2,370 reconstructed protected symbol
records; igame has 2,905. All decoded function fields pass four-byte alignment checks.
For igame, an evolving XOR key recovered 2,962 nonempty names, including precise file
read, text load and Lua buffer entry points. Code at those positions remains encrypted.
Reports: `android-analysis/reports/il2cpp_symbol_fields.json` and
`android-analysis/reports/igame_symbol_fields.json`. These supersede the earlier claim
that symbol addresses/sizes have not been reconstructed; runtime callability is still
unverified and code-body decryption has not succeeded.

Status: **No verified plaintext configuration contents recovered yet.**

- Expanded key testing accepts JSON directly or after size-prefixed LZ4, gzip or zlib,
  with bounded decompression and strict UTF-8 JSON validation across all four `.jsone`
  files. This addresses the former printable-text-only test limitation, but still assumes
  a common key across those four files and does not exclude untested wrappers or modes.
- Final expanded run: 315,825 candidate/algorithm tests, zero validated hits. The run
  includes recovered-symbol seeds and the newly recovered symbol-table XOR key.
- Symbol-table recovery succeeded: periodic XOR key `42 23 31 56` restores the protected
  IL2CPP symbol strings. Combined with untouched symbols, the inventory has 2,512 names.
  All 234 names resolved by `libunity.so`, including all 101 HTP-renamed APIs, match this
  recovered inventory. This is independent confirmation of string decoding.
- The key does not restore the tested code/data regions or configuration files. Symbol
  address/size fields remain protected and must not be treated as callable addresses.
- The same periodic-XOR probe did not recover `libigame.so` symbols.
- Outputs: `android-analysis/reports/compressed_cipher_recovered_seeds.json` and
  `android-analysis/reports/il2cpp_string_recovery/{symbols,recovery_summary}.json`.
- Current obstacle: the configuration decryptor's executable code/metadata remains
  protected, and the available emulator fails before game initialization. The remaining
  routes are deeper static reconstruction of that loader or a compatible isolated ARM64
  runtime. No game process or game/CDN connection was started during this follow-up.
- A fresh host process/network audit was not completed: the read-only CIM process query
  returned access denied. Earlier isolation results are historical, not a current guarantee.
