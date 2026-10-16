// Read-only promotion gate. Remote Actions result, not a locally asserted success.
import {readFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {verifyCurrentSourceStages} from './lib/source-stage-proof.mjs';
const json=async file=>JSON.parse(await readFile(file,'utf8'));
const result=await verifyCurrentSourceStages({
 doc:await json('docs/source-stage-proofs.json'),
 pins:(await json('docs/media-locations.json')).assets,
 packages:(await json('docs/package-locations.json')).packages,
 tag:'v'+(await json('.release.json')).version,
 readAt:async(commit,file)=>JSON.parse(execFileSync('git',['show',`${commit}:${file}`],{encoding:'utf8'}))
});
console.log(`Verified successful source-stage workflow SHA for ${result.pins} current-batch pins (${result.runs} runs).`);
