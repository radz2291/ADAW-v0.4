# ADAW v0.4 — Primary References and Evidence Basis

**Checked:** 13 November 2026. These are upstream documentation references, not evidence that ADAW itself implements the features or that each of the owner's VSTs works.

## Upstream audio framework

- DawDreamer project, README and supported features: <https://github.com/DBraun/DawDreamer>
- DawDreamer v0.9.0 release dated 12 August 2026: <https://github.com/DBraun/DawDreamer/releases/tag/v0.9.0>
- Changelog, including v0.9.0 Python wheel support, GIL and JUCE/Faust details: <https://github.com/DBraun/DawDreamer/blob/main/CHANGELOG.md>
- Windows/Python installation guide: <https://github.com/DBraun/DawDreamer/blob/main/docs/installation.rst>
- VST plugin processor / parameter API / state / automation / sidechain caveats: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/plugin_processor.rst>
- Faust DSP processor and parameter API: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/faust_processor.rst>
- Render engine, tempo, timing and block size: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/render_engine.rst>
- Multithreading and subprocess isolation considerations: <https://github.com/DBraun/DawDreamer/blob/main/docs/user_guide/threading.rst>
- Pickle/engine restore and plugin path caveats: <https://github.com/DBraun/DawDreamer/blob/main/PICKLE_FORMAT.md>
- Community compatibility matrix (illustrative, not definitive for the owner's plugins): <https://github.com/DBraun/DawDreamer/blob/main/docs/compatibility.rst>
- GPLv3 license and dependent-library warning: <https://github.com/DBraun/DawDreamer/blob/main/LICENSE>

## Quality measurement and professional delivery context

- ITU-R BS.1770-5 (in force) loudness and true peak: <https://www.itu.int/rec/R-REC-BS.1770/en>
- EBU R128 (broadcast recommendation, not a universal music master target): <https://tech.ebu.ch/publications/r128>
- EBU R128 S2 (streaming/broadcast context): <https://tech.ebu.ch/publications/r128s2>

## Internal specification lineage

The v0.3 documents used as direct planning inputs were:
- `ADAW-PRODUCT-VISION-v0.3.md`
- `ADAW-PRD-v0.3.md`
- `ADAW-TECHNICAL-SPEC-v0.3.md`
- `ADAW-PERMANENT-TESTS-v0.3.md`

v0.4 intentionally retains human-led artistic authority, authoritative revisions, code-as-source, immutable candidate rendering, inspectable quality evidence and permanent test IDs, while explicitly prioritizing DawDreamer-backed VST/Faust, a plugin registry, and a greenfield repository. The v0.3 source documents were reviewed; **the current v0.3 implementation was not retrieved or verified**.

## Verification distinctions for agents

**Documented upstream support:** DawDreamer states a feature exists in its API.  
**Tested target-host support:** A reproducible Windows execution proves it on the owner machine.  
**Tested specific VST support:** Named plugin/version can load, render, control and restore as appropriate.  
**ADAW product acceptance:** The whole production workflow and quality/revision gates work.  
These are different levels. Do not collapse them into one statement of 'supported'.
