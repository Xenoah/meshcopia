// Legacy square materials default to ordinary repeat. Atlas dimensions are explicit.
export const textureWrap = a => a.wrapMode || 'repeat';
export const textureSize = a => [a.width || a.resolution, a.height || a.resolution];
export const textureLabel = a => ({repeat:'SEAMLESS',mirror:'MIRROR',clamp:'ATLAS'})[textureWrap(a)];
export const textureWrapLabel = a => ({repeat:'通常リピート',mirror:'鏡像リピート',clamp:'Clamp（非タイル）'})[textureWrap(a)];
export const textureWrapLabelEn = a => ({repeat:'Repeat',mirror:'Mirrored repeat',clamp:'Clamp (non-tileable)'})[textureWrap(a)];

// Each tile displays the original image. Alternating flips exactly match GPU
// mirrored-repeat sampling; the downloaded source is never changed.
export function renderTextureTiles(root, {url, wrapMode='repeat', count=1, width=1, height=1, title=''}) {
 const n=wrapMode==='clamp'?1:count;
 root.replaceChildren();
 root.dataset.wrapMode=wrapMode;
 root.dataset.tileCount=String(n);
 root.style.aspectRatio=`${width} / ${height}`;
 root.style.gridTemplateColumns=`repeat(${n}, minmax(0, 1fr))`;
 root.style.gridTemplateRows=`repeat(${n}, minmax(0, 1fr))`;
 for(let y=0;y<n;y++)for(let x=0;x<n;x++){
  const img=new Image();img.src=url;img.alt=x===0&&y===0?title:'';img.draggable=false;
  img.style.transform=wrapMode==='mirror'?`scale(${x%2?-1:1}, ${y%2?-1:1})`:'none';
  root.append(img);
 }
}
