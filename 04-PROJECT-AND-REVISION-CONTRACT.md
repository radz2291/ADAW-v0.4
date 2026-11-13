# ADAW — Project, Source and Revision Contract v0.4

**Status:** Normative semantic contract; schemas in `schemas/` are draft representations to validate during G0  
**Primary invariant:** One authoritative revision captures every **supported editable decision** that determines a rendition. DawDreamer objects, plugin GUIs and cached WAVs are derived views/artifacts—not that source.

## 1. Logical project layout

```text
<song-name>.adaw/
  project.sqlite                  # revision log, operation ledger, jobs, metadata
  source/
    manifests/<revision>.json     # canonical snapshots or exported index
    modules/sha256/<hash>.dsp     # project-owned Faust source
    workflows/sha256/<hash>.json  # reusable expertise recipes
  assets/sha256/<hash>            # original audio/MIDI/source or generated frozen data
  plugin-states/sha256/<hash>     # opaque vendor state, never plugin binary
  profiles/sha256/<hash>.json     # selected quality/delivery profile versions
  artifacts/sha256/<hash>         # committed render/export audio and analyses
  cache/                          # throwaway intermediate render and compiled cache
  runtime/requirements.lock.json # engine, plugin dependencies, analyzer and tool versions
```

Paths are illustrative, not an enforced disk layout. Portable export may use a different archive structure but must preserve references and hashes. Third-party VST **binaries are not copied** into the project package; host requirements are recorded.

## 2. Canonical entities

| Entity | Minimum semantic fields |
|---|---|
| `project` | ID, title, schema, current head, creation metadata, production brief/profile references |
| `revision` | ID, parent(s), canonical source fingerprint, author, immutable operations, created time |
| `brief` | Target length/use, owner direction, reference IDs, protected decisions, permissions, allowed tools and budget |
| `arrangement` | Tempo/meter, 960 PPQ in first scope, explicit end tick, section IDs, tracks, start/end ranges |
| `track` | Stable ID, type (audio/sample/MIDI/instrument), event/clip IDs, gain/pan, route graph refs |
| `event` | Stable ID, start tick, duration/velocity, note or asset ref, source track; expression if supported |
| `bus` | Stable ID, ordered insert processor IDs, channel counts, output bus, trimmed/gain/pan state |
| `processor_instance` | Stable ID, kind (`built_in`, `faust`, `vst`), module/plugin reference, enabled, values, state hash and routing |
| `plugin_reference` | Registry ID and vendor/class/version/binary evidence; instance parameter-binding map and state blob |
| `faust_module` | Stable ID, revisioned source hash, input/output type, declared parameters and dependency lock |
| `parameter_binding` | Instance ID + stable ADAW binding ID + host parameter index/identifier and observed catalog version |
| `automation_lane` | Stable lane/point IDs, target binding, mode, interpolation, pre/post extrapolation, tick/value points |
| `asset` | SHA-256, media metadata, path/ref, provenance, copyright/usage note, reproducibility grade |
| `quality_profile` | Version/hash, destination, objective requirements, diagnostic/review sections, waiver policy |
| `rendition` | Revision hash + target profile + renderer/plugin/tool fingerprint + master/preview purpose |
| `quality_run` | Exact file/content hash, algorithms, thresholds, outputs, uncertainty and statuses |
| `approval` | Owner identity, rendition/hash, profile/version, comments, applicable waivers, date |
| `export` | Approved rendition ref, byte hash, format, stems/tap points and verification record |

All structure entities must have persistent IDs so later agent edits can target them without relying on UI positions. Example project schema is in [schemas/project-manifest.schema.json](schemas/project-manifest.schema.json).

## 3. Render identity

An audio render fingerprint includes at least: canonical musical snapshot, track/bus graph, source module hashes, audio asset hashes, plugin instance references, plugin opaque state hashes, plugin **binary identity and version where identifiable**, machine/renderer/worker versions, engine settings, sample rate, effective automation, random seeds (where supported), quality-profile-specific mastering chain, requested range/preroll/tail and output format.

**Important:** Fingerprint identity is not a guarantee of bit-identical output for nondeterministic VSTs. Record the observed reproducibility grade and hash the actual output. If a dependency is missing, reject exact replay rather than silently substitute an effect.

## 4. Time and automation

