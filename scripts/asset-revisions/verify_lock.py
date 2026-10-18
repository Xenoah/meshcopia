"""Bind reviewed source versions to repeatable consumer FBX/ZIP bytes."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
actual=json.loads((ROOT/'.cache/asset-revision-qa/candidate-final/candidate-packages.json').read_text())
keys=['id','assetVersion','metadataSha256','sourceGlbSha256','fbxBytes','fbxSha256','archiveBytes','archiveSha256','noticeBytes','noticeSha256']
lock={'publicationState':'unpublished-candidate','baseCommit':'fd595dfdc8b17fe515a618bf2f309e9cc61a7491','records':[{k:r[k] for k in keys} for r in actual['records']]}
for record in lock['records']:
    folder=ROOT/'asset-revisions/repair-appliances-v1'/record['id']
    record['retainedFiles']=[{'path':p.relative_to(folder).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix!='.blend1']
target=ROOT/'asset-revisions/repair-appliances-v1/candidate-lock.json'
if '--write' in sys.argv:target.write_text(json.dumps(lock,indent=2)+'\n')
else:assert json.loads(target.read_text())==lock,'Candidate FBX/ZIP/source bytes differ from the reviewed lock'
print('Three unpublished candidate source versions and exact FBX/ZIP hashes verified.')
