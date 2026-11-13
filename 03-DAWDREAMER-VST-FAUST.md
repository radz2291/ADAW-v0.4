# ADAW — DawDreamer, VST & Faust Engine Integration v0.4

**Status:** Primary proposed engine with mandatory compatibility verification  
**Upstream:** <https://github.com/DBraun/DawDreamer> · Release v0.9.0 (2026-08-12) · GPLv3  
**Normative:** [Architecture](02-ARCHITECTURE.md), [Project/Revision](04-PROJECT-AND-REVISION-CONTRACT.md), [Tests](08-PERMANENT-REAL-WORLD-TESTS.md)

## 1. Why this engine

DawDreamer supplies a Python-accessible JUCE-based offline audio graph, native VST effects and instruments, MIDI, automation, multi-channel graphs, Faust code compilation, DSP and plugin state interfaces, and rendering into NumPy audio arrays. It is a credible way to spend our engineering time on professional production intelligence rather than recreating all host functionality. It is **not** a full finished DAW UI, musical project revision system, autonomous mixer, validator, or quality judge.

**Adoption policy:** Make it the first backend implemented for v0.4, but merge it only after G0 demonstrates it actually works on the owner's Windows host. If critical capabilities fail, preserve the canonical project and adapter contract, log evidence and evaluate an alternative; do not hide missing support with fake previews.

## 2. G0 install/compatibility baseline

- Windows 11 x64, native Python 3.12 x64 (proposed), isolated virtual environment, `dawdreamer==0.9.0` (proposed), actual dependency lock and package checksums.
- Probe pure Faust tone/effect before VST. Probe one supported local VST effect and one instrument when owner-approved plugins are available. If not available, use clearly identified free/test fixtures; never claim owner-VST coverage based on fixture plugins.
- Use one worker process per fault-isolated job in the initial design. Native plugin crashes must leave service alive. Record host OS/version, Python, DawDreamer, plugin vendor/version/format/path/architecture and driver/licensing status.
- DawDreamer's documented import-order conflict with certain LLVM/JAX libraries requires worker dependency isolation; import DawDreamer before such libraries in the same process or separate processes.
- Test CLI can work when UI is closed and no plugin editor is open. Plugin `open_editor()` is blocking and does not constitute an agent automation API.

## 3. Render adapter (ADAW-owned)

The following is a **semantic interface**, not yet executable Python. Its implementation may use Python dataclasses/typed dictionaries and adapters.

```text
AudioBackend.probe_environment() -> EnvironmentReport
AudioBackend.probe_plugin(path, permission) -> PluginCapabilityReport
AudioBackend.validate_graph(graph, plugin_registry, module_registry) -> ValidationReport
AudioBackend.render(snapshot_hash, resolved_graph, range, output_spec, worker_policy)
    -> RenderJobResult(PCM_or_artifact_hash, stems, meters_raw, diagnostics, environment)
AudioBackend.capture_plugin_state(instance_id) -> HashedBlob
AudioBackend.restore_plugin_state(instance_id, hash) -> RestoreReport
AudioBackend.enumerate_parameters(instance_id) -> ParameterCatalog
AudioBackend.set_parameter(instance_id, parameter_binding, normalized_value)
AudioBackend.compile_faust(module_source_hash, declared_contract) -> CompileReport
```

The adapter consumes **immutable, validated** graphs from the project service. It never invents project metadata or mutates authoritative source. Rendering/compilation occur in the worker. Physical units for VST controls may be unavailable; the adapter always preserves the actual normalized value and reported display text if supported.

## 4. Local plugin registry

A VST downloaded and installed by the user is **not automatically trusted** merely because its filename ends in `.vst3` or `.dll`. The owner selects directories/plugins; ADAW scans each in a separate worker where possible, records evidence and offers an allowlist. Avoid automatic recursive loading of every plugin in common program folders at service startup.

Each registry entry stores:

