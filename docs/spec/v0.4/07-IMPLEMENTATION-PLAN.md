# ADAW — Greenfield Implementation Plan v0.4

**Status:** Proposed execution sequence for a brand-new repository  
**Guiding constraint:** Don't repeat v0.3's demo-first trap. Build audible, source-verified, agent-operated production capability before an elaborate UI.

## 1. New repository and no-migration doctrine

Create a **new Git repository** with this package under `docs/spec/v0.4/` or equivalent. The owner reports v0.3 Phase 1 had a satisfactory demo, but no previous code, screenshots, issues or test artifacts are provided here for independent verification. **Treat all older code as untrusted reference**, not a migration base. Capture useful lessons in `docs/decisions/` if material; do not import dependencies/components without an explicit, tested decision.

Start with a minimal monorepo layout, adapting after G0 evidence:

```text
adaw/
  AGENTS.md
  docs/spec/v0.4/...
  docs/decisions/ADR-*.md
  app/service/                 # project source, revision and API/CLI
  app/worker/                  # DawDreamer, plugin registry probe, render
  app/quality/                 # analyzers and profile evaluation
  app/studio/                  # deferred lightweight UI
  contracts/                   # schemas, API types, event types
  fixtures/                    # generated synthetic/test-licensed inputs
  tests/unit/
  tests/integration/
  tests/permanent/
  tools/                       # reproducible doctor/benchmark scripts
  evidence/gates/              # reports; large media via artifact refs if needed
```

Keep output fixtures and generated artifacts in an appropriate untracked content storage area; no proprietary VST binaries or paid sample packs in Git. Repository must have deterministic setup commands, pinned dependencies and Windows instructions.

## 2. Gates and non-negotiable artifacts

| Gate | Outcome | Required evidence | Prohibition |
|---|---|---|---|
| **G0 — Engine and plugin proof** | Native Windows DawDreamer/early Faust/VST worker works | Real audible example(s), plugin parameter/control/state proof, crash containment, timings, engine ADR | No GUI mock as substitute |
| **G1 — Codex composition-to-master** | Full original 60–90s cue produced with real audio, usable CLI and QA | Actual master, source/graph, iteration trace, quality report, listening-review status | Eight-bar demo is not product acceptance |
| **G2 — Shared interactive studio** | UI timeline/mixer/inspector/proposals work with same canonical source | UI/CLI parity, conflicts, direct plugin control, A/B evidence | No detached editor state |
| **G3 — Durable local first release** | Project restore, independent songs, portable archive, Windows lifecycle | Package/replay, second song, backup/recovery, export verification | No missing binary silently substituted |
| **G4 — Repeatable professional assessment** | Independent-sonic review protocol and repeated song tests | Pre-registered owner thresholds, level-matched listening, multi-song comparison | No self-certified 'industry standard' |
| **G5 — Extended production** | Further audio/recording/instrument/real-time capabilities | New acceptance matrix; unchanged permanent tests | No silent scope erosion |

Not all gates must be fully implemented immediately. They define durable direction and prevent architecture from optimizing for a small demo.

## 3. G0: first execution slice — mandatory

### Work item G0-01 — Environment and dependency decision

- Initialize new repo, Python 3.12 x64 Windows environment, pinned DawDreamer wheel/version; capture `doctor` environment report.
- Record plugin folders the owner explicitly authorizes; do not scan uncontrolled machine directories.
- Verify upstream features against version **actually installed**, release notes and Windows behavior.
- Record GPL/third-party license references for private-use context and limitations.
- Define stable audio adapter interface and minimal typed graphs before specific implementation coupling.
- Exit: environment boots on target; dependency versions+hashes logged; `doctor` and unit test command run repeatably.

### Work item G0-02 — Real Faust and signal graph

- Generate/test a source tone or sample, custom Faust saturation (drive + output trim) and bus chain in DawDreamer.
- Render wet/bypass/changed drive; measure harmonic change and level change, verify timing, PCM format and output.
- Inject syntactically invalid Faust; confirm worker error and unchanged last playable audio and source head.
- Exit: exact source/hash, executable commands, generated WAVs, metrics, and failure evidence.

### Work item G0-03 — VST agency proof

- Probe one owner-approved local installed instrument and effect **if available**. Otherwise use documented fixture plugins but label user collection untested.
- Enumerate parameter catalog, read and modify normalized value, demonstrate audible effect, test automation, save state, close worker, restore state in new worker, verify output and parameters.
- Test plugin GUI is not required for normal headless render, identify plugin crashes/hangs or limitation.
- Sidechain is **capability-specific stretch proof** in G0: test known compatible plugin; do not fake if unavailable.
- Exit: machine-readable compatibility report and real rendered audio/provenance per plugin.

