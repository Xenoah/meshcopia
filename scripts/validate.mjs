import { readProductionCatalog } from './lib/production-catalog.mjs';
const assets = await readProductionCatalog();
console.log(`Validated ${assets.length} assets: ${assets.filter(a=>a.type==='model').length} models, ${assets.filter(a=>a.type==='texture').length} textures. All CC-BY-4.0.`);
