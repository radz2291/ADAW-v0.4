import json,subprocess,urllib.request,hashlib,os
from pathlib import Path
py=r'C:/Users/RZ1/Desktop/RZ-Music/261113-ADAW-v0.4/.venv/Scripts/python.exe'
original=r'C:/Users/RZ1/Desktop/RZ-Music/261113-ADAW-v0.4'
report={}
for name,root,cwd in [('original','.local/glass-current-song',original),('fixture','.local/evaluation/final-04-main/project',str(Path.cwd()))]:
 result=json.loads(subprocess.check_output([py,'-m','app','--root',root,'--timeout','30','project-inspect'],cwd=cwd,encoding='utf8',env={**os.environ,'PYTHONIOENCODING':'utf-8'}))
 assert result['ok'];data=result['data'];report[name]={'revision':data['revision'],'source_sha256':data['source_sha256']}
 if name=='original':
  assert data['revision']=='rev-d5125b81c64cde95cecae7c48b071781152d743ae6a2f6f53782599096cb21e5'
  assert data['source_sha256']=='7d833b0cea0802f5a2d045171f4ddddc69066fc0aab41541b9f09faf4cf291f2'
 else:
  api=json.load(urllib.request.urlopen('http://127.0.0.1:8810/api/v1/state'))['data']['project'];assert data['revision']==api['revision'];assert data['source']==api['source'];report['cli_ui_exact']=True
report['original_wav_sha256']=hashlib.sha256(Path(original+'/.local/delivery/glass-current-song/Glass Current - Full Song.wav').read_bytes()).hexdigest()
assert report['original_wav_sha256']=='ac56815f8cfbf86a8153e8231d110f7a8ebb679d685e367ac8e2638a574e362b'
Path('evidence/evaluation/round-05/integrity.json').write_text(json.dumps(report,indent=2));print(report)

