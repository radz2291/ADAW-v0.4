# Independent everyday-interaction evaluation — round 03

**98/100. All mandatory checks PASS. The frozen functional threshold is met.**
This result applies to the exact candidate below and the tested workflows. It is
not98% of a commercial DAW's feature set, a population usability result, musical
listening approval, or owner acceptance of the presentation. A subsequent visual
pass must be assessed separately against this same unchanged rubric.

The sole lost check is **U3B (2 points)**: Help advertises Shift+Up/Down as octave
transpose, but the piano roll clamps movement to its currently visible pitch
range. In the independent test, MIDI 60 moved to70 rather than72. The reference
does not disclose that limitation. No criterion, weight or threshold changed.

## Fixed candidate and independence

- Commit: `88fe8026a8d78dea83a2037cd02477b0a9a171f9`.
- Before/after assessed code tree SHA-256 (identical):
  `c54623e0c40c9ff8a65925fbcf7c6b5301ebd3e124d665ecb8774d1b240eb86c`.
- Frozen rubric SHA-256:
  `904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253`.
- Independent evaluator authored fixtures and probes; did not edit production or
  rubric. All mandatory checks were rerun on this candidate. Per-file manifests
  are `tree-before.json` and `tree-after.json`.
- Windows AMD64, existing Python3.12.14 environment, Node24.22.1, installed Edge
  `157.0.4341.60` headless. Desktop1440×900 and1280×720; narrow390×844.

## All 50 fixed checks

Each A/B earns2 only on PASS. FAIL/UNTESTED earns0. No exclusions or fractional
credit. Evidence paths below are relative to this report's directory.

