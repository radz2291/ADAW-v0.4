# ADAW — Production Intelligence & Quality Governance v0.4

**Status:** Normative product behavior with proposed analyzer implementations  
**Important:** Mixing/mastering expertise cannot be reduced to a universal preset or single score. Technical measurement supports but does not replace listening.

## 1. Why this subsystem exists

The user's core objective is repeatable **high-standard finished music from one initial brief**, removing years of manual low-level audio engineering where possible. ADAW should supply executable expertise and measured feedback loops so a coding agent can work like a skilled technical producer. We must distinguish professional workflow execution from proven professional perceptual results.

The quality subsystem has four lanes:

| Lane | Role | Truth status |
|---|---|---|
| Technical compliance | Exact file properties, true peak/loudness under selected profile, decode/format, clipping, invalid samples, alignment | Objective when algorithm and target defined |
| Engineering diagnosis | Transient conflict, dynamics, tonal balance, spectral/temporal masking proxies, mono translation, sidechain behavior | Contextual diagnostic; not universal pass/fail |
| Perceptual review | Groove/punch, naturalness, image, unpleasant artifacts, emotional fit, reference similarity | Human listening or explicitly validated perceptual model |
| Artistic approval | Is this the owner's intended music and satisfactory finished release? | Owner's decision only |

## 2. Quality profiles and standards

A profile specifies target **destination**, media format, thresholds, diagnostics, and review/waiver policy. Profiles must be **versioned and user-selectable**, not hardcoded as one global mastering recipe. For example, a 48 kHz, 24-bit PCM stereo delivery profile may be a technical export preset. A broadcast profile based on EBU R128 has different loudness constraints from a streaming/music-release profile. **The v0.4 package intentionally does not assert an owner-approved universal LUFS target.**

The loudness/true-peak meter must implement or use a tested **ITU-R BS.1770**-compatible measurement, including declared version and oversampling conditions. Cite/encode destination-specific requirements as separate profile variants. Example draft schema is [schemas/quality-profile.schema.json](schemas/quality-profile.schema.json); examples with `null` targets mean not approved, not zero.

