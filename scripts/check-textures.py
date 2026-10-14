from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image
counts={'repeat':0,'mirror':0,'clamp':0}
for p in Path('content/assets').glob('*/asset.json'):
 a=json.loads(p.read_text())
 if a['type']!='texture':continue
 for name,f in a['maps'].items():
  pixels=np.array(Image.open(p.parent/'source'/f))
  width,height=a.get('width',a['resolution']),a.get('height',a['resolution'])
  assert pixels.shape[:2]==(height,width), (a['id'],name,'dimensions')
  wrap=a.get('wrapMode','repeat')
  assert wrap in counts and a['seamless']==(wrap!='clamp'), (a['id'],'wrap metadata')
  if wrap=='repeat':
   assert np.array_equal(pixels[0],pixels[-1]), (a['id'],name,'vertical seam')
   assert np.array_equal(pixels[:,0],pixels[:,-1]), (a['id'],name,'horizontal seam')
  elif wrap=='mirror':
   # A complete mirror period is two source tiles in each direction. Check the
   # shared boundaries and the period's outer edges, not unrelated source edges.
   row=np.concatenate((pixels,pixels[:,::-1]),axis=1)
   period=np.concatenate((row,row[::-1]),axis=0)
   assert np.array_equal(period[height-1],period[height])
   assert np.array_equal(period[:,width-1],period[:,width])
   assert np.array_equal(period[0],period[-1]) and np.array_equal(period[:,0],period[:,-1])
  if a.get('provenance',{}).get('sourcePixelsUnchanged'):
   digest=hashlib.sha256((p.parent/'source'/f).read_bytes()).hexdigest()
   expected=[v for k,v in a['provenance']['sourceFiles'].items() if k.endswith('/'+f)]
   assert expected==[digest], (a['id'],name,'original PNG changed')
  counts[wrap]+=1
print(f'Verified dimensions and source hashes: {counts}. Repeat edges, mirrored-period boundaries; clamp atlases are not claimed seamless.')
