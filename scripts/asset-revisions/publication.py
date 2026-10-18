"""New immutable release transport and anonymous verification; never edit old releases."""
import hashlib, io, json, os, subprocess, sys, time, urllib.request, urllib.error, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REPO='Xenoah/meshcopia'
TAG='cohort-repair-appliances-v1.0.0'
REVIEW='4d537fad080c50ec18f3e515695f4f9f582351c5'
RUN=39129140683
LOCK='asset-revisions/repair-appliances-v1/candidate-lock.json'
API='https://api.github.com/repos/'+REPO
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def request(url, data=None, method=None, auth=False, content='application/json'):
    headers={'User-Agent':'Meshcopia-revision-publication','Accept':'application/vnd.github+json'}
    if auth:headers['Authorization']='Bearer '+os.environ['GH_TOKEN']
    if data is not None:headers['Content-Type']=content
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,data=data,method=method,headers=headers),timeout=120) as r:return r.read()
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt==3:raise
            time.sleep(5*(attempt+1))
def api(path,**kw):return json.loads(request(API+path,**kw))
def reviewed_lock():
    raw=(ROOT/LOCK).read_bytes()
    assert raw==subprocess.check_output(['git','show',REVIEW+':'+LOCK],cwd=ROOT),'Reviewed lock changed'
    lock=json.loads(raw)
    for r in lock['records']:
        folder=ROOT/'asset-revisions/repair-appliances-v1'/r['id']
        paths=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.suffix!='.blend1')
        assert paths==sorted(x['path'] for x in r['retainedFiles'])
        for f in r['retainedFiles']:
            path=folder/f['path'];assert not path.is_symlink()
            data=path.read_bytes();assert len(data)==f['bytes'] and sha(data)==f['sha256']
    return raw,lock

def verify_review():
    run=api('/actions/runs/'+str(RUN))
    assert run['head_sha']==REVIEW and run['conclusion']=='success' and run['status']=='completed'
    assert run['path']=='.github/workflows/verify-asset-revisions.yml'
    jobs=api('/actions/runs/'+str(RUN)+'/jobs?per_page=100')['jobs']
    assert {(j['name'],j['conclusion']) for j in jobs}=={('verify','success'),('browser','success')}
    return {'commit':REVIEW,'runId':RUN,'runAttempt':run['run_attempt']}

def make_inventory(candidate):
    raw,lock=reviewed_lock();records=[];files={}
    manifest=json.loads((candidate/'candidate-packages.json').read_text())
    assert sorted(r['id'] for r in manifest['records'])==sorted(r['id'] for r in lock['records'])
    for r in manifest['records']:
        expected=next(x for x in lock['records'] if x['id']==r['id'])
        for k,v in expected.items():
            if k!='retainedFiles':assert r[k]==v,k
        fbx=(candidate/r['fbx']).read_bytes();archive=(candidate/r['archive']).read_bytes();notice=r['notice'].encode()
        assert len(fbx)==r['fbxBytes'] and sha(fbx)==r['fbxSha256']
        assert len(archive)==r['archiveBytes'] and sha(archive)==r['archiveSha256']
        assert len(notice)==r['noticeBytes'] and sha(notice)==r['noticeSha256']
        name=Path(r['archive']).name;assert name==f"{r['id']}-{r['assetVersion']}-fbx-minimal-1.0.0.zip"
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            assert sorted(z.namelist())==['LICENSE.txt',r['id']+'.fbx'] and z.testzip() is None
            assert z.read('LICENSE.txt')==notice and z.read(r['id']+'.fbx')==fbx
        files[r['id']+'.fbx']=fbx;files[name]=archive
        records.append({k:r[k] for k in ('id','assetVersion','metadataSha256','sourceGlbSha256','fbxBytes','fbxSha256','archiveBytes','archiveSha256','notice','noticeBytes','noticeSha256')})
    inventory={'schemaVersion':1,'repository':REPO,'releaseTag':TAG,'reviewCommit':REVIEW,'reviewRunId':RUN,'lockSha256':sha(raw),'records':records}
    files['revision-inventory.json']=encode(inventory)
    return inventory,files

def verify_release(release,files):
    assert release['tag_name']==TAG and not release['draft'] and not release['prerelease']
    ref=api('/git/ref/tags/'+TAG);assert ref['object']['type']=='commit' and ref['object']['sha']==REVIEW
    assets=api('/releases/'+str(release['id'])+'/assets?per_page=100')
    assert sorted(a['name'] for a in assets)==sorted(files),'Unexpected or missing release attachments'
    proof=[]
    for a in assets:
        expected=files[a['name']];assert a['state']=='uploaded' and a['size']==len(expected)
        assert a.get('digest')=='sha256:'+sha(expected),'GitHub attachment digest mismatch'
        assert a['browser_download_url']==f'https://github.com/{REPO}/releases/download/{TAG}/'+a['name']
        actual=request(a['browser_download_url']);assert actual==expected,'Anonymous attachment bytes differ'
        proof.append({'id':a['id'],'name':a['name'],'bytes':len(actual),'sha256':sha(actual)})
    return {'schemaVersion':1,'state':'anonymous-byte-readback-passed','releaseId':release['id'],'releaseTag':TAG,'reviewCommit':REVIEW,'reviewRunId':RUN,'inventorySha256':sha(files['revision-inventory.json']),'attachments':proof}

def publish(candidate):
    verify_review();inventory,files=make_inventory(candidate)
    try:release=api('/releases/tags/'+TAG)
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        # Do not modify a pre-existing draft, tag or release on retries.
        existing=api('/releases?per_page=100',auth=True)
        assert not any(r['tag_name']==TAG for r in existing),'Existing draft requires explicit inspection; no overwrite'
        try:api('/git/ref/tags/'+TAG);raise AssertionError('Pre-existing tag; refusing creation')
        except urllib.error.HTTPError as missing:assert missing.code==404
        release=api('/releases',method='POST',auth=True,data=encode({'tag_name':TAG,'target_commitish':REVIEW,'name':'Starter winding repairs and refrigerator — verified FBX','body':f'Immutable consumer FBX and minimal ZIPs for garden-arch 1.0.2, wayfinding-sign 1.0.2 and household-two-door-refrigerator 1.0.0. CC BY 4.0; each ZIP contains FBX and one LICENSE.txt. Preview GLB, production originals and QA remain in Git and review artifacts. Verified review: https://github.com/{REPO}/actions/runs/{RUN}. Existing washer and all other models are retained. No application-specific Unity/Godot or physical manufacturing certification.','draft':True,'prerelease':False,'make_latest':'false'}))
        for name,data in files.items():
            url=release['upload_url'].split('{')[0]+'?name='+name
            request(url,data=data,method='POST',auth=True,content='application/octet-stream')
        release=api('/releases/'+str(release['id']),method='PATCH',auth=True,data=encode({'draft':False,'make_latest':'false'}))
    proof=verify_release(release,files)
    proof['transportCommit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    proof['transportRunId']=int(os.environ['GITHUB_RUN_ID'])
    (ROOT/'test-results/asset-revisions').mkdir(parents=True,exist_ok=True)
    (ROOT/'test-results/asset-revisions/publication.json').write_bytes(encode(proof))
    print('REVISION_PUBLICATION '+json.dumps(proof),flush=True)
if __name__=='__main__':
    root=Path(sys.argv[1]);candidates=list(root.rglob('candidate-packages.json'));assert len(candidates)==1
    publish(candidates[0].parent)
