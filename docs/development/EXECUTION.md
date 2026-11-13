# ADAW G2–G5 execution ledger

Owner accepted G1 development at baseline `189e39a1fdedd388d4baa94a82c4198bf67e94a9`.
Existing listening notes apply to their recorded WAVs. Integration branch is
`adaw/g2-g5`. See [owner handoff](OWNER-RETURN.md) for the current verified checkpoint.

| Workstream | Assignment | Integration |
|---|---|---|
| Revision semantics and plugin controls | Core specialist | Shared service merge, undo, catalog and controls |
| Replaceable Studio | Frontend specialist | Browser client under apps/studio |
| Independent verification | Verification specialist | API-only, native VST and archive tests |
| API, review records, recovery, delivery, timing | Lead integration | Local API, project archives, job leases and independent cue |

G2 work depends on real G1 source and the shared HTTP/CLI service. G3 restores
verified content and resolves only named VSTs. G4 uses measured audio and awaits
owner listening. G5 validates tempo and meter in the existing offline engine.
Remaining acceptance items are listed in the handoff and permanent spec.
