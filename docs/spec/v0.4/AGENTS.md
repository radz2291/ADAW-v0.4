# AGENTS.md — ADAW v0.4 Repository Constitution

This file is intended to be copied to the **root of the new ADAW repository** (and kept in sync with the package). It applies to every coding/design agent in the project.

## Mission

Build a new, independent, local Windows music production system: human-directed, Codex-operated, **DawDreamer-first**, with real VST/Faust audio processing, revisioned source, reusable professional workflows, objective quality evaluation, and owner-controlled listening/approval. First primary outcome: an original complete 60–90-second cue that is composed/arranged, mixed, mastered, measured, reviewable and exportable through one project. All permanent tests remain in force.

## Required reading before coding

Read in order: `docs/spec/v0.4/README.md` → `00-VISION.md` → `01-PRD.md` → `02-ARCHITECTURE.md` → `03-DAWDREAMER-VST-FAUST.md` → `07-IMPLEMENTATION-PLAN.md` → `08-PERMANENT-REAL-WORLD-TESTS.md`. For contracts also read `04`, `05`, `06`, `09`.

## Working doctrine

1. **Greenfield:** This is not a continuation of previous ADAW code. Do not import previous repo by default; report any reused component and its independent verification.
2. **Sound first:** Implement measurable G0 audio proof and G1 complete cue before investing in an elaborate DAW shell.
3. **DawDreamer first, not DawDreamer everywhere:** Use it in isolated render workers. ADAW owns project/revisions/registry/quality/workflow. Backend adapter remains narrow.
4. **No mock success:** Do not report VST, DSP, render, compatibility, sidechain, quality, sandbox or professional listening as PASS without real reproducible evidence.
5. **One project truth:** No direct SQLite or authoritative filesystem edits by agents/workers; all persist through service validations and atomic commits.
6. **Editable sound:** Structured source, Faust code and exposed plugin parameters are revisioned. Opaque plugin state is acknowledged as opaque; downloaded binaries remain external dependencies.
7. **Agent CLI first:** Provide machine-readable commands and stable errors; Codex can use ADAW without UI.
8. **Human owns taste:** Objective compliance is not a subjective professional-quality guarantee; never fabricate a listening verdict or AI 'heard the mix'.
9. **Reproducibility honesty:** Pin engine/modules/plugins and hash files. Record nondeterministic/missing dependencies rather than claiming exact portable replay.
10. **Permissions:** Plugins are executable binaries; only scan/load owner-approved paths in separate workers, with crash containment and explicit residual risks. Do not trust a native subprocess as a hardened sandbox.
11. **No hidden magic constants:** Every product limit, quality target, default and behavior is a decision. Classify as owner-approved rule, versioned profile, tested engineering constant, or temporary fixture. Never silently hardcode universal mixing values or policy.
12. **Keep permanent tests:** RWT-01..12 must retain identities and evidence. Changes require documented owner approval; don't downgrade the hard cases.

## Code and development discipline

- Create reproducible Windows setup using version-locked dependencies and explicit Python/Node versions.
- Modularize: project/service, plugin registry, audio worker/backend adapter, production orchestration, quality, CLI, and eventual UI.
- Use validation schemas + typed operations, IDs and hashes; no positional UI selectors as persistent entity identity.
- Tests: unit for schema/time/transactions; integration for Faust/VST/worker/QA; permanent gates for complete audio and reuse.
- Segregate test-generated/temporary media from repository. Do not commit proprietary plugins, purchased samples or credentials.
- Each coding cycle returns exact commit, changed files, runnable commands, environment, output audio hashes/logs, test statuses, blockers, next bounded step.
- If G0 evidence contradicts a spec, propose ADR and revise docs intentionally; do not silently alter behavior.

## Agent's first deliverable

Follow `CODEX-START-HERE.md` and finish **G0** in bounded slices. Do not claim G1 or full v0.4 is complete based only on a waveform preview, static UI or 8-bar loop.
