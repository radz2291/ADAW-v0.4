# Supporting regression disclosure

The 44-pass/1-skip concurrent-development run skips
`tests/test_studio_api.py`'s approved native Dexed fixture because
`ADAW_TEST_APPROVED_DEXED` is not `1` (reason: “Opt in to the approved native fixture”).
This optional skip is not a pass. No baseline S5A points were awarded.

The production diff present during that run included a compiler stem expectation
change from `track_kick_level` to `track_kick_monitor, track_kick_level` in
`tests/test_project.py`. The final candidate evaluation must independently verify
the audio meaning of monitor stems instead of treating this expectation change
as evidence of correct monitoring.
