from pathlib import Path
import json,zipfile,hashlib,shutil
root=Path('dist');out=Path('release')
config=json.loads(Path('.release.json').read_text());version=config['version'];catalog=json.loads((root/'api/catalog.json').read_text())
assert catalog['schemaVersion']=='3.0.0'
assert not list((root/'assets').rglob('*.zip')), 'Retired ZIP copied into site'
assert not out.is_symlink(), 'Generated release directory must not be a symlink'
if out.exists():shutil.rmtree(out)  # Generated local output only, never a GitHub Release.
out.mkdir()
def archive(name,items):
 with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for source,target in sorted(items,key=lambda p:p[1]):
   info=zipfile.ZipInfo(target,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,source.read_bytes())
archive(f'meshcopia-{version}-site.zip',[(p,str(p.relative_to(root))) for p in root.rglob('*') if p.is_file()])
# Consumer ZIPs live at their verified immutable Release URLs. The browser
# builds selected collections. Do not create empty/legacy ZIP-of-ZIP collections
# when the site no longer contains full/models archives. Existing Releases stay.
(out/'catalog.json').write_bytes((root/'api/catalog.json').read_bytes())
lines=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS']
(out/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
