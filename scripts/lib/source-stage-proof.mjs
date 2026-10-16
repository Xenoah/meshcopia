import assert from 'node:assert/strict';
import {repository} from './package-location-policy.mjs';
export const emptySourceStageProofs=()=>({schemaVersion:1,repository,proofs:[]});
export function validateSourceStageProofs(doc){
 assert.equal(doc.schemaVersion,1);assert.equal(doc.repository,repository);assert.ok(Array.isArray(doc.proofs));
 const commits=new Set();for(const proof of doc.proofs){assert.match(proof.commit,/^[0-9a-f]{40}$/);assert.ok(Number.isSafeInteger(proof.runId)&&proof.runId>0);assert.ok(!commits.has(proof.commit),'Duplicate source-stage proof');commits.add(proof.commit)}
 return doc;
}
export function assertSuccessfulSourceStageRun(proof,run){
 assert.equal(run.id,proof.runId,'Source-stage run ID mismatch');
 assert.equal(run.repository?.full_name,repository,'Source-stage repository mismatch');
 assert.equal(run.head_repository?.full_name,repository,'Source-stage head repository mismatch');
 assert.equal(run.path,'.github/workflows/publish.yml','Wrong source-stage workflow');
 assert.equal(run.event,'push','Source-stage must be an actual push workflow');
 assert.equal(run.head_branch,'main','Source-stage must verify main');
 assert.equal(run.head_sha,proof.commit,'Raw pin must equal successful source-stage workflow SHA');
 assert.equal(run.status,'completed','Source-stage workflow is not completed');
 assert.equal(run.conclusion,'success','Source-stage workflow did not succeed');
}
export function assertSourceStageUnchanged(sourceOnly,hasStagedChanges){
 assert.ok(!sourceOnly||!hasStagedChanges,'Source-only workflow must not create a post-QA import commit. Commit all reviewed drafts and recipes before starting source-stage CI.');
}
export async function readSourceStageRun(proof,fetcher=fetch){
 const url=`https://api.github.com/repos/${repository}/actions/runs/${proof.runId}`;
 const response=await fetcher(url,{headers:{Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},redirect:'error',credentials:'omit',signal:AbortSignal.timeout(30000)});
 assert.equal(response.status,200,'Unable to verify source-stage Actions run');return response.json();
}
export async function verifyCurrentSourceStages({doc,pins,packages,tag,readAt,loadRun=readSourceStageRun}){
 validateSourceStageProofs(doc);
 const {validateSourceStage}=await import('./source-stage.mjs');
 const selected=pins.filter(a=>packages.some(p=>p.id===a.id&&p.version===a.version&&p.tag===tag));
 const groups=new Map();for(const pin of selected){if(!groups.has(pin.commit))groups.set(pin.commit,[]);groups.get(pin.commit).push(pin.id)}
 for(const [commit,ids] of groups){
  const proof=doc.proofs.find(p=>p.commit===commit);assert.ok(proof,'Missing source-stage CI proof for '+commit);
  const marker=await readAt(commit,'.source-stage.json'),protectedIds=(await readAt(commit,'docs/scaling-protected-ids.json')).ids;
  assert.ok(Array.isArray(marker.ids),'Missing source-stage marker IDs');
  const drafts=await Promise.all(marker.ids.map(id=>readAt(commit,`content/assets/${id}/asset.json`)));validateSourceStage(marker,drafts,protectedIds);
  for(const id of ids)assert.ok(marker.ids.includes(id),'Pinned ID absent from verified source-stage marker: '+id);
  assertSuccessfulSourceStageRun(proof,await loadRun(proof));
 }
 return {pins:selected.length,runs:groups.size};
}
