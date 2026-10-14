import { mkdir, writeFile } from 'node:fs/promises';
import { slugPattern } from './lib/catalog.mjs';
const [id,type='model'] = process.argv.slice(2);
if (!slugPattern.test(id||'') || !['model','texture'].includes(type)) throw new Error('Usage: npm run new:asset -- <lowercase-id> [model|texture]');
await mkdir(`_inbox/${id}`); // Deliberately refuse to overwrite.
await mkdir(`_inbox/${id}/source`);
const today = new Date().toISOString().slice(0,10);
const asset = {id,type,title:id,titleEn:id,description:'説明を記入',descriptionEn:'Add a description',category:type==='model'?'props':'materials',tags:[],author:'Xenoah',license:'CC-BY-4.0',version:'1.0.0',status:'draft',created:today,updated:today,thumbnail:'preview.webp',usages:[],provenance:{method:'Fill in generation method',tool:'Fill in tool and version',rights:'Confirm original work and permission to release under CC BY 4.0'},...(type==='model'?{unit:'m',upAxis:'Y',triangles:0,preview:`${id}.glb`}:{seamless:true,wrapMode:'repeat',width:1024,height:1024,resolution:1024,maps:{baseColor:'basecolor.png'}})};
await writeFile(`_inbox/${id}/asset.json`,JSON.stringify(asset,null,2)+'\n');
console.log(`Created _inbox/${id}. Add source files and preview, complete metadata, then import.`);
