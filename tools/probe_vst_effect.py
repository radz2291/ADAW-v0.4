"""Bounded installed-effect check; all runtime files stay in one fresh .local folder.

Uses the existing service and isolated worker. Does not alter song projects,
install plugins, open editors, select presets, or claim full compatibility.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from app.contracts import file_hash
from app.errors import AdawError
from app.service import Service
from tools.fixtures import graph, tone, vst_node


def run(folder, plugin, approval, timeout):
    folder = Path(folder).resolve()
    local = Path(__file__).resolve().parents[1] / '.local'
    if not folder.is_relative_to(local):
        raise ValueError('Use a fresh folder under this checkout\'s .local directory')
    folder.mkdir(parents=True, exist_ok=False)
    service = Service(folder / 'project')
    report = {'schema': 'adaw.installed-effect-probe@1',
              'time_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'Stereo default-state load/render and crash recovery only',
              'listening': 'NOT_EVALUATED', 'checks': []}

    def save():
        (folder / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')

    report['environment'] = service.run_worker({'operation': 'doctor'}, timeout)
    baseline_graph = graph([tone('source', 220, .1)], seconds=2)
    baseline = service.render(baseline_graph, timeout, commit=True,
                              base_revision=service.inspect()['head'], benchmark=False)
    shutil.copyfile(baseline['audio_path'], folder / 'dry.wav')
    report['baseline'] = baseline
    before = service.inspect()
    report['plugin'] = service.authorize_plugin(plugin, approval)
    save()
    try:
        probe = service.probe_plugin(report['plugin']['registry_id'], 48000, 256, timeout)
        report['probe'] = probe
        report['checks'].append({'id': 'load', 'status': 'PASS'})
        if (probe['data']['inputs'], probe['data']['outputs']) != (2, 2):
            report['checks'].append({'id': 'stereo_render', 'status': 'NOT_EVALUATED',
                                     'reason': 'Discovered I/O does not match the explicit stereo fixture'})
        else:
            wet_graph = graph([tone('source', 220, .1),
                               vst_node('effect', report['plugin']['registry_id'], ['source'])], seconds=2)
            report['render'] = service.render(wet_graph, timeout, benchmark=False)
            shutil.copyfile(report['render']['audio_path'], folder / 'wet.wav')
            report['checks'].append({'id': 'stereo_render', 'status': 'PASS'})
            # A default rack may pass audio unchanged; rendering alone proves no effect.
            import numpy as np
            import soundfile as sf
            dry, _ = sf.read(folder / 'dry.wav', always_2d=True)
            wet, _ = sf.read(folder / 'wet.wav', always_2d=True)
            report['default_state_peak_difference'] = float(np.max(np.abs(wet-dry)))
    except AdawError as exc:
        report['failure'] = {'code': exc.code, 'message': str(exc), 'details': exc.details}
        report['checks'].append({'id': 'plugin_load_or_render', 'status': 'FAIL', 'code': exc.code})
    finally:
        after = Service(folder / 'project').inspect()
        report['preservation'] = {'before': before, 'after': after,
                                  'baseline_sha256': file_hash(folder / 'dry.wav')}
        preserved = before == after and file_hash(service.content / before['last_playable']) == report['preservation']['baseline_sha256']
        report['checks'].append({'id': 'last_playable_preserved', 'status': 'PASS' if preserved else 'FAIL'})
        report['recovery'] = service.run_worker({'operation': 'doctor'}, timeout)
        save()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', required=True, help='New directory under .local')
    parser.add_argument('--plugin', required=True, help='Exact owner-approved plugin path')
    parser.add_argument('--approval', required=True)
    parser.add_argument('--timeout', type=float, default=60)
    args = parser.parse_args()
    result = run(args.folder, args.plugin, args.approval, args.timeout)
    print(json.dumps({'checks': result['checks'], 'report': str(Path(args.folder).resolve() / 'report.json')}))
    return int(any(c['status'] == 'FAIL' for c in result['checks']))


if __name__ == '__main__':
    raise SystemExit(main())
