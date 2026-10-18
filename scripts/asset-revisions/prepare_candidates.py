"""Create unpublished consumer packages with clean-import evidence, never a Release.

Use the frozen converter as-is. Temporary source basenames provide stable asset
IDs; exact copied GLB bytes are checked against the staged versioned source.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from minimal_packages import make_plan, package
from minimal_notices import baseline_notices, make_notice

p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
env={**os.environ,'PYTHONHASHSEED':'0','NPY_DISABLE_CPU_FEATURES':'AVX2,FMA3,AVX512F,AVX512_SKX,AVX512_CLX,AVX512_CNL,AVX512_ICL','BLENDER_USER_CONFIG':str(out/'blender-config')}
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for folder in sorted((ROOT/'asset-revisions/repair-appliances-v1').iterdir()):
    if not folder.is_dir() or not (folder/'asset.json').exists():continue
    meta=json.loads((folder/'asset.json').read_text());identity=meta['id'];target=out/identity;target.mkdir()
    source=folder/'source'/meta['preview'];copied=target/(identity+'.glb');shutil.copyfile(source,copied)
    assert digest(source)==digest(copied)
    conversion=target/'conversion'
    command=['blender','-b','--factory-startup','--python-use-system-env','--python-exit-code','1','-t','2','--python',str(ROOT/'scripts/fbx-verification/materialize_imported_images.py'),'--','--converter-script',str(ROOT/'scripts/fbx-verification/convert_and_audit_fbx.py'),'--source',str(copied),'--out',str(conversion),'--expected-sha256',digest(source),'--unique-image-paths','--normalize-materials','--deterministic']
    result=subprocess.run(command,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (target/'conversion.log').write_text(result.stdout)
    assert result.returncode==0,f'Clean FBX conversion failed: {identity}; inspect {target}/conversion.log'
    report_path=conversion/'roundtrip-report.json';report=json.loads(report_path.read_text());assert report['passed']
    recipe=hashlib.sha256(json.dumps(report['recipeSha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    license_text,credit=baseline_notices(meta)
    fbx_credit='Changes: Converted unchanged source GLB geometry to FBX, with documented compatible material/texture derivatives.\n'
    notice=make_notice(meta,license_text,credit,fbx_attribution=fbx_credit);notice_path=target/'LICENSE.txt';notice_path.write_text(notice)
    fbx=conversion/(identity+'.fbx')
    plan=make_plan(folder,notice_path,fbx_path=fbx,fbx_sha256=digest(fbx),pipeline_sha256=recipe,fbx_report=report_path)
    archive=target/plan['filename'];receipt=target/'package-receipt.json'
    package(plan,output=archive,receipt_path=receipt)
    records.append({'id':identity,'assetVersion':meta['version'],'metadataSha256':digest(folder/'asset.json'),'sourceGlbSha256':digest(source),'fbx':str(fbx.relative_to(out)),'fbxBytes':fbx.stat().st_size,'fbxSha256':digest(fbx),'archive':str(archive.relative_to(out)),'archiveBytes':archive.stat().st_size,'archiveSha256':digest(archive),'notice':notice,'noticeBytes':len(notice.encode()),'noticeSha256':digest(notice_path),'roundtripReport':str(report_path.relative_to(out)),'roundtripReportSha256':digest(report_path),'packageReceipt':str(receipt.relative_to(out))})
    print(identity,'clean-import and minimal package passed',fbx.stat().st_size,archive.stat().st_size,flush=True)
(out/'candidate-packages.json').write_text(json.dumps({'schemaVersion':1,'publicationState':'unpublished-candidate','scope':'Local conversion and exact archive verification; no anonymous Release publication claim','records':records},ensure_ascii=False,indent=2)+'\n')
