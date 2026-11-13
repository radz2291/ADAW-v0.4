# G0 temporary engineering fixtures

These are synthetic diagnostic signals, not a song or owner-approved production defaults.
The G0 runner supplies 48 kHz, 256-frame blocks, stereo FLOAT WAV, 16 seconds
(eight bars at 120 BPM, 4/4), source frequencies/amplitudes and parameter values.
Float WAV avoids an implicit integer quantization/dither policy during engine proof.
There is no mastering loudness target. Tests use explicit engineering tolerances.
Faust saturation is authored for this repository; no v0.3 code was reused.

Temporary G0 assertions: 1e-7 absolute error for Faust half-trim; third-harmonic
increase >5x for drive 4 vs 1; instrument restored RMS within 5% plus exposed values
within 1e-6; effect state PCM max difference below 1e-6; output/automation level
ratios below 0.8; nonzero floor 1e-5 RMS; onset detection floor 1e-9. Exact PCM identity
is reported separately. These are engineering fixtures, not sonic quality targets.
The meter's ±0.1 LU tolerance comes from the pinned upstream compliance tests.

State tests use fresh workers. Consolidated's strict gain fixture uses Dry/Wet=0
with active Output Level automation. Its wet processor remains separately retained
as nondeterministic evidence. PurestGain remains a known state-restore failure.
Fixture sources, versions, licenses and checksums are in `downloads.lock.json`.

