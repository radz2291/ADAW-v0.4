# ADAW repository instructions

Read and follow the complete [repository constitution](docs/spec/v0.4/AGENTS.md)
before coding. That file is the single authoritative copy of the project rules;
this root entry point includes it by reference without changing their scope.

All numbered documents in its required reading order are in `docs/spec/v0.4/`.
The initial G0 assignment is [CODEX-START-HERE](docs/spec/v0.4/CODEX-START-HERE.md).
Read the current [G0 decision](docs/decisions/G0-DECISION.md) and
[engine ADR](docs/decisions/ADR-0001-engine-adoption.md) for the implementation handoff.
The owner explicitly extended the assignment to G1 on 13 November 2026.
Read [G1 decision](docs/decisions/G1-DECISION.md) and
[G1 contract ADR](docs/decisions/ADR-0002-g1-production-contract.md) for the current
implementation. G1 technical delivery does not imply owner musical approval.

The owner accepted G1 as a development milestone and authorized work through G5.
Use the integration branch and [execution ledger](docs/development/EXECUTION.md)
for current work. Studio is a replaceable client of the published local service.
It must not own persisted project decisions, native audio or production workflows.
Keep the frontend-absent integration test as a permanent regression.
Read the [boundary map](docs/architecture/BOUNDARIES.md) before moving modules.

Repository organization:

- `docs/spec/v0.4/`: original specification, schemas, examples, references and manifest.
  Keep this package intact; do not create editable copies at the repository root.
- `docs/decisions/`: implementation decisions and gate dispositions.
- `app/`, `tests/`, `tools/`, `fixtures/`: implementation and reproducible tooling.
- `evidence/gates/<gate>/`: reports, logs and run-specific source graphs.
  Preserve historical failures; graphs belong under `graphs/<run-id>/`.
- `.local/`: ignored runtime projects, downloads, plugin binaries and generated audio.
- `requirements.lock`: sole installation lock with exact tested wheel hashes.

Historical evidence describes its recorded run. Do not overwrite its hashes or
results merely to make it describe the current repository layout.

## Studio UI development — owner direction, 16 November 2026

All future Studio UI work must use the established audio library stack first:

- `@audio-ui/elements` for DAW controls, timelines, piano rolls, faders, knobs and
  meters. Reuse the adapters and visual tokens in `apps/studio/`; do not build a
  competing control framework or adopt an upstream demo's project/audio state.
- `wavesurfer.js` for rendered-audio waveform navigation, bound to the existing
  media element and rendition identity. Supply measured peaks when available.
- Waveform Playlist is a candidate for future multitrack audio editing, not an
  installed dependency. Introduce it only with a tested ADAW service adapter and
  a documented need. Do not install every library discussed as an alternative.
- Keep exact npm versions and the integrity-bearing `apps/studio/package-lock.json`.
  Run `npm ci`, `npm run build`, and the real browser verification after UI changes.
  Commit the local distributable so ordinary Studio launch works without npm/CDNs.
- Preserve canonical ticks, tempo/meter maps, stable event IDs, service validation,
  proposal/apply/conflict/undo, protected tracks and frontend-absent tests.
- Musical edits must reach the service. Monitor volume, navigation, section loops
  and zoom are view state. Label stale audio; do not imply live synthesis, live
  fader monitoring or meters that the actual audio path does not provide.
- Target a compact desktop DAW workspace with keyboard support, clear selection,
  accessible controls, scrollable panes, and usable narrow layouts. Verify actual
  playback and edits in Edge against a disposable project; inspect screenshots.

Read [the UI adoption decision](docs/decisions/ADR-0005-desktop-studio.md) and
[Studio development instructions](apps/studio/README.md) before UI work.
The isolated development fork is branch `adaw/desktop-studio`, based on `3897f30`;
it does not replace or merge the prior integration branch automatically.

## Frozen everyday interaction acceptance

The owner froze [EVERYDAY-INTERACTION-v1](docs/evaluation/EVERYDAY-INTERACTION-v1.md)
before implementation. Never change its tasks, scoring, scope, mandatory checks,
thresholds, or SHA-256 lock unless the owner explicitly asks. Improvements must be
independently evaluated against those same criteria; keep every failed round.
The target is at least 90/100 with all mandatory checks, not DAW feature parity.
The main workspace serves musicians: keep it quiet, familiar and meaningful.
Show musical actions and clear feedback; put revisions, hashes and diagnostics
in optional history/details rather than requiring administrative knowledge.
Avoid repeated components and competing controls for the same action. Reuse the
established control adapters; keep one primary home for mixing and audition.
Precision editing and optional evidence should complement the main workflow.

Read [the direct editing decision](docs/decisions/ADR-0006-everyday-studio.md) for
current gesture, monitoring and native parameter semantics; it supersedes the
temporary Stage/Apply interaction in ADR-0005.
