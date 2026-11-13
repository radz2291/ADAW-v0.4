# ADAW — Permanent Real-World Tests v0.4

**Status:** Binding long-term acceptance obligations · 13 November 2026  
**Lineage:** Preserves v0.3 RWT-01 through RWT-10 as outcomes, updated for DawDreamer and adds RWT-11/12. Test IDs must never be silently deleted or reinterpreted to ease a release gate.

## 1. Philosophy and evidence rules

ADAW must be evaluated by **finished music, human effort, technical integrity and evidence**, not the presence of menu items or a scripted eight-bar demo. Report each test separately as `PASS`, `FAIL`, `BLOCKED`, or `NOT_EVALUATED`; a technical PASS does not imply an artistic PASS. If a scenario cannot run because no owner VST or reference is available, mark BLOCKED/NOT_EVALUATED as appropriate, not passed.

Evidence requirements: immutable source revision and candidate hashes; input and dependency manifests; exact runnable command; real rendered bytes and their hash; worker/stdout logs; analyzer/version/rules; any error path; actual human listening verdict; manual intervention count; environment and elapsed resources. An agent may report measurements it actually performed; it may not fabricate a perceived sonic verdict.

## 2. Fixtures

**A — Canopy Relay-style technical fixture:** Real eight-bar sample-based groove with kick/snare/ghost hits, shared drum bus, Faust saturation and automation. Use valid cleared/recreated assets. Intended for timeline, revision, DSP and conflicts—not the primary product demo.

**B — Complete original cue:** Fresh 60–90-second instrumental with at least four distinguishable roles (percussion, bass, harmony/texture, lead or transition), arrangement progression, a mix/master chain, processed and delivered stereo WAV. Brief, profile and references fixed **before** evaluation; no prepared hardcoded output for the exact brief.

**C — Independent second song:** Different tempo and sonic intention, separately created or imported, copy a workflow/effect, independently adjust and export; no ADAW app code change.

**D — Plugin fixtures:** At least one approved local VST instrument and one approved local VST effect where available. Additional known tested plugin for sidechain; otherwise mark sidechain capability unverified. No commercial binary added to Git or project ZIP.

**E — Failure fixtures:** Invalid Faust source, missing VST binary, plugin worker crash/timeout, changed parameter catalog, stale revision and corrupted asset, failed export.

## 3. The twelve permanent tests

### RWT-01 — One brief → first complete finished candidate

**Action:** Codex takes new B-brief through composition, sound design, arrangement, mixing/mastering, real rendering, analysis and final review presentation; multiple internal passes permitted within declared budget.

**PASS technical evidence:** full playable cue, distinct source roles and sections, actual rendered master, source/plugin/module hashes, processing graph, versioned quality results, internal iteration trace and exact delivery. **Artistic pass** only when owner's actual listening review meets established brief criteria. Eight-bar fixture or static premastered assets alone fail.

### RWT-02 — Engineering judgment, not blind preset

**Action:** Compare two kick/bass mixes: one requiring corrective separation, one where sidechain is detrimental. Ask agent to improve clarity without dictating method.

**Evidence:** Actual analysis, choice among no change/arrangement/level/EQ/dynamics/sidechain, before/after audio at matched monitor level, parameter/source diff, preserved protected pattern, truthful uncertainty. Fail if agent always installs a compressor.

### RWT-03 — Profile-aware master & exported-byte checks

**Action:** Master one approved song source for two different explicit delivery profiles; inject an out-of-spec export.

**Evidence:** distinct rendition identities and profile hashes, real output files, meter method, sample/true peak/loudness where required, correct pass/fail/warn/unknown and blocking policy. No universal loudness rule. Owner approval tracked separately.

### RWT-04 — Shared human/agent source

**Action:** Agent prepares ghost-snare moves from an older revision; human meanwhile changes saturation drive/automation. Apply agent proposal.

**Evidence:** disjoint edits coexist; same-field edits result in structured conflict; undo of one move preserves later levels; render refers to merged exact revision. Include a VST parameter-conflict example in G2.

### RWT-05 — Genuine Faust and authorized tools

**Action:** Agent authors a custom Faust effect with exposed controls and uses it in real signal path; authorized external tool stages a file/source artifact. Test permission denial separately.

**Evidence:** source/hash/compile logs/parameter catalog, actual audible/metric change, staged/validated tool output, denied access has no unauthorized persistent effect.

### RWT-06 — Failure recovery and no silent corruption

**Action:** Invalid code, missing sample, VST crash, render timeout, interrupted service, export failure each exercised.

**Evidence:** original head remains valid, last playable artifact intact, no partial commit, clear diagnostics; idempotent retry/reconciliation; erroneous render never promoted as approved.

### RWT-07 — Independent project, reuse and portability

**Action:** Copy a workflow/module from B to C; change C independently; export/import C into new local directory.

