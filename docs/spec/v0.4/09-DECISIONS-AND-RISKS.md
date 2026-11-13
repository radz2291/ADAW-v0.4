# ADAW — Decisions, Assumptions, Risks and Change Log v0.4

**Status:** Working register; explicit classification prevents the builder silently inventing product policy.  
**Change authority:** Owner accepts artistic/product decisions; implementation agent proposes evidence-backed technical ADRs.

## 1. Owner-confirmed decisions

| ID | Decision | Implication |
|---|---|---|
| OD-01 | The agent is a **production assistant** following the human's direction | Strong implementation discretion; no unsolicited artistic autonomy |
| OD-02 | Fast offline rendering is initially acceptable | Do not block first release on full real-time audio |
| OD-03 | Agent may use custom code and external tools | Programmable Faust/modules and governed tool boundary are essential |
| OD-04 | A single initial brief should yield a professionally engineered **first finished candidate** | Complete composition→mix→master workflow is primary acceptance |
| OD-05 | Repeatable high-standard workflows/quality governance are the core value | Measure evidence and manual effort, not number of UI features |
| OD-06 | Codex should be able to operate ADAW programmatically | CLI must work without GUI; tool contracts first-class |
| OD-07 | User-installed VST plugins should become production pipeline components | Registry, parameter control, state, compatibility and reuse are first-class |
| OD-08 | ADAW is for local personal bedroom use | Windows/local operation prioritized; no redistribution packaging required now |
| OD-09 | Prior v0.3 Phase 1 demo is enough; restart **new repo from scratch** at v0.4 | No automatic v0.3 code migration, but preserve proven product principles |

## 2. Proposed defaults requiring actual implementation proof

| ID | Proposal | Acceptance mechanism |
|---|---|---|
| PD-01 | DawDreamer `0.9.0` initial offline backend | G0 Windows real rendering/host test; newer version by ADR |
| PD-02 | Python 3.12 x64 native Windows | Wheel, installed VST compatibility and reproducible setup |
| PD-03 | TypeScript/React local studio and SQLite project service | G1/G2 integration design and source parity proof |
| PD-04 | 960 PPQ, fixed BPM/4/4 initial fixture | Actual sample timing tests; not permanent limits |
| PD-05 | 48kHz, stereo 24-bit WAV sample delivery format | Selected output profile may override it |
| PD-06 | Faust as first programmatic DSP runtime | G0 compilation/parameter/audio/restore proof |
| PD-07 | Versioned plugin capability registry and project state blobs | RWT-11, RWT-12 and G0/G3 checks |
| PD-08 | Separate native render workers with explicit allowlist | Crash containment and scoped security capability proof |
| PD-09 | Versioned quality profiles with BS.1770-compatible meter | Meter calibration and actual file measurement |
| PD-10 | Default preview-first for consequential audio changes | G1/G2 owner workflow feedback |

## 3. Owner decisions still to collect before consequential quality claims

- First song's actual composition brief, references and target medium; builder may use **explicit temporary fixtures** without labeling them owner-approved.
- At least one installed VST instrument and one effect to test, plus permission to load their binaries. A documented test plugin can prove mechanics first.
- Desired audio quality profile requirements (file format, loudness/true peak rules as relevant); there is no universal master target.
- Scope of external tools/network permissions, optional user-approved plugin directories and install locations.
- Internal iteration/time/cost budget for first complete candidate.
- G4 professional listening review protocol: comparator(s), quality dimensions, assessors, pre-agreed thresholds and owner verdict.

**Don't block G0 on these.** Document temporary technical fixtures and ask only when the decision affects an actual owner acceptance/release claim.

## 4. Risks, mitigations and kill conditions

| Risk | Severity | Mitigation / decision condition |
|---|---|---|
| Native VST may crash/hang or require activation/GUI | High | Trusted allowlist, separate worker process, timeout/kill and recovery; test per plugin |
| DawDreamer graph cannot express a specific sidechain topology | Medium–High | Capability tests; fallback validated Faust detector or different plugin, not fictitious graph |
| Plugin normalized values opaque/ambiguous | High for agent accuracy | Retain raw catalog and value; semantic adapters only when evidenced; don't guess units |
| Vendor plugin state fails after upgrade/move | High | Vendor/version/binary hash, state blob, restored test, explicit missing capability |
| Non-deterministic VST/audio tail behavior | Medium | Fingerprint and observed reproducibility grade, retained frozen outputs |
| Agent over-optimizes numerical loudness | High | Destination profile, human listening, context-sensitive diagnosis, no universal quality score |
| Code/tool execution mutates host outside scope | High | Separate workers, file/tool allowlist, Windows restriction testing, disclose residual risk |
| GPL and third-party licenses become distribution issue | Low now / High later | Private local install only; no bundling third-party binaries; revisit before sharing/distribution |
| UI built before real production capability | High | G0/G1 audio-first gating; reject decorative demo as acceptance |
| Overfitting to one kit/cue or plugin | High | Independent song + different plugin/genre where available; permanent tests |
| Quality checker produces misleading PASS | High | Meter calibration, actual byte verification, `unknown`, human review separation |
| Over-engineering backend abstraction | Medium | Narrow adapter interface for tested needs; no speculative alternate engine implementation |

## 5. ADR-required decisions after G0

1. DawDreamer adopted / selectively adopted / rejected, exact version and reasoning.
2. Worker isolation model and residual risk on Windows.
3. Plugin registry identity/mapping, state restore and version pin strategy.
4. Actual graph/routing/sidechain and latency support matrix.
5. Meter implementation and calibrated test fixtures.
6. Audio-source/data schema and exact content-hash canonicalization.
7. First-shippable CLI and response schemas.
8. Performance baseline + measured cold/warm render results.

## 6. v0.3 → v0.4 change log

| Area | v0.3 direction | v0.4 change |
|---|---|---|
| Repo and delivery | Build a probe and evolve existing plan | Explicit greenfield; previous demo/reference not migrated by default |
| Audio backend | Select through broad runtime feasibility | DawDreamer-first on Windows; go/no-go by G0 empirical probe |
| Native plugins | Optional/external adapter | User-owned VSTs and registry/pipeline are primary product capabilities |
| Agent parameter control | Abstract source and tool interface | Concrete VST parameter discovery, normalized values, state/automation contracts |
| Programmable DSP | Portable module candidate | Faust-first via DawDreamer, stored as project-authored source |
| Engine persistence | Opaque dependencies recorded | Explicit rule: DawDreamer pickles cache-only, no untrusted unpickle |
| Professional production | Full cue and QA central | Same ambition preserved, now with richer installed-tool execution path |
| Permanent suite | RWT-01..10 | RWT-01..10 retained; RWT-11/12 added for real plugin use and reuse |
| License/distribution | General packaging evaluation | Owner currently private local use; revisit if distributing |

## 7. Source integrity note

The v0.3 documents were recovered and used as the planning basis for this rewrite; v0.3 Phase 1 implementation code was **not provided or tested** as part of creating v0.4. No specific historical test pass is asserted for it. All new capability descriptions are proposals or documented upstream support unless explicitly marked as independently tested by the new repository.
