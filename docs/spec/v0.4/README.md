# ADAW v0.4 — Greenfield Specification Package

**Date:** 13 November 2026  
**Status:** Proposed architecture and implementation handoff; not a claim that v0.4 exists or has passed tests  
**Target:** New, independent Git repository; Windows 11 x64; single owner; Codex-led development  
**Foundation:** DawDreamer-first offline audio engine, Faust and locally installed VSTs, versioned project model, agent-native CLI, and real quality governance.

## Read this first

This is a **rebuild from scratch**, not a v0.3 patch or migration. The owner reports that the v0.3 Phase 1 demo was adequate to learn from; its code and tests have **not** been audited as part of drafting these documents. Use the older work as conceptual reference only if supplied, and never silently import it. Create a new repository and start with the explicit **Gate G0 integration proof**, then deliver a working **Gate G1 composition-to-master pipeline**. Do not build a beautiful empty DAW shell first.

**The product thesis:** A person directs original music; a coding/production agent uses a professional, programmable audio environment to compose, arrange, mix, master, measure, refine, and deliver one complete, reviewable first finished candidate. The owner has artistic authority; ADAW provides reproducible execution and honest quality evidence.

**Decisive v0.4 change:** DawDreamer is the proposed **default execution backend** for offline audio graphs, MIDI, Faust and supported VST plugins. ADAW retains responsibility for the project source of truth, editing transactions, production workflows, plugin registry, quality checks, and human approvals. Its adapter boundary prevents the project model becoming inseparable from DawDreamer.

## Document map — normative reading order

| Order | File | Purpose |
|---|---|---|
| 1 | [00-VISION.md](00-VISION.md) | Owner intent, product boundaries, operating principles |
| 2 | [01-PRD.md](01-PRD.md) | Functional and nonfunctional requirements and visible behavior |
| 3 | [02-ARCHITECTURE.md](02-ARCHITECTURE.md) | System design, components, process boundaries, rendering |
| 4 | [03-DAWDREAMER-VST-FAUST.md](03-DAWDREAMER-VST-FAUST.md) | Engine integration, plugin registry, programmable DSP, compatibility |
| 5 | [04-PROJECT-AND-REVISION-CONTRACT.md](04-PROJECT-AND-REVISION-CONTRACT.md) | Authoritative data, commits, conflicts, IDs, packages |
| 6 | [05-PRODUCTION-QUALITY.md](05-PRODUCTION-QUALITY.md) | Engineering expertise, analysis, quality profiles, mastering and evidence |
| 7 | [06-AGENT-INTERFACE.md](06-AGENT-INTERFACE.md) | CLI/API, operation contracts, permissions and agent workflows |
| 8 | [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) | Sequencing, deliverables, gates, first tickets |
| 9 | [08-PERMANENT-REAL-WORLD-TESTS.md](08-PERMANENT-REAL-WORLD-TESTS.md) | 12 binding scenarios and independent evidence |
| 10 | [09-DECISIONS-AND-RISKS.md](09-DECISIONS-AND-RISKS.md) | Accepted directions, proposals, open decisions, fallback triggers |
| Agent setup | [AGENTS.md](AGENTS.md) and [CODEX-START-HERE.md](CODEX-START-HERE.md) | Immediate instructions and first Codex handoff |
| Supporting | [reference/SOURCES.md](reference/SOURCES.md) | Official evidence and relevant specification lineage |
| Schemas | [schemas/](schemas/) | Draft illustrative JSON schema contracts; validate and revise at Gate G0 |

## Interpretation hierarchy

1. Owner's explicit decisions and this package's recorded **confirmed** constraints.
2. Verified observations from implementation/test evidence.
3. Normative requirements and contracts in this package.
4. Proposed technology choices, thresholds and examples, which require proof.

When documents differ, do **not** silently choose. Record an ADR or decision request. `P0` means required for the specified first integrated product path—not all of it must exist at G0. A check is not PASS if code merely exists; it must run against a real fixture with retained evidence.

## Current decisions (confirmed / proposed)

**Confirmed by owner:** human-directed assistant; first presented candidate should be end-to-end composed/mixed/mastered; quick offline renders acceptable initially; custom code and external tools encouraged; home/personal local use; installed VSTs should become reusable parts of pipelines; complete new repository with no obligation to preserve v0.3 implementation.

**Proposed and test-dependent:** Windows 11 + Python 3.12 x64, DawDreamer `0.9.0` pinned for G0, TypeScript/React lightweight UI when warranted, SQLite revisions and SHA-256 content store, 48 kHz stereo render default, 960 PPQ initial scheduling, versioned typed plugin capability registry, native managed worker subprocesses. Verify dependencies on the target machine before pinning implementation.

## Absolute prohibitions

- Do not fabricate a professional listening verdict, rendered audio, plugin compatibility, security isolation, or a successful test.
- Do not mark technical compliance equivalent to subjective sonic excellence.
- Do not substitute a hardcoded demo or pre-mastered audio asset for the permanent end-to-end test.
- Do not embed purchased third-party plugin binaries, licenses, credentials, or copyrighted reference tracks in the repository.
- Do not use DawDreamer's `pickle` as ADAW's canonical source; never deserialize untrusted pickle files.
- Do not permit a VST/third-party binary to run in the privileged project-service process.
- Do not set a universal mastering LUFS target in code. Delivery profile parameters and exceptions must be explicit and versioned.

## Starting point

Give the new Codex agent [CODEX-START-HERE.md](CODEX-START-HERE.md) and the entire package. Gate G0 produces runnable proof and an integration decision. Only then proceed to a real G1 music-production path, not to decorative UI work.
