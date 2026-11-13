# ADAW v0.4 — G0 Windows engine proof

New implementation; no v0.3 code reused. Working JSON CLI, immutable validated
signal graphs, transactional service, killable DawDreamer workers, real Faust/VST
renders and independent decoded-file measurement. **Not a finished DAW or cue.**

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
approval and delivery export are not implemented.

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
uses Dry/Wet=0 plus active VST output gain with a declared tolerance. True peak,
sidechains, arbitrary-plugin latency compensation, full service crash reconciliation,
all-plugin compatibility, professional listening and G1 remain unproven.

Primary license/source links: [DawDreamer GPLv3](https://github.com/DBraun/DawDreamer/blob/v0.9.0/LICENSE),
[Dexed GPLv3](https://github.com/asb2m10/dexed),
[Airwindows MIT](https://github.com/airwindows/airwindows),
[Consolidated GPLv3](https://github.com/baconpaul/airwin2rack/releases/tag/DAWPlugin),
[pyloudnorm MIT](https://github.com/csteinmetz1/pyloudnorm).
