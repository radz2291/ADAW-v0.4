# Independent evaluation — round 01

**74/100 verified points. NOT ACCEPTED.** Evaluator is independent of production
implementation. Every A/B is worth2; FAIL and UNTESTED receive0. Remaining
untested cases are not implied passes. Main blocking evidence gap is F1A's full
gain/mute/solo latency matrix (mute alone measured131.8ms). Fixes are also needed
for rapid toggle intent, Faust parameter rendering, short section hit targets,
stale Refresh feedback, and the shortcut reference.

Candidate commit: `9ee3f75`. Before AND after exact assessed tree SHA-256:
`aa3ce59ab4835135367fc7de24175ac4dffcd1825265fb3dbecbb00b6cf022fa`.
See complete per-file manifests `tree-before.json`, `tree-after.json`.
Frozen rubric SHA-256, reverified:
`904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253`.
No production edits occurred during this round. Evidence remains append-only.

## Score by fixed check

| ID | A | B | Points | Evidence and limits |
|---|---|---|---:|---|
| E1 | PASS | PASS | 4 | Main direct gain survives reload; workflow pending agent proposal stays unapplied and separately reviewable. |
| E2 | PASS | PASS | 4 | Pointer add with1/16snap/stableID; Delete,Escape,emptyDelete and reload agree with canonical source. |
| E3 | UNTESTED | PASS | 2 | Fresh gesture run observes move,resize,pitch/timing; velocity/readback/render sequence did not complete because inspector selection needed reselecting. Shift-click multi-select+CtrlD preserves originals,relative attributes and distinctIDs. |
| E4 | PASS | PASS | 4 | Three real CtrlZ/redo operations; visible buttons; unrelated external edit preserved. Independent service conflicting undo rejects without overwriting. |
| E5 | PASS | PASS | 4 | Visible group move/duplicate survives reload; split/trim source bounds,real native rendition,explicit sample split/front-trim limitation. |
| F1 | UNTESTED | PASS | 2 | Actual destination tap measured mute131.8ms; gain/solo latency still to measure. Live preview/render labels distinct; service/native decoded gain,pan,solo/mute semantics agree. |
| F2 | PASS | PASS | 4 | Actual2-bar note-edit auditions1531.94,1633.07,1612.14ms; real playback. Held old native response cannot replace newer; old playback/progress/exact revision checked. |
| F3 | PASS | PASS | 4 | Space,Home,ruler,waveform,section,text-field isolation. Settled exact sample boundary checks include Glass3/4 passage and bar/beat positions. |
| F4 | PASS | PASS | 4 | Intro loop wraps,stop/restart,visible range,no source mutation; identified A/B preserves2s position. Earlier run includes stale rendition switch. |
| F5 | FAIL | FAIL | 0 | Refresh stays labelled “Refreshing project…” after completion. Two rapid Mute clicks with300ms API latency persist one toggle instead of two; note nudges do converge. |
| M1 | UNTESTED | UNTESTED | 0 | Gain,pan,mute,solo individually exercised, but full refresh/multiple-solo/clear-all signal matrix not yet completed. |
| M2 | UNTESTED | UNTESTED | 0 | Actual sample path and pause-to-zero meter observed; complete stereo clipping and silent/louder fixture comparison pending. |
| M3 | PASS | FAIL | 2 | Instrument→ordered effects→bus→Master and read-only/bypass limitations displayed. Saving level0.15 creates `/dawdreamer/level`; native audition fails “Faust binding missing.” |
| M4 | UNTESTED | PASS | 2 | Keyboard,numeric,reset,pan center exercised; pointer fader adjustment still to verify. -72dB expands range without clipping, listening level does not mutate source. |
| M5 | PASS | PASS | 4 | Track selection across browser/arrangement/mixer/editor; zoom4× and timeline scroll160 retained; bridge editor section retained. Fixture mixer had no nonzero horizontal overflow, so that dimension observed at0. |
| U1 | PASS | PASS | 4 | Real divider drag,collapse both panels,alignment,reload persistence,Reset layout at1440×900 and1280×720; source unchanged. |
| U2 | PASS | FAIL | 2 | Both desktop screenshot/readability checks; section group buttons height19px fail24px requirement. Ignore hidden library input in raw geometry diagnostic. |
| U3 | PASS | FAIL | 2 | All required tools exposed through labelled controls. Help's blanket Shift+arrows resize statement is inaccurate: ShiftUp/Down changes octave. |
| U4 | UNTESTED | PASS | 2 | Help focus outline/Escape works but complete logical Tab traversal not yet exercised. Field shortcuts preserve source/transport; protected notes announce lock and reject editing. |
| U5 | PASS | PASS | 4 | Complete162.307688s Glass playable,real808 search/zoom,no exceptions;390px width390,play/review reachable,all requests local. |
| S1 | PASS | PASS | 4 | Browser mutations use validated service; Python/service and UI source agree for create/edit/delete/mix. Protected UI plus direct mixed API batch reject with unchanged head. |
| S2 | PASS | PASS | 4 | Visible stale conflict preserves newer source; disjoint edit survives undo/redo. Reload retains IDs/history; repeated exact command idempotent. |
| S3 | PASS | PASS | 4 | Old audio remains identified/stale after edits,successful previews match exactrevision,superseded response cannot relabel. Exact Glass export hashed and played; original source revision unchanged. |
| S4 | PASS | PASS | 4 | Real render network failure preserves playable previous audio,actionable error,successful retry. Actual invalid operation/missing dependency reject atomically; superseded real native render response not promoted. |
| S5 | PASS | PASS | 4 | Independent full suite60passed1optionalDexedskip; frontend-absent contract included. Pinned/local libraries and notices; currentAPI403origin/token,404static; frozenhash exact. |

