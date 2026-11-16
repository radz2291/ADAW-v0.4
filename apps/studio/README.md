# ADAW desktop Studio

Local client of HTTP v1. The service remains the sole project writer. See root
AGENTS.md and ADR-0005 for mandatory library and authority rules.

With Node 24 and npm installed, from this directory:

```powershell
npm ci --ignore-scripts
npm run build
```

The committed `dist/studio.js` is served by Python; npm is only needed to develop
or rebuild. `studio.js` retains service/proposal/review interaction; `desktop.js`
adapts audio/ui and WaveSurfer to that state. CSS is split between shared controls
and the desktop layout. Never edit the generated bundle directly.

From the repository root after Python setup:

```powershell
.\tools\start_studio.ps1 -Project .local/glass-current-song -Port 8767
```

The fork can reuse an explicitly supplied existing Python environment via the
launcher's `-Python` argument. Project paths remain explicit and independent.

Use Space for play/pause and Home for stop/start outside input controls. Click a
section to seek matching audio; Loop auditions that section. Select a MIDI track
and Piano roll to move or resize existing notes with pointer/keyboard and edit
velocity. Fader and note gestures create proposals: Apply, then Render head to
hear the edited source. The inspector also offers exact numeric editing. History
& review exposes proposals, selective undo, audio evidence and owner decisions.

Protected tracks and historical source are read-only in the note editor. There
is no live input/recording, live instrument audition, mute/solo or invented meter.
The piano keys are a silent pitch reference. Browser loops are not sample accurate.

Verification commands and results are retained under `evidence/ui/desktop/`.

To reproduce the disposable browser check from the repository root (use a new
folder for each run):

```powershell
.\.venv\Scripts\python.exe -m tools.create_studio_test_project .local/desktop-check
.\.venv\Scripts\python.exe -m app.studio_api --root .local/desktop-check/project --port 8768
```

Keep that server running; in a second terminal from `apps/studio`:

```powershell
npm test -- http://127.0.0.1:8768 C:/absolute/path/to/.local/desktop-check/project C:/absolute/path/to/.venv/Scripts/python.exe
```

The browser check uses installed Microsoft Edge and real Faust audio. It changes
only a project titled `Desktop UI fixture`. Screenshots go to `.local/desktop-qa`.
Use `node verify-browser.cjs export <origin> <report.json>` for the existing exact
export-byte playback check. The backend suite remains `python -m pytest -q`.
