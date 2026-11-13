# ADAW — Product Vision v0.4

**Status:** Owner direction incorporated; proposed detailed interpretation · 13 November 2026  
**Normative companions:** [PRD](01-PRD.md), [Architecture](02-ARCHITECTURE.md), [Quality](05-PRODUCTION-QUALITY.md)

## 1. Why ADAW exists

Music production requires years of accumulated competence across musical arrangement, synthesis, processing, mixing, mastering, technical delivery, and listening judgment. An agent may be good at generating code or choosing settings, but an ordinary coding environment does not give it a coherent, trustworthy way to hear consequences, reuse tools, govern revisions, or verify a finished master. ADAW supplies that environment.

**ADAW is a local, human-directed, agent-operated music production system that aims to deliver a fully composed, mixed, mastered and technically verified first finished candidate from one user brief.** A single user request may trigger many bounded internal edits, renders, analyses and corrections. 'First try' refers to the first complete candidate the human receives, not to a single processing pass and not a promise of artistic perfection.

The agent acts as a **production assistant**, not an autonomous creative director. It can choose engineering methods, invoke professional audio processing, author Faust DSP, configure installed VSTs, and run repeatable workflows. The owner defines musical taste, intended use, constraints, references and approval.

**ADAW's distinctive promise is production responsibility with evidence.** Production operations should be accessible and consistent; 'industry-standard quality' is a context-dependent target, not an automatic pass badge.

## 2. Representative experience

1. **Direct.** Give Codex or ADAW a brief such as '90-second energetic cinematic electronic cue; keep room for narration; punchy kick and controlled bass; strong ending.' Select a target output profile, protected motifs and permitted tools.
2. **Prepare source.** The agent creates song sections, tracks, clips, MIDI/performance events, and a multi-stage signal path. It may load a permitted installed VST synthesizer, use another plugin for EQ/dynamics, or write a project-owned Faust processor.
3. **Engineer continuously.** Arrangement and sound choices are informed by mix headroom, transient overlap, groove, spatial balance and downstream delivery—not followed by a blind rescue master.
4. **Evaluate and refine.** ADAW renders audio through DawDreamer, measures applicable properties, compares alternatives where meaningful, and returns failures/warnings to the agent. The agent chooses suitable corrections within the approved scope and iteration budget.
5. **Present a real candidate.** The owner receives a complete playable cue, exact revision, processor graph/plugin list, source and parameter changes, actual metering results, unresolved production judgments, and a clear listening-review state.
6. **Collaborate.** The owner changes an exposed plugin setting, moves a snare or changes an arrangement. Later agent edits use the resulting revision and do not erase unrelated human decisions. Any incompatible edit is explicitly resolved.
7. **Finish.** Once the owner approves the sound and the selected output profile passes, ADAW produces verified file(s), optional aligned stems, a reproducible project package and an export record tied to exact hashes.

## 3. The three product pillars

### 3.1 Production intelligence

Make mixing/mastering/composition expertise **operational**, not only natural-language suggestions. A technique declares its purpose, applicability, audio inputs, optional tools, decision space, validation, listening risk and evidence. Examples: gain staging; EQ masking investigation; kick-bass interaction; dynamic shaping; true-peak management; mono compatibility; mastering for a specified medium. An expert capability is **not** 'always insert a compressor'. 'No change' is a valid outcome.

### 3.2 Workflow automation

A professional production pass consists of coordinated steps: inspect → diagnose → plan → edit → render → measure → compare → refine → report. Codex orchestrates these steps using stable CLI/API commands; ADAW provides the machinery and durable records. Reusable workflows should not lock in song-specific values as universal defaults.

### 3.3 Quality governance

Quality has different kinds of evidence: technical compliance can be tested; engineering concerns can be diagnosed; artistic excellence requires appropriate listening judgment. Every delivery profile has versioned, relevant rules. Every PASS identifies the actual audio measured and method used; inconclusive evaluation remains UNKNOWN/REVIEW rather than magically passing.

## 4. Human and agent authority

| Decision | Owner | Agent | ADAW quality / project system |
|---|---|---|---|
| Creative brief, genre, emotion, protected motif | Final authority | Interpret, implement, ask on ambiguity | Record constraints |
| Instruments, processing choices, implementation techniques | Can choose/override | May choose within delegation | Validate capability and provenance |
| Installed VST and custom source usage | Authorizes plugins/tools | Loads, configures, writes source where permitted | Gate permissions, versions and state |
| Mix/master engineering | Can change/listen/approve | Diagnose and refine | Measure, compare, report limitations |
| Export readiness and release | Approves | Prepare delivery | Verify actual exported bytes and record owner approval |

**Operational autonomy is broad; creative authority is not.** A request for cleaner bass may permit level adjustment, EQ or sidechain testing. It does not permit changing the main melody or editing unrelated local files.

## 5. Crucial principles

1. Finished sound is the product, not the UI or number of automation steps.
2. An integrated production loop is the first required proof, not a beautified drum sequencer.
3. The agent can operate ADAW while its UI is closed; CLI is a first-class interface.
4. DawDreamer is an interchangeable *implementation backend* in concept, not the source-of-truth project format.
5. Installed VST plugins may be used as track instruments/effects or pipeline processors only after on-device compatibility discovery and approval.
6. The same VST parameters must be accessible programmatically where actually exposed; parameter metadata may be incomplete or ambiguous.
7. Faust/source code modules are first-class, versioned musical source; generated DSP has real audio output and exposed parameters.
8. All edits are revisioned, auditable, previewable and recoverable; failed code cannot corrupt the previous playable revision.
9. Quality standards are destination-aware and evidence-backed; no artificial universal mastering number.
10. A complete owner-approved output still may have artistic limitations; report what was actually evaluated.
11. Repeatable skills, test fixtures, workflow recipes, plugin capability adapters, and profiles are **versioned** and reusable across songs.
12. Home-use simplifies deployment and packaging but does not permit unsafe execution, unauthorized files, pirated plugins, or redistribution of vendor binaries.

## 6. What ADAW is not

- Not a one-click promise that every musical idea automatically becomes commercially competitive.
- Not a conventional DAW clone with a decorative chat pane.
- Not a replacement for humans deciding taste, reference alignment and emotional fit.
- Not a fixed preset generator that blindly runs EQ → compressor → limiter.
- Not a wrapper that assumes every VST or plugin GUI is agent-accessible.
- Not coupled to TORI/VICT or to any specific model provider for its initial operation.

## 7. Success definition

The core product succeeds when the owner can instruct a real Codex agent to produce an original 60–90-second complete cue, get a mixed/mastered **first finished candidate** backed by honest evidence, intervene directly, instruct further work without losing source integrity, and repeat the process with a different song. A comparable professionally finished reference is used for qualitative review when available; numerical metering alone is insufficient. Time and human-effort savings are **measured**, not assumed.

## 8. Explicit uncertainty

The owner has chosen a greenfield restart and high-value VST integration. Whether DawDreamer can host each of the owner's actual VSTs reliably, achieve needed sidechain routing, support deterministic rerenders, and meet preview speed on the Windows machine **must be demonstrated during G0**. Architectural documents express our intended contracts; they do not constitute running proof.
