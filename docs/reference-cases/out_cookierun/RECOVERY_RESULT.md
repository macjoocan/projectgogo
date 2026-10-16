# CookieRun Crumble 1.0.002 recovery

Date: 2026-09-15

Source: `C:\Users\NHN\Downloads\com.devsisters.cc-1.0.002.xapk`.
All processing was local; the game was not launched and no game server/CDN was contacted.

## Verified results

- `patch_binary_set`: 185 decrypted entries: 183 `.bytes` tables plus two CSV files.
- Follow-up: all 183 `.bytes` tables have been converted to named-field JSON (67,940 rows), with zero conversion failures or unknown fields. See `READABLE_TABLES.md` for validation and interpretation limits.
- `entities_binary_set`: 1,571 decrypted JSON files covering stages, cookies, skills and other entities. Every JSON parsed successfully.
- `raw_file_set`: five translation JSON files and one placeholder text file. Every translation JSON parsed successfully.
- All 1,762 files passed ZIP AES password verification, full payload HMAC, decompressed size and CRC32 checks.
- Per-file SHA-256 hashes and validation results: `decryption_validation.json`.
- Recovered files: `decrypted/`; packaged deliverable: `CookieRunCrumble_decrypted_1.0.002.zip`.

## Reproduction

- `inspect_local_archives.py` inventories the embedded archives and Unity 39 string literals.
- `test_zip_literals.py`: 35,680 literal candidates, no authenticated match.
- `test_zip_derived.py`: 8,670 bounded manifest/filename/salt-derived candidates, one authenticated match.
- `decrypt_archives.cjs` validates and extracts the three ZIP AES-128 containers with Node's built-in cryptography and compression libraries.
- The successful derived candidate is stored in `zip_derived_test.json`; the exact native `ComputeZipPassword` implementation has not been disassembled or proven equivalent.

## Remaining work

Readable tables are packaged in `CookieRunCrumble_readable_tables_1.0.002.zip`. Field names and CLR types have been recovered; enum names are provided separately. Game-specific units and scalar wire-type caveats remain documented in `READABLE_TABLES.md`. This package is a local version snapshot, not a claim about current server-side balance.
