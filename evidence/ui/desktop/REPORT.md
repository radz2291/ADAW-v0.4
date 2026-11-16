# Desktop Studio verification â€” 16 November 2026

Owner scope: fork the current project, use the researched audio UI libraries as
the main interface, record future UI instructions, and improve desktop workflow.
Branch `adaw/desktop-studio`, independent worktree, baseline `3897f30`.

## Delivered

- audio/ui timeline, piano roll with velocity and resize controls, track/bus/master
  faders. Existing numeric inspector and plugin bindings remain available.
- Searchable project browser, section navigation, meter-aware bar/beat transport,
  audition loops, keyboard transport, waveform seeking through WaveSurfer.
- Explicit proposals, apply, render, selective undo, exact-export owner review,
  historical/protected editing locks and visible stale audio identity.
- Local bundled runtime and integrity lock; no runtime CDN. Root AGENTS.md now
  requires these adapters/libraries for future UI work. ADR-0005 records the policy.
- Independent Glass Current archive restore; original song source and bytes match.

## Observed verification

Windows, CPython 3.12.14, DawDreamer 0.9.0, Node 24.22.1, npm 11.6.2, Edge headless.

| Check | Observed result |
|---|---|
| Existing Python regression suite | 43 passed, 1 optional VST skipped; 50.28 s |
| New local static assets / CSP / route isolation test | 1 passed; 34.91 s |
| Real browser source editing and playback | PASS; see browser.json |
| Exact copied song export over HTTP and playback | PASS; SHA-256 below; 390px viewport |
| Visual inspection | Desktop arrangement/mixer, piano roll and narrow layout screenshots |
| npm dependency audit at install | 0 vulnerabilities reported |
| Musical/listening approval | NOT_EVALUATED; no song changes made |

The browser uses actual pointer/keyboard events and the real service/CLI, not
mocked requests. It verifies local-only assets, zoom/filtering, meter-boundary
seeking, looping, transport, staged edits, CLI readback, protected and historical
locks, a new Faust render, A/B stale labels and no page/CSP errors. The backend
frontend-absent integration scenario remains passing. No existing RWT definition
was removed, weakened or relabeled as complete by this UI delivery.

During development the browser caught blocked library-injected CSS, faders left
disabled after load, and media-time rounding just before a meter boundary. All
were corrected and covered by the final browser scenario. Pointer-resize testing
also caught a nested note template; the template now provides only the handle
inside the library-generated note. Early harness failures
(required CLI timeout and an assertion typo) were corrected before recording PASS.

Glass Current source revision:
`rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5`.
Exact export SHA-256, checked against restored content and HTTP-delivered bytes:
`ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b`.
Archive SHA-256:
`c6cd9ab3dbf10879008e2218ff2abe22a80dedd540dbc1ae3212c7b253e67f6b`.

## Reproduce

Build with `npm ci --ignore-scripts` then `npm run build` in `apps/studio`.
See [Studio README](../../../apps/studio/README.md) for exact disposable-project,
server and browser commands. Run the backend suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

For this worktree's live copied song, reusing the existing verified Python env:

```powershell
.\tools\start_studio.ps1 -Project .local/glass-current-song -Port 8767 -Python ..\261113-ADAW-v0.4\.venv\Scripts\python.exe
```

## Limits and next slice

This is an offline-render Studio, not a claim of Ableton/FL feature parity.
There is no live recording/monitoring, track mute/solo or synthesized keyboard
audition. Adding/deleting notes is visibly rejected; existing events can be moved,
resized and velocity-edited. Arrangement section blocks navigate source rather
than implying a separate movable clip model. Browser loops are not sample accurate.
Waveform preparation still decodes the whole rendition in browser memory.

Next bounded slice: explicit service-backed event add/delete operations with
protected-track, undo/conflict, and real render verification; server-generated
waveform peaks for larger projects. No G4 professional listening claim is made.
