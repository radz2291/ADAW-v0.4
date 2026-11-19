# Guitar Rig 7 — installed-plugin compatibility check

19 November 2026. **BLOCKED: this installed plugin crashes during loading in
the current DawDreamer worker. No Guitar Rig-processed audio was produced.**

Owner explicitly authorized this installed plugin. The isolated branch is
`adaw/guitar-rig`, based on latest Studio `5e41769`. Existing song projects and
both earlier branches were not edited. The plugin remains in its vendor install
location; no binary, preset, activation data or third-party sample is committed.

## Observed results

| Check | Result |
|---|---|
| Guitar Rig 7.0.2 x64, exact installed file fingerprint | Recorded |
| Load at 48 kHz / 256 frames | FAIL: worker exit 3221225477 |
| Load at 44.1 kHz / 512 frames | FAIL: same exit |
| Fresh 48 kHz load after committing a real dry baseline | FAIL: same exit |
| Windows application event | Guitar Rig 7.vst3, exception 0xc0000005 |
| Previous source head and exact playable WAV after crash/reopen | PASS |
| New engine worker after failure | PASS |
| Existing contract/recovery regressions | 16 passed |
| Parameters, wet render, automation, state restoration, listening | BLOCKED / not evaluated |

Windows reports the fault inside the plugin. This does not establish whether the
underlying cause is plugin initialization, host compatibility, graphics or local
installation/activation. No cause is guessed and no alternate plugin substituted.
This is an RWT-11 effect-loading subset failure and RWT-06 preservation subset
pass, not certification of either full permanent scenario.

## Organization and reproduction

- `tools/probe_vst_effect.py`: reusable bounded probe using existing service and
  isolated workers. Accepts an exact approved path; creates a fresh `.local` run.
- `evidence/plugins/guitar-rig/run-001.json`: measured failures, exact identity,
  environment, Windows faults, dry audio hash and regression result.
- `.local/guitar-rig/run-001/`: initial approval, two probes and engine check.
- `.local/guitar-rig/run-002/`: disposable project, dry baseline, raw report and
  worker logs. No `wet.wav` exists because plugin loading failed.
- `.local/guitar-rig/pytest-temp/`: disposable regression files; ignored by Git.

Run from this fork; use a new run folder each time:

```powershell
& 'C:/Users/RZ1/Desktop/RZ-Music/261113-ADAW-v0.4/.venv/Scripts/python.exe' -m tools.probe_vst_effect --folder .local/guitar-rig/run-003 --plugin 'C:/Program Files/Common Files/VST3/Guitar Rig 7.vst3' --approval 'Owner requested Guitar Rig test' --timeout 60
```

The command exits nonzero for the observed plugin failure and retains evidence.
The 220 Hz, amplitude 0.1, two-second stereo source is an explicit engineering
fixture, not a song or musical quality claim. The tool's successful-load/wet-render
branch was not exercised with Guitar Rig. It does not choose a preset or certify
parameter/state compatibility even if a future installation loads successfully.

Next bounded step: establish whether the same installed version opens in its
standalone application or another trusted host, then retest any corrected or
updated vendor installation with a fresh run. No host/engine replacement or
plugin installation change was made in this task.
