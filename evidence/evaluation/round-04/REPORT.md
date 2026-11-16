# Independent everyday-interaction evaluation — round 04

**82/100 from completed evidence. This presentation candidate has NOT passed the frozen acceptance gate.**
The owner requested a quick conclusion; this report preserves untested checks as
zero rather than transferring the previous candidate's 98/100. That earlier
functional checkpoint remains recorded in round03. This is not a commercial-DAW
feature percentage, listening approval, or owner acceptance.

## Candidate and evidence integrity

- Assessed production commit: `5df27f67a1d97c5ba29781c8014a45be90db2a53`.
- Before/after assessed file tree SHA-256, identical:
  `582aaa046f803fb94b46fc24832b1ed065f80adeffa0e3e01db6a7bf0a08d981`.
  Parent subsequently committed documentation; assessed production files did not change.
- Frozen rubric SHA-256 remains
  `904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253`.
- Evaluator changed only evaluator harnesses/evidence and disposable projects.
  No production or rubric modifications. Windows, Python3.12.14, Node24.22.1,
  installed Edge157.0.4341.60; 1440x900,1280x720 and390x844.
- Fresh independent MIDI/sample/protected-MIDI, two-bus fixtures under
  `.local/evaluation/final-04-{main,two-bars,mix,gestures}/project`, ports8810–8813.
  Full Glass copy inspected on8814; original project was not mutated by evaluator.

## All 50 fixed checks

PASS earns2; FAIL and UNTESTED earn0. A failed harness assertion is not automatically
a confirmed product defect: the distinction is recorded below. Evidence paths are
relative to this directory.

| ID | A | B | Points | Evidence and limitation |
|---|---|---|---:|---|
| E1 | PASS | PASS | 4 | `main/interaction.json`: direct fader persists/reloads; `workflow/workflow.json`: pending proposal stays separately reviewable and unapplied. |
| E2 | PASS | PASS | 4 | Pointer note creation, snap, stable IDs/source; selected deletion, empty selection and refreshed state. |
| E3 | PASS | PASS | 4 | `editing/editing.json`: pointer move/resize, pitch/time keys, velocity77/native render; multiselect duplicate preserves originals/relative attributes with distinct IDs. |
| E4 | PASS | PASS | 4 | Three keyboard undo/redo operations; visible controls, validated disjoint-edit preservation and conflict regression coverage. |
| E5 | PASS | PASS | 4 | Visible group move/duplicate/reload, split/trim canonical bounds and native playback; sample limitation explicit. |
| F1 | PASS | PASS | 4 | `mix/mix.json`: actual digital signal gain117.5ms,solo160.6ms,mute138.8ms; native muted-solo output exactly zero and monitor/master distinction. |
| F2 | PASS | PASS | 4 | `audition/audition.json`: real 2-bar note audition6233.37/5233.43/5531.71ms; prior playback/progress, exact revision and superseded response safety. |
| F3 | FAIL | PASS | 2 | `glass-current/glass.json`: waveform pointer target is intercepted by arrangement ruler. Actual current-take tempo/meter/sample-boundary/fullsong3/4 tests pass. |
| F4 | PASS | PASS | 4 | Current fullsong loop wraps/stops/restarts without source mutation; identified A/B position/current-stale behavior passes. |
| F5 | PASS | PASS | 4 | Explicit loading/save/preview/failure and retry; delayed repeated mute and rapid note gestures converge. `identity/identity.json` shows Loading while metadata held. |
| M1 | PASS | PASS | 4 | Full channel controls persist; actual multi-solo, mute priority, clearing solo, bus/master behavior. |
| M2 | PASS | PASS | 4 | Independent actual stereo samples, silent/louder/clipping/pause checks. Peak7.51186895 produces CLIP; silence and pause clear. |
| M3 | UNTESTED | UNTESTED | 0 | Devices view exposes instrument and music-bus/Master route. Old harness incorrectly requires absent empty-chain text, then stops before parameter gesture/native comparison. Does not establish a product failure or complete either check. |
| M4 | PASS | PASS | 4 | Real pointer/keyboard fader, numeric/reset/pan center; -72dB source beyond normal travel and separate listening volume. |
| M5 | PASS | PASS | 4 | Shared selection/section/zoom/timeline position; `ergonomics/ergonomics.json` verifies actual overflowing mixer scroll retention during unrelated channel edit. |
| U1 | FAIL | UNTESTED | 0 | Divider pointer drag did not increase its value in workflow test; test stopped before completing both-size persistence/reset. Direction/layout adaptation remains a possible harness issue, not yet isolated. |
| U2 | PASS | FAIL | 2 | Desktop track/section/selection/editor readability and 24px control audit pass, but the actual waveform overlap violates the unobscured-control requirement. |
| U3 | PASS | UNTESTED | 2 | Labelled editing controls exercised. Shortcut probe stopped at an overlapped note from reused edited fixture before octave action; no claim that the prior octave-clamp defect persists or is fixed. |
| U4 | PASS | PASS | 4 | Named surfaces, keyboard/dialog/Escape and visible focus; field typing isolation and protected controls verified. |
| U5 | PASS | PASS | 4 | Complete162.307688s song playable/searchable/zoomable without browser exceptions;390px document has no horizontal overflow, playback/review reachable and assets local. |
| S1 | UNTESTED | PASS | 2 | Validation/atomic service behavior observed, but fresh CLI/UI full-source agreement was not rerun. Protected UI/direct API mixed batch rejects without source change. |
| S2 | PASS | PASS | 4 | Same-field stale conflict visible; unrelated edits survive editing/undo. Stable IDs/history/refresh and command idempotence verified. |
| S3 | PASS | UNTESTED | 2 | Correct metadata before source swap, Loading/empty title while held, edits make old rendition stale. Exact export hash/playback pass; original project source was not independently reread this round, so full B remains untested. |
| S4 | PASS | PASS | 4 | Failed native request retains playable last good and permits retry; invalid/missing dependency atomic rejection and superseded response safety. |
| S5 | PASS | PASS | 4 | Independent complete pytest62pass/1optional skip; frontend-absent/security tests included. Pinned local audio/ui0.5.1 and WaveSurfer8.1.0, notices and unchanged rubric hash inspected. |

