# ADR-0001 — Selectively adopt DawDreamer 0.9.0 for G0

Date: 2026-11-13. Status: **PARTIAL ADOPT**, bounded to tested Windows fixtures;
no G1 implementation authorization or owner musical acceptance is implied.

## Decision and evidence

Use native Windows CPython 3.12.14 x64 and the original proposed DawDreamer 0.9.0.
Keep native imports and plugin execution in a killable worker, behind a narrow adapter.
ADAW owns validation, immutable inputs, dependency resolution, source commits and QA.
Exact results and earlier failures are retained in `evidence/gates/g0/run-*.json`.
No v0.3 implementation was reused.

The initial PurestGain test **failed opaque state restoration**. The pinned engine's
[loadStateInformation implementation](https://github.com/DBraun/DawDreamer/blob/v0.9.0/Source/PluginProcessor.cpp#L421)
constructs an editor after loading state. The observed error is `Plugin has no available editor UI.`
ADAW does not swallow it or substitute a parameter patch while claiming state PASS.
This contradicts any blanket assumption that state loading is independent of editor
availability. Preserve PurestGain as limited, with the original failure trace.

Dexed 1.1.0 VST3 renders MIDI and restores all exposed values. Earlier runs had
sample-identical fresh-worker PCM; final run-004 differs by up to 1.2207e-5 while RMS
is effectively unchanged. Classify it D3, not guaranteed bit-exact replay.
The second effect is Airwindows Consolidated
build 316a048. Its default wet processing produced different fresh/warm PCM in run-003;
record this as D3, not deterministic replay. To isolate persistent gain-control behavior,
the separately named final test sets Dry/Wet=0 and varies the active Output Level.
The 1e-6 absolute PCM tolerance is unchanged; the configuration change is explicit.
This does not certify the wet algorithm, all Consolidated processors, or any user library.

## Implementation choices

1. G0 uses `adaw.g0.graph@1`, a distinct diagnostic graph. The full arrangement draft
   schema is not implemented. Stable node IDs, inputs, channels, parameters and render
   frames are explicit. Topological order and reachability are validated.
2. Snapshot bytes use sorted-key compact UTF-8 JSON, finite numbers only, on pinned
   Python 3.12.14. This is not RFC8785/JCS or cross-language canonicalization. No pickle.
   Tone PCM and Faust source have their own hashes.
3. The local service library is the sole persistence owner. Content files publish before
   SQLite transactionally commits source + report + head + last playable pointer.
   Failed candidates never update head. Orphan content may remain after a failed commit.
   Stale-head updates fail; general operation merging is future work.
4. Plugin identity combines an explicit file/bundle manifest and SHA-256. Bindings hash
   interface metadata, excluding mutable current-value/display text, and are rechecked
   after state restore. Normalized controls do not imply physical units. External DLL
   dependencies and licensing/activation are not exhaustively pinned.
5. Workers have direct-process kill/timeout and retained logs. Native code retains
   same-user host rights. No AppContainer, Job Object process-tree guarantee, memory/CPU
   cap or OS-enforced network/filesystem isolation is claimed. Only trusted fixtures load.
6. Stereo float WAV at 48 kHz/256-frame blocks is an explicit temporary G0 fixture,
   avoiding an untested 24-bit/dither policy. It is not an owner delivery default.
7. Actual-byte decoding uses libsndfile and SciPy. Pinned pyloudnorm 0.1.1 implements
   BS.1770-4 loudness. Three upstream vectors exercise 1 kHz level, absolute gate and
   relative gate to ±0.1 LU. This is a calibrated subset, not full meter conformance.
   True-peak metering is NOT_EVALUATED.
8. Temporary engineering assertions are disclosed in `fixtures/README.md` and code;
   they are not mastering standards. No owner-selected loudness target exists.

## Next-gate recommendation

Stop at this G0 handoff. RWT-01..12 identities and obligations remain unchanged;
only labeled RWT-05/06/11/12 subsets run. Fixture success does not pass a full permanent
test or musical approval.

For an authorized G1 slice, retain these boundaries and add the arrangement schema,
typed staged operations, idempotent commands, revision-bound plugin state associations,
job reconciliation and asset grants. Produce a real 60–90-second cue with role/section
progression, profile-specific conversion, calibrated true peak and owner listening.
Fix the brief/profile before musical evaluation. Test tails and latency before claiming
region-preview or stem alignment. Defer UI until composition-to-master works.

