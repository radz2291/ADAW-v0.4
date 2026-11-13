# ADAW — Product Requirements Document v0.4

**Status:** Proposed v0.4 requirements for a new repository · 13 November 2026  
**Source:** Supersedes v0.3 planning; preserves shared-source/revision/quality intentions while adding DawDreamer-first VST, Faust and adapter constraints.  
**Priorities:** P0 = required for the first complete production path; P1 = required for durable interactive first release; P2 = later.

## 1. Product outcome and users

**Primary user:** One local Windows producer directing a real coding agent, especially Codex, across original music creation and finishing. The first user already has locally installed VST instruments/effects and wants the agent to operate them without manually turning every GUI control. The same ADAW app must support multiple unrelated projects.

**Primary outcome:** One brief → a complete source-based musical arrangement → actual instrument/effect processing → measured, refined mix/master → reviewable first finished candidate → owner-approved output. ADAW should reduce manual engineering skill and repetitive operations, but it must never self-certify aesthetic quality without listening evidence.

## 2. Core user journeys

**J1 — New original cue:** Create project, set creative brief + target profile, authorize appropriate VSTs/Faust/external tools, let Codex build composition/mix/master, listen to candidate and QA, approve or revise, export.

**J2 — Installed VST as instrument:** Add trusted plugin via approved local registry, inspect its exposed parameters/presets and supported MIDI, select/load patch, send notes, render, modify settings, restore state next session.

**J3 — Installed VST as processing pipeline:** Assemble e.g. track EQ → bus compressor → custom Faust saturation → limiter on a selected profile; agent tunes only supported parameters, rerenders, reports actual changes. Save recipe with dependencies; apply to another project without silently duplicating sonic settings.

**J4 — Human override:** Owner moves notes or adjusts a VST control; Codex later refines the ending, preserving owner's unrelated changes. Same-field collisions are surfaced; stale audio is never misrepresented as the accepted revision.

**J5 — Failed or missing plugin:** Plugin fails loading, crashes, is unlicensed, or cannot restore state. Preview or export blocks appropriately, the previous playable revision remains intact, and ADAW records which plugin/environment failed. No quiet replacement.

## 3. Requirements and observables

| ID | Priority | Requirement | Verifiable outcome |
|---|---|---|---|
| PR-01 | P0 | Human creative authority | Agent follows authorized brief/protected decisions; high-impact changes require approval |
| PR-02 | P0 | Project independence | Two songs have independent source, assets, revisions, outputs and settings; no app-code changes between songs |
| PR-03 | P0 | Canonical revisioned source | Musical events, processors, plugin state, code, assets, manifests and dependencies identify each rendered revision |
| PR-04 | P0 | Real offline audio | DawDreamer-backed graph renders actual multitrack MIDI/sample audio and effect processing, not pre-rendered demo substitution |
| PR-05 | P0 | User VST hosting | Approved local Windows VST3 or supported legacy VST loads as instrument/effect where compatible; render evidence recorded |
| PR-06 | P0 | VST parameter control | Agent can enumerate available parameters, read and set normalized values, validate audible behavior, save/restore state |
| PR-07 | P0 | Plugin capability registry | Plugin identity, path resolution, format, version, scan status, automation/state/bus support, risks and permissions are recorded |
| PR-08 | P0 | Programmable DSP | Agent authors, compiles, parameterizes, versions and renders at least one genuine Faust audio effect or synth |
| PR-09 | P0 | Graph/routing | Ordered processors, tracks/buses/master, valid channel contracts and no illegal cycles; sidechain only when tested and supported |
| PR-10 | P0 | Agent-native operation | Codex can create/inspect/edit/render/analyze/export using stable JSON CLI/API, with UI closed |
| PR-11 | P0 | Real production loop | A real original 60–90s cue reaches a complete mix/master candidate with tracked internal iterations and actual outputs |
| PR-12 | P0 | Quality profiles | Versioned destination-aware constraints; no universal LUFS or prescribed compressor recipe |
| PR-13 | P0 | Quality evidence | Actual export-byte checks and signal diagnostics reported separately from listening and artistic approval |
| PR-14 | P0 | Recovery | Invalid code, plugin crash, failed render/export and interrupted job never corrupt accepted project or last good audio |
| PR-15 | P0 | Source editing and conflicts | Typed changes, immutable proposals, idempotent commits, no silent clobbering, recoverable history |
| PR-16 | P0 | Permissions and privacy | Only authorized plugins/files/tools execute; worker isolation and no fabricated sandbox guarantees |
| PR-17 | P0 | Preview and compare | Listen to labeled full/region renders and matched-level comparisons, keeping last playable version while rendering |
| PR-18 | P1 | Studio UI parity | Direct editor/mixer/inspector controls and CLI read/write same source; plugin controls have usable exposed metadata |
| PR-19 | P1 | Project export/import | Portable source/code/assets/locks with hash verification; third-party plugins referenced, not redistributed |
| PR-20 | P1 | Workflow/module reuse | Save and reuse versioned processing recipes, skills and module definitions across projects without hidden coupling |
| PR-21 | P1 | Master/stems delivery | Multiple profile-specific mastering outputs; aligned stems with declared tap points; actual exported-byte verification |
| PR-22 | P1 | Accessible interaction | Keyboard support, visible selection/delete, clear source/monitor distinction, accessible forms, no essential hidden state |
| PR-23 | P1 | Local Windows first-run | Install, detect compatible Python/audio dependency, registry, CLI/service lifecycle, backup/restore and diagnostics |
| PR-24 | P2 | Advanced music scope | Tempo/meter maps, complex arrangements, audio takes, sends, expression, external generator adapters |
| PR-25 | P2 | Low-latency live engine | Live monitoring and real-time DSP with explicit parity/discrepancy to offline renderer |
| PR-26 | P2 | Expanded plugin ecosystem | Additional plugin formats/DAW bridges, better semantic adapters, compatibility packs and advanced sidechain buses |

