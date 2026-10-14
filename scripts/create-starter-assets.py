"""Original deterministic Meshcopia starter assets, CC BY 4.0.
Optional regeneration: python -m pip install -r scripts/requirements-assets.txt
Y-up, meters, self-contained glTF 2.0, OBJ/MTL and STL. No third-party models.
Thumbnails are software renders of the actual distributed mesh.
"""
from pathlib import Path
import json, struct, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1] / 'content/assets'
TAU = math.tau
MATERIALS = [
 ('sage', [0.38,0.58,0.48],0.0,0.65), ('oak',[0.59,0.36,0.19],0.0,0.72),
 ('graphite',[0.12,0.16,0.19],0.55,0.36), ('cream',[0.88,0.82,0.66],0.0,0.8),
 ('terracotta',[0.67,0.30,0.19],0.0,0.88), ('brass',[0.72,0.51,0.24],0.65,0.32),
 ('blue',[0.25,0.42,0.56],0.15,0.52), ('light',[0.97,0.79,0.43],0.0,0.5)
]

class Mesh:
 def __init__(self): self.parts=[]
 def add(self, vertices, faces, material=0):
  v=np.array(vertices,dtype=float);f=np.array(faces,dtype=int)
  t=v[f];area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
  self.parts.append((v,f[area>1e-12],material))
 def box(self, center, size, mat=0, tilt=0):
  v=np.array([[x,y,z] for x in [-.5,.5] for y in [-.5,.5] for z in [-.5,.5]])*size
  if tilt:
   c,s=math.cos(tilt),math.sin(tilt);v=v@np.array([[1,0,0],[0,c,s],[0,-s,c]])
  v+=center
  self.add(v,[[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],[2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]],mat)
 def lathe(self, profile, center=(0,0,0), mat=0, n=48):
  v=[[r*math.cos(i*TAU/n)+center[0], y+center[1],r*math.sin(i*TAU/n)+center[2]] for r,y in profile for i in range(n)]
  f=[]
  for j in range(len(profile)-1):
   for i in range(n):
    a=j*n+i;b=j*n+(i+1)%n;c=(j+1)*n+i;d=(j+1)*n+(i+1)%n
    f.extend([[a,c,b],[b,c,d]])
  self.add(v,f,mat)
 def cylinder(self,x,y,z,r,h,mat=0,n=32): self.lathe([(0,0),(r,0),(r,h),(0,h)],(x,y,z),mat,n)
 def torus(self, center, radius, tube, mat=0, vertical=False):
  v=[];f=[];n=48;m=12
  for i in range(n):
   for j in range(m):
    a=i*TAU/n;b=j*TAU/m
    x=(radius+tube*math.cos(b))*math.cos(a);z=(radius+tube*math.cos(b))*math.sin(a);y=tube*math.sin(b)
    if vertical:y,z=z,y
    v.append(np.array([x,y,z])+center)
  for i in range(n):
   for j in range(m):
    a=i*m+j;b=((i+1)%n)*m+j;c=i*m+(j+1)%m;d=((i+1)%n)*m+(j+1)%m
    f.extend([[a,c,b],[b,c,d]])
  self.add(v,f,mat)
 def export(self,folder,slug):
  buffers=[];views=[];accessors=[];primitives=[];offset=0
  def accessor(array, typ, component=5126, bounds=False):
   nonlocal offset
   arr=np.asarray(array,dtype='<f4' if component==5126 else '<u4');data=arr.tobytes()
   views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data)})
   a={'bufferView':len(views)-1,'componentType':component,'count':len(arr),'type':typ}
   if bounds:a.update(min=arr.min(axis=0).tolist(),max=arr.max(axis=0).tolist())
   accessors.append(a);buffers.append(data);offset+=len(data)
   return len(accessors)-1
  obj=[f'mtllib {slug}.mtl'];stl=bytearray(b'Meshcopia CC BY 4.0'.ljust(80,b'\0'));count=sum(len(f) for _,f,_ in self.parts);stl+=struct.pack('<I',count);idx=1
  for v,f,mat in self.parts:
   tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);length=np.linalg.norm(norm,axis=1);norm/=np.maximum(length,1e-12)[:,None]
   flat=tri.reshape(-1,3);normals=np.repeat(norm,3,axis=0);uv=flat[:,[0,2]]
   primitives.append({'attributes':{'POSITION':accessor(flat,'VEC3',bounds=True),'NORMAL':accessor(normals,'VEC3'),'TEXCOORD_0':accessor(uv,'VEC2')},'material':mat,'mode':4})
   obj.append('usemtl '+MATERIALS[mat][0]);obj += ['v %.6f %.6f %.6f'%tuple(p) for p in v];obj += [f'f {a+idx} {b+idx} {c+idx}' for a,b,c in f];idx+=len(v)
   for t,n in zip(tri,norm):stl+=struct.pack('<12fH',*n,*t.flatten(),0)
  mats=[{'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':color+[1],'metallicFactor':metal,'roughnessFactor':rough}} for name,color,metal,rough in MATERIALS]
  doc={'asset':{'version':'2.0','generator':'Meshcopia original procedural generator'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':slug}],'meshes':[{'primitives':primitives}],'materials':mats,'buffers':[{'byteLength':offset}],'bufferViews':views,'accessors':accessors}
  j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=b''.join(buffers);b+=b'\0'*((-len(b))%4)
  glb=struct.pack('<III',0x46546C67,2,28+len(j)+len(b))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(b),b'BIN\0')+b
  (folder/f'{slug}.glb').write_bytes(glb);(folder/f'{slug}.obj').write_text('\n'.join(obj)+'\n');(folder/f'{slug}.stl').write_bytes(stl)
  (folder/f'{slug}.mtl').write_text('\n'.join(f'newmtl {name}\nKd {color[0]} {color[1]} {color[2]}\nNs 32\n' for name,color,_,_ in MATERIALS))
  return count
 def render(self,file):
  w,h=1000,800
  bg=np.zeros((h,w,3),dtype=np.uint8);yy,xx=np.mgrid[0:h,0:w];glow=np.exp(-((xx-w*.5)**2/(w*.6)**2+(yy-h*.48)**2/(h*.5)**2))
  for c,(base,gain) in enumerate([(25,23),(32,27),(37,29)]):bg[:,:,c]=base+gain*glow
  im=Image.fromarray(bg);shadow=Image.new('RGBA',(w,h));d=ImageDraw.Draw(shadow);d.ellipse((w*.22,h*.77,w*.80,h*.87),fill=(0,0,0,140));im=Image.alpha_composite(im.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(25)))
  az=2.45;el=.40;right=np.array([math.cos(az),0,-math.sin(az)]);forward=np.array([math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el)]);up=np.cross(forward,right)
  allv=np.concatenate([v for v,_,_ in self.parts]);center=(allv.max(axis=0)+allv.min(axis=0))/2
  points=np.array([(allv-center)@right,(allv-center)@up]).T;scale=min(w*.77/max(np.ptp(points[:,0]),.01),h*.70/max(np.ptp(points[:,1]),.01))
  faces=[];light=np.array([-.5,.85,-.45]);light/=np.linalg.norm(light)
  for v,f,mat in self.parts:
   tri=v[f];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-12)[:,None]
   depth=(tri.mean(axis=1)-center)@forward;shade=.42+.53*np.maximum(0,normal@light)+.1*np.maximum(0,normal@forward)
   for t,z,s in zip(tri,depth,shade):
    p=t-center;xy=np.stack([w*.5+p@right*scale,h*.49-p@up*scale],axis=1)
    col=np.clip(np.array(MATERIALS[mat][1])*255*s+12,0,255).astype(int)
    faces.append((z,xy,tuple(col.tolist())))
  draw=ImageDraw.Draw(im)
  for _,xy,color in sorted(faces,key=lambda a:a[0]):draw.polygon([tuple(p) for p in xy],fill=color,outline=color)
  im.convert('RGB').save(file,'WEBP',quality=94)

