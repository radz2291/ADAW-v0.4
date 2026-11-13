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