- `registry_id` (ADAW stable identity), `name`, `vendor`, `version`, `format`, `architecture`, `path_on_host`, optional VST3 class/component ID if available, binary hash and scan timestamp;
- `role` instrument/effect/unknown, main inputs/outputs, MIDI support, parameters, reported buses, tail/latency clues, UI availability, known compatibility issues;
- `state_restore` capability/observed result, `headless_render` test result, `automation` test result, `sidechain` test result, sample-rate and output-level behavior;
- trust/allowlist and owner approval, required activation, missing/incompatible flags, diagnostics;
- optional **semantic capability adapter** mapping confirmed parameter identifiers to meaning/units/behaviors, with version and evidence source.

**Identity:** On host, resolve by owner-approved registry ID plus stored plugin class/vendor/version and binary fingerprint when available; treat path as host-specific locator, not canonical cross-computer identity. After a plugin update, re-probe and verify automation mapping before reusing old bindings.

### Plugin capability states

`unscanned` → `scanned` → `authorized` → `tested_compatible` or `limited` / `incompatible` / `missing`. Declared capability is not equal to tested capability. Each test notes sample rate, buffer size, plug-in version and outcome. If a plugin requires GUI/interactive activation, handle it as a manual setup task, not a headless automation success.

## 5. Agent controls the VST **without turning a GUI knob**

1. Ask DawDreamer for actual `get_parameters_description()` and available parameter/range data.
2. Create a versioned ADAW parameter binding from a stable plugin/instance identity plus discovered host parameter index/ID. Names and order might change across versions; index is not globally stable.
3. Read current normalized value and, where available, unit/label. VST parameters in DawDreamer use normalized values **0..1**; do not assume `0.5` means 0 dB, 50 ms or 2:1.
4. For a scoped user request, the agent chooses a parameter based on verified metadata/manual/behavioral tests; proposes setting with prior value, reason and source revision.
5. Apply in candidate graph, render affected audio, compare at matched monitor level, retain effects/quality diagnostics and record exact setting.
6. Restore the plugin's opaque state blob for full state replay; after restoration, verify relevant parameter values and perform a test render.

If a control is not exposed, **do not fake it**. Offer preset/state import, a supported alternate processor, or request an owner GUI intervention followed by state capture. The GUI is an optional human editor; it is not the agent's primary interface.

## 6. VST audio graph and sidechaining

- VST instruments produce audio from MIDI; VST effects process audio. Both have separate capability tests.
- Bus/channel counts must be explicitly verified (`get_num_input_channels`, `get_num_output_channels`, bus configuration checks when available) before graph loading.
- Normal routing: source/instrument → ordered track inserts → bus inserts → master inserts → output. Branching and multi-input behavior require tested graph semantics.
- Sidechain needs both a compatible target plugin and correct auxiliary input/channel/bus routing. Documentation notes main signal first/sidechain second for relevant examples, but plugin-specific input order and activation vary. For G0, test a **known working actual sidechain plugin** with main+key isolation and audibly verify gain ducking, otherwise leave `sidechain` as UNVERIFIED or UNSUPPORTED.
- If no compatible third-party sidechain exists, a project-owned Faust module with an explicitly tested detector input may be used to prove the mechanism; this does **not** prove every VST's sidechain works.
- Avoid assuming plugin latency compensation: measure alignment and record compensation policy before multistage/mastering reliance.

## 7. Faust modules as first-class project source

The agent can author Faust DSP text for a real instrument or effect; DawDreamer can compile it and expose parameters. Store **source text and hash**, declared I/O and parameter contract, runtime/library versions, tests, sample-rate assumptions, and dependencies. Parameterized Faust modules are rendered using the same revision and quality system as VSTs.

G0 must prove:

- Valid Faust code compiles and changes actual audio;
- A declared parameter moves sound in the expected direction (e.g. saturation drive affects harmonics, output trim controls level);
- Invalid syntax/unsafe inputs fail without altering project head or last playable audio;
- Code update requiring changed controls invalidates automation/bindings and prompts revalidation;
- Repeated render identity is characterized on target environment;
- Source and compiled artifacts are not conflated; compilation cache is replaceable.

**Do not** require every arbitrary Python script to become in-process DSP. Use Faust for registered audio-rate source and separate authorized tool workers for general scripts/generators.

