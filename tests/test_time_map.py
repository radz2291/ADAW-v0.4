"""Pin scheduling and backward-compatible fixed-tempo behavior."""

import pytest

from app.arrangement import timing
from app.errors import AdawError


def source():
    return {"schema": "adaw.arrangement@2", "tempo": 120, "length_ticks": 9600,
            "ppq": 960, "sample_rate": 48000, "time_map": [
                {"tick": 0, "bpm": 120, "numerator": 4, "denominator": 4},
                {"tick": 1920, "bpm": 60, "numerator": 4, "denominator": 4},
                {"tick": 3840, "bpm": 60, "numerator": 3, "denominator": 4},
            ]}


def test_piecewise_endpoints_and_crossing_duration():
    frame = timing(source())
    assert [frame(tick) for tick in (0, 960, 1920, 2880, 3840, 6720)] == [
        0, 24000, 48000, 96000, 144000, 288000]
    assert frame(2400) - frame(1440) == 36000
    original = timing({**source(), "schema": "adaw.arrangement@1"})
    assert original(3840) == 96000


def test_meter_change_rejects_mid_bar_boundary():
    data = source()
    data["time_map"][-1]["tick"] += 1
    with pytest.raises(AdawError, match="bar boundary"):
        timing(data)
