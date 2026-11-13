# G0 decision — PARTIAL ADOPT

The Windows-native engine foundation is implemented and tested. Final evidence:
[run report](evidence/gates/g0/REPORT.md), [machine-readable results](evidence/gates/g0/run-004.json),
[independent hash verification](evidence/gates/g0/verification-004.json),
[ADR-0001](docs/decisions/ADR-0001-engine-adoption.md).

15 bounded G0 checks and 14 regression tests pass. Real Faust, Dexed MIDI/state,
VST effect gain/automation/state, multitrack routing, independent project reuse,
worker failure preservation and a three-vector loudness calibration are exercised.

Adoption is limited: PurestGain opaque state restoration fails; tested VSTs do not
guarantee bit-identical rerenders; true peak, sidechains, general latency compensation,
hardened Windows isolation, arbitrary plugin compatibility, full permanent scenarios
and human listening remain unverified. All failures remain in the evidence history.

G0 handoff only. G1's original complete 60–90-second cue has not started.