Each objective check record must include: `check_id`, `category`, `algorithm`, `version`, `audio_sha256`, `profile_sha256`, `measured`, `unit`, `constraint`, `status`, `severity`, `evidence_path`, `notes`. Status values: `pass`, `fail`, `warn`, `unknown`, `not_applicable`. If a target is unspecified, status is **unknown**/**not_applicable** rather than a fabricated pass.

## 3. Minimum technical analyzers (G1 scope)

1. Verify container decode, duration, channels, sample rate, format/bit depth and output hash.
2. Check NaNs/infinities, unintended silent/missing regions, hard digital clipping, and possible signal discontinuities via documented algorithms.
3. Measure sample peak, DC offset, RMS (with meaningful scope), BS.1770 integrated loudness where duration/content allows, and true peak via a verified meter.
4. Reopen final **exported bytes**, not only in-memory float audio; measure and compare against the selected profile.
5. Validate stem duration/start alignment and disclosed tap points if stems are requested.
6. Verify render/output belongs to exact revision and source/dependency lock; stale approvals are not transferable.

Early diagnostic algorithms are **advisory** until independently validated and calibrated on curated fixtures.

## 4. Engineering intelligence library

Each reusable capability declares a machine-readable contract:

```text
capability_id/version
purpose + intended use
eligibility/input prerequisites
optional analysis methods
permitted source/processor edits
required plugin/module capabilities
measurement and listening validation
stopping conditions and known false positives
failure/rollback behavior
evidence output schema
```

### Initial capabilities

**Gain/headroom:** inspect track/bus peaks and gain staging; adjust where justified, preserve intended dynamics and final output target, and report changed stages.

**EQ / spectral balance:** use spectra as clues, consider tonal roles and reference context, avoid indiscriminate matching to a fixed target curve. Test whether audible result improves via level-matched review.

**Kick–bass interaction / sidechaining:** inspect actual overlap and arrangement. Choose among no change, envelope/performance, level, EQ/dynamic EQ or tested sidechain. Record gain reduction/attack/release as available, compare groove/impact and avoid unwanted pumping. Do not insert compressor automatically.

**Dynamics/limiting:** measure peaks/short-term dynamics and selected destination. Apply suitable processing with true-peak/limiter checks; don't destroy transients to chase a number.

**Stereo/mono translation:** analyze phase correlation and mono behavior; a widened sound is not automatically better. Protect intentional spaciousness.

**Transitions/tails:** analyze structural boundaries, noise, clip tails and abrupt changes; automatically fix only clearly technical issues without altering composition intentions.

**Master delivery:** create profile-specific rendition(s), measure actual files, label remaining listening requirements, record master processing and export hashes.

## 5. Agent optimization loop

`inspect source + current render → identify material issue → generate candidate fix → render → measure → level-matched compare → decide keep/revise/revert → report`.

Loop constraints:

- Each issue must have evidence (objective diagnostic or authorized owner listening note). No speculative random plugin twiddling indefinitely.
- Track all candidates and change rationale; evaluate at comparable conditions and matched **monitor** loudness. Never normalize the actual export to create a favorable A/B impression.
- Reject changes that improve one number but violate protected motifs, create other failures, or degrade owner-approved qualities.
- An agent can automate measurement and propose judgments, but cannot silently mark 'subjectively excellent' from statistics alone.
- Iteration, wall-clock, local resource and tool limits are user-set/visible. If exhausted, return best candidate plus blockers/uncertainties, not a fake PASS.
- Avoid oscillation: preserve baseline and candidate metrics; only continue if a material issue remains and candidate improvement is justified.

### Example: low-frequency conflict workflow

User: 'Kick lacks punch, bass is masking it. Keep the groove and loudness.'

1. Inspect track instruments/VST patches and source performance, and render isolated/mix stems where possible.
2. Measure overlapping frequency/time energy and transient relationship. Treat it as a **proxy**, not proof of masking.
3. Consider timing/velocity/level changes, EQ, dynamic EQ, sidechain. Confirm actual VST capability before attempting aux routing.
4. Make one scoped proposal; capture plugin-state changes or Faust source diff.
5. Render same region with sufficient preroll, level-match only for listening, compare relevant diagnostics and actual audio.
6. Present 'what I changed', 'what improved by measurement', 'what may sound worse', 'what remains for listening'.
7. Respect owner's protected kick pattern; do not change it without approval.

## 6. Readiness and approval model

`draft` → `candidate` → (`technical_pass` OR `technical_blocked`) → `listening_review_needed` → `owner_approved` → `export_verified`.

- Engineering warnings or approved waivers may coexist with owner-approved audio; waiver records have owner identity, reason, specific revision/profile/check.
- A user change after approval creates a new revision. Previous approval remains historical only; affected evidence is invalidated for the new rendition.
- No export may claim `owner_approved` merely because Codex ran an analyzer. An owner can explicitly export a technical-pass candidate without artistic approval, but the export label must say so.
- If analyzer is unavailable/throws, status is `unknown` or `blocked` according to required check; no bypass via 'tool failure = pass'.

## 7. Listening evaluation and professional-quality claims

Permanent testing includes level-matched review with documented source material and, where possible, independently professionally finished reference output. Prefer same composition engineered independently for comparisons; when comparing unrelated tracks, make the contextual limitations explicit. Record assessor identity/role, method, blinded/ABX if chosen, exact audio hashes and written listening judgments. Owner defines any threshold/assessor roster **before** claiming externally comparable quality.

A successful technical QA report proves only the specified technical checks. A professional sonic-quality claim requires a separate **human listening validation protocol** and repeated independent-song evidence. If that protocol is not yet established, status `NOT_EVALUATED` is accurate and acceptable during development.

## 8. Measurement examples and common traps

- **Short loops:** integrated loudness may be invalid or misleading; label short-region matching method such as RMS or documented gated loudness; don't treat it as the full master.
- **Peak vs true peak:** sample peak and reconstructed true peak differ; report separately.
- **Clipping:** intentional creative distortion is not the same as unintended digital clipping; still verify actual format and consequences.
- **EQ curve:** similar averaged spectra do not establish matching artistic timbre.
- **Sidechain:** compressor present is not proof a valid detector receives the kick; verify gain reduction when kick triggers.
- **Mastering:** loudness target achievement is not proof of good mix; dynamics and genre matter.
- **Reference:** monitor level matching cannot change the file being judged for technical delivery.

## 9. G1 acceptance conditions

A real 60–90s cue (several distinct musical roles and sections) reaches a complete candidate via real source → DawDreamer graph → processing chain → export, with: quality profile selection; actual finished WAV; decoded actual-byte verification; objective measurements including peak/loudness/true peak when meter available; documented automation/corrections; owner listening review; unresolved warnings accurately labeled. The result may be technically passing but artistically unaccepted; record that honestly.

## 10. Authoritative reference URLs

- ITU-R BS.1770-5: <https://www.itu.int/rec/R-REC-BS.1770/en>
- EBU R128 broadcast loudness: <https://tech.ebu.ch/publications/r128>
- EBU R128 S2 streaming context: <https://tech.ebu.ch/publications/r128s2>
- DawDreamer engine: <https://github.com/DBraun/DawDreamer>
