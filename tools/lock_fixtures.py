"""Maintainer-only: record already retrieved fixture bytes, never run during setup."""
import json
from pathlib import Path
from app.contracts import file_hash


def main():
    entries = [
        {"url": "https://github.com/asb2m10/dexed/releases/download/v1.1.0/Dexed-1.1.0-win.zip",
         "local_path": ".local/downloads/Dexed-1.1.0-win.zip", "license": "GPL-3.0; archive LICENSE",
         "publisher_sha256_verified": True,
         "extract": [{"member": "Dexed.vst3", "destination": ".local/plugins/dexed/Dexed.vst3"},
                     {"member": "LICENSE", "destination": ".local/plugins/dexed/LICENSE"}]},
        {"url": "https://www.airwindows.com/wp-content/uploads/WinVST64s.zip",
         "local_path": ".local/downloads/WinVST64s.zip", "license": "MIT; https://github.com/airwindows/airwindows/blob/master/LICENSE",
         "publisher_sha256_verified": False,
         "extract": [{"member": "WinVST64s/PurestGain64.dll", "destination": ".local/plugins/airwindows/PurestGain64.dll"}]},
        {"url": "https://github.com/baconpaul/airwin2rack/releases/download/DAWPlugin/AirwindowsConsolidated-2026-11-08-316a048-Windows.zip",
         "local_path": ".local/downloads/AirwindowsConsolidated-316a048.zip", "license": "GPL-3.0; archive LICENSE.gpl3",
         "publisher_sha256_verified": True,
         "extract": [{"member": "Airwindows Consolidated.vst3", "destination": ".local/plugins/consolidated/Airwindows Consolidated.vst3"},
                     {"member": "LICENSE.gpl3", "destination": ".local/plugins/consolidated/LICENSE.gpl3"}]},
    ]
    commit = "b8d67bfd3ce5deef872f688fcfa491a0ca69fddd"
    for name in ("1770-2_Comp_23LKFS_1000Hz_2ch.wav", "1770-2_Comp_AbsGateTest.wav", "1770-2_Comp_RelGateTest.wav"):
        entries.append({"url": f"https://raw.githubusercontent.com/csteinmetz1/pyloudnorm/{commit}/tests/data/{name}",
                        "local_path": f".local/calibration/{name}",
                        "usage": "Local meter calibration only; not redistributed; upstream BS.1770 compliance vectors"})
    for entry in entries:
        entry["sha256"] = file_hash(entry["local_path"])
    Path("fixtures/downloads.lock.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

