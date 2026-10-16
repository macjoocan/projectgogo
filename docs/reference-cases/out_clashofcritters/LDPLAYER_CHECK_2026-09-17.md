# LDPlayer local cache availability check — 2026-09-17

## Latest: ADB connected after user enabled USB debugging

This supersedes the earlier disconnected-state observations below. An initial retry still returned no devices and localhost5555 connection-refused (10061), but a subsequent live check after the VM process changed found `emulator-5554 device`. No reboot was issued by Codex; the exact cause/timing of registration is not proven.

- Guest identity: `uid=2000(shell)`, not root.
- Android package-manager confirmation: `com.farlightgames.pgame.gp`, **versionName 0.47.1 / versionCode4242**, minSdk23 / targetSdk35.
- `/sdcard/Android/data/com.farlightgames.pgame.gp`: du -k total **10,708 KiB** allocated (~10.46 MiB). This is filesystem usage, not a sum of exact file lengths.
- `files/il2cpp`: 10,392 KiB, predominantly `Metadata/global-metadata.dat` (9,967,284 bytes); four standard assembly resources and unity.ver are also present. File contents/protection status not tested.
- Other observed entries are small cp/ex/sdk cache files, park/log, neCrash and startkv_debug.txt. Contents were not read; they may contain account/telemetry data and were not copied.
- `/sdcard/Android/obb/com.farlightgames.pgame.gp` is empty.
- `/data/user/0/com.farlightgames.pgame.gp/files` and `/cache`: **Permission denied**. No privilege escalation or access bypass attempted.
- Installed readable package files include base.apk (25,647,879 bytes), split_BinaryAssets.apk (17,200,212 bytes), split_UnityDataAssetPack.apk (127,287,155 bytes), plus an arm64 split reported by pm path. These are installation APKs, NOT proof of CDN cache contents. No APKs or cache files have been pulled in this check.

Conclusion: local non-root ADB works. Downloaded CDN bundle presence/completeness remains unverified; no distinct CDN bundle collection was found in the accessible external app directories. Private storage is a possible location, not a confirmed one. A separate static audit of readable 0.47.1 APK assets is feasible without reading private app storage.

Security note: the VM-owned5555 listener was observed bound to **0.0.0.0**, not loopback-only. This does not prove reachability through Windows Firewall, which was not audited. Codex connected locally only, did not change listener/firewall settings, and recommends turning off debugging after use. Never describe the current setup as verified local-only exposure.

Read-only checks used bundled adb with explicit `-s emulator-5554`: `shell id`, package-scoped `dumpsys package` filtered to version fields, `pm path`, scoped `ls -ld/-la/-ln`, and `du -k -d 3/4`. No game launch, original game/CDN request, root, hook, or file export was performed by this pass. Existing emulator traffic was not blocked or audited.

## Follow-up: authorized local ADB configuration inspection

The user approved checking/adjusting local-only ADB. Inspected the running LDPlayer14 v14.0.25.2 UI using the computer-use skill, without saving settings. Other settings showed Root permission OFF; no ADB selector was visible there, in Network, or in Device settings. Network remained enabled. Closed the dialog with Cancel. The game was already running when the minimized window was restored; no launch command was issued.

A fresh elevated bundled `adb.exe devices -l` still returned an empty device list. No guest cache was read. The reason for missing ADB remains unresolved; an absent UI option does not establish that the feature is unsupported.

Official current documentation describes selecting local ADB then saving/restarting, but the observed installed UI does not match it: https://jp.ldplayer.net/support/ldplayer-adb-command.html (2026-09-09). No restart, reinstall, update, root toggle, invented configuration field, or access-control workaround was attempted. The computer-use skill prohibits directly changing in-app security/access settings, so any needed debugging authorization step must be performed by the user. A user-exported game cache is an alternative input; whole-instance backups may contain unrelated account data and were not collected.

## Confirmed

- Installation: `C:\LDPlayer\LDPlayer14`, CLI reports v14.0.25.2.
- Elevated `ldconsole.exe list2` confirms instance index 0 / LDPlayer is running. Sandboxed list2 incorrectly appeared stopped; do not use that initial result as current state.
- Host-side `vms\leidian0\appsinfo.data` lists `com.farlightgames.pgame.gp`, display name `뚜까펫: 서바이벌`, versionCode **4242**. Human-readable version is empty in this inventory. This is host inventory evidence, not an Android package-manager query.
- Existing APK analysis was versionCode4097 / 0.46.1. The installed inventory therefore differs from that old analysis build.
- Existing `ANALYSIS_PROGRESS_2026-09-15.md` says APK Config extraction succeeded: 2,670 chunks (2,632 literal JSON and 38 graph configurations with symbolic references). This is historical evidence, not a fresh output revalidation.

## Not yet confirmed

Downloaded CDN cache file presence, counts, sizes, integrity, version, and whether it adds balance tables have NOT been checked successfully.

`adb.exe devices -l` returned no devices. It started the host-side local ADB server on port5037. Official LDPlayer query:

```powershell
& 'C:\LDPlayer\LDPlayer14\ldconsole.exe' adb --index 0 --command 'shell ls -ld /sdcard/Android/data/com.farlightgames.pgame.gp /sdcard/Android/obb/com.farlightgames.pgame.gp'
```

returned `adb.exe: device 'emulator-5554' not found`. Thus no Android directory listing was obtained. A listener survey showed localhost5037 and VM-owned2222, but no5554/5555 listener; the protocol of2222 was not established or probed. This does not prove why ADB is unavailable.

## Scope / next step

No game launch, game/CDN request, root enablement, hooking, protection bypass, emulator configuration change, shutdown, or bulk disk copy was performed. The user's running emulator has networking enabled; this check is NOT a whole-host traffic audit and does not claim its existing game traffic stopped.

Next needs either an already-exported game cache/backup location or an authorized local-only ADB connection. Do not assume changing a setting is sufficient, or that ADB access guarantees access to app-private storage. Preserve the current instance and avoid copying a live virtual disk as if it were a consistent backup. Do not collect account preferences, tokens, or unrelated app data.
