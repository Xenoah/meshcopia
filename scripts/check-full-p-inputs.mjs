// Structural/pinned-file preflight only. npm run check performs real remote verification.
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {validateMinimalActivation} from './lib/minimal-downloads.mjs';
import {RELEASE,sha256,measureDist} from './lib/download-browser-contract.mjs';

const activation=validateMinimalActivation(JSON.parse(await readFile('docs/minimal-activation.json','utf8')));
assert.equal(activation.activations.length,1,'Full P requires actual release activation');
const actual=activation.activations[0];for(const [key,value] of Object.entries(RELEASE))assert.equal(actual[key],value,key);
const receiptBytes=await readFile(actual.transportEvidenceFile);assert.equal(sha256(receiptBytes),actual.transportEvidenceSha256);
const receipt=JSON.parse(receiptBytes);assert.equal(receipt.status,'anonymous-byte-readback-passed');assert.equal(receipt.releaseId,RELEASE.releaseId);assert.equal(receipt.verificationCommit,RELEASE.verificationCommit);assert.equal(receipt.inventorySha256,RELEASE.inventorySha256);assert.equal(receipt.attachmentCount,174);
const pinned=[];
for(const file of ['scripts/minimal-verification/common.py','scripts/minimal_packages.py','scripts/minimal_notices.py']){
 const data=await readFile(file),expected=execFileSync('git',['show',`${RELEASE.verificationCommit}:${file}`],{maxBuffer:8*1024*1024});
 assert.deepEqual(data,expected,`Pinned F module differs: ${file}`);pinned.push({file,bytes:data.length,sha256:sha256(data)});
}
const report={schemaVersion:1,scope:'activation receipt and local F module preflight; remote verification is npm run check',sourceCommit:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),release:RELEASE,transportEvidenceSha256:sha256(receiptBytes),pinned,...(process.argv.includes('--dist')?{dist:await measureDist('dist')}:{})};
await mkdir('test-results',{recursive:true});await writeFile('test-results/minimal-p-inputs.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
