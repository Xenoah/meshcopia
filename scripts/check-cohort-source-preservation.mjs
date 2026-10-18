import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {loadCohortPolicy} from './lib/cohort-policy.mjs';
const base='1f8661231767719ebc53956e6c55a51b468c2fde',policy=await loadCohortPolicy();
const git=(...args)=>execFileSync('git',['--no-replace-objects',...args]);
const changes=git('diff','--name-only',base,'--','content','.release.json','docs/archive-lock.json').toString().trim().split('\n').filter(Boolean);
assert.deepEqual(changes.sort(),policy.newIds.map(id=>`content/assets/${id}/asset.json`).sort());
for(const file of changes){const before=JSON.parse(git('show',base+':'+file));assert.equal(before.status,'draft');before.status='public';assert.deepEqual(JSON.parse(await readFile(file)),before);}
console.log(`Preserved all original files/history and existing Releases; ${changes.length} metadata status-only activations.`);
