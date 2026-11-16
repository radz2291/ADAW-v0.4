# Independent evaluation — round 02

**82/100 verified points. NOT ACCEPTED: mandatory S3A fails.** Other unfinished
checks receive zero. A transient identity defect was deliberately reproduced:
historical audio is loaded while the previous current revision remains in the
tooltip and the transport still says “Latest mix.” The ordinary settled state
is correct; that does not excuse the incorrect loading state.

Candidate: `434af87b98e331a67ff94be080a15e3e622573cd`.
Exact before/after assessed tree hash, unchanged:
`120d5635c61d83a111e936e3524e225408bff6d19ebeff62192ff60cba830442`.
Frozen rubric:
`904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253`.
No production changes during assessment. All 50 fixed subchecks are scored below.

| ID | A | B | Points | Observed evidence or missing check |
|---|---|---|---:|---|
| E1 | PASS | PASS | 4 | Direct gain reload; pending agent proposal stays separate. |
| E2 | PASS | PASS | 4 | Pointer creation/snap/stableID; Delete and empty selection/reload. |
| E3 | PASS | PASS | 4 | Pointer move+resize, pitch/timing keyboard, velocity77, native render; Shift-click/CtrlD preserves originals/relative attributes/uniqueIDs. |
| E4 | PASS | UNTESTED | 2 | Three CtrlZ/redo pass. External-disjoint sequence interrupted by overly strict helper expecting Saved despite an older unresolved fault. |
| E5 | PASS | PASS | 4 | Group move/duplicate/reload, split/trim/native render, explicit unsupported sample front trim/split. |
| F1 | PASS | PASS | 4 | Real signal gain54ms,solo80.9ms,mute143.6ms. Canonical native muted-solo render exactlyzero; preview/render labels distinct outside identity defect. |
| F2 | PASS | PASS | 4 | 2-bar note auditions1630.77/1580.32/1578.70ms, all played. Previous playback/progress/exact revision; real held-old/newer response ordering correct. |
| F3 | PASS | PASS | 4 | All transport gestures/text isolation; exact sample timing including Glass3/4 and rounded bar positions. |
| F4 | PASS | FAIL | 2 | Loop wrap/stop/restart pass. A/B loading retains incorrect current identity until metadata arrives. |
| F5 | FAIL | PASS | 2 | Loading state can show old Latest mix. Rapid doubleMute with300ms delay now returns original state; rapidnotes and retry pass. |
| M1 | PASS | PASS | 4 | All controls/reload; two solos doubles signal, mute wins, clear solos, bus/master functional. |
| M2 | PASS | PASS | 4 | Actual stereo signal/zero/clipping/pause readings and mode labels; independent tap peak7.5119 with CLIP indicator, silence0, pause clears. |
| M3 | PASS | PASS | 4 | Routing/read-only order displayed; parameter0.15 persists and native decoded RMS changes0.0205116→0.0101872. Earlier exact-halving assertion was stricter than frozen rubric and is not a product failure. |
| M4 | PASS | PASS | 4 | Pointer/keyboard/numeric/reset/pan center; -72dB expands range; listening volume separate. |
| M5 | PASS | PASS | 4 | Selection across views, timeline zoom/scroll and section retained. Mixer zero-scroll observation here will be supplemented with actual overflow in final round. |
| U1 | PASS | UNTESTED | 2 | Supplement confirms real drag at both sizes280→340 and170→230; collapse/alignment observed. Full second-size reload/reset loop interrupted by offscreen pointer geometry in original helper. |
| U2 | PASS | PASS | 4 | Readability both sizes; section hit areas fixed. Raw remaining1px input is hidden toolkit input, not the essential visible pointer target. |
| U3 | PASS | UNTESTED | 2 | Tools exposed; revised shortcut text correct for inspected/observed bindings; full empty-state/clipboard sequence pending. |
| U4 | FAIL | PASS | 2 | Help dialog lacks accessible name (named dialog query returns0); field isolation/protected lock/Escape/focus restoration pass. |
| U5 | PASS | PASS | 4 | Full Glass/search/zoom/play/no exceptions;390px no document overflow and local assets. |
| S1 | PASS | PASS | 4 | Validated source agreement and protected direct API mixed-batch atomic rejection. |
| S2 | UNTESTED | PASS | 2 | Same-field stale conflict passes; disjoint sequence interrupted by helper. Reload history/IDs and exact-command idempotence pass. |
| S3 | FAIL | PASS | 2 | Held historical metadata demonstrates wrong Latest mix and old revision tooltip during loading. Exact Glass export unchanged and played. |
| S4 | PASS | PASS | 4 | Failed native request preserves previous playable audio and retries; actual invalid/missing dependency rejects, superseded response not promoted. |
| S5 | UNTESTED | PASS | 2 | Full independent backend suite deferred to corrected candidate; local pins/notices and current origin/token403/static404/hash checks pass. |

Category totals: E18,F16,M20,U14,S14 = **82**.

## Important evidence

`identity/identity.json` and `identity/loading-identity.png`: new audio URL is
historical `rendition-559e5ebec8da4cc2b926d49e2a9b9ab0` at source `rev-a6f7…`,
while tooltip says current `rev-d512…` and transport says Latest mix.
The API response was held after actual retrieval; source/audio bytes were real.

`mix/mix.json`: sustained3-track/two-bus fixture, independently sampled actual
WebAudio output before an evaluator-only silent hardware sink (avoids loud output
during the clipping test). No fake product meter values or listening claims.
Combined RMS0.0425223,one-solo0.0211251,-6dB0.0106154; two-solo0.0423247,
mute-priority0.0210176. Native silent render SHA-256
`0ca85071e2ebd69b2ae901481b32d3562d7009d4cabdada2db0ef8534e8aa306`.

`main/interaction.json`, `editing/editing.json`, `workflow/workflow.json`,
`audition/audition.json`, `glass/glass.json`, `layout-supplement.json`,
`security.json` contain independent raw observations/screenshots. No JS exceptions.
Fixtures are `.local/evaluation/final-02-{main,two-bars,mix,gestures}/project`,
ports8780–8783. Glass copy read-only on8784. Initial main source
`rev-397d00ff05607ec2c45a1953e61ceb9cfc7dd87c2fa102630aa46abf76c60316`;
sustained source `rev-d9e2f9c800da7434461af6642801a547887a4908201214b7063a4580758f3c0d`.

Native device level evidence, real decoded48kHz stereo313846frame outputs:
before SHA-256 `57873787d0552a3474b4b2594639ecb171c8f31d96cd1c9715d0a94f6979c3d4`,
RMS0.020511597504992297; after
`3b6f3a78d422994ad767ac1e9252e9e1204471749043dde1e6e204c51f1716e4`,
RMS0.01018716220368228. The rubric requires a real audible-signal change, not the
test's additional0.1% exact-halving tolerance; this meets the unchanged criterion.

Glass exported WAV hash remains
`ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b`;
canonical revision remains `rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5`.

## Next candidate

Clear stale identity immediately on load; show Loading and do not call historical
audio Latest mix while metadata is pending. Name the Help dialog. Complete the
remaining tests and rerun all mandatory checks on one fixed candidate. Preserve
this report and raw failed assertions, including harness corrections; do not
change the frozen criteria. Owner listening acceptance remains separate.
