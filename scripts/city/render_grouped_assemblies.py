"""Render exact grouped GLBs and optional original A/B views; never changes models.
Use a new output directory, separate from frozen source assets.
"""
import argparse,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import bpy,common,infrastructure as I

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--original',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--samples',type=int,default=384)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    if not 1<=args.samples<=4096:parser.error('samples must be between 1 and 4096')
    if args.output.exists():parser.error('Refusing to overwrite render directory')
    args.output.mkdir(parents=True);os.environ['CITY_RENDER_SAMPLES']=str(args.samples)
    slug=args.input.name
    az=-60 if slug in ['city-solar-module-rack','city-scaffold-bay','city-roller-shutter','city-cable-tray-elbow'] else -55
    el=48 if slug=='city-inspection-cover' else 32 if slug=='city-cable-tray-elbow' else 20 if slug in ['city-solar-module-rack','city-scaffold-bay'] else 24
    if args.original:
        common.reset();bpy.ops.import_scene.gltf(filepath=str(args.original/'source'/(slug+'.glb')))
        common.render(args.output/'original-front.png',az,el)
    common.reset();bpy.ops.import_scene.gltf(filepath=str(args.input/'source'/(slug+'.glb')))
    common.render(args.output/'preview.png',az,el);common.render(args.output/'back.png',az+180,el)
    if slug in ['city-inspection-cover','city-scaffold-bay','city-solar-module-rack']:
        I.render_underside_qa(slug,args.output)
if __name__=='__main__':main()
