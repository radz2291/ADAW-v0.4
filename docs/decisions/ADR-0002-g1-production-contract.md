# ADR-0002 — G1 composition-to-export contract

Date: 14 November 2026. Status: implemented bounded G1 contract.
Owner extended the initial G0 assignment: “Pls continue development to G1 now”.
Musical direction: modern electronic 808 trap, different structure, swing and
moods. Intended use: listening/demo WAV. No reference or loudness number supplied.

## Source and authority

`adaw.arrangement@1` is the implemented source contract, separate from the
illustrative full-product schema in the immutable specification package.
`app/arrangement.py` validates it and compiles it to `adaw.graph@2`. The old
`adaw.g0.graph@1` remains supported. Nothing was imported from old ADAW code.

Source contains explicit fixed tempo, PPQ, sample rate, block size, tail/fade,
contiguous named sections, stable track/event IDs, MIDI performance values,
balance pans, gains, ordered Faust/VST inserts, buses, master and delivery profile.
G1 supports fixed-tempo 4/4; swing is materialized into event ticks, not a hidden
renderer setting. Tick boundaries use the existing exact rational origin and
nearest-sample ties-to-even conversion. Note ends are half-open. Sample events
have explicit durations/fades; no implicit resampling or time stretching.

`ProjectService` is the only writer of authoritative content and SQLite. It
validates WAV/Faust imports before content publication; Faust compilation is in
a worker. Opaque VST state is captured in a worker and bound to binary identity
and parameter catalog. State is opaque, not represented as editable source.
Every render resolves actual binaries again; no missing-plugin substitute exists.

New G1 tables coexist with historical G0 fixture tables. Initial source and each
applied proposal are immutable revisions. Typed operations include track/master
gain, event timing/note/velocity/duration, Faust instrument module replacement,
instrument parameter changes and ordered bus inserts. Protected event edits fail.
Proposals do not change head; preview renders do not replace last playable.
Apply revalidates dependencies and atomically checks the base revision. Command
IDs are idempotent and cannot be reused with different payloads. Stale proposals
fail explicitly: disjoint rebase/undo belongs to G2, not an implicit merge here.

Jobs retain stage/log paths and status. Renditions bind revision, exact source,
graph, profile, native environment, plugin identities, float audio and stems.
Only a successful render of the still-current head updates last playable.
Exports identify one rendition, reopen the actual PCM24 bytes, block failed
profiles, preserve occupied destinations and publish via same-directory rename.
No export or new revision is automatically labelled owner-approved. A full
approval ledger and G3 host-interruption recovery are not implemented.

## Explicit engineering choices

- `demo-wav-v1` is a **temporary engineering profile**, not an owner loudness
  preference: stereo 48 kHz PCM24, -18..-11 LUFS, sample peak <= -1 dBFS,
  estimated true peak plus 0.25 dB margin <= -1 dBFS, absolute mean DC <= 0.001.
- Production aimed at -16 LUFS, constrained by -1.5 dBFS estimated true peak.
  Measured headroom selected transparent gain; no automatic limiter or compressor.
- Export uses seeded TPDF dither and round-to-nearest 24-bit quantization. The
  seed is in the versioned profile. This is not a universal dither preference.
- True peak is an **8x FIR engineering estimate**: 128 taps per phase, Kaiser
  beta 12, zero extension, SciPy 1.15.3. Analytic phase-shifted sine calibration
  covers 997/6000/12000/18000/20000 Hz at 48 kHz, error bound 0.12 dB. The profile
  adds 0.25 dB margin. Full EBU/ITU conformance is NOT claimed. BS.1770 loudness
  retains the G0 three-vector calibration and independently decoded WAV checks.
- Mono/stereo sample import and matching rates are a tested G1 capability limit.
  Generic module import compilation uses a 48 kHz/256-frame validation fixture;
  the actual graph recompiles at the source's explicit rate/block size.
- Center balance pan is unity; there is no hidden equal-power center loss.
  Seeded drum synthesis and all musical/mix numbers live in the composition
  recipe/source, not generic app behavior. The worker takes explicit deadlines.
- Native plugins may report nonfinite **metadata**, observed in Consolidated's
  unused catalog default. Such fields become `UNAVAILABLE` with a warning path.
  Active bound control readbacks and audio still must be finite. Failed run-001
  is retained; this is not permission to treat invalid audio as successful.

## Native audio and limits

DawDreamer 0.9.0 performs the real multitrack render: original sample events,
Faust polyphonic bass/pad, Dexed MIDI, ordered Faust processors, Consolidated
VST output gain, buses and master/fade. All ten track stems come from this graph.
Consolidated's evidence-backed role uses Dry/Wet=0 and active Output Level gain;
it does not certify its wet algorithm. Two bass voices retain release tails
without the first attempt's monophonic voice stealing.

Fresh-worker replay is D3, not exact PCM or portable determinism. Native process
crash/timeout containment remains same-user execution, not a hardened sandbox.
No all-plugin, arbitrary-latency, sidechain, subjective mastering, or user-plugin
collection claim is made. No new dependency or binary is committed.

Primary implementation references: [DawDreamer 0.9.0 Faust/MIDI documentation](https://github.com/DBraun/DawDreamer/blob/v0.9.0/docs/user_guide/faust_processor.rst),
[SciPy 1.15.3 polyphase resampling](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.resample_poly.html).
Native installed API signatures and real renders verified the used features.
