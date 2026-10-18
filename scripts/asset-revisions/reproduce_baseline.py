"""Reproduce the eight immutable published FBXs before diagnosing their winding."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from audit_mesh import STARTERS

p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.repo.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
expected={r['id']:r for r in json.loads((root/'docs/fbx-minimal-verification/expected137.json').read_text())['models']}
runtime=json.loads((root/'docs/fbx-minimal-verification/runtime.json').read_text())
for name,digest in runtime['recipe'].items():assert hashlib.sha256((root/'scripts/fbx-verification'/name).read_bytes()).hexdigest()==digest
env={**os.environ,'PYTHONHASHSEED':'0','NPY_DISABLE_CPU_FEATURES':'AVX2,FMA3,AVX512F,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL','BLENDER_USER_CONFIG':str(out/'blender-config')}
def run(identity):
    row=expected[identity];source=root/f'content/assets/{identity}/source/{identity}.glb';target=out/identity
    command=['blender','-b','--factory-startup','--python-use-system-env','--python-exit-code','1','-t','2','--python',str(root/'scripts/fbx-verification/materialize_imported_images.py'),'--','--converter-script',str(root/'scripts/fbx-verification/convert_and_audit_fbx.py'),'--source',str(source),'--out',str(target),'--expected-sha256',row['sourceGlbSha256'],'--unique-image-paths','--normalize-materials','--deterministic']
    completed=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(identity+'.log')).write_text(completed.stdout)
    if completed.returncode:raise RuntimeError(f'{identity}: Blender failed; see {out/(identity+".log")}')
    payload=(target/(identity+'.fbx')).read_bytes();digest=hashlib.sha256(payload).hexdigest();assert len(payload)==row['fbxBytes'] and digest==row['fbxSha256'],f'Published FBX reproduction differs: {identity}'
    print(identity,'matches immutable published FBX',flush=True)
    return {'id':identity,'bytes':len(payload),'sha256':digest,'matchesPublishedExpected':True}
with ThreadPoolExecutor(max_workers=2) as pool:records=list(pool.map(run,STARTERS))
(out/'reproduction.json').write_text(json.dumps({'scope':'exact deterministic reproduction, not a fresh anonymous Release download','records':records},indent=2)+'\n')
