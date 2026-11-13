# ADAW v0.4 — G1 composition-to-master

New implementation; no v0.3 code reused. Working JSON CLI, immutable validated
signal graphs, transactional service, killable DawDreamer workers, real Faust/VST
renders and independent decoded-file measurement. G1 now produces an original
75-second cue through editable source, proposals, revisions, real rendering and
verified PCM24 export. **Owner listening review remains pending.**

See the [G1 decision](docs/decisions/G1-DECISION.md),
[implemented contract](docs/decisions/ADR-0002-g1-production-contract.md) and
[production evidence](evidence/gates/g1/REPORT.md). The current candidate is
`.local/delivery/g1-v2/Night-Circuit-G1-review.wav`: modern electronic 808 trap,
six sections with changing swing/mood, stereo 48 kHz/24-bit, 75 seconds.

See [G0 decision](docs/decisions/G0-DECISION.md), [engine ADR](docs/decisions/ADR-0001-engine-adoption.md)
and [real run report](evidence/gates/g0/REPORT.md). The original specification is
preserved once under [docs/spec/v0.4](docs/spec/v0.4/README.md), including its draft
schemas, examples, references and original file manifest. New agents start with
[AGENTS.md](AGENTS.md) and the [G0 assignment](docs/spec/v0.4/CODEX-START-HERE.md).
The repository is [radz2291/ADAW-v0.4](https://github.com/radz2291/ADAW-v0.4).

## Setup

Tested Windows 11 x64 build 26100, CPython **3.12.14 x64**, DawDreamer **0.9.0**.
All runtime/test wheels have exact version/hash locks in `requirements.lock`.
Node is not used or required. No machine-wide Python/plugin installation occurs.

From this repository in PowerShell:

```powershell
.\tools\setup.ps1 -PythonExe 'C:\Users\RZ1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
.\.venv\Scripts\python.exe -m app --root .local/g0-project --timeout 60 doctor
.\.venv\Scripts\python.exe -m pytest -q
```

On another machine, supply native Windows CPython 3.12.14 x64 to setup.
The wheel lock is target-specific, not a Linux/macOS dependency lock.

## Reproduce G0

The owner requested online test plugins on 13 November 2026. These commands fetch
only named, hashed fixtures; they do not scan installed plugin folders. Changed
downloads fail checksum validation. Binaries, calibration WAVs, audio, state and
project databases remain in ignored `.local/` and are not committed or redistributed.

```powershell
.\.venv\Scripts\python.exe -m tools.prepare_fixtures --allow-test-downloads
.\.venv\Scripts\python.exe -m tools.probe_fixtures --root .local/g0-project --timeout 60 --approval 'Owner requested online test plugins on 2026-11-13'
.\.venv\Scripts\python.exe -m tools.run_g0 --root .local/g0-project --timeout 60 --report evidence/gates/g0/my-run.json
.\.venv\Scripts\python.exe -m tools.verify_evidence evidence/gates/g0/my-run.json
```

Use a new report name each run. The timeout is per worker, not a performance SLA.
Reports retain artifact paths, hashes, parameters, source, meters and failure logs.

## Reproduce G1

Install the locked environment and prepare the approved fixture plugins as above.
Use fresh project/input/evidence/delivery directories; do not overwrite a retained
run. The composition recipe generates original samples and editable arrangement,
imports through the service, and initializes the pinned Dexed instrument.

```powershell
.\.venv\Scripts\python.exe -m tools.compose_g1 --root .local/my-g1 --inputs .local/my-g1-inputs --timeout 90
.\.venv\Scripts\python.exe -m app --root .local/my-g1 --timeout 180 project-render | Set-Content -Encoding utf8 .local/my-g1-baseline.json
.\.venv\Scripts\python.exe -m tools.produce_g1 --root .local/my-g1 --baseline .local/my-g1-baseline.json --evidence evidence/gates/g1/my-run --delivery .local/delivery/my-g1 --timeout 180
.\.venv\Scripts\python.exe -m tools.verify_g1 evidence/gates/g1/my-run
```

The recipe is separate from generic app behavior. Event IDs, pitches, velocities,
durations, Faust source, parameters, track gains, inserts, routing, sections and
profile are stored in the source. Native replay is D3: source is retained, but a
fresh VST render can differ from the delivered file. Never replace an exact
listening-approved artifact with a rerender under the same identity.

Useful G1 commands (all use the existing JSON envelope):

```powershell
.\.venv\Scripts\python.exe -m app --root .local/g1-night-circuit-v2 --timeout 180 project-inspect
.\.venv\Scripts\python.exe -m app --root .local/g1-night-circuit-v2 --timeout 180 history
.\.venv\Scripts\python.exe -m app --root .local/g1-night-circuit-v2 --timeout 180 analyze --rendition rendition-b46fc75786a04352929b4367b2c277b7
```

Other commands: `project-create --source`, `asset-import --path --kind --provenance`,
`proposal-create --command`, `proposal-apply --id`, `project-render --revision`
or `--proposal`, `export --rendition --path`, `job-status --id`, and
`plugin-state-capture --id --sample-rate --block-size`. Required arguments can be
inspected with command help. `project-inspect` opens existing local project truth.
CLI file paths are explicit grants by a trusted local operator; there is no
untrusted remote command server.

## Working CLI

Commands emit `adaw.result@1` JSON; failures return a nonzero exit code.
Worker diagnostics are captured in each job's stdout/stderr log files.

```powershell
.\.venv\Scripts\python.exe -m app --root .local/g0-project --timeout 60 inspect
.\.venv\Scripts\python.exe -m app --root .local/g0-project --timeout 60 module-validate --source fixtures/saturation.dsp --sample-rate 48000 --block-size 256
.\.venv\Scripts\python.exe -m app --root .local/g0-project --timeout 60 render --graph evidence/gates/g0/graphs/run-004/faust-drive-4.json
```

`render` creates an uncommitted candidate. Only `--commit-fixture` with the correct
`--base-revision` updates source head and last playable artifact atomically. These
are G0 engineering commits, not owner musical approval. Proposal merging, musical
approval is not implemented. G1 uses separate proposal/revision/rendition commands
above and implements delivery export with independent byte verification.

`plugin-allow --path <exact-file-or-bundle> --provenance <approval>` authorizes one
binary fingerprint. `plugin-probe --id <registry-id> --sample-rate 48000 --block-size 256`
loads it in a separate worker. Missing, changed, unapproved or unprobed plugins fail.

## Source layout and limits

- `docs/spec/v0.4/`: the original specification package; its manifest covers this directory only.
- `docs/decisions/`: engine decisions and the G0 handoff disposition.
- `evidence/gates/g0/`: historical run reports, logs and `graphs/run-001/` through `graphs/run-004/`.
- `app/contracts.py`: immutable graph, canonical hashing, validation and timing.
- `app/service.py`: SQLite source/revisions/jobs/registry and atomic content publication.
- `app/worker.py`: DawDreamer adapter; Faust/VST/MIDI/state/automation.
- `app/arrangement.py`, `app/project.py`, `app/project_cli.py`: G1 source compiler,
  validated imports, transactional proposals/revisions, rendition and export CLI.
- `app/quality.py`: libsndfile + SciPy decode agreement, peak/RMS/DC and pyloudnorm.
- `tools/`: setup, fixture acquisition, real-audio checks and independent hash verifier.
- `tests/`: schema, timing, identity, permission and CLI regressions.

`requirements.lock` is the sole installation lock. `pyproject.toml` declares the
package and runtime dependencies. Run-specific graph files intentionally retain
each run's inputs, even when two runs use the same graph; loose duplicate exports
are not kept. Historical reports describe the repository at the time of their run.

Workers retain the same Windows user's filesystem/network rights. Direct-process
crash/timeout containment is tested; this is not a hardened sandbox, process-tree
containment, resource quota or protection from malicious native code. No HTTP server
is exposed. CLI/service callers are trusted local operators.

PurestGain's opaque state restoration fails on this engine; the failure is retained.
Consolidated's wet algorithm is not sample-deterministic. Its strict state fixture
uses Dry/Wet=0 plus active VST output gain with a declared tolerance. G1 adds an
analytic-test-calibrated true-peak estimate with a margin, not full EBU/ITU meter
conformance. Sidechains, arbitrary-plugin latency compensation, full service crash
reconciliation, all-plugin compatibility and professional listening remain unproven.

Primary license/source links: [DawDreamer GPLv3](https://github.com/DBraun/DawDreamer/blob/v0.9.0/LICENSE),
[Dexed GPLv3](https://github.com/asb2m10/dexed),
[Airwindows MIT](https://github.com/airwindows/airwindows),
[Consolidated GPLv3](https://github.com/baconpaul/airwin2rack/releases/tag/DAWPlugin),
[pyloudnorm MIT](https://github.com/csteinmetz1/pyloudnorm).
# Studio and integration branch

From the checkout with its Windows Python environment installed:

```powershell
.\.venv\Scripts\python.exe -m app.studio_api --root .local/g1-night-circuit-v2 --port 8765
```

Open [local Studio](http://127.0.0.1:8765/). Choose a project directory at launch.
Use `--api-only` to run the same service without the frontend. The existing
`python -m app --root ... --timeout 180` commands work against that project.
Project creation and asset import remain available in the CLI.

See the [owner handoff](docs/development/OWNER-RETURN.md) for verified scope,
portable project commands, audio evidence and remaining work.