Category totals: E18, F14, M8, U14, S20 = **74**.

## Reproduction and artifacts

Windows host, installed headless Edge, existing Python3.12 environment and Node24.
Own fixture generator: `tools/evaluation/fixture.py`. Main and fresh gesture
fixtures have3tracks (MIDI,sample,protectedMIDI),2buses,tempo+meter changes,real
Faust sine synth and independently synthesized sample. Main roots:
`.local/evaluation/final-01-main/project` (8775),
`.local/evaluation/final-01-two-bars/project` (8776),
`.local/evaluation/final-01-gestures/project` (8778).
Fullsong copied project read-only at8777; original sibling project not edited.
Initial full fixture source:
`rev-397d00ff05607ec2c45a1953e61ceb9cfc7dd87c2fa102630aa46abf76c60316`.
Two-bar source:
`rev-2ffa8d37bf8b7ec1f5c11adcb1d64e4ec37ef398d5af67ecb981fe0c62b31cb2`.

Independent scripts in `tools/evaluation/`:
`interaction-probe.cjs` → `main/interaction.json`;
`audition-probe.cjs` → `audition/audition.json`;
`workflow-probe.cjs` → `workflow-rerun/workflow.json`;
`editing-probe.cjs` → `gestures-fresh/editing.json`;
`glass-probe.cjs` → `glass-settled/glass.json`;
`python -m tools.evaluation.service_probe` → `service.json`.
Each browser command receives the fixture origin and output directory.
`python -m pytest -q -rs` → `pytest.txt`:60passed,1skipped,16WAVmetadata warnings,
65.76s. The skip requires opt-in `ADAW_TEST_APPROVED_DEXED=1` and is not a pass.
`security.json` records this candidate's actual HTTP status codes.

Native signal evidence: -6dB ratio0.5011872473430448; panright left-channel zero;
muted solo peak0. Native source revisions and audio hashes are in `service.json`.
Browser signal taps the real WebAudio node feeding destination, independently of
the product meter. No subjective listening claim is made.

Glass exact export SHA-256 remains
`ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b`;
source remains
`rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5`.
Read-only test did observe additional same-source renditions from another builder
process; it never mutated the song or original export. No browser exceptions.

## Preserved attempts and next round

Earlier test failures remain. The first workflow helper wrongly expected Refresh
notice to hide (the permanent loading notice is also a real feedback issue).
First pointer test targeted a note below viewport; subsequent tests scrolled it
into view. Ctrl-click was corrected to supported Shift-click multiselection.
The first sample-boundary probe used a0.01step range input and too-short settling;
the final probe seeks actual audio time and waits500ms. Full exact timing matrix
then passes. These harness corrections do not change the rubric or production.

Next candidate must fix recorded production failures and independently rerun all
mandatory checks together, complete remaining signal/focus/precision cases, and
reach>=90 without changing this rubric. Owner listening acceptance remains separate.
