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
section to seek matching audio; Loop auditions that section. Piano roll supports
pointer creation, note movement/resizing, velocity, multi-selection, copy/paste
and deletion. Changes save through validated service operations immediately.
Undo/Redo works through the shared revision service. Audition prepares the latest
source while the previous audio remains playable. Pending agent proposals remain
separate in History & review.

Track gain/pan/mute/solo and bus/master gain persist. Multiple solos play together;
mute wins. Live mix uses verified native pre-level track stems for immediate
monitoring. It approximates downstream bus/master effects and final fade; use
Audition for the canonical finished sound. Stereo output meters measure actual
WebAudio samples; listening volume does not change source gain. Exact rendition
identity remains available in transport tooltips and History.

Protected tracks and historical source are read-only in the note editor. There
is no live input/recording or live instrument synthesis. The piano keys are a
silent pitch reference. Browser loops are not sample accurate. Sample groups
support end trim; leading sample trim and split are explicitly unsupported.
Browser/inspector visibility and pane height persist locally; Help has Reset layout.

The workspace opens with arrangement above a single contextual dock. Piano roll,
Mix console and Devices share that dock; Properties is optional in Piano view.
Browser and History open on demand. Compare & waveform contains the A/B players
and WaveSurfer navigation. Escape closes History or comparison before clearing
musical selection. Track headers and the mixer reuse one channel adapter; rail
mix controls hide when the console is open. Faders retain numeric precision.
Device cards use audio/ui knobs with direct numeric entry (Enter or blur saves).
Sample waveforms use decoded native monitor stems mapped through the tempo map;
missing or incompatible stems never produce a placeholder waveform.

The frozen everyday rubric and independent round reports live under
`docs/evaluation/` and `evidence/evaluation/`. Never change the rubric without an
explicit owner request. Older evidence describes its historical build.

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
