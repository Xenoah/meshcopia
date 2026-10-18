"""Reproduce and hash-check the already published washing-machine FBX."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[2];ID='city-front-loading-washing-machine';out=ROOT/'.cache/asset-revision-qa/washer';out.mkdir(parents=True,exist_ok=False)
expected=next(r for r in json.loads((ROOT/'docs/cohorts/new251/expected.json').read_text())['models'] if r['id']==ID)
env={**os.environ,'PYTHONHASHSEED':'0','NPY_DISABLE_CPU_FEATURES':'AVX2,FMA3,AVX512F,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL','BLENDER_USER_CONFIG':str(out/'blender-config')}
command=['blender','-b','--factory-startup','--python-use-system-env','--python-exit-code','1','-t','2','--python',str(ROOT/'scripts/fbx-verification/materialize_imported_images.py'),'--','--converter-script',str(ROOT/'scripts/fbx-verification/convert_and_audit_fbx.py'),'--source',str(ROOT/f'content/assets/{ID}/source/{ID}.glb'),'--out',str(out/'conversion'),'--expected-sha256',expected['sourceGlbSha256'],'--unique-image-paths','--normalize-materials','--deterministic']
result=subprocess.run(command,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(out/'conversion.log').write_text(result.stdout);assert result.returncode==0
fbx=(out/'conversion'/(ID+'.fbx')).read_bytes();assert len(fbx)==expected['fbx']['bytes'] and hashlib.sha256(fbx).hexdigest()==expected['fbx']['sha256']
print('Existing washer FBX matches the immutable published hash:',expected['fbx']['sha256'])
