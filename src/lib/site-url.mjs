// Only canonical Pages URLs become local paths. External, pinned production
// originals and thumbnails must retain their host in both preview and image UI.
export function toLocalSiteUrl(url) {
 const value=new URL(url,'https://xenoah.github.io');
 if(!['https:','http:'].includes(value.protocol))throw new TypeError('Unsupported asset URL protocol');
 return value.origin==='https://xenoah.github.io'?value.pathname+value.search+value.hash:value.href;
}
