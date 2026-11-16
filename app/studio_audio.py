"""Read-only descriptions of verified native audio for the replaceable Studio.

Monitor stems are native post-insert/pre-fader outputs. Browser gain/balance is
only an audition aid: buses' inserts, master inserts and final fades still belong
to the native renderer. No source or rendition is persisted here.
"""

from urllib.parse import quote

from app.errors import AdawError


MONITOR_LIMITATIONS = (
    "Live stem monitor: track inserts are rendered; bus/master inserts and final "
    "fade are bypassed. Use Audition for the authoritative native master."
)


def _stem(report, track_id):
    if track_id not in {track["id"] for track in report["source"]["tracks"]}:
        raise AdawError("NOT_FOUND", "Track is not part of this rendition")
    stem = report["render"]["data"].get("stems", {}).get("track_" + track_id + "_monitor")
    if stem is None:
        raise AdawError("MONITOR_UNAVAILABLE", "Audition this revision once to prepare live monitoring stems")
    return stem["sha256"]


def monitor_stem_sha(service, rendition_id, track_id):
    """Resolve only a declared monitor tap, never an arbitrary content-store hash."""
    report = service.rendition(rendition_id)
    return _stem(report, track_id)


def monitor_manifest(service, rendition_id):
    """Describe exact immutable source/taps; audio routes verify bytes on access."""
    report = service.rendition(rendition_id)
    source = report["source"]
    tracks = []
    available = True
    for track in source["tracks"]:
        try:
            content_hash = _stem(report, track["id"])
        except AdawError as error:
            if error.code != "MONITOR_UNAVAILABLE":
                raise
            available = False
            continue
        tracks.append({"id": track["id"], "sha256": content_hash,
                       "url": "/api/v1/renditions/" + quote(rendition_id, safe="") +
                              "/stems/" + quote(track["id"], safe="") + "/audio"})
    return {"schema": "adaw.studio-monitor@1", "rendition_id": rendition_id,
            "revision": report["revision"], "source_sha256": report["manifest"]["source_sha256"],
            "audio_sha256": report["render"]["data"]["audio_sha256"],
            "source": source, "available": available, "tracks": tracks,
            "tap": "post-track-inserts/pre-gain-pan-mute-solo", "limitations": MONITOR_LIMITATIONS,
            "sample_rate": report["graph"]["sample_rate"], "frames": report["graph"]["frames"]}
