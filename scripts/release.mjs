import {readFile,readdir} from 'node:fs/promises';import {execFileSync} from 'node:child_process';
const config=JSON.parse(await readFile('.release.json','utf8'));const pkg=JSON.parse(await readFile('package.json','utf8'));
if(!/^\d+\.\d+\.\d+(?:-rc\.\d+)?$/.test(config.version)||config.version!==pkg.version)throw new Error('Release version must match package.json');
if(config.prerelease!==config.version.includes('-'))throw new Error('prerelease flag must match version');
if(!/^docs\/releases\/[a-zA-Z0-9.-]+\.md$/.test(config.notes))throw new Error('Invalid notes path');
const tag=`v${config.version}`;const repo=process.env.GITHUB_REPOSITORY;
let existing=false;
try{execFileSync('gh',['release','view',tag,'--repo',repo],{stdio:'pipe'});existing=true}catch(error){if(!String(error.stderr).includes('release not found')&&!String(error.stderr).includes('Not Found'))throw error;}
if(existing){console.log(`${tag} already exists; immutable release preserved.`);process.exit(0)}
const artifacts=(await readdir('release')).map(f=>'release/'+f);const screenshots=(await readdir('screenshots')).filter(f=>f.endsWith('.png')).map(f=>'screenshots/'+f);
const args=['release','create',tag,...artifacts,...screenshots,'--repo',repo,'--target',process.env.TARGET_SHA,'--title',config.name,'--notes-file',config.notes];if(config.prerelease)args.push('--prerelease');else args.push('--latest');
console.log(execFileSync('gh',args,{encoding:'utf8'}));
