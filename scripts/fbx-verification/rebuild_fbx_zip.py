"""Rebuild reviewed FBX ZIP bytes from a hash-verified FBX and fixed notices.

Fresh conversion QA is an independent gate and must not overwrite these reviewed
metadata inputs. This script never reads raw executor QA or original metadata.
"""
from pathlib import Path
import argparse,hashlib,io,json,re,zipfile

def digest(data):return hashlib.sha256(data).hexdigest()
def rebuild(metadata_dir,fbx):
 m=Path(metadata_dir);manifest=json.loads((m/'package-inputs.json').read_text());model=manifest['id'];assert re.fullmatch('[a-z0-9-]+',model);assert set(manifest['metadataFiles'])=={'README.md','asset.json','CONVERSION.json','CONVERSION_NOTES.md','LICENSE.txt','ATTRIBUTION.txt','FILES.sha256'};b=Path(fbx).read_bytes();assert digest(b)==manifest['fbxSha256']
 entries={model+'/'+model+'.fbx':b}
 for name,proof in manifest['metadataFiles'].items():
  assert Path(name).name==name and name!='package-inputs.json'
  data=(m/name).read_bytes();assert len(data)==proof['bytes'] and digest(data)==proof['sha256'];entries[model+'/'+name]=data
 stream=io.BytesIO()
 with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(entries.items()):
   i=zipfile.ZipInfo(name,date_time=(2026,10,15,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o644<<16;i.create_system=3;z.writestr(i,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
 blob=stream.getvalue();assert digest(blob)==manifest['archiveSha256'],'Archive byte hash differs from reviewed release candidate'
 return blob
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--metadata-dir',required=True);p.add_argument('--fbx',required=True);p.add_argument('--out',required=True);a=p.parse_args();blob=rebuild(a.metadata_dir,a.fbx);out=Path(a.out)
 if out.exists():assert out.read_bytes()==blob,'Never overwrite a different archive'
 else:out.write_bytes(blob)
 print(json.dumps({'archive':out.name,'bytes':len(blob),'sha256':digest(blob),'matchesReviewedArchive':True}))
