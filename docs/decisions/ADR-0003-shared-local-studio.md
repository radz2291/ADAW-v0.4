# ADR-0003 — Shared localhost Studio

Use a dependency-free browser frontend and the Python standard-library HTTP
transport. Keep the existing Python CLI, worker, source and SQLite schema
compatible. Add tables for undo, validated module catalogs and export reviews.

Three-way merge uses stable source identities where available and protects
ordered insert chains. Applying an older proposal checks its precise edited
fields and reports conflicts. Preview source may be stale after a successful
rebase. Undo reverses one revision's changes against the current head. Review
records bind verified export bytes, rendition, revision and profile.

HTTP exposes state, revision/proposal/rendition reads, WAV ranges, and typed
propose, apply, undo, render, analyze and review writes. Browser mutations include
the exact local origin and a per-process session token. This is a single-user local
service. The token separates browser origins and does not distinguish local
processes running as the same user.
