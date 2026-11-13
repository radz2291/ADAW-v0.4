# ADR-0004 — Project archives and musical time

The package contains a consistent SQLite backup and hashed content objects.
Plugin registry paths are cleared. Restore takes explicit approved plugin paths
and checks the existing binary and bundle fingerprints. Unresolved plugins remain
visible as missing. Historical stage and export paths remain provenance.
Portable playback resolves content hashes through the service.

Worker ownership uses an advisory OS file lock held by the service process.
Reconcile marks abandoned tracked jobs interrupted. A worker orphan can still
finish under the same user. The recovered service does not promote that result.
Legacy jobs without a lease are listed as untracked.

Arrangement version 2 adds a stepwise tempo and meter map. Tempo can change at
an explicit tick. Meter changes align to a bar boundary in the preceding meter.
The compiler accumulates exact rational time and rounds event endpoints to
frames. Version 1 keeps its original timing and graph format. This slice covers
offline scheduling. VST transport tempo sync and live tempo changes require
separate evidence.
