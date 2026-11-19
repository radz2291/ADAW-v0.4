"""Original plucked-string listening fixture through the approved installed VST.

Not a finished song or an owner listening verdict. All media/state/logs remain
under a fresh .local/guitar-rig folder; vendor binaries remain external.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil

import numpy as np
import soundfile as sf

from app.contracts import canonical, file_hash
from app.errors import AdawError
from app.project import ProjectService
from tools.fixtures import graph, node, vst_node


def run(folder, plugin, approval):
    folder = Path(folder).resolve()
    local = Path(__file__).resolve().parents[1] / '.local/guitar-rig'
    if not folder.is_relative_to(local):
        raise ValueError('Use a fresh folder under .local/guitar-rig')
    folder.mkdir(parents=True, exist_ok=False)
    rate = 48000
    audio = np.zeros(rate * 8, dtype=np.float32)
    # Temporary original listening fixture: 100 BPM eighth notes, E-minor riff.
    pitches = [40, 47, 52, 55, 40, 47, 54, 52, 43, 50, 55, 59, 45, 52, 57, 59]
    t = np.arange(round(rate * .75)) / rate
    for i, pitch in enumerate(pitches):
        freq = 440 * 2 ** ((pitch-69)/12)
        pluck = sum(np.sin(2*np.pi*freq*h*t) * np.exp(-t*(3+h*1.3))/h**1.4 for h in range(1, 12))
        pluck *= .12 * np.minimum(1, t/.003)
        start = round(i*.3*rate)
        audio[start:start+len(pluck)] += pluck.astype(np.float32)
    sf.write(folder/'original-plucks.wav', audio, rate, subtype='FLOAT')
    service = ProjectService(folder/'project')
    asset = service.import_file(folder/'original-plucks.wav', 'audio', 'Original synthesized plucked-string fixture', 60)
    identity = service.authorize_plugin(plugin, approval)
    profile = service.configure_plugin_host(identity['registry_id'], 'windows-stereo-zero-aux-isolated-v1', approval)
    probe = service.probe_plugin(identity['registry_id'], rate, 256, 60)
    binding = next(str(p['index']) for p in probe['data']['parameters'] if p['name']=='Rack Master Volume')
    source = node('plucks', 'samples', [], {'events': [dict(asset_sha256=asset['sha256'], start_frame=0,
                  duration_frames=len(audio), gain=1, pan=0, fade_frames=0)]})
    dry_graph = graph([source], seconds=8)
    dry_graph['schema'] = 'adaw.graph@2'
    wet_graph = deepcopy(dry_graph)
    wet_graph['nodes'].append(vst_node('guitar_rig', identity['registry_id'], ['plucks'], parameters={binding:.7}))
    wet_graph['output'] = 'guitar_rig'
    report = {'profile':profile, 'plugin':identity, 'parameter':{'binding':binding,'name':'Rack Master Volume'},
              'listening':'NOT_EVALUATED', 'fixture':'Original synthesized strings; not recorded guitar', 'renders':{}}
    for name, config in [('dry',dry_graph),('guitar-rig',wet_graph),('quieter',deepcopy(wet_graph))]:
        if name=='quieter': config['nodes'][-1]['config']['parameters'][binding]=.4
        (folder/(name+'-graph.json')).write_bytes(canonical(config))
        result = service.render(config, 60, benchmark=False)
        shutil.copyfile(result['audio_path'], folder/(name+'.wav'))
        samples, _ = sf.read(folder/(name+'.wav'), always_2d=True)
        report['renders'][name] = {'result':result, 'rms':float(np.sqrt(np.mean(samples**2))),
                                  'sha256':file_hash(folder/(name+'.wav'))}
        (folder/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    assert report['renders']['guitar-rig']['rms']>0
    assert report['renders']['quieter']['rms']<report['renders']['guitar-rig']['rms']*.5
    state_graph = deepcopy(wet_graph)
    state_graph['nodes'][-1]['config']['state_sha256'] = report['renders']['guitar-rig']['result']['data']['nodes']['guitar_rig']['state_sha256']
    try:
        report['state_restore']={'status':'PASS','result':service.render(state_graph,60,benchmark=False)}
    except AdawError as exc:
        report['state_restore']={'status':'FAIL','code':exc.code,'message':str(exc),'details':exc.details}
    report['parameter_audio_change']='PASS'
    (folder/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'audio':str(folder/'guitar-rig.wav'),'parameter_audio_change':'PASS','state_restore':report['state_restore']['status']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',required=True)
    parser.add_argument('--plugin',required=True)
    parser.add_argument('--approval',required=True)
    args=parser.parse_args()
    run(args.folder,args.plugin,args.approval)
