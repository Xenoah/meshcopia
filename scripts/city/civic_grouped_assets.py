"""Generate a separate grouped draft from an original generated civic asset.
The GLB buffer merger preserves normal/UV/material data. Blender is used only to
reimport the new exact bytes for STL export and actual thumbnails, never GLB re-export.
"""
import argparse,copy,hashlib,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bpy
import common
from civic_static_groups import group_glb

if __name__=='__main__':
 argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output','--out',dest='output',type=Path,required=True);p.add_argument('--profile',choices=['bicycle','trolley','vending'],required=True);p.add_argument('--samples',type=int,default=384);a=p.parse_args(argv)
 metadata=json.loads((a.source/'asset.json').read_text());slug=metadata['id'];folder=a.output/slug
 if folder.exists():p.error('Refusing to overwrite existing target asset')
 if Path(metadata['preview']).name!=metadata['preview']:p.error('Expected a basename GLB preview')
 raw=(a.source/'source'/metadata['preview']).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=metadata['provenance']['sourceSha256']:p.error('Source GLB hash differs from metadata')
 grouped,report=group_glb(raw,a.profile);(folder/'source').mkdir(parents=True);qa=a.output/'_qa';qa.mkdir(exist_ok=True)
 glb=folder/'source'/f'{slug}.glb';glb.write_bytes(grouped);common.reset();bpy.ops.import_scene.gltf(filepath=str(glb))
 count=common.export_stl_from_scene(folder/'source'/f'{slug}.stl');assert count==report['triangles']
 bounds=[obj.matrix_world@v.co for obj in bpy.context.scene.objects if obj.type=='MESH' for v in obj.data.vertices]
 lo=[min(v[i] for v in bounds) for i in range(3)];hi=[max(v[i] for v in bounds) for i in range(3)];dims=[round(hi[i]-lo[i],6) for i in [0,2,1]]
 metadata['status']='draft';metadata['triangles']=count;metadata['dimensions']=dims
 metadata['provenance']['sourceSha256']=report['groupedSha256'];metadata['provenance']['stlSha256']=hashlib.sha256((folder/'source'/f'{slug}.stl').read_bytes()).hexdigest()
 metadata['provenance']['staticGrouping']={k:v for k,v in report.items() if k!='groups'}
 metadata['provenance']['changes']='Repeated static parts grouped by material and assembly; no decimation or material/UV changes. Source GLB SHA-256: '+report['sourceSha256']+'.'
 metadata['provenance']['postprocessGeneratorUrl']='https://github.com/Xenoah/meshcopia/blob/main/scripts/city/civic_grouped_assets.py'
 metadata['provenance']['tool']+='; Meshcopia attribute-preserving static grouping 1.0'
 for item in metadata.get('usages',[]):
  for source in ['scripts/city/civic_static_groups.py','scripts/city/civic_grouped_assets.py']:
   if source not in item['sourcePaths']:item['sourcePaths'].append(source)
 metadata['description']+=' 繰り返し部品は材質と構成単位ごとに統合済み。'
 metadata['descriptionEn']+=' Repeated static details are grouped by material and assembly; the procedural source retains the editable construction.'
 (folder/'asset.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
 (qa/f'{slug}-grouping.json').write_text(json.dumps(report,indent=2)+'\n')
 os.environ['CITY_RENDER_SAMPLES']=str(a.samples);az,el=(-72,18) if a.profile=='bicycle' else (-55,24)
 common.render(folder/'preview.png',az,el);common.render(qa/f'{slug}-back.png',az+180,el)
 assert hashlib.sha256(glb.read_bytes()).hexdigest()==report['groupedSha256']
 print('GROUPED_CIVIC_COMPLETE',json.dumps({k:v for k,v in report.items() if k!='groups'}),flush=True)
