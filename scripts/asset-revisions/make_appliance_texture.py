"""Original, brand-free control-panel artwork; no third-party image or font."""
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]/'asset-revisions/repair-appliances-v1/household-two-door-refrigerator/production'
ROOT.mkdir(parents=True,exist_ok=True)
im=Image.new('RGB',(512,512),(17,24,29));d=ImageDraw.Draw(im)
for y in range(512):d.line((0,y,511,y),fill=(17+y//85,24+y//100,29+y//100))
d.rounded_rectangle((14,14,498,498),radius=30,outline=(82,104,110),width=5)
segments={'0':'abcdef','1':'bc','2':'abdeg','3':'abcdg','4':'bcfg','5':'acdfg','6':'acdefg','7':'abc','8':'abcdefg','9':'abcdfg','-':'g'}
lines={'a':(0,0,54,0),'b':(54,0,54,54),'c':(54,54,54,108),'d':(0,108,54,108),'e':(0,54,0,108),'f':(0,0,0,54),'g':(0,54,54,54)}
def digit(value,x,y,scale=1):
    for s in segments[value]:
        a,b,c,e=lines[s];d.line((x+a*scale,y+b*scale,x+c*scale,y+e*scale),fill=(178,233,220),width=10)
def snow(x,y,r):
    import math
    for a in range(0,180,60):
        co,si=math.cos(math.radians(a)),math.sin(math.radians(a));d.line((x-r*co,y-r*si,x+r*co,y+r*si),fill=(155,203,211),width=5)
snow(92,126,27);digit('4',211,72);d.ellipse((297,73,313,89),outline=(178,233,220),width=4)
d.arc((326,89,379,147),70,290,fill=(178,233,220),width=7)
d.line((50,224,462,224),fill=(65,87,94),width=3)
snow(92,314,34);digit('-',166,259,.8);digit('1',235,259,.8);digit('8',304,259,.8)
for x in (92,256,420):d.ellipse((x-31,416,x+31,478),outline=(116,141,145),width=3)
d.line((72,447,112,447),fill=(203,215,211),width=5)
d.line((400,447,440,447),fill=(203,215,211),width=5);d.line((420,427,420,467),fill=(203,215,211),width=5)
d.arc((238,430,274,466),-45,225,fill=(203,215,211),width=5);d.line((256,423,256,444),fill=(203,215,211),width=5)
im.save(ROOT/'control-panel.png',optimize=True)
print(ROOT/'control-panel.png')
