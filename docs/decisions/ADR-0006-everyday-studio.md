# ADR-0006 — Direct musical editing and explicit audition

16 November 2026. Owner asked for a frozen everyday interaction standard,
independent evaluation and fixes until at least 90/100, then clarified that Studio
must be a quiet musician's workspace with minimal repeated components.

This supersedes ADR-0005's temporary manual Stage/Apply workflow. Manual gestures
call ProjectService.edit(), which validates and applies only that command using
the existing proposal and atomic revision contracts. Agent proposals remain
separately reviewable. Failed or stale edits stay visible; no force overwrite is
introduced. Undo/redo commits validated inverses and preserves disjoint changes.
Stable event IDs support creation, deletion, duplication, movement, MIDI split and
trim. Sample leading trim/split remains explicitly unsupported without a source
sample-offset model; end trim is supported.

One primary Audition action renders the current source in the native worker. The
previous audio remains usable during preparation. A request sequence and revision
check prevent superseded completions from replacing the selected newer audio.
Exact identity is available in optional details/tooltips; the main surface uses
musical actions and current/stale feedback. Mixer precision entry and faders share
one channel strip; the duplicate inspector mixer and competing primary render
button were removed.

The native graph now records post-track-insert, pre-level monitor stems. Their
manifest and bytes are verified through read-only rendition routes. WebAudio
applies current track gain, linear balance pan, mute/solo, bus weights and master
gain for immediate monitoring. Multiple solos play together; mute wins. This
preview bypasses bus/master inserts and the final fade, and is visibly labelled
Live mix preview. Audition remains the canonical finished master. Note/device
changes invalidate compatible monitor stems. Actual stereo output analyser
samples drive meters; no track meter values are fabricated.

Faust instruments expose catalogs compiled with their actual polyphonic voices,
release, sample rate and block settings. The derived service cache includes the
module, native engine binary and adapter hashes. Catalog work occurs before
source write transactions; a context race fails safely. Reserved monophonic MIDI
controls are not offered as editable instrument parameters. Native render tests
verify that accepted controls change actual audio.

Monitor profile v1 uses a 2048-sample analyser, 3ms gain smoothing and 15ms stem
start scheduling. These are tested implementation settings, not universal mixing
rules. Their measured interaction latency is recorded in the evaluation evidence.

Layout persistence is browser-only view state. The existing pinned audio/UI and
WaveSurfer adapters remain the UI foundation. Pane sizing, snap choices and
control travel are view policies, never audio constraints. Runtime stays local;
origin/token/static-file protections remain enforced.

The acceptance rubric was committed before implementation at b8edc8c and is
immutable without an explicit owner request. Its SHA-256 is
904217d07d250e4fa1677b522372313fbf449c9a15177f022a229457f0d78253.
A permanent test checks the exact bytes. Independent evidence is retained by
round under evidence/evaluation; earlier failures are not overwritten.

Scope remains local arrangement/mixing/audition, not full DAW feature parity,
recording, live synthesis, hardened plugin sandboxing or owner musical approval.
The original Glass Current project/export remain separate and unchanged.
