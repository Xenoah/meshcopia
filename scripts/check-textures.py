from pathlib import Path
import json
import numpy as np
from PIL import Image
count=0
for p in Path('content/assets').glob('*/asset.json'):
 a=json.loads(p.read_text())
 if a['type']!='texture':continue
 for name,f in a['maps'].items():
  pixels=np.array(Image.open(p.parent/'source'/f))
  assert pixels.shape[:2]==(a['resolution'],a['resolution']), (a['id'],name,'resolution')
  assert np.array_equal(pixels[0],pixels[-1]), (a['id'],name,'vertical seam')
  assert np.array_equal(pixels[:,0],pixels[:,-1]), (a['id'],name,'horizontal seam')
  count+=1
print(f'Verified {count} texture maps: correct dimensions and exact matching opposite edge pixels.')
