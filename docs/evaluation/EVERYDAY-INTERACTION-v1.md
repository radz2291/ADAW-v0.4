# ADAW everyday interaction acceptance rubric v1 — FROZEN

Owner request, 16 November 2026: define criteria first, do not change them unless
the owner asks, use another agent to evaluate, fix and repeat until at least 90%.
This document is frozen before implementation. IDs, tasks, weights, thresholds,
scoring, blockers and scope cannot change without an explicit owner request.
New findings may be recorded separately; they cannot lower this standard.

## Meaning of the target

The target is 90/100 on the observable everyday workflows below, inspired by
conventional DAW interaction. It is not 90% of Ableton/Logic/Pro Tools features,
professional listening approval, or a measured population usability score.
Scope: local desktop composition, arrangement, mixing and audition of an existing
editable project, including Glass Current. Audio recording, plugin compatibility
expansion, time stretching, notation and live MIDI performance are outside this
iteration. Existing RWT-01..12 and architecture/permission rules remain binding.

## Fixed scoring and evidence rules

25 criteria, 4 points each. Each criterion has A and B checks worth 2 points each.
A check earns 2 only if all stated behavior is observed; otherwise 0. No fractional
credit, N/A exclusions, renormalizing, or credit for code presence/screenshots alone
when behavior is required. Untested is zero. Total is the sum out of 100.

An independent evaluator (not the implementer of the assessed code) runs browser
gestures, service/CLI reads, audio evidence and regression checks. It may author its
own tests and reports but must not fix production code or change this rubric.
Keep every evaluation round, failed checks and exact code/tree/rubric hashes.
Builder-authored tests are supporting evidence, not the sole independent score.
No fabricated listening: audible-feedback claims require decoded signal/output
measurement and actual browser playback, not assertions that an agent heard it.

Evaluate at 1440x900 and 1280x720 desktop sizes, plus the specified narrow check.
Use an independent disposable project with at least 3 tracks (MIDI, sample and
protected MIDI), 2 buses, and tempo/meter changes; also inspect the complete
Glass Current song without changing the owner's original. Test both populated
and empty selections. Use real Faust rendering and the installed Edge browser.
Timing is wall-clock on this Windows host, reported with machine/environment.

Success requires >=90 points AND every check in S1-S5, E1, E2, F1 and F2 passes.
Any source loss, silent overwriting, wrong audio labelled current, fake metering,
broken protected-track enforcement or reproducible crash in these tasks blocks
success regardless of points. The evaluator must report remaining lost points.

## E — Editing and familiar gestures (20 points)

| ID | A — 2 points | B — 2 points |
|---|---|---|
| E1 Direct manual edits | A fader or note gesture persists through the validated service without a separate Stage/Apply step; the resulting value is visible and survives refresh. | Agent proposals remain separately reviewable; manual edits neither auto-apply pending agent proposals nor erase unrelated changes. |
| E2 Note creation/deletion | Create a note on empty piano-roll space by pointer, with selectable snap; stable ID, pitch, start and duration appear in service source. | Delete selected note(s) by Delete/Backspace; service source and refreshed editor agree; deleting an empty selection is harmless. |
| E3 Note manipulation | Pointer move and resize, keyboard pitch/timing adjustment and velocity editing persist and render with correct bounds. | Multi-select and duplicate/copy-paste notes produce distinct IDs and preserve relative timing/pitch/velocity; originals stay intact. |
| E4 Undo/redo | Ctrl+Z and Ctrl+Shift+Z (or Ctrl+Y) undo/redo at least three consecutive manual operations in the expected order; visible controls also exist. | Undo/redo uses service validation, preserves an unrelated external edit and reports same-field conflicts instead of overwriting them. |
| E5 Arrangement editing | Select a visible MIDI or sample clip/group, move and duplicate it through UI; changes affect real source events and survive refresh. | Split and trim a selected clip/group through discoverable controls; resulting source boundaries and playback are correct, or an unsupported source type is explicitly identified while the tested supported type works. |

## F — Audible feedback and transport (20 points)

| ID | A — 2 points | B — 2 points |
|---|---|---|
| F1 Mix feedback | While playing, track gain and mute/solo gestures change actual monitored audio within 250ms after monitoring assets are ready; measure signal changes rather than control movement alone. | Preview/monitor sound is visibly distinguished from the canonical rendered master; source edits persist and a subsequent native render agrees with the intended gain/mute/solo semantics. |
| F2 Automatic audition | A note edit automatically queues an audible update, or has one obvious Audition action; no Stage→Apply→Render chain. A 2-bar fixture becomes playable within 8 seconds in at least 2 of 3 warm attempts. | During preparation, previous playback stays usable, progress/failure is visible, and the completed preview identifies the exact source revision. Superseded jobs cannot silently replace newer audio. |
| F3 Navigation | Space play/pause, Home return, clicking ruler/waveform and section navigation work without changing source; text-entry keys do not trigger transport. | Bar/beat, tempo and meter agree with canonical timing before/after changes, including rounded sample boundaries and the full song's 3/4 passage. |
| F4 Loop/compare | Select/loop a section and stop/restart it predictably; loop state/range is visible and source remains unchanged. | A/B switches between identified renditions, preserves reasonable transport position, and clearly identifies stale/current audio. |
| F5 Feedback quality | Loading, commit, preview and failure states are visible; no enabled dead button or silent rejected gesture in the tested workflows. | Rapid successive edits converge to the last requested state without silent dropped edits; failures permit retry and preserve last good playback. |

