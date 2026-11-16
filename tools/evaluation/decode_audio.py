"""Decode endpoint bytes independently for evaluator signal evidence."""
import hashlib,io,json,sys,urllib.request
import numpy as np
import soundfile as sf
data=urllib.request.urlopen(sys.argv[1]).read()
audio,rate=sf.read(io.BytesIO(data),always_2d=True)
print(json.dumps(dict(sha256=hashlib.sha256(data).hexdigest(),rate=rate,frames=len(audio),rms=np.sqrt(np.mean(audio**2,axis=0)).tolist(),peak=np.max(np.abs(audio),axis=0).tolist())))
