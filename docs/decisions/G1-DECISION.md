# G1 — Technical production path delivered; listening review pending

14 November 2026. The owner authorized G1 and selected modern electronic 808
trap with changing structure/swing/moods, for a listening/demo WAV.

The original **Night Circuit** candidate is 75 seconds: 44 bars at 144 BPM plus
an explicit tail, six sections, ten tracks and 1,085 events. Original synthesized
percussion, Faust 808 and harmonic texture, and Dexed lead are composed in
structured source. This is not a repeated eight-bar export or a pre-mastered
input. All source/mix/master changes run through the project service.

Candidate: `.local/delivery/g1-v2/Night-Circuit-G1-review.wav`.
SHA-256: `39cd4a229d4367466be3cb44b718e67d91e44a7865eb0efe2ab42fb9c80e1991`.
Revision: `rev-e35b37a8ce95e04dd955aa3fd300ffeddf518cab30201817ab81dbbf106b51e4`.
Rendition: `rendition-b46fc75786a04352929b4367b2c277b7`.

Actual exported bytes: 3,600,000 frames, stereo 48 kHz PCM24, -16.499568 LUFS,
-1.529184 dBFS sample peak, -1.499403 dBFS **estimated** true peak. Eight explicit
profile checks pass. The numeric profile is temporary engineering guidance;
the owner has not chosen a loudness number or approved the sound.

## Evidence and decisions

The complete [run report](../../evidence/gates/g1/run-002/report.json),
[CLI trace](../../evidence/gates/g1/run-002/trace.json),
[independent verification](../../evidence/gates/g1/verification.json), and
[gate report](../../evidence/gates/g1/REPORT.md) retain source, processing graphs,
hashes, environment, timings, measurement rules, errors and limitations.

Three applied proposals follow the initial source:

1. Delay 808 onsets by 144 ticks (62.5 ms) in the overlapping drops. The measured
   30–140 Hz bass/kick RMS ratio over the first 70 ms of 26 kick onsets fell from
   0.7276 to 0.1515. The already-separated section's events remain unchanged;
   its ratio was 0.2993/0.3170. No automatic sidechain was inserted. These are
   overlap diagnostics, not proof of perceived clarity. Two context pairs are
   rendered and matched to -23 LUFS for listening.
2. Raise the low-level lead and hat/clap stems for review, and add the proven
   VST output-gain stage after Faust drum processing. This balance is provisional.
3. Use actual meter results to set transparent master gain within the profile's
   headroom constraint. The -16 LUFS working aim was constrained by peak headroom.

Invalid Faust, stale proposals, an occupied export path, and an excessive-gain
proposal preview all fail as expected. Source head and last playable remain
intact; clipped PCM24 is not published. Earlier failed run-001 remains available.
Replay of the final source is D3: max sample delta 0.00272715, RMS delta 0.00017914.
Do not describe it as exact or portable replay.

## Gate disposition

G1's implemented composition-to-master **technical path is delivered**. Owner
listening review is `NOT_EVALUATED`; professional quality is not self-certified.
The exact permanent-test subset dispositions are in the gate report. Their full
identities and future obligations remain unchanged. This is not full v0.4 release
acceptance or G2/G3 completion.

Next bounded step: listen to this exact WAV and the matched comparisons, then
record the owner's musical feedback against this rendition and implement the
requested musical revision. UI, general conflict merging and portability remain
later gates. No listening verdict has been fabricated.
