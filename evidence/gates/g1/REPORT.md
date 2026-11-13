# G1 technical production evidence

Date: 14 November 2026. **Technical production path delivered; owner listening
review NOT_EVALUATED.** Full product, artistic and professional acceptance are
not claimed. The owner selected modern electronic 808 trap with changing
structure/swing/moods, for a listening/demo WAV. No reference was supplied.

## Exact delivery

- Title: **Night Circuit**. 75.000 seconds, 44 bars at 144 BPM plus tail.
- Six named sections, ten tracks, 1,085 structured events. Four musical candidates
  in completed run-002, one fresh-worker replay, one deliberately excessive-gain
  preview rejected at export. No human technical intervention was needed; owner
  provided genre/use choices. This is not a recorded listening verdict.
- File: `.local/delivery/g1-v2/Night-Circuit-G1-review.wav`.
- SHA-256: `39cd4a229d4367466be3cb44b718e67d91e44a7865eb0efe2ab42fb9c80e1991`.
- Source revision: `rev-e35b37a8ce95e04dd955aa3fd300ffeddf518cab30201817ab81dbbf106b51e4`.
- Rendition: `rendition-b46fc75786a04352929b4367b2c277b7`.
- Profile hash: `e44665742626becd8d0db3380927988977920ebb677d86f45dbe1ec6d211f5c1`.

| Exported-byte measurement | Result |
|---|---:|
| Frames / rate / channels | 3,600,000 / 48,000 Hz / stereo |
| Encoding | PCM24, seeded TPDF dither |
| Integrated loudness | -16.499568 LUFS |
| Sample peak | -1.529184 dBFS |
| 8x FIR estimated true peak | -1.499403 dBFS |
| Crest factor | 14.921866 dB |
| Mono-fold RMS ratio | 0.992495 |
| Last 10 ms peak | 0.0000001192 |
| Explicit profile rules | 8 PASS |

The profile is **temporary engineering guidance** (-18..-11 LUFS, <=-1 dBFS
sample peak, estimated true peak plus 0.25 dB margin <=-1 dBFS). The owner chose
listening/demo WAV but did not choose these numbers. True peak is calibrated to
five analytic phase-shifted sines, not full EBU/ITU conformance. Pyloudnorm's G0
three-vector loudness calibration passes again. libsndfile and SciPy agree exactly
on exported integer PCM decoding. No loudness number proves artistic quality.

## Production and native evidence

[Run-002 report](run-002/report.json) and [trace](run-002/trace.json) link exact
CLI invocations, source, graph, parameters, measured files, environment and jobs.
`baseline.json` retains the initial CLI result. Each `*-project-render.json`
retains one source/graph/render identity, including the rejected preview.

Actual processing: original seeded drum samples → sample-event tracks → track
inserts/gains → Faust drum body → Consolidated VST output-gain stage → buses;
Faust 808/pad and Dexed MIDI lead/echo → music bus; master highpass, measured gain
and explicit fade. The two fixture VST binary fingerprints and opaque state
hashes are in each relevant rendition. Consolidated uses Dry/Wet=0 and active
Output Level .47, not a claim about its wet algorithm. No proprietary audio or
plugin binary is committed. No old ADAW source was reused.

[Kick/bass evidence](run-002/kick-bass-comparison.json): move only drop 808 events
by 144 ticks. Onset overlap ratio falls 0.7276→0.1515. The already-separated
fracture section has no event edits or added sidechain (ratio 0.2993→0.3170;
state/tail/phase effects prevent treating unchanged source as identical audio).
Two actual A/B context pairs are matched to -23 LUFS in the delivery directory.
Perceptual improvement remains for a human to judge. Protected snare and lead
event lists remain intact; their mix levels can change independently.

Fresh final-source replay is **D3**: max sample difference 0.00272715, RMS
difference 0.00017914. [Replay report](run-002/replay.json) retains both identities.
Do not overwrite the review WAV with a new render under its old hash/approval.

Run-001 failed after adding the VST effect because native catalog field
`defaultValue` for an unused slot contained NaN, breaking JSON serialization.
Its [failure result](run-001/08-project-render.json) and worker logs are retained.
The fix explicitly reports unavailable native metadata and validates finite
active controls/audio; it does not coerce invalid values to zero. Bass source
was also changed to two release-capable voices; run-002 has no voice-stealing
warnings. Historical failures are not rewritten as passes.

## Tests and scope

- [Unit/contract tests](unit-tests.log): **29 passed**.
- [G1 independent verification](verification.json): **6 full rendered artifacts**,
  source/graph/PCM/state/stem/dependency identities, exact export, matched pairs,
  protected events and explicit failures verified.
- [G0 regression](g0-regression.json): **15 checks passed, 16 real renders**;
  [independent identities](g0-verification.json) verified. Original G0 evidence
  remains untouched. Regression graphs live in `graphs/g0-regression/`.
- Failure cases: stale command, invalid Faust import, occupied export path,
  deliberately wrong frame contract and a real excessive-gain proposal preview.
  Clipped PCM24 is blocked; failed operations do not change source/last playable.
- [Source snapshot](source-snapshot.json) binds the final implementation and
  retained worker logs, and verifies all 20 original specification package files.
  Historical audio identity is bound by its own source/graph, not by rewriting
  older records to claim a later implementation was used.

| Permanent ID | G1 disposition; full obligation retained |
|---|---|
| RWT-01 | PASS technical complete-cue path; artistic NOT_EVALUATED |
| RWT-02 | PASS bounded overlap/context/matched-pair subset; full judgment/listening NOT_EVALUATED |
| RWT-03 | PASS one-profile/export/failure subset; two owner-selected profiles NOT_EVALUATED |
| RWT-04 | NOT_EVALUATED full disjoint merge/undo; stale rejection tested, not a substitute |
| RWT-05 | PASS bounded real Faust/validated-import/denial regression; broader tools NOT_EVALUATED |
| RWT-06 | PASS bounded worker/render/import/export failure subsets; interrupted host recovery NOT_EVALUATED |
| RWT-07 | NOT_EVALUATED independent song/archive portability |
| RWT-08 | NOT_EVALUATED controlled professional listening |
| RWT-09 | NOT_EVALUATED actual owner-approval invalidation ledger; candidates never auto-approved |
| RWT-10 | PASS protected-event rejection subset; full forged-tool scenario NOT_EVALUATED |
| RWT-11 | PASS fixture instrument/effect in real graph plus G0 parameter/state regression; owner plugin collection UNTESTED |
| RWT-12 | G0 bounded reuse/mismatch regression passes; independent-song pipeline/sidechain NOT_EVALUATED |

## Reproduction and environment

Use the [README G1 commands](../../../README.md#reproduce-g1) with fresh
directories, or inspect the recorded trace for this exact run. Windows 11 x64
build 26100, CPython 3.12.14, DawDreamer 0.9.0, NumPy 2.2.6, SciPy 1.15.3,
soundfile 0.13.1, pyloudnorm 0.1.1. Existing version/hash lock is unchanged.
Native module and plugin hashes are recorded per rendition. No Node dependency.

Native workers have the same Windows user's filesystem/network rights. Tested
direct-process crash/timeout containment is not a hardened sandbox, process-tree
quota, general plugin compatibility or host-crash reconciliation. Generic
latency compensation and sidechains are unproven. G2/G3/G4 remain future gates.

Next bounded action is owner audition of the exact review WAV, followed by a
revision based on that feedback. No owner approval or listening impression has
been invented.
