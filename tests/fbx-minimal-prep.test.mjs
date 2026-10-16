import test from 'node:test';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
test('minimal FBX prep Python boundary regressions',async()=>{
 await promisify(execFile)('python3',['-m','unittest','discover','-s',fileURLToPath(new URL('.',import.meta.url)),'-p','test_fbx_minimal_prep.py'],{maxBuffer:4*1024*1024});
});