## M — Mixing and device workflow (20 points)

| ID | A — 2 points | B — 2 points |
|---|---|---|
| M1 Channel controls | Track gain, pan, mute and solo are discoverable, labelled and functional through the shared service; values survive refresh. | At least two solos, mute+solo interaction and clearing all solos have documented, consistent signal behavior; bus/master gains remain usable. |
| M2 Metering | At least master stereo meters respond to actual playback samples, decay/clear on pause and distinguish clipping; no fabricated track meters. | Meter labels identify monitor versus rendered values; a silent and a louder fixture produce independently checked differing readings. |
| M3 Devices/routing | Selecting a track reveals its instrument, ordered inserts and destination bus with understandable names and bypass/read-only capability where applicable. | Change at least one exposed instrument/effect parameter through UI and verify canonical readback plus a real rendered audio change; unsupported controls say so. |
| M4 Precision | Faders support pointer and keyboard, numeric gain entry, reset and visible units; pan has a clear center/reset. | User can inspect source values beyond the visible fader travel without silently clipping them; monitor volume is unmistakably separate from project gain. |
| M5 Context continuity | Track selection stays synchronized across arrangement, browser, editor and mixer; switching views preserves the selected entity. | Editing a channel does not reset timeline zoom/scroll or unrelated mixer scroll; returning to a MIDI editor preserves the working section. |

## U — Layout, discoverability and ergonomics (20 points)

| ID | A — 2 points | B — 2 points |
|---|---|---|
| U1 Workspace sizing | Arrangement/editor or mixer divider can be resized, and browser/inspector can be collapsed without breaking timeline alignment. | Useful pane preferences survive reload; Reset layout restores an operable default on both desktop sizes. |
| U2 Readability/targets | Track/section names, selected notes/clips, transport state and active editor are identifiable at both desktop sizes; full names available when truncated. | Essential pointer controls have at least 24x24 CSS-pixel hit areas (note/resize geometry excepted with keyboard alternative); no overlapping or obscured essential controls. |
| U3 Discoverable tools | Add/delete/duplicate, split/trim, undo/redo, snap and audition are exposed by labelled controls, menus or tooltips; no external CLI knowledge needed. | An in-app concise shortcut/workflow reference matches actual bindings, and empty states explain the next available action. |
| U4 Keyboard/accessibility | Logical keyboard focus, visible focus indicator and accessible names for transport, mixer, editor and dialogs; Escape exits/cancels transient selection or menus predictably. | Editing shortcuts do not hijack typing in fields; protected/read-only controls announce their status and do not accept mutations. |
| U5 Project scale/layout | Glass Current's complete arrangement remains navigable and playable with no browser exceptions; browser search and zoom operate on actual entities. | At 390x844 there is no document-level horizontal overflow; essential playback/review remains reachable; local asset loading works without a CDN. |

## S — Safety, source truth and regression (20 points; all mandatory)

| ID | A — 2 points | B — 2 points |
|---|---|---|
| S1 Canonical editing | All musical edits use service validation/atomic revisions; CLI and UI agree after create/edit/delete/mix actions; no direct browser DB/filesystem mutations. | Protected tracks reject event/clip mutations through both UI and direct API; rejected batches leave head/source unchanged. |
| S2 Conflicts/history | A stale same-field edit yields visible conflict and preserves current source; disjoint external edits survive ordinary editing and undo. | Undo/redo and refresh/reopen retain stable IDs and recoverable history; no silent overwrite or duplicated command application. |
| S3 Audio identity | Every presented master/preview has correct revision identity; edits invalidate current/approved claims and do not relabel old bytes as new. | Exact Glass Current exported bytes still hash correctly and play; original project source remains unchanged throughout tests. |
| S4 Fault recovery | A failed preview/render gives a visible actionable error, preserves last good playback and allows retry. | Invalid operation, interrupted/superseded update and missing dependency do not partially publish source or promote wrong audio. |
| S5 Regression/library integrity | Existing backend suite and frontend-absent contract remain passing, with existing optional skips disclosed; no RWT identity is weakened. | audio/ui and WaveSurfer remain pinned/local with notices; origin/token/static-route protections remain; frozen rubric hash verifies unchanged. |

## Required evaluation report

Report each A/B check as PASS/FAIL/UNTESTED with evidence and points; exact total;
mandatory blockers; observed timings; code commit or tree hash; rubric SHA-256;
fixture identities; audio hashes where relevant; screenshots; browser errors;
test commands; findings to fix; and any remaining subjective uncertainties.
The final >=90 result must be independently rerun after fixes, with all mandatory
checks passing on that same assessed code. Owner listening/acceptance stays separate.
