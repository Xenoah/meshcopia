// Self-contained so Playwright can serialize this function into the page.
// A returned failure is diagnostic data, never permission to ignore a failed image.
export async function inspectImageDecode(image, {decode=true}={}) {
 const snapshot=()=>{
  const rect=image.getBoundingClientRect();
  const timing=globalThis.performance?.getEntriesByName?.(image.currentSrc)?.at(-1);
  return {src:image.getAttribute('src'),srcset:image.getAttribute('srcset'),sizes:image.getAttribute('sizes'),currentSrc:image.currentSrc,complete:image.complete,naturalWidth:image.naturalWidth,naturalHeight:image.naturalHeight,isConnected:image.isConnected,loading:image.loading,layoutWidth:rect.width,layoutHeight:rect.height,resourceTiming:timing?{encodedBodySize:timing.encodedBodySize,decodedBodySize:timing.decodedBodySize,transferSize:timing.transferSize}:null};
 };
 const before=snapshot();
 if(!decode)return {ok:true,before};
 try {
  if(!before.isConnected||!before.complete||before.naturalWidth<=0||before.naturalHeight<=0)throw new Error('Image is not completely loaded with positive natural dimensions');
  await image.decode();
  const after=snapshot();
  if(!after.isConnected||!after.complete||after.naturalWidth<=0||after.naturalHeight<=0)throw new Error('Image became unavailable during decode');
  if(before.currentSrc!==after.currentSrc||before.src!==after.src||before.srcset!==after.srcset||before.naturalWidth!==after.naturalWidth||before.naturalHeight!==after.naturalHeight)throw new Error('Image source or natural dimensions changed during decode');
  return {ok:true,before,after};
 }catch(error){return {ok:false,before,after:snapshot(),error:{name:error.name,message:error.message}};}
}
