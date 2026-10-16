const root='https://github.com/Xenoah/meshcopia/releases/download/fbx-minimal-v1.0.0/';
const hash=/^[a-f0-9]{64}$/;
const size=n=>Number.isSafeInteger(n)&&n>0;
// Presentation-only selector. Availability is created by trusted same-job prep,
// then checked against current source/metadata by the generator before output.
export function fbxMinimalForAsset(asset,projection){
 if(asset?.status!=='public'||asset.type!=='model')return undefined;
 const matches=(projection?.formats||[]).filter(x=>x.id===asset.id&&x.assetVersion===asset.version);
 if(matches.length!==1)return undefined;
 const x=matches[0];
 if(x.format!=='FBX'||x.packageVersion!=='1.0.0'||x.selfContained!==true||x.verification?.state!=='published-verified'||x.verification.releaseTag!=='fbx-minimal-v1.0.0')return undefined;
 if(x.direct?.filename!==`${x.id}.fbx`||x.archive?.filename!==`${x.id}-${x.assetVersion}-fbx-minimal-1.0.0.zip`)return undefined;
 for(const f of [x.direct,x.archive])if(f.url!==root+f.filename||!size(f.bytes)||!hash.test(f.sha256))return undefined;
 if(x.notice?.filename!=='LICENSE.txt'||!Array.isArray(x.limitations)||!x.limitations.length)return undefined;
 return x;
}
