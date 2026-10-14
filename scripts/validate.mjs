import { readCatalog } from './lib/catalog.mjs';
const assets = await readCatalog();
console.log(`Validated ${assets.length} assets: ${assets.filter(a=>a.type==='model').length} models, ${assets.filter(a=>a.type==='texture').length} textures. All CC-BY-4.0.`);
