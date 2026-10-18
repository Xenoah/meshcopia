"""Inspect original/revised imports without touching any published source."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess,sys
from audit_mesh import STARTERS
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'.cache/asset-revision-qa';OUT=ROOT/'test-results/asset-revisions/imports';OUT.mkdir(parents=True,exist_ok=True)
tasks=[]
for identity in STARTERS+['city-front-loading-washing-machine']:
    meta=json.loads((ROOT/f'content/assets/{identity}/asset.json').read_text())
    tasks.append((identity+'-original-glb',ROOT/f'content/assets/{identity}/source'/meta['preview'],None))
    fbx=BASE/'original-fbx-attempt2'/identity/(identity+'.fbx') if identity in STARTERS else BASE/'washer/conversion'/(identity+'.fbx')
    tasks.append((identity+'-original-fbx',fbx,None))
    if identity not in STARTERS:
        expected=next(r for r in json.loads((ROOT/'docs/cohorts/new251/expected.json').read_text())['models'] if r['id']==identity)
        assert fbx.stat().st_size==expected['fbx']['bytes'] and hashlib.sha256(fbx.read_bytes()).hexdigest()==expected['fbx']['sha256']
for folder in sorted((ROOT/'asset-revisions/repair-appliances-v1').iterdir()):
    if not (folder/'asset.json').is_file():continue
    meta=json.loads((folder/'asset.json').read_text());identity=meta['id']
    production=folder/'production'/(identity+'.blend') if identity in STARTERS and '--save-production' in sys.argv else None
    tasks.append((identity+'-fixed-glb',folder/'source'/meta['preview'],production))
    tasks.append((identity+'-fixed-fbx',BASE/'candidate-final'/identity/'conversion'/(identity+'.fbx'),None))
def inspect(task):
    name,source,production=task;command=['blender','-b','--factory-startup','--python-exit-code','1','-t','2','--python',str(ROOT/'scripts/asset-revisions/audit_import.py'),'--','--source',str(source),'--out',str(OUT/(name+'.json'))]
    if production:command+=['--save-production',str(production)]
    result=subprocess.run(command,env={**os.environ,'BLENDER_USER_CONFIG':str(BASE/'blender-config')},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (OUT/(name+'.log')).write_text(result.stdout);assert result.returncode==0,f'{name}: inspect log'
    data=json.loads((OUT/(name+'.json')).read_text());parts=data['parts'];components=[c for p in parts for c in p['components']]
    summary={'name':name,'triangles':data['triangles'],'dimensions':data['dimensionsMetersYUp'],'inward':sum(c['orientation']=='inward' for c in components),'open':sum(not c['closedOriented'] for c in components),'negativeTransforms':sum(p['worldDeterminant']<0 for p in parts),'degenerate':sum(p['degenerateFaces'] for p in parts),'minNormalDot':min(p['minStoredNormalDotFaceNormal'] for p in parts)}
    assert summary['negativeTransforms']==0 and summary['degenerate']==0 and summary['minNormalDot']>0
    if '-fixed-' in name:assert summary['inward']==0 and summary['open']==0,summary
    print(json.dumps(summary),flush=True);return summary
with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(inspect,tasks))
(OUT/'summary.json').write_text(json.dumps(results,indent=2)+'\n')
