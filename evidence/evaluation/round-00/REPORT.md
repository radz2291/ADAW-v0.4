# Independent baseline — round 00

Date: 16 November 2026, approximately 03:54–03:57 UTC. Evaluator: independent
`ux_evaluator` agent, with no production edits. Frozen rubric SHA-256:
`904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253`.
Assessed frontend: commit `b8edc8c306270789eba26329fdd12b4d974ae838` before
builder replacement of bundle. Baseline service processes were already running;
implementation began concurrently after browser collection. The separate backend
regression run therefore describes an intermediate development tree, not a
reproducible baseline commit; it earns no baseline S5A points.

## Result

**8/100 verified points. NOT ACCEPTED.** This is the frozen rubric's conservative
evidence score, not a claim that 92% of existing functionality is broken. Many
checks are UNTESTED and receive zero exactly as required. Baseline blocker failures
are already decisive: manual gestures require Stage/Apply, note creation/deletion
is unavailable, and no track mute/solo monitor or automatic note audition exists.

Independent fixture: `.local/evaluation/round-00-fixture/project`, revision
`rev-397d00ff05607ec2c45a1953e61ceb9cfc7dd87c2fa102630aa46abf76c60316`, rendition
`rendition-e19713328f894284a2106f11d065a20b`. Three tracks (editable Faust MIDI,
sample, protected Faust MIDI), two buses, 120→104 BPM, 4/4→3/4. Synth and sample
were independently authored; real Faust rendered successfully. Playwright used
installed headless Edge, Windows AMD64, Python 3.12.14, node 24; exact browser
version and snapshots in `browser.json`. No browser exceptions or external asset
requests occurred. Screenshots cover 1440×900, 1280×720, and 390×844.

## Fixed scoring

Each A or B PASS earns 2. FAIL and UNTESTED earn 0. No partial credit.

| ID | A | B | Points | Evidence / missing observation |
|---|---|---|---:|---|
| E1 | FAIL | UNTESTED | 0 | Real fader ArrowDown only stages; canonical revision unchanged. Pending-agent isolation not exercised. |
| E2 | FAIL | FAIL | 0 | Implementation rejects note-count additions; actual Delete displays “Adding or deleting notes is not available yet,” and source remains unchanged. |
| E3 | UNTESTED | FAIL | 0 | Complete manipulation/render bounds not retested; duplicates rejected by existing-note-only contract. |
| E4 | FAIL | FAIL | 0 | No redo command/control or three-step undo/redo workflow. |
| E5 | FAIL | FAIL | 0 | Arrangement blocks navigate sections; no move/duplicate/split/trim source operations through UI. |
| F1 | FAIL | FAIL | 0 | No track mute/solo or live source-gain monitoring. Playback is rendered WAV. |
| F2 | FAIL | UNTESTED | 0 | Explicit Stage→Apply→Render required. No automatic audition race test. |
| F3 | UNTESTED | UNTESTED | 0 | Space/Home/input isolation and fixture 104 BPM 3/4, bar3.1 at 4.307692s passed. Ruler/waveform and full-song rounding matrix not completed. |
| F4 | UNTESTED | UNTESTED | 0 | Complete loop/stop/restart and multi-rendition position matrix not independently exercised. |
| F5 | UNTESTED | UNTESTED | 0 | Baseline errors are visible; full loading/fault/rapid edit coverage not run. |
| M1 | FAIL | FAIL | 0 | Source mixer lacks pan/mute/solo controls, thus no multi-solo behavior. |
| M2 | FAIL | FAIL | 0 | No live stereo meters or silent/loud meter readings. |
| M3 | UNTESTED | UNTESTED | 0 | Instrument chain/parameter rendered-audio comparison not run. |
| M4 | FAIL | UNTESTED | 0 | No pan center/reset. Out-of-travel/reset/numeric matrix not run. |
| M5 | UNTESTED | UNTESTED | 0 | Partial track switching exercised, not every surface and scroll preservation. |
| U1 | FAIL | FAIL | 0 | No resizable divider, collapsible inspector, persisted layout or Reset layout. |
| U2 | UNTESTED | UNTESTED | 0 | Screenshots collected at both sizes; full truncation and hit-area audit not completed. |
| U3 | FAIL | FAIL | 0 | Missing add/delete/duplicate/split/trim/redo/snap/audition tools; only Space/Home hint rather than full workflow guidance. |
| U4 | UNTESTED | UNTESTED | 0 | Input Space does not start transport; protected roll disabled. Full focus/Escape/typing/protection mutation matrix not complete. |
| U5 | PASS | PASS | 4 | Complete Glass Current duration162.307688s plays; actual808 search,4× zoom; no browser errors.390px document width390, playback reachable, no CDN requests. |
| S1 | FAIL | UNTESTED | 0 | UI cannot create/delete, so required create/edit/delete/mix source agreement fails. Protected editor visibly disabled; direct API batch not independently exercised. |
| S2 | UNTESTED | FAIL | 0 | Stale/disjoint matrix not run. Redo unavailable. |
| S3 | UNTESTED | PASS | 2 | Full identity invalidation matrix pending. Exact exported Glass WAV fetched, hashed and played; unchanged canonical revision below. |
| S4 | UNTESTED | UNTESTED | 0 | Failure/interruption/supersession/missing dependency matrix pending. |
| S5 | UNTESTED | PASS | 2 | Concurrent-tree suite44passed1skipped supporting only. Pinned versions/notices inspected, local-only requests, origin/token403, nonallowlisted static404, frozen hash exact. |

## Safety and reproducibility

Glass read-only before/after source revision:
`rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5`.
Original sibling project inspected separately in `original-glass-inspect.json`.
No mutating calls targeted Glass. Exact export bytes SHA-256:
`ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b`.
`safety.json` records actual export playback and security status codes.
No subjective listening or owner musical acceptance is claimed.

Commands from repository root:

```
<original-repo>/.venv/Scripts/python.exe -m tools.evaluation.fixture .local/evaluation/round-00-fixture
<original-repo>/.venv/Scripts/python.exe -m app.studio_api --root .local/evaluation/round-00-fixture/project --port 8771
node tools/evaluation/baseline.cjs
node tools/evaluation/baseline-safety.cjs
<original-repo>/.venv/Scripts/python.exe -m pytest -q
```

Fixture construction and native render completed in approximately4.1s (not a
warm audition measurement). Browser harness5.24s; exact-export safety3.63s.
Concurrent-tree suite44passed,1skipped,9 existing WAV metadata warnings,48.08s.

Priority: direct canonical manual edits plus safe history; note add/delete and
automatic audition; actual monitor gain/pan/mute/solo and meter measurements;
then clip tools/layout/discoverability. Re-evaluate all mandatory checks on one
fixed candidate tree. Preserve this report and original failed observations.
