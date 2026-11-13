# Repository map

* `app/` contains existing Python modules grouped by ownership in the boundary map.
  Keeping the package path preserves historical CLI and worker entry points.
* `apps/studio/` contains the browser client. Its three static files use the local API.
* `tests/` contains source, timing, HTTP contract, recovery and real fixture checks.
* `tools/` contains setup, production recipes and repeatable verification.
* `docs/spec/v0.4/` holds the immutable original specification.
* `docs/architecture/`, `docs/decisions/` and `docs/development/` hold current architecture,
  decisions and execution state.
* `evidence/gates/` retains test output, source identities and artifact hashes.
* `.local/` holds ignored runtime projects, archives, native binaries and WAVs.
