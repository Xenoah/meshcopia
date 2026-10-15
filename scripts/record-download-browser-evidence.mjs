// Run only after both browser test commands succeed. Preserve exact output hashes.
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';

const proof=JSON.parse(await readFile('live-browser-proof.json','utf8'));
assert.equal(proof.origin,'https://xenoah.github.io');
assert.deepEqual([...proof.ids].sort(),['sage-terrazzo','studio-chair']);
assert.equal(proof.extractionVerified,true); // Original proof's ZIP reader/CRC check.
assert.equal(proof.raw.status,200);assert.equal(proof.raw.type,'cors');
assert.match(proof.raw.url,/^https:\/\/raw\.githubusercontent\.com\/Xenoah\/meshcopia\//);
const archives=['live-browser-proof.zip','batch-desktop.zip','batch-mobile.zip'];
// Independently inspect every actual browser-produced archive. All source bytes
// must match the real-source proof; notices differ intentionally between fixtures.
const python=`import hashlib,json,sys,zipfile\nproof=json.load(open('live-browser-proof.json'))\nexpected={r['name']:r for r in proof['entries'] if r['name']!='LICENSE.txt'}\nfor path in sys.argv[1:]:\n with zipfile.ZipFile(path) as z:\n  names=z.namelist()\n  assert len(names)==len(set(names)) and set(names)==set(expected)|{'LICENSE.txt'}, path\n  assert z.testzip() is None, path\n  for name,row in expected.items():\n   data=z.read(name)\n   assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'], (path,name)\n  notice=z.read('LICENSE.txt').decode('utf-8')\n  for asset_id in proof['ids']: assert '=== '+asset_id+' ===' in notice, (path,asset_id)\n  assert not any(n.endswith('.zip') for n in names), path\nprint('All three browser-produced ZIPs have exact source payloads and one aggregate notice.')\n`;
execFileSync('python3',['-c',python,...archives],{stdio:'inherit'});
const files=[];
for(const name of [...archives,'live-browser-proof.json','batch-desktop.png','batch-mobile.png']) {
  const data=await readFile(name);assert.ok(data.length>0,`Empty browser evidence: ${name}`);
  files.push({name,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')});
}
const report={schemaVersion:1,status:'candidate-browser-checks-passed',repository:process.env.GITHUB_REPOSITORY??null,sourceCommit:process.env.GITHUB_SHA??null,runId:process.env.GITHUB_RUN_ID??null,runAttempt:process.env.GITHUB_RUN_ATTEMPT??null,scope:{realPublicSources:['studio-chair','sage-terrazzo'],rawGithubCors:true,zipPayloadHashesVerified:true,aggregateNoticeCount:1,fixtureNoticeText:true,fixtureReadiness:true,desktopAnd390pxMobileUI:true,productionActivation:'empty',releaseZipReadback:false,new232Coverage:false,fbxCoverage:false,siteBuild:false,sitePublication:false},files};
await mkdir('test-results',{recursive:true});
await writeFile('test-results/minimal-ui-browser.json',JSON.stringify(report,null,2)+'\n');
console.log('Recorded candidate browser proof with explicit fixture and publication limits.');