Totals: **E20 + F18 + M16 + U12 + S16 =82/100**.
Mandatory **S1A and S3B remain UNTESTED**. All other mandatory A/B checks pass.
There is no observed source loss, silent overwrite, fake meter, protected-track
bypass, wrong audio labelled current, or application exception in completed probes.
The current candidate nevertheless cannot be described as meeting the frozen gate.

## Preserved failures and setup state

The first `glass/glass.json` run opened a legitimately stale rendition: source
was `rev-b9147b180d54c340ee1a0e040e7faa6c0486b230360015d417de691198cae63e`
while audio was the previous d5125 revision. Its Edits to hear label and disabled
tempo-dependent navigation were truthful, not the old wrong-current identity bug.
Parent identified an intervening edit adding explicit snare mute:false/solo:false;
the evaluator did not revert it. After parent finished rendering the same current
source, `glass-current/glass.json` tested
`rendition-007bf8c32b2e40ec82070d0f493b493b`. Tempo/meter/loop now pass. The actual
waveform pointer interception remains and is scored as failure.

The identity test held historical rendition metadata. During the hold, the previous
verified current audio URL stayed in place, the identity title was empty, and both
context and playback status read Loading mix. The correct historical identity was
shown after resolution. This passes the previously mandatory identity regression.

The shortcut probe's pointer timeout is caused by another overlapping test note
covering eval-0. It did not reach Shift+Up; it supplies no evidence about60→72.
The device harness similarly stopped on an obsolete text expectation before it
could exercise the new knob numeric control. These are recorded as untested.

## Audio, regression and commands

Actual native muted-solo SHA-256:
`9504e30b935eb3b2a61068a2ee8012dbe19cb07be771b769c27f3c9c279df791` (peak0).
Exact Glass exported bytes still hash
`ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b` and play.
Signal measurement is not a claim of human listening or musical approval.

`pytest.txt`:62passed,1skipped,18warnings in125.48s. Skip is the existing opt-in
approved native fixture at tests/test_studio_api.py:224. Existing frontend-absent
tests and origin/token/static-route checks are included in that independent run.

Commands used the original environment Python from the studio fork working
directory: `python -m pytest -q -rs`; own
`node tools/evaluation/v4-{interaction,editing,mix,audition,workflow,ergonomics,glass,identity}-probe.cjs <URL> <output>`;
and `python -m tools.evaluation.capture_tree <output>` before/after. Probe logs,
JSON and failure/desktop/narrow screenshots are preserved in corresponding folders.

To complete acceptance, correct or isolate divider/waveform issues and finish the
unverified device, shortcut, CLI agreement and original-source checks on one fixed
candidate. No additional tests were started after the parent's request to conclude.