def metadata(slug,title,en,desc,desc_en,category,tags,kind='model'):
 return dict(id=slug,type=kind,title=title,titleEn=en,description=desc,descriptionEn=desc_en,category=category,tags=tags,author='Xenoah',license='CC-BY-4.0',version='1.0.0',status='public',created='2026-10-14',updated='2026-10-14',thumbnail='preview.webp',usages=[dict(relationship='original',project='Meshcopia',sourceUrl='https://github.com/Xenoah/meshcopia',sourcePaths=['scripts/create-starter-assets.py'],selectors=[slug],context='Created for the Meshcopia asset library; no external project usage recorded.')],provenance={'method':'AI-agent-authored deterministic procedural geometry' if kind=='model' else 'AI-agent-authored periodic procedural material','tool':'Meshcopia starter generator 1.0 / Python, NumPy, Pillow','rights':'Original geometry/material formulas for Meshcopia. No third-party model, photograph, trademark, or scanned asset included.'})

def save_model(slug,title,en,desc,desc_en,category,tags,mesh):
 folder=ROOT/slug;(folder/'source').mkdir(parents=True,exist_ok=True)
 count=mesh.export(folder/'source',slug);mesh.render(folder/'preview.webp')
 a=metadata(slug,title,en,desc,desc_en,category,tags);v=np.concatenate([v for v,_,_ in mesh.parts]);a.update(unit='m',upAxis='Y',triangles=count,dimensions=np.round(np.ptp(v,axis=0),4).tolist(),preview=f'{slug}.glb',uv='Planar XZ per face; custom UV unwrap recommended for directional textures')
 (folder/'asset.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(slug,count)

def models():
 m=Mesh()
 for x in [-.23,.23]:
  for z in [-.22,.22]:m.box((x,.25,z),(.045,.5,.045),1)
 m.box((0,.49,0),(.56,.07,.56),0)
 for x in [-.23,.23]:m.box((x,.76,.23),(.045,.55,.045),1,tilt=-.10)
 m.box((0,.86,.26),(.55,.27,.06),0,tilt=-.10)
 save_model('studio-chair','スタジオチェア','Studio chair','セージ色の座面と木製フレーム。カフェやワークスペース向けの軽量プロップ。','Sage upholstery and an oak frame. A lightweight prop for cafés and workspaces.','furniture',['chair','椅子','cafe','wood','low-poly'],m)
 m=Mesh();m.cylinder(0,0,0,.22,.045,2);m.cylinder(0,.04,0,.016,.66,5);m.lathe([(0,.0),(.26,0),(.12,.26),(.11,.275),(.245,.02),(0,.02)],(0,.69,0),0);m.cylinder(0,.69,0,.09,.015,7)
 save_model('atelier-lamp','アトリエランプ','Atelier lamp','真鍮の支柱とコニカルシェード。デスクやカフェカウンターに。','A brass stem and a conical sage shade for desks and café counters.','props',['lamp','照明','cafe','brass'],m)
 m=Mesh()
 for x in [-.62,.62]:
  for z in [-.20,.20]:m.box((x,.20,z),(.07,.40,.07),2)
 for z in [-.22,-.11,0,.11,.22]:m.box((0,.44,z),(1.65,.065,.095),1)
 m.box((0,.25,0),(1.3,.05,.06),2)
 save_model('slat-bench','ウッドスラットベンチ','Slat bench','独立した5枚の座板とスチール脚。屋外スペース、広場、休憩所に。','Five individual timber slats on steel legs for plazas and outdoor resting spaces.','furniture',['bench','ベンチ','wood','outdoor'],m)
 m=Mesh();m.lathe([(0,0),(.19,0),(.27,.48),(.265,.50),(.24,.50),(.17,.05),(0,.05)],mat=4);m.torus((0,.48,0),.255,.024,4);m.cylinder(0,.41,0,.232,.018,1)
 save_model('terracotta-planter','テラコッタプランター','Terracotta planter','中空の鉢と独立した土面。植物の組み合わせに使えるベースモデル。','A hollow terracotta pot with a separate soil surface, ready for your plant meshes.','props',['planter','鉢','garden','terracotta'],m)
 m=Mesh()
 for y in [.06,.18,.30,.42]:
  for z in [-.28,.28]:m.box((0,y,z),(.72,.10,.035),1)
  for x in [-.35,.35]:m.box((x,y,0),(.035,.10,.56),1)
 for x in [-.29,.29]:
  for z in [-.23,.23]:m.box((x,.24,z),(.055,.49,.055),1)
 for z in [-.21,-.07,.07,.21]:m.box((0,.015,z),(.68,.035,.12),1)
 save_model('market-crate','マーケット木箱','Market crate','開いた上面と組み板を持つ木箱。倉庫・市場・横丁の小物に。','An open timber crate with individual boards for markets, workshops and alley scenes.','props',['crate','木箱','market','wood'],m)
 m=Mesh()
 for x in [-.65,.65]:m.box((x,.70,0),(.22,1.4,.32),3)
 n=24;v=[];f=[]
 for z in [-.16,.16]:
  for r in [.54,.76]:
   for i in range(n+1):a=i*math.pi/n;v.append([r*math.cos(a),1.4+r*math.sin(a),z])
 for i in range(n):
  a=i;b=i+1;c=n+1+i;d=c+1;e=2*(n+1)+i;g=3*(n+1)+i
  f.extend([[a,c,b],[b,c,d],[e,e+1,g],[e+1,g+1,g],[a,b,e],[b,e+1,e],[c,g,d],[d,g,g+1]])
 m.add(v,f,3)
 save_model('garden-arch','ガーデンアーチ','Garden arch','明るい石色のアーチ。Y軸上向き、幅1.52 mの建築用モジュール。','A pale stone arch. Y-up architectural module with a 1.52 m outer width.','architecture',['arch','アーチ','stone','garden'],m)
 m=Mesh();m.box((0,.36,0),(.64,.60,.38),6);m.box((0,.36,-.205),(.56,.50,.04),2);m.box((0,.46,-.23),(.43,.18,.018),3)
 for x in [-.17,0,.17]:m.box((x,.24,-.238),(.07,.055,.025),0)
 m.box((0,.02,0),(.72,.04,.45),2)
 save_model('field-terminal','フィールドターミナル','Field terminal','独立したスクリーンとボタンを持つレトロ端末。研究室・工場風シーンに。','A compact retro terminal with separate screen and buttons for lab and industrial scenes.','technology',['terminal','端末','industrial','retro'],m)
 m=Mesh();m.cylinder(0,0,0,.27,.05,2);m.cylinder(0,.05,0,.05,.72,5);m.torus((0,.95,0),.24,.028,5,vertical=True);m.box((0,.95,0),(.34,.31,.035),0)
 save_model('wayfinding-sign','ラウンドサイン','Round wayfinding sign','丸いフレームと無地の看板。文字やロゴを追加できる案内用プロップ。','A round frame and blank sign face, ready for your lettering or original logo.','props',['sign','看板','cafe','wayfinding'],m)

def texture(slug,title,en,kind,base):
 n=1024;y,x=np.mgrid[0:n,0:n]/(n-1);rng=np.random.default_rng(20261014)
 noise=np.zeros((n,n));fine=np.zeros((n,n))
 for freq,amp in [(1,.5),(2,.25),(4,.15),(8,.09),(16,.05),(32,.025),(64,.012)]:
  for k in range(4):
   ax=int(rng.integers(1,freq+1));ay=int(rng.integers(1,freq+1));phase=rng.random()*TAU
   noise+=amp/4*np.sin(TAU*(ax*x+ay*y)+phase)
 for k in range(8):fine+=np.sin(TAU*(int(rng.integers(60,200))*x+int(rng.integers(60,200))*y)+rng.random()*TAU)/8
 grain=noise*.16+fine*.015;h=.5+grain;color=np.zeros((n,n,3))+np.array(base)/255
 if kind=='stone':color+=grain[:,:,None];h=.5+grain*.65
 elif kind=='wood':
  rings=np.sin(TAU*(24*x+1.2*np.sin(TAU*y)+.3*np.sin(TAU*3*y)))
  joint=np.minimum((x*4)%1,1-(x*4)%1)<.009
  grain=grain*.45+rings*.025+np.sin(TAU*x*128)*.012
  color+=grain[:,:,None];color[joint]*=.48;h=.52+grain*.3;h[joint]=.35
 elif kind=='brick':
  row=np.floor(y*8).astype(int);u=(x*4+(row%2)*.5)%1;v=(y*8)%1
  mortar=(u<.023)|(u>.977)|(v<.045)|(v>.955)
  color+=grain[:,:,None]*.8;variation=.045*np.sin(TAU*(np.floor(x*4+(row%2)*.5)/4+row/8));color+=variation[:,:,None]
  color[mortar]=[.49,.46,.40];h=.6+grain*.1;h[mortar]=.3
 elif kind=='tiles':
  u=(x*4)%1;v=(y*4)%1;mortar=(u<.015)|(u>.985)|(v<.015)|(v>.985)
  color+=grain[:,:,None]*.35;color[mortar]=[.72,.73,.68];h=.6+grain*.07;h[mortar]=.3
 elif kind=='metal':
  brushed=np.zeros((n,n))
  for k in range(40):brushed+=np.sin(TAU*(k*9+45)*y+rng.random()*TAU)*.0018
  color+=(brushed+grain*.08)[:,:,None];h=.5+brushed*.15
 elif kind=='terrazzo':
  color+=grain[:,:,None]*.35;h=.5+grain*.02
  for i in range(430):
   cx,cy=rng.random(2);r=rng.uniform(.002,.014);dx=(x-cx+.5)%1-.5;dy=(y-cy+.5)%1-.5;ang=rng.random()*TAU
   u=dx*np.cos(ang)+dy*np.sin(ang);v=-dx*np.sin(ang)+dy*np.cos(ang);mask=(abs(u)/r+abs(v)/(r*.65))<1
   color[mask]=np.array([[.21,.31,.32],[.63,.36,.26],[.78,.70,.54],[.44,.48,.42]][i%4]);h[mask]=.5
 color=np.clip(color,0,1);rough=np.clip(.68+grain*.12,0,1)
 if kind=='tiles':rough[:]=.27;rough[mortar]=.85
 if kind=='metal':rough[:]=.38
 # Match both end rows/columns exactly; use periodic derivatives for normals.
 for a in [color,h,rough]:a[-1]=a[0];a[:,-1]=a[:,0]
 dx=(np.roll(h,-1,axis=1)-np.roll(h,1,axis=1))*8;dy=(np.roll(h,-1,axis=0)-np.roll(h,1,axis=0))*8
 normals=np.stack([-dx,dy,np.ones_like(h)],axis=2);normals/=np.linalg.norm(normals,axis=2)[:,:,None];normals=normals*.5+.5;normals[-1]=normals[0];normals[:,-1]=normals[:,0]
 folder=ROOT/slug;(folder/'source').mkdir(parents=True,exist_ok=True)
 maps={'baseColor':'basecolor.png','normal':'normal.png','roughness':'roughness.png','height':'height.png'}
 for name,a in [('basecolor',color),('normal',normals),('roughness',rough),('height',h)]:Image.fromarray(np.uint8(np.clip(a,0,1)*255)).save(folder/'source'/f'{name}.png')
 Image.fromarray(np.uint8(color*255)).resize((1000,1000)).save(folder/'preview.webp',quality=93)
 a=metadata(slug,title,en,'XY両方向に繰り返せる1024pxのプロシージャル素材。Base Color・Normal・Roughness・Heightを同梱。','A periodic 1024px material with base color, OpenGL normal, roughness and height maps. Procedural, not a photograph.','materials',[kind,'seamless','PBR','シームレス'],kind='texture');a.update(seamless=True,resolution=n,maps=maps,normalConvention='OpenGL +Y',colorSpace={'baseColor':'sRGB','normal':'linear','roughness':'linear','height':'linear'},physicalSize=[2,2],metalness=1 if kind=='metal' else 0)
 (folder/'asset.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(slug,'1024px')

if __name__=='__main__':
 models()
 for args in [
  ('warm-limestone','ウォームライムストーン','Warm limestone','stone',[165,159,140]),
  ('cedar-boards','シダーボード','Cedar boards','wood',[132,82,49]),
  ('clay-brick','クレイブリック','Clay brick','brick',[153,76,51]),
  ('sage-terrazzo','セージテラゾー','Sage terrazzo','terrazzo',[174,186,166]),
  ('brushed-aluminum','ヘアラインアルミ','Brushed aluminum','metal',[170,177,180]),
  ('cobalt-ceramic','コバルトセラミック','Cobalt ceramic','tiles',[43,89,118])]:texture(*args)
