"""Fresh anonymous, same-job activation of three approved immutable revisions."""
from publication import *
def prepare():
    config=json.loads((ROOT/'docs/asset-revision-activation.json').read_text())
    assert config['releaseTag']==TAG and config['reviewCommit']==REVIEW and config['reviewRunId']==RUN
    raw,lock=reviewed_lock();assert sha(raw)==config['lockSha256'];verify_review()
    evidence_bytes=(ROOT/'docs/asset-revisions/publication.json').read_bytes();assert sha(evidence_bytes)==config['evidenceSha256']
    evidence=json.loads(evidence_bytes);assert evidence['state']=='anonymous-byte-readback-passed' and evidence['releaseId']==config['releaseId']
    transport=api('/actions/runs/'+str(evidence['transportRunId']))
    assert transport['head_sha']==evidence['transportCommit'] and transport['conclusion']=='success' and transport['path']=='.github/workflows/release-asset-revisions.yml'
    inventory_bytes=request(f'https://github.com/{REPO}/releases/download/{TAG}/revision-inventory.json')
    assert sha(inventory_bytes)==config['inventorySha256'] and inventory_bytes==(ROOT/'docs/asset-revisions/revision-inventory.json').read_bytes()
    inv=json.loads(inventory_bytes);assert inv['lockSha256']==sha(raw) and inv['reviewCommit']==REVIEW and inv['reviewRunId']==RUN
    assert [r['id'] for r in inv['records']]==[r['id'] for r in lock['records']]
    files={'revision-inventory.json':inventory_bytes};projection=[]
    cache=ROOT/'.cache/fbx-delivery-payloads';cache.mkdir(parents=True,exist_ok=True)
    for r,expected in zip(inv['records'],lock['records']):
        for k,v in expected.items():
            if k!='retainedFiles':assert r[k]==v
        identity=r['id'];version=r['assetVersion'];root=f'https://github.com/{REPO}/releases/download/{TAG}/'
        direct=identity+'.fbx';archive=f'{identity}-{version}-fbx-minimal-1.0.0.zip'
        fbx=request(root+direct);packed=request(root+archive);notice=r['notice'].encode()
        assert len(fbx)==r['fbxBytes'] and sha(fbx)==r['fbxSha256']
        assert len(packed)==r['archiveBytes'] and sha(packed)==r['archiveSha256']
        assert len(notice)==r['noticeBytes'] and sha(notice)==r['noticeSha256']
        with zipfile.ZipFile(io.BytesIO(packed)) as z:
            assert sorted(z.namelist())==['LICENSE.txt',direct] and z.testzip() is None
            assert z.read('LICENSE.txt')==notice and z.read(direct)==fbx
        files[direct]=fbx;files[archive]=packed;(cache/(sha(fbx)+'.fbx')).write_bytes(fbx)
        sources=[];original=ROOT/'content/assets'/identity
        if original.exists():
            # Bind every preserved legacy source to the exact reviewed revision.
            prefix=f'content/assets/{identity}/'
            paths=subprocess.check_output(['git','ls-tree','-r','--name-only',REVIEW,'--',prefix],cwd=ROOT,text=True).splitlines()
            actual=sorted(p.relative_to(ROOT).as_posix() for p in original.rglob('*') if p.is_file())
            assert actual==sorted(paths)
            for name in paths:assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',REVIEW+':'+name],cwd=ROOT)
        for folder in [original/'source',ROOT/'asset-revisions/repair-appliances-v1'/identity/'source']:
            if folder.exists():
                for p in sorted(folder.rglob('*')):
                    if p.is_file():
                        b=p.read_bytes();sources.append({'name':p.relative_to(folder).as_posix(),'bytes':len(b),'sha256':sha(b)})
        assert len({s['name'] for s in sources})==len(sources)
        projection.append({'id':identity,'assetVersion':version,'format':'FBX','packageVersion':'1.0.0','selfContained':True,'sources':sources,'direct':{'filename':direct,'url':root+direct,'bytes':len(fbx),'sha256':sha(fbx)},'archive':{'filename':archive,'url':root+archive,'bytes':len(packed),'sha256':sha(packed)},'notice':{'filename':'LICENSE.txt','text':r['notice'],'bytes':len(notice),'sha256':sha(notice)},'verification':{'state':'published-verified','releaseTag':TAG},'limitations':['Clean Blender import and actual front-face rendering verified. FBX Phong is not lossless glTF PBR; Unity/Godot, Safari, physics and manufacturing not certified.']})
    release=api('/releases/tags/'+TAG);assert release['id']==config['releaseId']
    fresh=verify_release(release,files)
    for key in fresh:assert fresh[key]==evidence[key],key
    inputs=json.loads(subprocess.check_output(['node','scripts/asset-revisions/activation.mjs','--inputs'],cwd=ROOT))
    receipt={'schemaVersion':1,'createdBy':'same-job-revision-prep/1','head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'execution':{'runId':os.getenv('GITHUB_RUN_ID'),'runAttempt':os.getenv('GITHUB_RUN_ATTEMPT'),'job':os.getenv('GITHUB_JOB')},'releaseId':release['id'],'inventorySha256':sha(inventory_bytes),'projection':projection,'projectionSha256':sha(json.dumps(projection,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),'inputs':[{'path':p,'sha256':sha((ROOT/p).read_bytes())} for p in inputs]}
    (ROOT/'.cache/asset-revision-verified.json').write_bytes(encode(receipt))
    print('REVISION_PREP '+json.dumps({'state':fresh['state'],'releaseId':release['id'],'models':len(projection),'attachments':fresh['attachments']}),flush=True)
if __name__=='__main__':prepare()
