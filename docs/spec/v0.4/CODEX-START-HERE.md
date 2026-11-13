# Codex — First Handoff for ADAW v0.4 (New Repository)

**Intended use:** Give this entire specification package and these instructions to a new coding agent. It must create a fresh repo and produce an independently verifiable audio-engine foundation, not a prototype UI.

## Your assignment

You have implementation authority for **ADAW v0.4 Gate G0 only**. Read `AGENTS.md` and all normative docs, with primary attention to the greenfield doctrine, DawDreamer/VST/Faust, project/revision, quality evidence and permanent tests. Previous v0.3 demo is **not** the codebase for this version. Create an entirely new repository; do not copy code unless the owner explicitly requests and you can justify/test it.

### First outcome

A running Windows-native proof that an agent can **actually operate a music production engine**:

1. Install and pin a working DawDreamer `0.9.0` baseline (or document a verified compatible alternative release through ADR) on Python 3.11–3.14 x64; proposed baseline 3.12.
2. Render an authentic Faust DSP effect with adjustable parameters and a small multitrack graph, producing actual audio files.
3. Scan/load at least one approved VST effect and one VST instrument if available. Discover real parameters, change values through API, send MIDI to instrument, automate effect where supported, save and restore plugin state in a fresh worker. If owner's VSTs are unavailable, label the test fixture and leave owner-plugin compatibility open.
4. Test at least one working pipeline `source → track processing/VST or Faust → bus/master → WAV` and record source+audio hashes.
5. Run native VST in a separately killable worker process; simulate a worker failure and prove project source and last playable artifact are preserved. State whether Windows isolation is actually enforceable beyond crash containment.
6. Meter actual WAV/decoded output using independent checks, including a calibrated BS.1770-compatible meter if selected; report algorithm/version and applicable thresholds rather than invent 'professional' grading.
7. Measure cold/warm render and plugin load times on the user's target machine; describe performance and unsupported functions honestly.
8. Deliver `docs/decisions/ADR-0001-engine-adoption.md`, a real run report, exact setup/run commands, test logs, audio refs and recommended G1 architecture.

### Initial repo structure

Use [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) as an initial map. Put this package under `docs/spec/v0.4/`, copy `AGENTS.md` to repo root, and create a minimal `README.md` for setup/test. Ensure the work is organized for future G1/G2—not hardcoded around the first plugin or test audio.

### Important operating constraints

- No GUI required for G0. A text CLI and real audio outputs are preferable.
- No unverified claims about arbitrary VST compatibility, headless behavior or sidechain bus support.
- Never package plugin binaries/activation secrets; scan only explicit owner-approved paths. If no plugin supplied, use suitable licensed test fixture and clearly disclose the substitution.
- Do not default to arbitrary shell permissions from a music brief; tool access remains explicit.
- Do not assert universal mastering quality; G0 proves engine and meters only.
- Preserve failures as evidence. Never mark tests PASS because code was written.
- Need actual Windows/VST execution: if you are operating in Linux/cloud without access to user's Windows host, prepare runnable scripts but mark the Windows/plugin portions **BLOCKED**, not PASS.

### Gate G0 final report format

```text
Repo URL, branch, commit SHA:
Target OS/Python/engine versions and dependency lock:
Exact setup and reproduction commands:
Real Faust audio demonstration (inputs, changes, artifacts/hashes):
Real approved VST instrument/effect tests (or explicitly BLOCKED):
Plugin parameter discovery/change and state restore evidence:
Routing, automation, optional sidechain findings:
Crash/recovery and residual Windows security limitations:
Quality meter method/calibration and measured actual output:
Timing/performance results:
Permanent-test status matrix (G0 portions of RWT-05/06/11/12):
ADOPT / PARTIAL / BLOCKED decision with rationale:
Open issues + proposed G1 scope:
```

**Stop at this handoff gate with evidence.** Do not claim the complete ADAW experience until G1 produces a real, finished original cue, and do not imply the user must approve minor implementation details that can be tested empirically.