- Early fixture: fixed 4/4 and fixed tempo with 960 ticks per quarter note, single origin. Event/section ranges half-open `[start, end)`.
- `end_tick` explicitly marks song arrangement extent; export tail independently specifies time for reverbs/delays. Zero-length and out-of-range clips rejected.
- Automation lanes contain individually addressable point IDs; hold/linear initially; value range and normalization taken from **bound processor schema**.
- `pre_first` and `post_last` are explicit (`base`/`hold` where implemented). No undocumented implicit fade to zero.
- Plugin automation binds against **instance+catalog version**; if an installed VST update changes parameter index/order/semantics, suspend old automation until verified/rebound.
- A MIDI note's timing uses the canonical tick origin; the adapter converts to DawDreamer's supported MIDI/time representation and tests resulting sample positions.

## 5. Candidate/proposal/commit contract

Every change submitted by UI or CLI is a typed command:

```json
{
  "command_id": "f22a42b1-5c16-48c0-8193-cb9c62d18a02",
  "base_revision": "r-00017",
  "author": {"kind": "agent", "id": "codex-session-local"},
  "apply_mode": "preview",
  "operations": [
    {"op": "move_event", "event_id": "snare-ghost-07", "start_tick": 3360},
    {"op": "set_parameter", "instance_id": "drum-saturation", "binding_id": "drive_db", "value": 4.0}
  ]
}
```

**Command semantics:**

1. Validate schema, permissions, asset/code refs, graph invariants and plugin capability catalog. Never mutate head during preview.
2. Materialize immutable **candidate** and operation diff against `base_revision`.
3. Render candidate using a frozen reference; return actual rendition/audio/quality info or a concrete failure.
4. At apply, compare candidate's operation dependencies with current head. Disjoint edits can rebase; identical value changes converge; divergent same-field updates, deleted target, timing assumptions, module interface changes and plugin catalog changes must conflict/revalidate.
5. Return a structured conflict with base/current/proposed values and IDs, not 'last writer wins'. An owner may submit explicit resolution against latest head.
6. Atomically commit operations and new head after complete validation. Same `command_id` and payload are idempotent; reusing ID with changed payload is error.
7. If merged head differs from previously heard candidate, mark preview **STALE** and require new audition before attributing sound to that commit.
8. Undo is an inverse typed operation on current head, with ordinary conflict semantics. It must not roll back unrelated later work.

### Special plugin/state concerns

A plugin's opaque state blob is usually a unit of change; two concurrent edits to the same opaque state must conflict unless a verified parameter-level merge can safely reconstruct the full state. Direct changes to a plugin editor must be captured as a new staged blob and integrated with known parameter diffs; the GUI is not an independent hidden source. Changing plugin binary/version may invalidate the entire instance's parameter mapping and state, requiring explicit review.

### Code-module interface concerns

If agent edits Faust code to rename/remove `drive_db`, all automation lanes and UI/agent bindings that refer to `drive_db` must be validated. A broken dependency blocks apply; it cannot silently retarget by parameter index.

## 6. Staging and immutable artifacts

External tool output, new Faust source, imported WAV, and plugin state must be staged outside the canonical source. Stage operation records content hash, type, size, media metadata, producer/tool provenance, and explicitly permitted source path. Project service moves verified bytes into the content store atomically. Executable output is never directly promoted without compilation/test evidence and source validation. Failed workers leave only discardable staged files.

## 7. Backup, import/export and reproducibility

`project export` produces source manifest, structured composition, Faust source, assets, plugin-state blobs, readable plugin dependency manifest, quality profile, provenance notes, and optionally recent master/stems. `project import` validates hashes/schema, resolves local approved plugin references, and reports unresolved dependencies. Never rewrite historical quality evidence based on remeasured audio without a new quality-run identity.

A project opened on a different machine can be:

- **Fully replayable on tested pinned environment** (D1, exact criteria recorded),
- **Asset reproducible** (D2: committed frozen audio/stems play but generator not replayable),
- **Dependency-blocked/environment-dependent** (D3: plugin install/activation needed),
- **Invalid/corrupt** (import fails with diagnostics).

If plugin is missing, the app may play a previously exported/frozen audio artifact as a labeled fallback if it exists and permission allows; it must not claim the editable plugin was successfully reconstructed.

## 8. UI/source parity and monitor-only controls

Persistent musical controls — note timing, plugin parameters, automation, routing, processor enable, output trim — issue project commands. Monitor-only playhead, zoom, loop, compare level, selection and playback volume remain view state; they do not change master render. A browser UI and CLI must resolve exact same project head and conflict semantics.

## 9. Schemas, migrations and verification

Schemas are versioned and migrated with backup. Canonical JSON is sorted/normalized before hashing with fixed float behavior specified. G0 must determine actual stable hashing approach (no naive platform-dependent Python `repr` as authoritative). Verify equal CLI/UI operations yield same canonical source hash. Demonstrate source restore after service restart, conflict handling, deleted automation parameter, corrupt asset hash and missing installed VST. Document all known untested assumptions.