**P0 gate allocation:** G0 proves PR-04 through PR-09 and PR-14/16 at bounded technical scope. G1 proves PR-01/02/10/11/12/13/17 with a full cue. G2/G3 build collaboration, UI and durability; no P0 is automatically PASS simply because an API route exists. See [roadmap](07-IMPLEMENTATION-PLAN.md).

## 4. Operational production requirements

A production task consumes an explicit **brief**, **revision**, **selected scope**, **quality profile**, **tool/VST allowlist**, and **resource budget**. Agent may perform multiple planned passes, record candidate files and metrics, and return the best justifiable candidate within budget. It must not claim to have 'heard' the music if it only inspected numerical data; real owner listening is recorded separately.

Workflows/skills are machine-executable contracts, not prompt-only prose. Each declares: preconditions; allowed operations; required audio/metadata; candidate algorithms; render/analysis steps; diagnostics; stopping conditions; review requirements; version. Techniques are conditional: doing *nothing* can be correct.

## 5. Boundaries of editability

- **Structured source:** notes, timing, velocity, clip arrangement, mixer routing, parameters, automation, output profiles; editable through typed commands and UI where supported.
- **Custom Faust source:** code and declarations remain editable, versioned, validated; its registered controls are directly adjustable.
- **VST plugin:** external binary remains vendor-owned and may expose only some controls. ADAW records normalized parameter values, internal state blobs, vendor/version and compatibility grade. Display 'opaque/unmapped' where meaning is unknown; do not fake physical-unit semantics.
- **Frozen audio:** agent may mix/edit the audio, but the upstream synthesis may not be reconstructable; retain provenance and report the reproduction grade.

## 6. Audition and quality states

Suggested readiness state machine: `draft -> candidate -> technical_pass | technical_blocked -> listening_review_needed -> owner_approved -> export_verified`, with warnings, waivers and unresolved evidence attached. All transitions bind exact revision + rendition + quality profile. Changes that affect the audio invalidate dependent checks and prior approval for the new revision.

A quality report has four separate columns: objective tests (PASS/FAIL/UNKNOWN/NOT_APPLICABLE), engineering observations (WARN/CONTEXT), listening judgment (owner/independent assessor/unknown), and final owner decision. Technical PASS never sets `owner_approved` automatically.

## 7. Explicit non-goals for first release

- Automatically guaranteeing universally 'top-notch' subjective music;
- Complete DAW feature parity with Ableton/REAPER;
- Hosting arbitrary/incompatible VSTs regardless of licensing, UI/headless behavior or CPU architecture;
- Redistributing third-party plugin binaries in the ADAW project package;
- Full real-time MIDI/audio instrument recording;
- Multiuser internet collaboration;
- A provider-specific embedded AI chat as a prerequisite for Codex;
- Universal sidechain support without plugin-specific routing validation;
- Silent edits outside the selected project directory.

## 8. Nonfunctional and verification requirements

| Area | Constraint |
|---|---|
| Reliability | Atomic persistence, backup before migrations, crash-safe last good audio, independent worker failure |
| Reproducibility | Pin engine/version/module/assets/plugin fingerprints; declare deterministic vs environment-dependent behavior; compare actual PCM |
| Performance | Measure warm eight-bar preview and full-cue render on owner's Windows host; proposed two-second warm simple preview benchmark from v0.3 is **not** a guaranteed SLA for plugin graphs |
| Local security | Service loopback only, session auth and origin protections; explicit file/plugin/tool grants; third-party binaries in separate worker processes |
| Workflow observability | Source commits, plugin scans, dependency locks, job traces, quality methods, cost/time/iteration history |
| Portability | Content-addressed project assets and code; clear missing-plugin errors when moved |
| Accessibility | Keyboard-accessible primary editor, readable statuses, no essential action available solely via hidden GUI gesture |
| Honest claims | Don't label mastering quality as verified solely from loudness or signal checks |

## 9. Acceptance

Binding acceptance is [08-PERMANENT-REAL-WORLD-TESTS.md](08-PERMANENT-REAL-WORLD-TESTS.md). Minimum complete-vision demonstration: a real Codex turn causes real DawDreamer MIDI/VST/Faust processing on an original complete cue, finishes audio with measured outputs, supports an owner listening review, and leaves an inspectable source revision. G0 alone is not this product.

## 10. Open owner decisions (do not silently set)

First musical genre/reference set; actual user plugin(s) to certify; intended first delivery medium and its output thresholds; independent engineer assessment design if claiming commercial parity; iteration/time budget. Builders can supply **explicit temporary engineering fixtures** to run feasibility tests, but those are not owner-approved production defaults.
