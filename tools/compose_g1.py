"""Author the original Night Circuit cue as editable inputs, then use the service.

This is a composition recipe, not application behavior or a premastered fixture.
All randomness is seeded; no external samples, previous ADAW code or AI API.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

from app.contracts import canonical, file_hash
from app.project import ProjectService

RATE, PPQ, BPM, BAR = 48000, 960, 144, 3840

BASS = '''declare name "Bass808";
freq = nentry("freq",440,20,20000,1);
gain = nentry("gain",0.5,0,1,0.01);
gate = button("gate");
drive = hslider("drive",2.2,1,5,0.01);
env = gain * en.adsr(0.005,0.16,0.72,0.055,gate);
wave = os.osc(freq) + 0.12*os.osc(2*freq);
process = ma.tanh(drive*wave)*env*0.48 <: _,_;
effect = _,_;
'''
PAD = '''declare name "Atmosphere";
freq = nentry("freq",440,20,20000,1);
gain = nentry("gain",0.5,0,1,0.01);
gate = button("gate");
env = gain * en.adsr(0.18,0.4,0.66,0.8,gate);
left = (os.osc(freq*0.998)+0.3*os.osc(freq*2.002))*env*0.25;
right = (os.osc(freq*1.002)+0.3*os.osc(freq*1.998))*env*0.25;
process = left,right;
effect = _,_;
'''
PLUCK_DELAY = '''declare name "PrismEcho";
left(x) = x*0.8 + (x : de.delay(96000,10000))*0.19 + (x : de.delay(96000,30000))*0.08;
right(x) = x*0.8 + (x : de.delay(96000,15000))*0.19 + (x : de.delay(96000,35000))*0.08;
process = left,right;
'''
DRUM_BUS = '''declare name "DrumBody";
body(x) = ma.tanh(x*1.2)/1.2;
process = body,body;
'''
MASTER = '''declare name "MasterClean";
clean = fi.highpass(2,22);
process = clean,clean;
'''


def make_samples(directory):
    rng = np.random.default_rng(20261113)
    out = {}
    def save(name, audio):
        audio = np.asarray(audio, dtype=np.float64)
        fade = min(96, len(audio)//2)
        audio[:fade] *= np.linspace(0,1,fade)
        audio[-fade:] *= np.linspace(1,0,fade)
        peak = np.max(np.abs(audio))
        audio *= .86/peak
        path = directory/(name+".wav")
        sf.write(path, audio, RATE, subtype="FLOAT")
        out[name] = path
    def noise(seconds, cutoff, kind="highpass"):
        n = round(seconds*RATE)
        x = sosfilt(butter(2, cutoff, btype=kind, fs=RATE, output="sos"), rng.normal(0,1,n))
        return np.arange(n)/RATE,x
    t = np.arange(round(.46*RATE))/RATE
    phase = 2*np.pi*(48*t + 95*.019*(1-np.exp(-t/.019)))
    save("kick", np.sin(phase)*np.exp(-t/0.105) + .065*rng.normal(0,1,len(t))*np.exp(-t/.0025))
    t,x = noise(.24,1400)
    save("snare", x*np.exp(-t/.055)*.65 + np.sin(2*np.pi*185*t)*np.exp(-t/.035)*.45)
    t,x = noise(.25,[1300,7200],"bandpass")
    clap = sum(np.where(t>=d,np.exp(-np.maximum(t-d,0)/.018),0) for d in (0,.011,.024))
    save("clap",x*clap)
    t,x = noise(.10,6800)
    metal = sum(np.sin(2*np.pi*f*t) for f in (7103,8621,10111,12503))/4
    save("hat",(x*.8+metal*.2)*np.exp(-t/.017))
    t,x = noise(.34,6300)
    save("openhat",x*np.exp(-t/.078))
    t,x = noise(1.15,4300)
    save("crash",x*np.exp(-t/.26)*(1+.2*np.sin(2*np.pi*37*t)))
    t,x = noise(1.55,[1000,12000],"bandpass")
    save("riser",x*(t/t[-1])**2*.65 + np.sin(2*np.pi*(500*t+800*t*t))*(t/t[-1])**3*.15)
    return out


def compose(service, directory, timeout):
    directory.mkdir(parents=True, exist_ok=True)
    samples = {name: service.import_file(path,"audio","Original seeded synthesis: tools/compose_g1.py; no third-party samples",timeout)["sha256"] for name,path in make_samples(directory).items()}
    modules = {}
    for name, code in {"bass":BASS,"pad":PAD,"echo":PLUCK_DELAY,"drumbus":DRUM_BUS,"master":MASTER}.items():
        path = directory/(name+".dsp")
        path.write_text(code, encoding="utf-8")
        modules[name] = service.import_file(path,"faust","Original G1 module source; editable in revisioned project",timeout)["sha256"]
    fixtures = json.loads(Path(".local/fixture-plugins.json").read_text(encoding="utf-8"))
    # The fixture manifest is an input, not permission to scan other directories.
    instrument = fixtures["instrument"]["entry"]
    entry = service.authorize_plugin(instrument["path"],"Owner requested online test VSTs, 2026-11-13; exact pinned Dexed fixture")
    service.probe_plugin(entry["registry_id"],RATE,256,timeout)
    state = service.capture_plugin_state(entry["registry_id"],timeout,RATE,256)
    profile = {"id":"demo-wav-v1", "status":"temporary_engineering_profile", "purpose":"Listening/demo WAV; engineering targets selected for review, not owner loudness preference",
        "sample_rate":RATE,"channels":2,"subtype":"PCM_24", "min_lufs":-18,"max_lufs":-11,
        "max_sample_peak_dbfs":-1,"max_estimated_true_peak_dbfs":-1,"true_peak_margin_db":.25,"max_dc":.001,"dither_seed":261113}
    sections = []
    for name, start, end, mood, swing in [
        ("neon_intro",0,4,"Sparse F-sharp minor, suspended and distant",.56),
        ("first_drop",4,12,"Heavy half-time 808 groove, restrained tension",.56),
        ("fracture",12,20,"Darker syncopation, triplet interruptions",.60),
        ("suspended",20,24,"Drumless airy harmonic opening",.50),
        ("second_drop",24,36,"Brighter upper motif, heavier bass responses",.58),
        ("dissolve",36,44,"Half-time deconstruction into a quiet resolved ending",.54)]:
        sections.append(dict(id=name,start_tick=start*BAR,end_tick=end*BAR,mood=mood,swing=swing))
    source = {"schema":"adaw.arrangement@1","title":"Night Circuit","brief":"Original modern electronic 808 trap; changing structure, swing and moods; listening/demo WAV. Owner request 2026-11-13. No reference or subjective approval supplied.",
        "tempo":BPM,"ppq":PPQ,"sample_rate":RATE,"block_size":256,"length_ticks":44*BAR,
        "tail_frames":80000,"fade_frames":24000,"sections":sections,"tracks":[],
        "buses":[{"id":"drums","gain_db":0,"inserts":[{"module_sha256":modules["drumbus"],"parameters":{}}]},
                 {"id":"music","gain_db":0,"inserts":[]}],
        "master":{"gain_db":-3,"inserts":[{"module_sha256":modules["master"],"parameters":{}}]},"profile":profile}
    tracks = {}
    def track(name,role,kind,bus,gain,pan,instrument,inserts=None,protected=False):
        t = dict(id=name,role=role,kind=kind,bus=bus,gain_db=gain,pan=pan,protected=protected,instrument=instrument,events=[],inserts=inserts or [])
        source["tracks"].append(t)
        tracks[name]=t
    for name,gain,pan in [("kick",-5,0),("snare",-11,0),("clap",-17,.12),("hat",-21,-.25),("openhat",-24,.3),("crash",-25,-.1),("riser",-25,.18)]:
        track(name,"percussion" if name not in ("crash","riser") else "transition","samples","drums",gain,pan,{"asset_sha256":samples[name],"fade_frames":24},protected=name=="snare")
    track("bass808","bass","faust_synth","music",-5,0,{"module_sha256":modules["bass"],"parameters":{},"voices":2,"release_seconds":.07})
    track("haze","harmony_texture","faust_synth","music",-16,0,{"module_sha256":modules["pad"],"parameters":{},"voices":12,"release_seconds":.85})
    track("prism","lead","vst","music",-14,.06,{"registry_id":state["registry_id"],"catalog_sha256":state["catalog_sha256"],"state_sha256":state["state_sha256"],"parameters":{"0":.4}},[{"module_sha256":modules["echo"],"parameters":{}}],True)
    def event(name,tick,duration,note=60,velocity=90):
        tick,duration = round(tick),round(duration)
        if tick >= source["length_ticks"]:
            return
        tracks[name]["events"].append({"id":f"{name}_{len(tracks[name]['events']):04d}","start_tick":tick,
            "duration_ticks":min(duration,source["length_ticks"]-tick),"note":note,"velocity":velocity})
    rng = np.random.default_rng(808144)
    chords = [[54,57,61,68],[50,54,57,61],[57,61,64,68],[52,57,59,66]]
    roots = [30,26,33,28]
    for bar in range(44):
        sec = next(s for s in sections if s["start_tick"] <= bar*BAR < s["end_tick"])
        active = 4 <= bar < 20 or 24 <= bar < 40
        if bar < 42 and bar%2 == 0:
            ci = (bar//2)%4
            for note in chords[ci]:
                event("haze",bar*BAR, int(1.85*BAR),note,56 if active else 73)
        # Original short call/answer motif; omissions leave room around the bass.
        if bar < 43 and (bar%2==0 or 24<=bar<36):
            motif = [73,69,68,66] if bar%4 < 2 else [66,68,61,64]
            for i,beat in enumerate([.5,1.75,2.5,3.25] if bar%2==0 else [.75,2.25]):
                event("prism",bar*BAR+beat*PPQ,PPQ*.28,motif[i]+(12 if 28<=bar<32 else 0),60+(i%2)*12)
        if active:
            kick_beats = [0,1.5,2.75] if bar%2==0 else [0,.75,2.5,3.5]
            if 12<=bar<20:
                kick_beats = [0,1.75,3.0] if bar%2==0 else [.5,2.25,3.5]
            if bar in (11,19,35,39):
                kick_beats = [0,1.5]
            for b in kick_beats:
                event("kick",bar*BAR+b*PPQ,PPQ*1.05,velocity=112 if b==0 else 99)
            event("snare",bar*BAR+2*PPQ,PPQ*.65,velocity=108)
            event("clap",bar*BAR+2*PPQ+14,PPQ*.65,velocity=90)
            if bar%4==3:
                event("snare",bar*BAR+3.65*PPQ,PPQ*.32,velocity=40)
            for step in range(16):
                if bar>=36 and step%2:
                    continue
                if step in (13,15) and bar%4==3:
                    continue
                swing_offset = (sec["swing"]-.5)*PPQ*.5 if step%2 else 0
                event("hat",bar*BAR+step*PPQ/4+swing_offset,PPQ*.23,velocity=int(rng.integers(47,88)))
            if bar%4 in (1,3):
                for j in range(6):
                    event("hat",bar*BAR+3.5*PPQ+j*PPQ/12,PPQ/12,velocity=44+j*7)
            event("openhat",bar*BAR+(1.5 if bar%2==0 else 3.25)*PPQ,PPQ*.7,velocity=65)
            root = roots[(bar//2)%4]
            bass_beats = [(0,1.25),(1.5,.85),(2.75,.65)] if bar%2==0 else [(0,.55),(.75,1.1),(2.5,.65),(3.5,.38)]
            if 12<=bar<20:
                bass_beats = [(.20,1.3),(1.95,.65),(3.2,.55)]  # already separated texture
            for i,(b,dur) in enumerate(bass_beats):
                note = root+(12 if i==len(bass_beats)-1 and bar%4==3 else 0)
                event("bass808",bar*BAR+b*PPQ,dur*PPQ,note,104 if i==0 else 91)
        elif bar in (2,3,40,41):
            for b in (0,1.5,3):
                event("hat",bar*BAR+b*PPQ,PPQ*.23,velocity=48)
            if bar==40:
                event("kick",bar*BAR,PPQ*1.1,velocity=80)
                event("bass808",bar*BAR,PPQ*2.7,30,78)
        if bar in (4,12,24,32,36):
            event("crash",bar*BAR,PPQ*3,velocity=74 if bar!=24 else 92)
        if bar in (3,11,23,31):
            event("riser",bar*BAR+.3*PPQ,PPQ*3.7,velocity=78)
    # Last resolving F# minor chord is shorter, leaving room for the release.
    for note in (54,57,61):
        event("haze",42*BAR,PPQ*3.2,note,58)
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root",required=True)
    parser.add_argument("--inputs",required=True)
    parser.add_argument("--timeout",type=float,required=True)
    args = parser.parse_args()
    service = ProjectService(args.root)
    source = compose(service,Path(args.inputs),args.timeout)
    path = Path(args.inputs)/"arrangement.json"
    path.write_bytes(canonical(source))
    result = service.create(source)
    print(json.dumps({**result,"input_source":str(path.resolve()),"tracks":len(source["tracks"]),"events":sum(len(t["events"]) for t in source["tracks"])}))


if __name__ == "__main__":
    main()