## 8. Plugin state, presets and serialization

DawDreamer supports plugin state save/load and render-graph pickling. v0.4 chooses **our canonical manifest + opaque VST state blobs + version pins** as project source. `pickle` is a transient cache optimization only and should generally be disabled in G0 until source-based round-trip is proven. Never unpickle untrusted files: Python pickle can execute code. A plugin state blob remains opaque; do not promise full cross-platform reproducibility or vendor independence.

**Restore proof:** Save instrument/effect state, close worker, reopen same plugin version in fresh process, restore, verify parameter catalog and audible/rendered result. Record if re-render fails or is nondeterministic; missing plugin produces explicit unresolved dependency, not silent fallback.

## 9. Plugin-centric workflow example

User: 'Use my installed synth for the bass. Make it tight, duck it slightly under the kick, then master to the selected video profile.'

1. Resolve approved local synth via registry; verify MIDI/patch compatibility.
2. Instantiate synth, load its stored state/preset, schedule notes.
3. Analyze kick/bass relationship (instrument/stem outputs if possible).
4. Choose between timing/velocity, EQ/level, or sidechain; only use a sidechain route when tested compatible.
5. Render a candidate through DawDreamer, capture a dry/wet reference and processing graph.
6. Quality checker measures actual audio; agent sees diagnostic outcomes and may refine within the brief.
7. Candidate includes VST names/versions, controlled parameter diffs, state blob hashes, audio hash, metrics and known limitations.
8. Human reviews; approved master is exported from the exact accepted revision/profile.

**What ADAW adds:** all decisions/revisions/QA/agent access. **What DawDreamer adds:** actual plugin/DSP/audio execution.

## 10. Performance, concurrency and failure considerations

DawDreamer v0.9.0 releases the Python GIL during rendering and other expensive calls; separate engine objects can render concurrently, but Faust compilation and plugin loading are serialized internally. Do not share a live `RenderEngine` between render threads. Native VSTs can crash or be nondeterministic; start with per-job subprocess isolation. Render benchmarks must record cold vs warm startup, plugin load, Faust compile, MIDI/graph build, render, meter and export separately.

## 11. Licensing & personal use

Owner says ADAW is intended only for private local bedroom use. That removes the immediate need for commercial distribution packaging; it does **not** remove the obligation to respect licenses on GPLv3 software, DawDreamer dependencies, proprietary VST plugins, samples and output assets. Do not distribute third-party binaries or activation data with project exports or repository. A later decision to distribute ADAW requires a fresh legal/packaging review.

## 12. G0 engine acceptance and fallback

**PASS:** Native Windows setup works, Faust/source and VST effects render audible changed audio, instrument MIDI works (using available approved fixture), parameter automation and state round-trip are real, crashes do not corrupt service/project, audio timing and output are measured, known limitations documented, and licensing/host workflow acceptable for personal use.

**PARTIAL:** A tested plugin lacks sidechain/UI/automation support but the core engine works. Mark that plugin limited, prove alternatives and keep corresponding feature scoped. **BLOCKED:** Basic offline rendering, source reproducibility, or safe worker separation cannot meet the core contracts. Record evidence and select a replacement backend **through ADR**, not ad hoc rewrites.

## 13. Official integration references

- Repo/release/README: <https://github.com/DBraun/DawDreamer> ; <https://github.com/DBraun/DawDreamer/releases/tag/v0.9.0>
- Windows installation: <https://github.com/DBraun/DawDreamer/blob/main/docs/installation.rst>
- VST host/state/automation/sidechain notes: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/plugin_processor.rst>
- Faust source/parameters: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/faust_processor.rst>
- Threading/process notes: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/threading.rst>
- Engine serialization caveats: <https://github.com/DBraun/DawDreamer/blob/main/PICKLE_FORMAT.md>
- Compatibility reports: <https://github.com/DBraun/DawDreamer/blob/main/docs/compatibility.rst>
- License: <https://github.com/DBraun/DawDreamer/blob/main/LICENSE>
