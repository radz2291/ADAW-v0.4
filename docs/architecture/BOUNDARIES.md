# ADAW component boundaries

The project service owns canonical source and transactions. The Studio, CLI and
independent clients operate on the same explicit project directory and revision IDs.

| Responsibility | Implementation | Public entry point |
|---|---|---|
| Source and typed revision semantics | `app/arrangement.py`, `app/revisions.py` | Project service operations |
| Authoritative persistence and job coordination | `app/project.py`, `app/service.py`, `app/job_leases.py` | ProjectService and Service |
| Native engine | `app/worker.py` | Validated render and probe requests through Service |
| VST registry | Service with worker probe | CLI approval and catalog operations |
| Production workflows | `app/production.py`, musical recipes under `tools/` | Python workflow calls and CLI recipes |
| Metering and listening records | `app/quality.py`, `app/reviews.py` | Analysis, export and exact-byte review operations |
| Application API and agent interface | `app/studio_api.py`, `app/project_cli.py`, `app/__main__.py` | HTTP v1 and JSON CLI |
| Replaceable Studio | `apps/studio/` | Same-origin HTTP v1 |
| Project archive transport | `app/portability.py` | Backup, restore and reconcile CLI |

An engine request contains a compiled graph and resolved immutable dependencies.
The worker publishes artifacts to its staging area. The service verifies artifacts
before referencing them from the project store. The browser plays a selected
rendition through a content-verified WAV endpoint.
