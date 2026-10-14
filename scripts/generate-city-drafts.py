"""Generate original city assets as drafts, never catalog-public automatically.
The marker is a bounded explicit roster. Rebuilt bytes require fresh visual QA.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
marker=ROOT/'.generate-city-drafts.json'
plan=json.loads(marker.read_text())
stage=ROOT/'.cache/city-drafts'
stage.mkdir(parents=True,exist_ok=False)
qa=ROOT/'docs/city-qa'/plan['batch']
qa.mkdir(parents=True,exist_ok=False)
manifest=[]
for lane,ids in plan['lanes'].items():
 assert lane in ('access','civic','infrastructure')
 out=stage/lane
 for slug in ids:
  assert slug.startswith('city-') and '/' not in slug and '..' not in slug
  assert not (ROOT/'content/assets'/slug).exists(),slug+' already exists'
  subprocess.run([sys.executable,str(ROOT/'scripts/city'/f'{lane}.py'),'--output',str(out),'--only',slug],check=True,cwd=ROOT)
  folder=out/slug
  metadata=json.loads((folder/'asset.json').read_text())
  assert metadata['id']==slug and metadata['status']=='draft'
  glb=folder/'source'/metadata['preview']
  assert hashlib.sha256(glb.read_bytes()).hexdigest()==metadata['provenance']['sourceSha256']
  subprocess.run(['npm','run','new:asset','--',slug,'model'],check=True,cwd=ROOT)
  shutil.copytree(folder,ROOT/'_inbox'/slug,dirs_exist_ok=True)
  for f in sorted((out/'_qa').glob(slug+'*')):
   if f.is_file():shutil.copyfile(f,qa/f.name)
  manifest.append({'id':slug,'lane':lane,'triangles':metadata['triangles'],'dimensions':metadata['dimensions'],'glbSha256':metadata['provenance']['sourceSha256'],'previewSha256':hashlib.sha256((folder/'preview.png').read_bytes()).hexdigest(),'status':'draft'})
 for side in ('front','back'):
  sheet=Image.new('RGB',(1200,840),(35,39,42));draw=ImageDraw.Draw(sheet)
  for i,slug in enumerate(ids):
   path=out/slug/'preview.png' if side=='front' else out/'_qa'/f'{slug}-back.png'
   image=Image.open(path).convert('RGB');image.thumbnail((400,400))
   x=(i%3)*400;y=(i//3)*420
   sheet.paste(image,(x+(400-image.width)//2,y+(400-image.height)//2))
   draw.text((x+8,y+402),slug,fill='white')
  sheet.save(qa/f'{lane}-{side}.png')
(qa/'manifest.json').write_text(json.dumps({'batch':plan['batch'],'state':'draft outputs; visual review required','assets':manifest},indent=2)+'\n')
assert len(manifest)==sum(map(len,plan['lanes'].values()))
marker.unlink()
print('CITY_DRAFT_GENERATION '+json.dumps(manifest),flush=True)