| ID | A | B | Points | Independent evidence |
|---|---|---|---:|---|
| E1 Direct edits | PASS | PASS | 4 | `main/interaction.json`: manual gain commits and reloads without staging. `workflow/workflow.json`: pending agent proposal remains separate/unapplied. |
| E2 Create/delete | PASS | PASS | 4 | Pointer add on empty space, selectable1/16snap, stableID/pitch/start/duration; Delete+Escape+emptyDelete+reload match source. |
| E3 Manipulation | PASS | PASS | 4 | `editing/editing.json`: pointer move/resize, pitch/timing keys, velocity77 and native render; Shift-click/CtrlD retains originals, relative attributes, distinctIDs. |
| E4 Undo/redo | PASS | PASS | 4 | Three CtrlZ/redo operations and visible controls. Workflow disjoint external edit survives undo/redo; `service.json` rejects conflicting inverse without overwrite. |
| E5 Arrangement | PASS | PASS | 4 | Visible group move/duplicate persists/reloads; split/trim canonical boundaries/native rendition; explicit sample split/front-trim limitation. |
| F1 Mix feedback | PASS | PASS | 4 | `mix/mix.json`: gain87.9 ms,solo143.6 ms,mute188 ms measured at actual digital output. Native subsequent muted-solo render exactlyzero; live preview/canonical render visibly distinguished. |
| F2 Audition | PASS | PASS | 4 | `audition/audition.json`: actual 2-bar note updates playable in1932.06/1703.92/2065.77 ms; real playback. Previous audio/progress/exact revision, held old native response cannot replace newer. |
| F3 Navigation | PASS | PASS | 4 | Space/Home/ruler/section/text isolation plus `waveform-settled.json` click62.375→113.547185s. Fullsong exact sample boundaries/bar/beat including3/4 pass. |
| F4 Loop/compare | PASS | PASS | 4 | `glass/glass.json`: visible intro loop wraps/stops/restarts without source mutation; identified A/B retains2s position and current/stale identity. |
| F5 Feedback | PASS | PASS | 4 | Explicit loading/save/preview/failure states and successful retry. `identity/identity.json` loading never says old Latest mix. Delayed doubleMute and rapid note nudges preserve last requested state. |
| M1 Channels | PASS | PASS | 4 | Gain/pan/mute/solo reload; two solos sum, mute takes priority, solos clear; bus/master gains usable and source-backed. |
| M2 Metering | PASS | PASS | 4 | Actual stereo samples, independent silent/louder comparison, clipping and pause clear. Digital peak7.51187 produces CLIP; zero signal produces zero/−60dBFS display. No fabricated track meters. |
| M3 Devices | PASS | PASS | 4 | Ordered instrument/effects/bus routing and read-only limitations. UIlevel0.15 persists and native decoded RMS0.0205116→0.0101872. |
| M4 Precision | PASS | PASS | 4 | Pointer+keyboard fader, numeric/reset/pan center. -72dB expands inspectable range; listening level leaves musical source unchanged. |
| M5 Continuity | PASS | PASS | 4 | Selection across views, zoom4×/timeline160 px/bridge section retained. `ergonomics/ergonomics.json`: actual overflowing mixer retains148 px during unrelated channel edit. |
| U1 Sizing | PASS | PASS | 4 | Real divider drag, browser/inspector collapse, timeline alignment, reload preferences and Reset layout at both desktop sizes. |
| U2 Readability | PASS | PASS | 4 | Both desktop screenshots identify tracks/sections/selection/editor/transport; actual essential pointer targets meet24 px. The raw1 px diagnostic is a clipped hidden ruler keyboard input, not its visible pointer target (`hitarea-supplement.json`). |
| U3 Tools/reference | PASS | FAIL | 2 | Add/delete/duplicate/split/trim/undo/redo/snap/audition exposed. Shift-octave help is inaccurate at current visible pitch bounds:60→70, not72. |
| U4 Keyboard/access | PASS | PASS | 4 | Named surfaces/dialog; Tab/ShiftTab/Escape focus flow. `focus-supplement.json`: actual keyboard focus on Play and mixer numeric gain shows2 px solid outline; editor/volume also visible. Fields isolated; protected controls announce/reject. |
| U5 Scale/layout | PASS | PASS | 4 | Full162.307688 s Glass/search/zoom/play without exceptions.390px document width390; play/review reachable; all assets local. |
| S1 Source truth | PASS | PASS | 4 | `cli-ui-agreement.json`: actual CLI and API source/revision identical after edits. Service validation/atomic history; protected UI/direct API mixed batch leaves head/source unchanged. |
| S2 Conflicts/history | PASS | PASS | 4 | Visible same-field stale conflict; disjoint external edits survive edit/undo/redo. Refresh retains stable IDs/history; duplicate command idempotent. |
| S3 Audio identity | PASS | PASS | 4 | Held historical metadata now shows Loading/emptyidentity and retains previous verified bytes until response; correct identity precedes switch. Original project/source/export separately verified below. |
| S4 Recovery | PASS | PASS | 4 | Failed native request retains last good playback and retries. Actual invalid operation/missing dependency atomic rejection; interrupted/superseded native response not promoted. |
| S5 Regression/integrity | PASS | PASS | 4 | Independent full suite62 passed1 optional Dexed skip; frontend-absent contract included. Local pinned libraries/notices, current origin/token403, static404, frozen hash exact. |

Totals: **E20 + F20 + M20 + U18 + S20 =98/100**.
Mandatory E1,E2,F1,F2,S1–S5: **all A/B PASS**. No observed source loss, silent
overwrite, fake meter, broken protected enforcement, wrong-current audio identity
or reproducible application crash remains in the tested candidate.

## Actual signal and audio evidence

Live mix latency is measured from gestures to independently sampled WebAudio
signal changes, not control movement or trusting product meter values. The mix
probe inserts an evaluator-only silent sink after the real digital mix tap to
avoid loud physical output during clipping checks; the application meters still
receive actual generated playback samples. This is measurement, not a claim of
listening. Combined RMS0.0421472 → solo0.0212729 → -6dB0.0106054; mute reaches0.
Two-solo RMS0.0422811 versus one-solo0.0212523; mute-priority0.0210336.

