"""Reproduce the approved original inspection-cover tread optimization.
Authoring recipe only. Exact archived GLB reproduction additionally depends on the
Blender/exporter version; grouping uses a separately hash-pinned baseline GLB.
"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bpy
import infrastructure as I
from common import reset, publish_asset

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    slug='city-inspection-cover'
    if (args.output/slug).exists(): parser.error('Refusing to overwrite existing asset')
    reset(); spec=I.inspection_cover()
    for obj in bpy.context.scene.objects:
        if obj.name.startswith('Raised diamond tread'):
            for modifier in obj.modifiers:
                if modifier.type=='BEVEL': modifier.segments=1
    publish_asset(*spec,out_dir=args.output,generator='scripts/city/infrastructure_manhole_optimized.py',elevation=48)
    I.render_underside_qa(slug,args.output)
if __name__=='__main__': main()
