// Real local HTTPS hosting also covers Chromium's separate download manager.
// Browser-only DNS mapping preserves the built canonical origin and bytes.
import {createServer} from 'node:https';
import {readFile,mkdtemp,rm,stat} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import assert from 'node:assert/strict';
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.wasm':'application/wasm','.glb':'model/gltf-binary','.zip':'application/zip'};
export async function serveReview(directory){
 const root=path.resolve(directory),tls=await mkdtemp(path.join(tmpdir(),'meshcopia-review-tls-'));
 execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=xenoah.github.io','-addext','subjectAltName=DNS:xenoah.github.io,DNS:localhost','-keyout',tls+'/key.pem','-out',tls+'/cert.pem'],{stdio:'ignore'});
 const served=[];
 const server=createServer({key:await readFile(tls+'/key.pem'),cert:await readFile(tls+'/cert.pem')},async(req,res)=>{
  try{
   const pathname=new URL(req.url,'https://xenoah.github.io').pathname;
   assert.ok(pathname.startsWith('/meshcopia/'));assert.ok(['GET','HEAD'].includes(req.method));
   let file=path.resolve(root,decodeURIComponent(pathname.slice('/meshcopia/'.length)));
   assert.ok(file===root||file.startsWith(root+path.sep));if((await stat(file)).isDirectory())file=path.join(file,'index.html');
   const body=await readFile(file);res.writeHead(200,{'content-type':types[path.extname(file)]??'application/octet-stream','content-length':body.length,'cache-control':'no-store'});
   served.push({method:req.method,path:pathname,bytes:body.length});res.end(req.method==='HEAD'?undefined:body);
  }catch{res.writeHead(404).end('Missing built file')}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;
 return {served,port,args:[`--host-resolver-rules=MAP xenoah.github.io 127.0.0.1:${port}`],async close(){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));await rm(tls,{recursive:true,force:true})}};
}
