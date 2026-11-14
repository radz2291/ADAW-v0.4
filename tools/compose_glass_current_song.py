"""Extend the Glass Current study into an original full-length instrumental."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from app.project import ProjectService
from tools.compose_g1 import PLUCK_DELAY, make_samples


LEAD = '''declare name "GlassLead";
freq = nentry("freq",440,20,20000,1);
gain = nentry("gain",0.5,0,1,0.01);
gate = button("gate");
env = en.adsr(0.024,0.23,0.67,0.22,gate)*gain;
f = freq*(1+0.0027*os.osc(5.1));
voice(r) = os.osc(f*r + 0.26*f*os.osc(2*f*r)) + 0.22*os.osc(2*f*r) + 0.08*os.osc(3*f*r);
process = (voice(0.999)*env*0.33), (voice(1.001)*env*0.33);
effect = _,_;
'''

PLUCK = '''declare name "GlassPluck";
freq = nentry("freq",440,20,20000,1);
gain = nentry("gain",0.5,0,1,0.01);
gate = button("gate");
env = en.adsr(0.003,0.22,0.1,0.14,gate)*gain;
tone = os.osc(freq + 0.7*freq*os.osc(3*freq)) + 0.22*os.osc(2*freq);
process = (env*tone*0.28) <: _,_;
effect = _,_;
'''

# Bar counts, tempo and meter are choices for this song.
FORM = [
    ("intro", 4, 120, 4, "Cold glass and an exposed fragment of the hook"),
    ("verse_one", 8, 120, 4, "Low-slung pocket with space around the pulse"),
    ("lift_one", 4, 120, 4, "Rising answer phrase and a held breath"),
    ("chorus_one", 8, 120, 4, "Wide hook over the original Am–F–G–E tension"),
    ("post_hook", 4, 120, 4, "Rhythmic answer and release"),
    ("verse_two", 8, 120, 4, "Darker restatement with offbeat percussion"),
    ("lift_two", 4, 120, 4, "Higher lead pickup and drum fill"),
    ("chorus_two", 8, 120, 4, "Hook returns with octave answers"),
    ("undertow", 8, 104, 4, "Slow, spacious bridge with suspended harmony"),
    ("three_beat_turn", 8, 104, 3, "Hook recast as a three-beat refrain"),
    ("final_chorus", 12, 120, 4, "Full hook, counterline and final held tonic"),
    ("outro", 4, 120, 4, "Drums fall away into a resolved A minor color"),
]

CHORDS = [(57, 60, 64, 71), (53, 57, 60, 64), (55, 59, 62, 69), (52, 56, 59, 65)]
ROOTS = (33, 29, 31, 28)
HOOK = [
    [(0, 76, .68), (.75, 76, .42), (1.5, 79, .4), (2, 81, 1.45), (3.5, 79, .36)],
    [(0, 76, 1.12), (1.5, 72, .42), (2, 74, .65), (3, 76, .68)],
    [(0, 74, .66), (.75, 74, .42), (1.5, 76, .42), (2, 79, 1.4), (3.5, 76, .35)],
    [(0, 71, .68), (1, 72, .46), (1.75, 71, .45), (2.5, 68, .65)],
]


def compose(origin, destination, inputs):
    original_revision, original = origin.source()
    source = deepcopy(original)
    ppq = original["ppq"]
    source.update(title="Glass Current", brief="Full instrumental song extending the Glass Current meter study.",
                  sections=[], time_map=[], tail_frames=2 * source["sample_rate"])
    inputs.mkdir(parents=True, exist_ok=True)
    source["master"]["gain_db"] = 0
    source["tracks"] = deepcopy(original["tracks"])
    for track in source["tracks"]:
        assert not track["protected"], track["id"]
        track["events"] = []
        key = "asset_sha256" if track["kind"] == "samples" else "module_sha256"
        destination.import_file(origin.content / track["instrument"][key],
                                "audio" if track["kind"] == "samples" else "faust", "Original Glass Current study", 30)
    for channel in [*source["buses"], source["master"]]:
        for insert in channel["inserts"]:
            destination.import_file(origin.content / insert["module_sha256"], "faust", "Original Glass Current study", 30)

    def module(name, dsp):
        path = inputs / f"{name}.dsp"
        path.write_text(dsp, encoding="utf-8")
        return destination.import_file(path, "faust", "Original Glass Current song instrument", 30)["sha256"]

    echo = module("glass_echo", PLUCK_DELAY)
    for name, dsp, role, gain, pan in [
        ("hook", LEAD, "Lead hook", -12, 0),
        ("prism", PLUCK, "Arpeggio and answers", -17, -.24),
    ]:
        source["tracks"].append(dict(id=name, role=role, kind="faust_synth", bus="music",
            gain_db=gain, pan=pan, protected=False, events=[],
            instrument=dict(module_sha256=module(name,dsp), parameters={}, voices=8, release_seconds=.28),
            inserts=[dict(module_sha256=echo, parameters={})]))
    samples = make_samples(inputs)
    for name, gain, pan in [("snare",-10,.04), ("clap",-20,-.10), ("openhat",-21,.20),
                            ("crash",-21,-.17), ("riser",-22,.18)]:
        asset = destination.import_file(samples[name], "audio", "Original synthesized percussion", 30)["sha256"]
        source["tracks"].append(dict(id=name, role="Percussion", kind="samples", bus="drums",
            gain_db=gain, pan=pan, protected=False, events=[], inserts=[],
            instrument=dict(asset_sha256=asset, fade_frames=24)))
    tracks = {track["id"]: track for track in source["tracks"]}
    tracks["haze"]["gain_db"] = -14
    tracks["bass808"]["gain_db"] = -7
    tracks["kick"]["gain_db"] = -9
    tracks["hat"]["gain_db"] = -18

    tick = 0
    timing = None
    for section, count, bpm, beats, mood in FORM:
        if timing != (bpm, beats):
            source["time_map"].append(dict(tick=tick,bpm=bpm,numerator=beats,denominator=4))
            timing = (bpm, beats)
        end = tick + count * beats * ppq
        source["sections"].append(dict(id=section,start_tick=tick,end_tick=end,mood=mood,swing=.5))
        chorus = section.startswith("chorus") or section == "final_chorus"
        verse = section.startswith("verse")
        lift = section.startswith("lift")
        for bar in range(count):
            def add(name, beat, duration, pitch=60, velocity=90):
                events = tracks[name]["events"]
                start = tick + round(beat * ppq)
                events.append(dict(id=f"{name}_{len(events)}",start_tick=start,
                    duration_ticks=min(round(duration * ppq), end - start), note=pitch, velocity=velocity))

            if verse or section in ("intro", "undertow", "outro"):
                chord_index = (bar // 2) % 4
            elif lift:
                chord_index = (1, 2, 0, 3)[bar]
            else:
                chord_index = bar % 4
            if (section in ("outro","final_chorus") and bar >= count-1):
                chord_index = 0
            chord = CHORDS[chord_index]
            chord_span = 2 if verse or section in ("intro","undertow","outro") else 1
            if section == "outro":
                chord = CHORDS[0]
            if bar % chord_span == 0:
                for pitch in chord:
                    add("haze", 0, beats * chord_span - .18, pitch, 76 if chorus else 63)
            if chorus:
                phrase = HOOK[bar % 4]
                if bar == count - 1 and section == "final_chorus":
                    phrase = [(0, 81, 3.65)]
                for beat, pitch, length in phrase:
                    add("hook",beat,length,pitch,108 if section == "final_chorus" else 98)
                    if section == "final_chorus" and beat in (0, 2):
                        add("prism",beat+.015,length,pitch+12,68)
                for step, pitch in enumerate((chord[2]+12,chord[1]+12,chord[3],chord[0]+12)):
                    add("prism",.5+step,.26,pitch,63)
            elif section in ("intro","outro"):
                if bar % 2 == 0:
                    for beat,pitch,duration in HOOK[0][:3]:
                        add("hook",beat+.5,duration,pitch,65 if section=="intro" else 56)
                if section == "outro" and bar == 3:
                    add("prism",0,1,69,55)
            elif section == "three_beat_turn":
                for beat,pitch,duration in HOOK[bar % 4]:
                    add("hook",beat*.75,duration*.62,pitch-12,85)
                add("prism",1.5,.3,chord[2]+12,69)
            elif lift:
                for offset,pitch in enumerate((69,71,72,76) if bar < 3 else (76,77,79,80)):
                    add("prism",.25+offset*.75,.42,pitch+(12 if section=="lift_two" and bar==2 else 0),76+offset*5)
            elif section=="undertow":
                if bar in (0, 2, 4, 6):
                    add("hook",.5,2,chord[2]+12,64)
                    add("prism",3,.45,chord[3]+12,64)
            else:
                for offset,pitch in enumerate((chord[2], chord[1], chord[3])):
                    add("prism",.5+offset, .35, pitch + (12 if offset==2 else 0), 72-offset*4)
                if bar % 4 == 3:
                    add("hook",2.5,.75,71 if verse else 76,77)

            drums = chorus or verse or lift or section in ("post_hook","three_beat_turn")
            if drums:
                kicks = ([0, 1.5, 2.5, 3.25] if bar%2 else [0,1.5,2.75]) if chorus else [0,2]
                if section=="three_beat_turn":
                    kicks = [0, 1.75] if bar%2 else [0]
                if section=="verse_two" and bar%2:
                    kicks = [0,.75,2.5]
                cutoff = beats - .75 if lift and bar==count-1 else beats
                for idx, beat_at in enumerate(kicks):
                    if beat_at >= cutoff:
                        continue
                    add("kick",beat_at,.65,60,112 if chorus and idx==0 else 95)
                    next_kick = kicks[idx+1] if idx+1 < len(kicks) else cutoff
                    length = min(1.15 if chorus else 1.5, next_kick-beat_at-.24)
                    if length > .15:
                        note = ROOTS[chord_index] + (12 if chorus and idx==len(kicks)-1 and bar%4==3 else 0)
                        add("bass808",beat_at+.14,length,note,110 if chorus else 90)
                backbeats = (1,3) if chorus else (1,2) if beats==3 else (2,)
                for beat_at in backbeats:
                    if beat_at < cutoff:
                        add("snare",beat_at,.37,60,112 if chorus else 89)
                        if chorus:
                            add("clap",beat_at+.016,.33,60,96)
                for step in range(beats*2):
                    beat_at = step/2
                    if beat_at >= cutoff or (verse and step%2==0):
                        continue
                    add("hat",beat_at + (.032 if step%2 else 0),.21,60,76 if step%2 else 59)
                if chorus and bar%2==0:
                    add("openhat",1.5,.55,60,86)
                if bar % 4 == 3:
                    for step in range(3):
                        add("hat",cutoff-.68+step*.16,.11,60,62+step*13)
                if bar==0 and (chorus or section=="three_beat_turn"):
                    add("crash",0,1.7,60,94)
            if (lift or section in ("intro","three_beat_turn")) and bar==count-1:
                add("riser",beats-2.65,2.4,60,92)
            if section=="undertow" and bar>=4:
                add("bass808",.18,1.6,ROOTS[chord_index],70)
            tick += beats * ppq
    source["length_ticks"] = tick
    result = destination.create(source)
    return {**result, "based_on": original_revision, "sections": source["sections"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-project", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(compose(ProjectService(args.from_project), ProjectService(args.root), args.inputs)))


if __name__ == "__main__":
    main()
