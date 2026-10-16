import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {assertSourceStageUnchanged} from './lib/source-stage-proof.mjs';
assert.ok(['true','false'].includes(process.env.SOURCE_ONLY),'Missing or invalid source-stage result');
if(process.env.SOURCE_ONLY==='true'){
 assert.match(process.env.SOURCE_HEAD??'',/^[0-9a-f]{40}$/,'Missing exact source-stage HEAD');
 const git=(...args)=>execFileSync('git',['--no-optional-locks',...args],{encoding:'utf8'}).trim();
 assert.equal(git('rev-parse','HEAD'),process.env.SOURCE_HEAD,'Source-stage HEAD changed after QA');
 // Include staged, unstaged and new source/code files. Generated output and QA
 // evidence are ignored explicitly by the repository, never staged here.
 assertSourceStageUnchanged(true,Boolean(git('status','--porcelain=v1','--untracked-files=all')));
}
