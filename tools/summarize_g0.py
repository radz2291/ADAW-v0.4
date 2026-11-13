"""Package retained logs/source inputs and a readable report; no audio regeneration."""
import json
from pathlib import Path
import shutil

from app.contracts import RenderGraph, canonical, file_hash


def main():
    root = Path.cwd()
    base = root / "evidence/gates/g0"
    for path in sorted(base.glob("run-*.json")):
        report = json.loads(path.read_text())
        graphs = base / "graphs" / path.stem
        graphs.mkdir(parents=True, exist_ok=True)
        for name, render in report["renders"].items():
            request = json.loads((Path(render["stage"]) / "request.json").read_text())
            graph = RenderGraph.parse(request["graph"])
            if graph.sha256 != render["source_sha256"]:
                raise RuntimeError("Retained request/source mismatch: " + name)
            (graphs / (name + ".json")).write_bytes(graph.source)
        log = root / ".local" / (path.stem + ".log")
        if log.exists():
            shutil.copyfile(log, base / (path.stem + ".log"))
    code = [*root.glob("app/*.py"), *root.glob("tools/*.py"), *root.glob("tests/*.py"),
            root / "fixtures/saturation.dsp", root / "fixtures/downloads.lock.json",
            root / "requirements.lock", root / "pyproject.toml", root / "tools/setup.ps1"]
    (base / "source-files.json").write_bytes(canonical({p.relative_to(root).as_posix(): file_hash(p) for p in sorted(code)}))
    r = json.loads((base / "run-004.json").read_text())
    audio = r["renders"]["pipeline-project-a"]
    lines = ["# G0 actual Windows run report", "", "Date: 13 November 2026. Decision: **PARTIAL ADOPT**.", "",
        "Local Git repository; branch `main`; no remote URL configured. Obtain the exact delivery commit with `git rev-parse HEAD` (also supplied in the chat handoff). Code fingerprints: [source-files.json](source-files.json).",
        "", "## Result", "",
        f"{len(r['checks'])} bounded integration checks PASS; 14 unit/CLI checks PASS. Independent verification checks all {len(r['renders'])} final WAV/PCM/source/state identities. This is G0 engineering evidence, not a complete cue or full permanent-test acceptance.",
        "", "Windows 11 build 26100 AMD64; native CPython 3.12.14; DawDreamer 0.9.0. NumPy 2.2.6, SciPy 1.15.3, soundfile 0.13.1, pyloudnorm 0.1.1. Exact wheel checksums: [dependency-wheels.json](dependency-wheels.json); install lock: [requirements.lock](../../../requirements.lock). Node not used.",
        "", "Setup and exact reproduction commands: [README](../../../README.md). Run command:", "", "```powershell",
        ".\\.venv\\Scripts\\python.exe -m tools.run_g0 --root .local/g0-project --timeout 60 --report evidence/gates/g0/my-run.json",
        ".\\.venv\\Scripts\\python.exe -m tools.verify_evidence evidence/gates/g0/my-run.json", "```",
        "", "Raw final evidence: [run-004.json](run-004.json), [run log](run-004.log), [unit log](unit-tests.log), [independent verification](verification-004.json), [doctor](doctor.json), [module validation](module-validation.json).",
        "", "## Audio and processing", "",
        "A 16-second diagnostic graph combines Dexed MIDI, a second synthetic tone, authored Faust saturation, summing bus/master, and a VST effect. This is not the RWT eight-bar drum fixture or a composed cue. Pipeline A/B share a template with independent settings; different outputs and unchanged A head were verified.",
        "", f"[Play pipeline A]({Path(audio['audio_path']).as_posix()})", "", f"WAV SHA-256: `{audio['data']['audio_sha256']}`.",
        f"Source SHA-256: `{audio['source_sha256']}`. 48 kHz stereo FLOAT WAV; {audio['quality']['frames']} frames. Metered actual file: {audio['quality']['integrated_lufs']:.3f} LUFS, {audio['quality']['sample_peak_dbfs']:.3f} dBFS sample peak. No delivery target or listening verdict.",
        "", "Faust third/fundamental harmonic ratio: bypass 1.90e-11; drive 1 = 0.003300; drive 4 = 0.046033. Halving trim halves PCM exactly; fresh and warm Faust renders match. Input onset 12345 lands at sample 12345 with 256-frame blocks.",
        "", "## Plugin results and retained failures", "",
        "- Dexed 1.1.0 VST3 (Digital Suburban): real MIDI audio, Output 0.8→0.4 halves RMS, all exposed values restored in fresh worker. Final PCM max delta 1.2207e-5; RMS ratio 1.000000000095. Earlier identity was observed but is not guaranteed: D3.",
        "- Airwindows Consolidated build 316a048 VST3: strict test uses Dry/Wet=0 and active Output Level gain. State restores all values; max PCM delta 2.4564e-8 < 1e-6 fixture tolerance. Hold automation lowers late/early RMS to 0.512000. Default wet processor renders, but fresh/warm PCM differs: D3; not certified deterministic.",
        "- PurestGain64 VST2: loads and changes audio, but opaque state restoration fails because DawDreamer constructs an unavailable editor. [Original failure](run-001.json) is retained; no exception is suppressed. Catalog-validation failure [run-002](run-002.json) and wet-effect identity failure [run-003](run-003.json) are also retained.",
        "", "Plugin identities, exact paths, binary/bundle hashes, observed channels, parameter counts and probe times are in run-004. Full parameter catalogs and worker stdout/stderr remain in its referenced local staging paths. Download provenance/licenses/checksums: [fixtures lock](../../../fixtures/downloads.lock.json). Publisher checksum verified for Dexed and Consolidated; PurestGain uses a locally recorded hash from its official download.",
        "", "Normal rendering used no opened plugin editor. State loading can internally construct an editor; display-independent operation is not claimed. Sidechain and latency compensation remain NOT_EVALUATED. No owner plugin collection was supplied.",
        "", "## Timing (seconds)", "", "Cold means first render on a newly built engine; warm means second render on the same engine. Whole worker includes startup, both renders, file write and report. These are observations on this host, not SLAs.", "",
        "| Fixture | Prepare | Cold render | Warm render | Whole worker |", "|---|---:|---:|---:|---:|"]
    for name in ("faust-drive-4", "dexed-base", "consolidated-base", "pipeline-project-a"):
        x = r["renders"][name]
        t = x["data"]["timing"]
        lines.append(f"| {name} | {t['prepare_seconds']:.4f} | {t['cold_render_seconds']:.4f} | {t['warm_render_seconds']:.4f} | {x['wall_seconds']:.4f} |")
    lines += ["", "## Measurement and recovery", "",
        "Actual WAV bytes decode identically via libsndfile and SciPy. Sample peak, RMS, DC, format and frame count are measured. Pyloudnorm BS.1770-4 calibration: −23 reference → −23.034979 LUFS; −69.5 absolute gate → −69.492971; −10 relative gate → −10.070214. All within the upstream ±0.1 LU threshold. This is three-vector coverage, not full meter certification; true peak is NOT_EVALUATED.",
        "", "Invalid Faust, deleted control binding, synthetic worker exit code 73, 0.5-second timeout, stale commit, denied plugin, missing file and changed fingerprint were exercised. Source head and hashed last playable bytes survived. Service reopen retains committed pointers. This does not test a real vendor crash, Windows host interruption, full service-job reconciliation or every export failure.",
        "", "Native workers retain same-user filesystem/network rights. Direct child termination is tested; no hardened sandbox, process-tree control or CPU/memory quota is claimed.",
        "", "## Permanent test matrix", "", "All full RWT scenarios remain NOT_EVALUATED; the table reports only G0 subsets.", "",
        "| ID | Full scenario | G0 subset |", "|---|---|---|"]
    for key, val in r["permanent_tests"].items():
        lines.append(f"| {key} | {val['status']} | {val.get('g0_subset', 'NOT_EVALUATED')} |")
    lines += ["", "## Handoff", "",
        "Changed implementation: app contracts/service/worker/quality/CLI; generated-signal fixture; pinned setup/download tools; test/evidence runners; 14 regressions; engine ADR; original spec copied under docs/spec/v0.4. No prior ADAW code, proprietary plugins or purchased samples imported.",
        "", "Next bounded step, after G0 review: begin G1 arrangement and revision operations, idempotency/state associations, job reconciliation, profile/export conversion and true-peak calibration. Collect the musical brief/profile before producing the required 60–90-second cue. UI remains deferred. No G1 or subjective professional-quality claim.", ""]
    (base / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

