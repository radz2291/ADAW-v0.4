# ADR-0005 — Library-backed desktop Studio

16 November 2026. Owner requested an isolated project fork, adoption of the
recommended UI libraries, durable agent instructions, and a desktop DAW experience.
This supersedes only ADR-0003's dependency-free frontend choice.

Use audio/ui custom elements 0.5.1 (core 0.29.1, MIT) for timeline, piano roll and
faders; WaveSurfer 8.1.0 (BSD-3-Clause) for a waveform sharing the existing audio
element. Source: https://github.com/ouestlabs/audio-ui and
https://github.com/katspaugh/wavesurfer.js. Pin esbuild 0.28.2 and Playwright 1.65.1
for build and verification. Node 24.22.1 and npm 11.6.2 were used on Windows.

Keep framework-free application code. Compile the browser dependencies into a
same-origin local ES module. Commit its distributable and license notices; runtime
does not contact a CDN. Dependencies are integrity-locked in package-lock.json.
No production graph, database schema or native renderer changes are required.

Timeline units are canonical ticks. Piano-roll units are quarter notes relative to
a selected section, explicitly converted through source PPQ; seek/playhead timing
uses the complete tempo map. Meter-aware bar positions are independent of tempo
segments. The library does not own project tempo, source or an audio engine.

Fader gestures and note moves/resizes/velocity changes stage typed proposals.
Apply and render remain explicit, and old audio remains identified/playable.
Read-only revisions and protected notes remain locked. Unsupported note additions
and deletion are rejected visibly instead of existing only in browser state.

WaveSurfer receives measured peaks from the existing decoder and uses the same
media element. Full decoding still consumes memory proportional to file length;
server-side peak generation is future work, not claimed here. Loops are audition
controls using browser playback timing, not sample-accurate engine loops.

The audio components inject CSS. Permit inline **styles only** in CSP while keeping
script-src self, no external connections, no objects/frames, exact loopback origin,
session tokens, and the static asset allowlist. This is a deliberate narrowly
scoped frontend policy change, not permission for inline scripts or remote code.

Fader travel (-60 to +12 dB, 0.1 dB increments) is a versioned UI navigation choice,
not a service/DSP gain constraint. Existing out-of-range values expand the travel;
numeric inspector fields retain exact source editing. Layout dimensions, colors,
1/16 note snap and collapsed review default are view policy v1.

The fork uses a Git branch plus a separate worktree, retaining history and origin.
Glass Current is copied through the verified service archive/restore path. Its
original project remains separate. No native plugins or generated song audio enter
Git. This delivery improves offline Studio interaction; it does not claim Ableton
feature parity, real-time recording or subjective professional music approval.
