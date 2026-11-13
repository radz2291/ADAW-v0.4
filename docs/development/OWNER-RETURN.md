# ADAW G2–G5 owner handoff

The G1 development milestone is owner-accepted. Its original Night Circuit
master and arrangement preview retain their recorded feedback and identities.
Use the `adaw/g2-g5` branch. Its latest checkpoint and the tested code commit
are recorded in [checkpoint evidence](../../evidence/gates/g2/checkpoint.json).

## Open Studio

Run from the repository in Windows PowerShell after the pinned setup in README.

```powershell
.\.venv\Scripts\python.exe -m app.studio_api --root .local/g1-night-circuit-v2 --port 8765
```

Open [Night Circuit in Studio](http://127.0.0.1:8765/). Use port 8766 and
`--root .local/g5-glass-current` to open Glass Current separately. To run the
same public service with Studio absent, add `--api-only`. The CLI remains
available through `python -m app`. [Architecture boundaries](../architecture/BOUNDARIES.md).

## Gate status

| Gate | Verified in this checkpoint | Remaining acceptance |
|---|---|---|
| G2 | Browser timeline, event and mixer controls, real plugin edits, proposals and playback, independent API client and CLI parity, selective undo, native Faust automation interleave, exact export review binding | Actual owner-approved RWT-09 scenario remains open |
| G3 | Verified archive inventory and bytes, independent-song restore and edit, Faust/VST pipeline reuse on a second song, missing-plugin block and explicit rebind, interrupted-service lease reconciliation, Windows local launch, four validated track taps | Full permission audit and installed Windows application lifecycle remain open |
| G4 | Measured gain-only matched comparison, two explicit engineering profiles and out-of-spec detection, separate musical projects | AWAITING_OWNER_REVIEW for controlled professional comparison. Reference, owner criteria and repeated professional assessment remain open |
| G5 | Offline tempo and meter map, a real second cue, linear post-fader sends and a native Faust main/key routing test | VST sidechain, transport-synced plugins, recording and responsive live playback remain open |

The permanent RWT-01 through RWT-12 definitions remain in the original package.
Tests exercised real Faust drive and hold automation interleaved with an event move, same-field Dexed
conflict and owner-decision binding in disposable fixtures. Approved Dexed
Output 0.8 to 0.4 changed browser-rendered RMS by a factor of 0.5. Native
Consolidated catalog controls are exposed on Night Circuit. PurestGain opaque
state remains limited as recorded in G0. Plugin support covers the tested fixtures.

Studio uses the shared service and one project root per process. Existing
module assets can be re-imported to discover Faust control metadata. Browser
edits are staged first and apply by explicit action. Browser render requests
remain open during offline processing. Review entries bind verified PCM export
bytes and the exact rendition.

## Listen and inspect

* Night Circuit original and Arrangement 02 have matched copies in
  `.local/delivery/g4-night-circuit-review/`. Both measured -23 LUFS, selected
  as a comparison monitoring level. [Comparison report](../../evidence/gates/g4/night-circuit-matched-comparison.json).
* Glass Current is a 65.3-second cue in `.local/delivery/g5-glass-current/` with
  a 120-to-104 BPM change and a 4/4-to-3/4 ending. Its master passed the
  engineering profile at -17.27 LUFS. [Render and archive evidence](../../evidence/gates/g5/glass-current.json).
* Glass Current restored into a fresh project and reproduced identical decoded
  samples on this machine. A subsequent independent pad edit changed the copy
  and preserved the source project. [Restore evidence](../../evidence/gates/g3/independent-project.json).
* Four stereo float track taps share the render frame grid and precede bus and
  master processing. [Stem manifest](../../evidence/gates/g3/glass-current-stems.json).
* Glass Current's independent copy reused Night Circuit's Faust and Consolidated
  drum pipeline on the music bus with a different gain parameter. A restored
  copy blocked render until the approved fingerprint was resolved. [Pipeline evidence](../../evidence/gates/g3/glass-current-vst-pipeline.json).
* Both Glass Current engineering profiles passed. A deliberately tighter peak
  rule failed on the measured bytes. [Profile comparison](../../evidence/gates/g4/glass-current-profiles.json).

## Reproduce

```powershell
$env:ADAW_TEST_APPROVED_DEXED = '1'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tools.verify_g1 evidence/gates/g1/run-002
.\.venv\Scripts\python.exe -m app.portability backup --root .local/g5-glass-current --archive .local/glass-copy.adaw.zip
.\.venv\Scripts\python.exe -m app.portability restore --archive .local/glass-copy.adaw.zip --root .local/glass-copy
.\.venv\Scripts\python.exe -m app.portability reconcile --root .local/glass-copy
```

Use fresh paths for archive restore. For a trusted plugin-based archive,
provide exact owner-approved binaries with repeated `--allow-plugin` arguments.
Alternatively, use the existing CLI plugin authorization after restore. Archive
hashes verify integrity. Import only project packages you trust. Historical
stage and export paths retain their original provenance. Restored Studio audio
uses the content store.

Use the [execution ledger](EXECUTION.md), gate evidence, and permanent spec to
resume. The next engineering work is a compatible VST sidechain fixture and
live transport tests.
Professional listening evidence requires owner-supplied criteria.
