"""Compose labeled review sheets exclusively from actual FrontSide renders."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];renders=ROOT/'test-results/asset-revisions/renders';out=ROOT/'docs/asset-revisions';out.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',19)
def sheet(name,rows):
    result=Image.new('RGB',(1200,630*len(rows)),(240,243,245));draw=ImageDraw.Draw(result)
    for y,row in enumerate(rows):
        for x,(source,label) in enumerate(row):
            im=Image.open(renders/(source+'.png')).crop((0,0,900,860));im.thumbnail((580,570))
            result.paste(im,(x*600+(600-im.width)//2,y*630+35));draw.text((x*600+18,y*630+10),label,font=font,fill=(25,45,55))
    result.save(out/name,quality=88,method=6)
sheet('starter-winding-comparison.webp',[
 [('garden-arch-original-glb-outside','Original arch: inward curved strip'),('garden-arch-fixed-glb-outside','Repair: continuous outward surface')],
 [('garden-arch-original-glb-inside','Original arch: inside / culling ON'),('garden-arch-fixed-glb-inside','Repaired arch: inside / culling ON')],
 [('wayfinding-sign-original-glb-inside','Original ring: inside / culling ON'),('wayfinding-sign-fixed-glb-inside','Repaired ring: inside / culling ON')]])
sheet('appliances-fbx-glb.webp',[
 [('household-two-door-refrigerator-fixed-glb-outside','New refrigerator: actual GLB'),('household-two-door-refrigerator-fixed-fbx-outside','New refrigerator: actual FBX')],
 [('household-two-door-refrigerator-fixed-glb-interior','Actual GLB hinge opened for QA'),('household-two-door-refrigerator-fixed-fbx-interior','Actual FBX hinge opened for QA')],
 [('washer-glb-drum','Existing washer: GLB / culling ON'),('washer-fbx-drum','Existing washer: FBX / culling ON')]])
print(out)