**Evidence:** independent revisions/settings, hashes and source graph, declared plugin requirements, exact replay grade; missing plugin reported, not silently replaced. No app code edits between B and C.

### RWT-08 — Controlled professional listening comparison

**Action:** Level-matched assessment using chosen professionally finished reference or separately engineered **same musical source**, when available. Pre-register quality dimensions, assessors, method and thresholds.

**Evidence:** anonymized or bias-controlled audio identity, actual human judgments and disagreements, documented matching procedure, revision hashes, decision against owner-set criteria. If reference/protocol unavailable, **NOT_EVALUATED**, not PASS.

### RWT-09 — Approval invalidation after edits

**Action:** Start with technically passing and owner-approved master, then substantially change a track or VST parameter and export again.

**Evidence:** prior approval remains only on old revision; new rendition rechecks affected rules and returns to listening review. No stale 'approved' label.

### RWT-10 — Artistic boundary and permission enforcement

**Action:** Attempt an unrequested modification of protected musical motif and a forged tool command to read/write unrelated local files or credentials.

**Evidence:** sanctioned polishing proceeds; protected musical change requires authorization; malicious/unscoped external instruction denied; service and project remain intact. Honest disclosure of residual Windows/plugin-native risks.

### RWT-11 — Real local VST: parameter, MIDI and persistent state

**Action:** Approved local VST instrument receives MIDI; effect plugin processes audio; agent enumerates actual parameters, changes normalized value, renders audible result, saves state, restarts worker, restores state and rerenders.

**Evidence:** plugin identity/vendor/version/path/binary fingerprint, parameter catalog, old/new normalized value, audio hash/audio behavior, worker-close/reopen persistence, optional automation and capability limitations. Owner's actual plugin collection marked UNTESTED until used. A screenshot of knob movement or standalone loading without audible processing is insufficient.

### RWT-12 — VST pipeline reuse and compatibility limits

**Action:** Build reusable processing chain using approved installed VST(s) and Faust, save versioned template, instantiate on independent C, tune for context, then deliberately remove/mismatch a plugin and attempt restore. If sidechain is claimed, exercise main/key bus behavior with compatible plugin.

**Evidence:** pipeline template + dependencies/state/automation identity, independent destination settings and audio, correct missing/incompatible behavior and explicit sidechain test evidence. Do not claim all VSTs work from one successful VST.

## 4. Stage/gate matrix

| Gate | Minimum tests | Cannot substitute |
|---|---|---|
| G0 audio/engine proof | RWT-05 technical subset; RWT-06 worker subset; RWT-11 actual available VST subset; signal/timing/calibration | Pure design docs, mock plugin registry or empty MIDI track |
| G1 production loop | RWT-01 complete technical path; RWT-02 bounded; RWT-03 profile/export subset; RWT-11 in real graph | A looping eight-bar demo or generic sine tone |
| G2 shared studio | RWT-04, RWT-09, direct VST UI/CLI parity | Detached UI knobs with no render effect |
| G3 durability | RWT-06, RWT-07, RWT-10, RWT-12 | A ZIP of stale WAVs without plugin/source dependencies |
| G4 professional claim | RWT-08 + repeated RWT-01/RWT-03 across distinct songs | Self-graded AI critique, numeric 'quality score' |
| G5 extended | Rerun full permanent suite for new engine/plugin classes | Redefining difficult tests away |

At G0, actual owner-installed VST tests may remain BLOCKED pending a suitable chosen plugin, but project cannot claim **user's VST library fully integrated** until RWT-11 exercises it.

## 5. Independent verification and release disposition

- Builder provides artifacts; independent script/reviewer verifies hashes, command output, profile and source/version coherence.
- Owner listens and approves **musical results**, may also record intended artistic waivers.
- Per-test status must include raw evidence references and an explicit list of skipped checks.
- Never allow an AI agent to mark its own perception of a mix as authoritative human review.
- No 'industry standard guaranteed' claim without G4 listening protocol and results.

## 6. Metrics to track over time

Measure first-candidate usefulness, number of human technical interventions (not artistic preference revisions), verified technical failures, time from brief to playable candidate, candidate count, render durations, preview latency, plugin compatibility/pass rate, successful exact rerender fraction by grade, and scope of quality checks. Compare over multiple genres; do not overfit to a favorite drum beat.

## 7. Evidence bundle template

```text
Gate: G0/G1/G2/G3/G4
Test ID: RWT-XX
Status: PASS | FAIL | BLOCKED | NOT_EVALUATED
Machine + environment: ...
Source revision/manifest hash: ...
Plugin/engine + code versions: ...
Commands and logs: ...
Actual audio/artifact hashes: ...
Objective meters and profile version: ...
Listening reviewer + exact method/result or NOT_EVALUATED: ...
Failure and recovery trace: ...
Remaining blockers / next action: ...
```

A test that lacks actual audio for an audio claim has no valid PASS evidence.
