# Independent everyday-interaction evaluation — round 05

**90/100. All mandatory checks PASS.** This is a bounded regression assessment of
the presentation candidate after the single production CSS fix described below.
Unchanged checks explicitly retain round04 evidence; this is not a claim that all
50 checks were freshly executed again. The frozen rubric, weights and threshold
have not changed. The result measures the specified workflows, not90% of a
commercial DAW's features or owner approval of its sound or visual finish.

## Candidate and bounded evidence

- Candidate: `b3d96e3686efc2a304ec6120873f18f4b63d7c66`.
- Assessed tree SHA-256:
  `8ac746d5625d28162f6bc8a26e34c653c98666d82ed402f9f5f3751b09efedd7`.
- Frozen rubric SHA-256:
  `904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253`.
- The only production delta from the round04 assessed code is
  `apps/studio/layout.css`: transport z-index40 becomes50, placing its open
  waveform/compare surface above the arrangement ruler. README and builder test
  changes are non-production. Evaluator inspected the diff and did not modify it.
- Round04's identical before/after manifest pins all unchanged service, editor,
  audio, validation and library code. Its independently executed native/browser
  and62pass/1optional-skip backend results remain the evidence for those checks.
- Fresh read-only CLI/UI agreement and original integrity are in `integrity.json`.
  Fresh actual pointer tests at1440x900 and1280x720 are in `waveform.json`, with
  screenshots. The waveform now seeks from1s to113.396785s at both sizes; section
  navigation into3/4 and text-entry transport isolation pass, source unchanged.
- This bounded pass follows the parent's instruction to conclude promptly and
  retest the affected layer without repeating unaffected native audio tests.

## All 50 fixed checks

PASS earns2. FAIL/UNTESTED earn0. References to round04 mean preserved independent
evidence for unchanged code, with the relevant limitations retained.

| ID | A | B | Points | Evidence |
|---|---|---|---:|---|
| E1 | PASS | PASS | 4 | Round04 direct commit/reload and separate pending agent proposal. |
| E2 | PASS | PASS | 4 | Round04 pointer add, snap/stable source ID; delete/empty/reload. |
| E3 | PASS | PASS | 4 | Round04 pointer/keyboard/velocity/native bounds and multi-note duplicate. |
| E4 | PASS | PASS | 4 | Round04 three undo/redo, disjoint preservation and conflict checks. |
| E5 | PASS | PASS | 4 | Round04 group move/duplicate, split/trim/native bounds and sample limitation. |
| F1 | PASS | PASS | 4 | Round04 independent actual signal117.5/160.6/138.8ms; canonical muted output zero. |
| F2 | PASS | PASS | 4 | Round04 real2-bar audition6233.37/5233.43/5531.71ms; prior playback/progress/supersession. |
| F3 | PASS | PASS | 4 | Fresh waveform click/section/text isolation completes round04 Space/Home/ruler; round04 exact sample-boundary tempo/meter/fullsong3/4. |
| F4 | PASS | PASS | 4 | Round04 current-song loop and identified A/B position/current-stale. |
| F5 | PASS | PASS | 4 | Round04 visible pending/error/retry, held identity, rapid gain/mute/note intent. |
| M1 | PASS | PASS | 4 | Round04 labelled source-backed channels and measured multi-solo/mute/bus/master. |
| M2 | PASS | PASS | 4 | Round04 actual stereo meters, silent/loud/clipping/pause and mode labels. |
| M3 | UNTESTED | UNTESTED | 0 | New device card harness still needs ordered-effects/read-only and UI parameter/native audio comparison. Obsolete text assertion was not treated as a product defect or pass. |
| M4 | PASS | PASS | 4 | Round04 pointer/keyboard/numeric/reset/pan; -72dB inspected and listening volume separate. |
| M5 | PASS | PASS | 4 | Round04 entity/section/zoom continuity and actual overflowing mixer scroll. |
| U1 | FAIL | UNTESTED | 0 | Round04 divider drag did not increase value; direction adaptation not isolated. Both-size preference/reset test did not complete. |
| U2 | PASS | PASS | 4 | Round04 desktop readability/24px audit plus fresh fixed waveform overlap at both desktop sizes. |
| U3 | PASS | UNTESTED | 2 | Round04 labelled tools; shortcut chain stopped before octave gesture because reused fixture notes overlapped.60→72 remains unverified. |
| U4 | PASS | PASS | 4 | Round04 names/focus/Escape, field isolation and protected controls. |
| U5 | PASS | PASS | 4 | Round04 complete162.307688s song, search/zoom;390px/local assets/review. |
| S1 | PASS | PASS | 4 | Fresh CLI/API complete source+revision equality after edits, plus round04 validation/atomic/protected UI/API checks. |
| S2 | PASS | PASS | 4 | Round04 stale conflict, disjoint edits/undo, stable IDs/history/idempotence. |
| S3 | PASS | PASS | 4 | Round04 held metadata exact identity and stale indication; fresh original source/WAV integrity completes exact export/playback evidence. |
| S4 | PASS | PASS | 4 | Round04 failed-render last-good/retry, invalid/missing dependency and superseded-update safety. |
| S5 | PASS | PASS | 4 | Round04 independently executed62pass/1optional skip suite, frontend-absent and API protections; pinned local libraries/notices/rubric hash. Only production delta is inspected CSS stacking. |

Totals: **E20 + F20 + M16 + U14 + S20 =90/100**.
Mandatory E1,E2,F1,F2,S1–S5: **all A/B PASS**. Remaining10 points are explicitly
unearned: U1A/B4, M3A/B4, U3B2. These are the next verification/usability work;
they have not been erased or reweighted to obtain the threshold.

No source loss, silent overwrite, fake meter, protected-track bypass, wrong-current
audio identity or browser crash was observed in the completed evidence. Human
listening and preference about the presentation remain outside this assessment.

## Fresh integrity evidence

Original project inspected by its own CLI from its original working directory:
revision `rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5`,
source SHA-256 `7d833b0cea0802f5a2d045171f4ddddc69066fc0aab41541b9f09faf4cf291f2`.
These match the independently recorded original. Original delivered WAV remains
`ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b`, matching the
exact bytes played in round04. No original project mutation was performed.

Disposable fixture CLI and API source objects are exactly equal at revision
`rev-0a8f365d3f9cf447d0f6e7b7a8eaeed7b349c9d174196be81eb0cfc39ecaa8a9`.
The first CLI capture encountered Windows stdout encoding; setting only the child
process PYTHONIOENCODING=utf-8 allowed reliable JSON decoding. No source was changed.

Reproduction: `python -m tools.evaluation.round05_integrity`,
`node tools/evaluation/round05-waveform.cjs`, and
`python -m tools.evaluation.capture_tree evidence/evaluation/round-05/tree-after.json`.
All previous failures and raw harness reports remain preserved in round04.