### Work item G0-04 — Worker and measurement proof

- Separate project service and render native process. Simulate crash/timeout and prove service survives; no staged output promoted on failure.
- Implement one independent peak/sample/decode check and a BS.1770-compatible meter with calibration fixture; record analyzer version and reference methodology.
- Measure cold and warm render times for eight bars and short multi-track fixture; mark targets measured vs proposed.
- Exit: worker/QA evidence, limitations and security residual risks recorded.

### Work item G0-05 — Architecture recommendation

- Produce `G0-DECISION.md` with **ADOPT**, **PARTIAL ADOPT** or **BLOCKED**, limitations, accepted adapter shape, version locks and next-step plan.
- Do not promote G0 to PASS if VST state or command operation are only mocked. If user plugin unavailable, approve generic engine G0 but leave real user-VST acceptance PENDING.

## 4. G1: first integrated complete production path

**Fixture:** An original 60–90s instrumental cue with at least drums/percussion, bass, harmony/texture, and a lead or meaningful transitions. Owner selects musical direction, reference(s), target technical delivery profile and tool permissions; use an explicitly labeled temporary test brief only while owner choices are pending.

Minimum implementation:

1. Local project create/open, structured arrangement, content-addressed WAV and Faust source imports; VST and/or Faust instrument use where proven.
2. MIDI/performance scheduling, multitrack routing, ordered inserts and mastering chain via DawDreamer.
3. Codex-operable CLI: inspect, stage/propose, apply, render, analyze, export, history; durable job and artifact IDs.
4. Production cycle: agent interprets brief, builds source and processing, renders actual audio, uses feedback/QA, performs at least one justified revision.
5. Quality runner checks actual file and attaches technical and engineering results. No fake/perceptual 'mastering score'.
6. Owner can audition the complete candidate via local player or generated audio file; comparison label and file identity accurate.
7. All relevant artifacts (WAV, source manifest, plugin/source hashes, quality report, real trace) retained and versioned.

Exit: a *complete musical candidate*, not a demo screenshot or a canned premaster. Permanent `RWT-01`, `RWT-03`, and initial `RWT-11/12` relevant parts executed; artistic listening remains separately accepted/rejected/not-evaluated.

## 5. G2: shared working studio, only after G1 audible value

- Simple arrangement view with sections and MIDI/sample events, track/bus mixer, source inspector, parameter controls and minimal waveform render playback; not full Ableton clone.
- Plugin registry browser with status and normalized/verified controls; clear manual plugin UI option if supported, no hidden state divergence.
- CLI and UI issue same typed operations; proposals, compare and undo; conflicts visible.
- Persistent song-state controls distinguish monitor volume and zoom/selection.
- Keyboard accessibility and clear edit/preview/current/approved labels.
- Exit: real UI edit of VST control followed by agent inspection; no source divergence; stale conflict tests PASS.

## 6. G3 and G4: durability and professional benchmarking

G3: independent songs; Windows local launcher; store backup/migrations; archive import/export; plugin discovery on new host; precise missing VST diagnostics; optional aligned stems with tested tap semantics; durable monitoring; permission audit.

G4: owner-defined listening dimensions and thresholds, matched-loudness comparison to comparable professional results, repeated different-song tests, adjudication of automation success vs engineering interventions. Don't invent threshold percentages; collect before evaluation.

## 7. Initial delivery protocol for every coding cycle

Each agent cycle returns:

1. Goal and bounded scope with test IDs.
2. Files changed, commit SHA, new interfaces and dependencies.
3. Runnable exact Windows commands and environment versions.
4. Raw proof: generated WAV/source or artifact refs, test logs, measured numbers and method.
5. PASS/FAIL/BLOCKED/NOT_EVALUATED per acceptance test; discrepancies and known risks.
6. No undocumented hardcoded product assumptions; changes to contracts require ADR.
7. Next suggested bounded slice, no claiming completion ahead of evidence.

## 8. Explicit 'do not do' list for fresh builder

Do not ask the owner to commission the old repo for migration; do not copy the v0.3 demo wholesale; do not build only static UI; do not write own full VST host; do not promise any arbitrary VST works; do not include copyrighted commercial samples/plugin binaries; do not pretend personal use resolves all plugin licensing; do not invent user listening results or a universal mastering standard; do not run untrusted downloaded native DLLs in privileged service; do not replace quality/permanent tests with self-report.