Subsequent canonical silent render (48 kHz stereo313846 frames):
`8b3062b6a6e1a1208130c716588ce362f4edb586560f0910fa3623d1ce7be7c9`.
Independent native gain ratio is0.5011872473430448; pan-right yields silent left,
muted solo yields peak0 (`service.json` includes every source and audio hash).

Device parameter native outputs:
before `9d21e408b45315196978aa1b3543ac2ab5047d06149ccf09efa89bb034beb5c1`,
after `da406553c789f0d9b3b74cef153d1caf47afde0e0033cc71f83d75592ccd0bcf`.
Decoded RMS ratio0.4966537687 demonstrates actual signal change with canonical
parameter readback. The rubric requires a real change, not exact mathematical
halving within an evaluator-invented0.1% tolerance.

## Original Glass Current integrity

All mutation probes used disposable projects. Glass testing used the copied
project read-only. The original repository's own CLI was finally invoked with
its required `--timeout 30`; successful result is
`original-glass-inspect-verified.json`, not the preserved earlier parse error.
`original-integrity.json` verifies the actual original delivery WAV as well.

- Original and copied source revision:
  `rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5`.
- Original source SHA-256:
  `7d833b0cea0802f5a2d045171f4ddddc69066fc0aab41541b9f09faf4cf291f2`.
- Exact exported bytes, fetched and played, and actual original delivery file:
  `ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b`.

Earlier original-CLI snapshot attempts omitted `--timeout` and were parse errors.
Each earlier round has an append-only AUDIT-CORRECTION explaining this and
conservatively removing its unverified S3B credit. Corrected earlier totals are
6,72,80; prior reports/errors remain. This final round verifies the original
correctly. No criterion was changed to account for the correction.

## Fixtures, commands and retained evidence

Independent generated3-track fixtures contain editable MIDI,sample,protectedMIDI,
2 buses,tempo/meter changes and real Faust rendering. Main/gesture initial source:
`rev-397d00ff05607ec2c45a1953e61ceb9cfc7dd87c2fa102630aa46abf76c60316`.
Two-bar source:
`rev-2ffa8d37bf8b7ec1f5c11adcb1d64e4ec37ef398d5af67ecb981fe0c62b31cb2`.
Sustained signal source:
`rev-d9e2f9c800da7434461af6642801a547887a4908201214b7063a4580758f3c0d`.
Roots: `.local/evaluation/final-03-{main,two-bars,mix,gestures}/project`;
service probe root `.local/evaluation/final-03-service/project`.
API ports8790–8793; copied Glass read-only 8794.

From repository root, Python is the original repo's `.venv/Scripts/python.exe`:

```
python -m tools.evaluation.fixture <new-folder> [--two-bars | --sustained]
python -m app.studio_api --root <fixture>/project --port <port>
node tools/evaluation/<probe>.cjs http://127.0.0.1:<port> evidence/evaluation/round-03/<group>
python -m tools.evaluation.service_probe <new-folder> evidence/evaluation/round-03/service.json
python -m pytest -q -rs
python -m tools.evaluation.capture_tree evidence/evaluation/round-03/tree-after.json
```

Probes: interaction,editing,workflow,mix,audition,glass,identity,ergonomics.
`pytest.txt`: **62 passed,1 skipped,18 existing WAV metadata warnings,87.44 s**.
The optional Dexed test is skipped without `ADAW_TEST_APPROVED_DEXED=1`; no pass
is claimed for it. Browser exception arrays are empty.

Preserved raw assertions include one waveform check before settled waveform
initialization (focused read-only confirmation subsequently passes), and the1 px
hidden-input geometry diagnostic (its clipped implementation recorded explicitly).
Neither raw failure was erased. The octave/help discrepancy remains a genuine
lost check. Screenshots in main,editing,workflow,glass,identity and ergonomics
directories preserve the assessed presentation.

