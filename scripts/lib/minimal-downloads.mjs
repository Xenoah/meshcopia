import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import path from 'node:path';
import {sha256} from './catalog.mjs';
import {minimalDownloadReadiness} from '../../src/lib/downloads.mjs';

export const minimalActivationPath = 'docs/minimal-activation.json';
export const minimalIdentity = asset => `${asset.id}@${asset.version}`;

export function validateMinimalActivation(value) {
  assert.deepEqual(Object.keys(value).sort(),['activations','repository','schemaVersion']);
  assert.equal(value.schemaVersion,1);assert.equal(value.repository,'Xenoah/meshcopia');
  assert.ok(Array.isArray(value.activations));
  assert.ok(value.activations.length<=1,'Only the reviewed published173 adapter is supported');
  for(const a of value.activations) {
    assert.deepEqual(Object.keys(a).sort(),['cohort','inventorySha256','releaseId','releaseTag','transportEvidenceFile','transportEvidenceSha256','verificationCommit']);
    assert.equal(a.cohort,'published173');assert.equal(a.releaseTag,'minimal-v1.0.0');
    assert.ok(Number.isSafeInteger(a.releaseId)&&a.releaseId>0);
    assert.match(a.verificationCommit,/^[a-f0-9]{40}$/);
    for(const key of ['inventorySha256','transportEvidenceSha256'])assert.match(a[key],/^[a-f0-9]{64}$/);
    assert.match(a.transportEvidenceFile,/^docs\/minimal-publication\/[a-zA-Z0-9][a-zA-Z0-9._-]*\.json$/);
  }
  return value;
}

/** Join only independently verified bindings to exact current source bytes. */
export async function validateMinimalProjection(bindings,assets) {
  assert.ok(Array.isArray(bindings));
  const map=new Map();
  for(const binding of bindings) {
    const key=`${binding.id}@${binding.assetVersion}`;
    assert.ok(!map.has(key),'Duplicate minimal binding');
    const asset=assets.find(a=>minimalIdentity(a)===key&&a.status==='public');
    assert.ok(asset,`Minimal binding is not a current public asset: ${key}`);
    const files=await Promise.all(asset.sources.map(async name=> {
      const data=await readFile(path.join(asset.dir,'source',name));
      return {name,bytes:data.length,sha256:sha256(data)};
    }));
    const readiness=minimalDownloadReadiness({...asset,files,downloads:{minimal:binding}});
    assert.ok(readiness.ready,`Invalid minimal binding ${key}: ${readiness.reason}`);
    map.set(key,binding);
  }
  return map;
}

export async function prepareMinimalDownloads(assets) {
  const activation=validateMinimalActivation(JSON.parse(await readFile(minimalActivationPath,'utf8')));
  if(!activation.activations.length)return new Map();
  // No cache, offline flag, environment override or injected verifier in this
  // production path. Python re-fetches actual anonymous public Release bytes.
  const {stdout}=await promisify(execFile)('python3',['scripts/verify-minimal-activation.py','--repo',process.cwd()],{maxBuffer:16*1024*1024});
  const bindings=JSON.parse(stdout);
  assert.equal(bindings.length,173,'Published173 activation must prove the entire cohort');
  return validateMinimalProjection(bindings,assets);
}

export function bindMinimalDownload(asset,bindings) {
  const binding=bindings.get(minimalIdentity(asset));
  if(!binding)return asset;
  assert.ok(!Object.hasOwn(asset.downloads,'minimal'),'Minimal binding already present');
  const next={...asset,downloads:{...asset.downloads,minimal:binding}};
  const readiness=minimalDownloadReadiness(next);
  assert.ok(readiness.ready,`Invalid final minimal binding: ${readiness.reason}`);
  return next;
}
