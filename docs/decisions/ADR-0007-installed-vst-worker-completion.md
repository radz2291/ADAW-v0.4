# ADR-0007 — Opt-in Windows offline plugin host profile

19 November 2026. Status: LIMITED ADOPT, isolated Guitar Rig branch only.

## Evidence and correction

The initial Guitar Rig report described a loading crash. Raw worker result files
show successful instantiation, 2,594 controls and four inputs/two outputs, followed
by a native process-exit crash. The service correctly rejected nonzero exits.
Lifecycle checkpoints reproduce the crash after all work, including explicit
processor/engine removal. COM STA initialization and os._exit do not solve it.
This local evidence narrows the phase; it does not identify the vendor's internal
bug. The owner's standalone application works.

Upstream [plugin creation and destruction](https://github.com/DBraun/DawDreamer/blob/v0.9.0/Source/PluginProcessor.cpp)
and [bus handling](https://github.com/DBraun/DawDreamer/blob/v0.9.0/Source/PluginProcessor.cpp#L194)
were inspected. Disabling non-main buses still reports four inputs locally;
forcing two inputs is rejected. No channel truncation is introduced.

## Versioned compatibility profile

`windows-stereo-zero-aux-isolated-v1` is an explicit host-local opt-in for one
approved plugin fingerprint. Standard behavior remains the default. Changing the
profile clears its previous probe, requires re-probing and is recorded in each
render's plugin dependency manifest. Restored archives must configure host-local
requirements explicitly; portable profile replay is not certified here.

- Accept only actual 2-in/2-out or 4-in/2-out plugins. If a four-input instance is
  fed stereo, add a named playback node carrying two exact zero channels. The
  rendered node report records this mapping. This is not an active sidechain.
- Run native work normally. Save audio/state through the existing worker paths;
  serialize, flush, fsync and close the result file. Only after successful work,
  end the disposable Windows worker using self-TerminateProcess with exit zero.
  Its warning is `HOST_SHUTDOWN_BYPASSED`. This skips DLL detach, not rendering.
- Preserve normal error exits, crash rejection, timeout handling, service leases,
  artifact hash/format verification and atomic publication. No failed historical
  job is relabelled successful. Fault tests verify that the profile cannot convert
  an earlier crash, exception or timeout into success.

[Microsoft documents](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process)
that TerminateProcess omits DLL-detach notifications. It terminates all threads,
so plugin shutdown/cleanup and background side effects are not certified. The
worker is disposable and owns no project database. Parent service publication
still verifies actual staged bytes. This is an explicit compatibility workaround,
not a fix to Guitar Rig's internal cleanup or a hardened sandbox.

## Limits retained

Actual stereo rendering and a measured Rack Master Volume change now work.
Opaque state restoration is still rejected: parameter 0's reported `min` changes
from `no sound` to `Rock Seeker`. A diagnostic also found master-volume readback
reset by state loading. Catalog binding rules are not weakened; full preset/state
replay, arbitrary rack edits, UI integration and portability remain unverified.
No engine version, dependency lock, plugin binary or owner song was changed.

Evidence and runnable commands are under `evidence/plugins/guitar-rig/`.
