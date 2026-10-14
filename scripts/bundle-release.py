from pathlib import Path
import json,zipfile,hashlib
root=Path('dist');out=Path('release');out.mkdir(exist_ok=True)
config=json.loads(Path('.release.json').read_text());version=config['version'];catalog=json.loads((root/'api/catalog.json').read_text())
def archive(name,items):
 with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for source,target in sorted(items,key=lambda p:p[1]):
   info=zipfile.ZipInfo(target,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,source.read_bytes())
archive(f'meshcopia-{version}-site.zip',[(p,str(p.relative_to(root))) for p in root.rglob('*') if p.is_file()])
for kind in ['all','models','textures']:
 selected=[a for a in catalog['assets'] if kind=='all' or a['type']=={'models':'model','textures':'texture'}[kind]]
 items=[]
 for a in selected:
  folder=root/'assets'/a['id']
  # Bundles contain full asset packages with provenance and attribution.
  for p in folder.glob('*.zip'):
   if '-models.zip' not in p.name:items.append((p,p.name))
 for name in ['LICENSE','README.md','THIRD_PARTY_NOTICES.md']:items.append((Path(name),name))
 archive(f'meshcopia-{version}-{kind}.zip',items)
(out/'catalog.json').write_bytes((root/'api/catalog.json').read_bytes())
lines=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
(out/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
