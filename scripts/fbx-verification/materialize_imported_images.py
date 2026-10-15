"""Evidence wrapper: materialize actual imported packed images after frozen QA.

It does not modify the converter, FBX, report, pixels, or shader connections.
Materialized bytes come from the clean FBX import's Blender packed images,
not the source GLB or a separate FBX parser.
"""
from pathlib import Path
import sys,runpy,json,hashlib
import bpy
if not __debug__:raise RuntimeError('Image evidence wrapper requires enabled assertions')
idx=sys.argv.index('--converter-script');converter=Path(sys.argv[idx+1]).resolve();del sys.argv[idx:idx+2]
runpy.run_path(str(converter),run_name='__main__')
out=Path(sys.argv[sys.argv.index('--out')+1]).resolve();clean=out/'clean-reimport';q=json.loads((out/'roundtrip-report.json').read_text());records=[];seen=set()
for material in q['after']['materials'].values():
 for rec in material['images']:
  path=Path(rec['filepath']);assert path.is_absolute() and path.resolve().is_relative_to(clean.resolve())
  assert not any(parent.is_symlink() for parent in [path,*path.parents] if parent==clean or clean in parent.parents), 'Symlink in materialization path'
  image=bpy.data.images[rec['name']];assert image.packed_file is not None
  assert Path(bpy.path.abspath(image.filepath)).resolve()==path.resolve()
  data=bytes(image.packed_file.data);digest=hashlib.sha256(data).hexdigest();relative=path.relative_to(clean).as_posix()
  embedded=next(e for e in q['container']['embeddedImages'] if e['relativeFilename']==relative)
  assert len(data)==embedded['embeddedBytes'] and digest==embedded['sha256']
  if str(path) in seen:continue
  seen.add(str(path))
  path.parent.mkdir(parents=True,exist_ok=True)
  if path.exists():assert path.read_bytes()==data
  else:
   with path.open('xb') as output:output.write(data)
  records.append({'relativePath':relative,'bytes':len(data),'sha256':digest,'source':'actual-clean-import-bpy-packed-image'})
(out/'materialized-imported-images.json').write_text(json.dumps({'images':records,'count':len(records),'noPixelReencoding':True,'importerPackedBytesMaterializedByValidationWrapper':True,'wrapperSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
print('IMPORTED_PACKED_IMAGE_EVIDENCE '+json.dumps({'count':len(records),'bytes':sum(x['bytes'] for x in records)}),flush=True)
