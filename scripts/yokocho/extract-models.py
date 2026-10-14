import json,struct,copy,hashlib,math,os
from pathlib import Path
import numpy as np
OUT=Path(os.environ.get('YOKOCHO_OUTPUT',Path(__file__).parent));OUT.mkdir(parents=True,exist_ok=True)
SOURCE_ROOT=Path(os.environ.get('YOKOCHO_SOURCE_ROOT',Path(__file__).resolve().parents[2]/'tree-baseline-v219'/'TreeTopYokocho'))
SRC=SOURCE_ROOT/'Source'/'TreeTopYokocho.glb'
b=SRC.read_bytes(); jl=struct.unpack_from('<I',b,12)[0]; J=json.loads(b[20:20+jl]); blob=b[28+jl:]
def arr(i):
 a=J['accessors'][i];v=J['bufferViews'][a['bufferView']]; dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]; n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];return np.ndarray((a['count'],n),dtype=dt,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*n),np.dtype(dt).itemsize)).copy()
def pal(name):
 s=name.lower(); c=[.52,.55,.57,1];metal=0;rough=.65
 if any(k in s for k in ['wood','timber','cedar','walnut','chestnut','cypress','counter']):c=[.39,.23,.12,1];rough=.7
 if any(k in s for k in ['iron','charcoal','speaker','cable']):c=[.055,.065,.075,1];metal=.35
 if any(k in s for k in ['bronze','copper','trim']):c=[.48,.29,.12,1];metal=.65
 if any(k in s for k in ['paper','cream','ceramic','enamel','gauge','light','window']):c=[.82,.78,.63,1];rough=.55
 if any(k in s for k in ['wine','oxblood','upholstery']):c=[.28,.07,.10,1]
 if any(k in s for k in ['indigo','blue']):c=[.07,.17,.29,1]
 if any(k in s for k in ['teal','green']):c=[.07,.29,.23,1]
 if 'leather' in s:c=[.17,.105,.07,1]
 return {'name':'Neutral replacement - '+name,'pbrMetallicRoughness':{'baseColorFactor':c,'metallicFactor':metal,'roughnessFactor':rough},'doubleSided':True}
rows=[]
def add(slug,ja,en,prefix,category='props',source='nightlife_venues.py',note=''):
 rows.append(dict(id='yokocho-'+slug,title=ja,titleEn=en,prefix=prefix,category=category,generator=source,note=note))
for i,(slug,ja,en) in enumerate([('dragon-ember-sign','竜と熾火の立体看板','Dragon Ember Projecting Sign'),('noodle-guild-sign','麺ギルドの立体看板','Noodle Guild Projecting Sign'),('traveler-pot-sign','旅人の鍋の立体看板','Traveler Pot Projecting Sign'),('witch-moon-sign','魔女と月の立体看板','Witch Moon Projecting Sign'),('moon-tea-sign','月のお茶の木製看板','Moon Tea Timber Sign'),('star-distillery-sign','星の蒸留所の立体看板','Star Distillery Projecting Sign'),('bard-lyre-sign','吟遊詩人の竪琴看板','Bard Lyre Projecting Sign'),('fairy-confection-sign','妖精菓子店の立体看板','Fairy Confection Projecting Sign')],1):
 add(slug,ja,en,f'Shops/S{i:02d}/ProjectingSigns/','signs','venue_projecting_signs.py')
for slug,ja,en,prefix,cat in [
 ('snack-chair','スナックの背付き椅子','Snack Bar Upholstered Chair','S04/Personality/Seating/4_snack','furniture'),
 ('cocktail-stool','カクテルバーのハイスツール','Cocktail Bar High Stool','S06/Personality/Seating/1_cocktail','furniture'),
 ('club-armchair','ラウンジの肘掛け椅子','Lounge Club Armchair','S06/Personality/Seating/5_club','furniture'),
 ('listening-chair','音楽喫茶の肘掛け椅子','Listening Bar Armchair','S07/Personality/Seating/1_listening','furniture'),
 ('banquette','三席のボタン留めベンチ','Three-Seat Upholstered Banquette','S04/Personality/Seating/Banquette','furniture'),
 ('snack-counter','折れ曲がりスナックカウンター','Bent Snack Bar Counter','S04/Personality/BentSnackCounter','furniture'),
 ('walnut-counter','段付きウォールナットカウンター','Stepped Walnut Bar Counter','S06/Personality/SteppedWalnutCounter','furniture'),
 ('listening-counter','直角の音楽喫茶カウンター','Right-Angle Listening Bar Counter','S07/Personality/RightAngleListeningBar','furniture'),
 ('booth-table','スナックのボックス席テーブル','Snack Booth Table','S04/Personality/BoothTable','furniture'),
 ('lounge-table','ラウンジテーブル','Lounge Table','S06/Personality/LoungeTable','furniture'),
 ('bottle-keep-wall','ボトルキープ棚','Bottle-Keep Display Wall','S04/Personality/BottleKeepWall','furniture'),
 ('geometric-backbar','幾何学バックバー棚','Geometric Backbar Display','S06/Personality/GeometricBackbar','furniture'),
 ('record-library','レコード棚とスピーカーセット','Record Library and Speaker Set','S07/Personality/RecordLibrary','furniture'),
 ('turntable-amplifier','ターンテーブルとアンプ','Turntable and Amplifier Set','S07/Personality/TurntableAndAmplifier','electronics'),
 ('medallion-chandelier','メダリオン型五灯シャンデリア','Five-Light Medallion Chandelier','S04/Personality/MedallionCeiling','lighting'),
 ('pendant-ceiling','バーのペンダント照明セット','Bar Pendant Lighting Set','S06/Personality/PendantCeiling','lighting')]:
 add(slug,ja,en,'Shops/'+prefix,cat)
add('noh-pavilion','瓦屋根の能舞台','Tiled Noh Stage Pavilion','Stage/Noh/','architecture','noh_stage.py; noh_roof_detail.py','舞台下の支持構造を含みます。 / Includes the under-stage support structure.')
add('booster-pump-skid','地上用増圧ポンプユニット','Ground Booster Pump Unit','Infrastructure/Boosters/Ground','industrial','booster_pumps.py')
add('upper-water-storage','高所貯水タンクユニット','Elevated Water Storage Unit','Infrastructure/Boosters/UpperStorage','industrial','booster_pumps.py')
add('timber-stair-flight','木造階段ユニット','Timber Stair Flight','Stairs/R01','architecture','build_world.py')
add('telecom-mast','通信アンテナマスト','Telecommunications Mast','Infrastructure/Telecom/Mast','industrial','tree_infrastructure.py')
add('utility-service-bank','配管サービスバンク','Utility Service Bank','Infrastructure/Ground/ServiceBank','industrial','tree_infrastructure.py')
for slug,ja,en,pre in [
 ('charcoal-stool-set','炭火店の木製スツールセット','Charcoal Bar Timber Stool Set','Shops/S01/Personality/CharcoalSeats'),
 ('noodle-stool-set','麺処の金属脚スツールセット','Noodle Diner Tubular Stool Set','Shops/S02/Personality/NoodleSeats'),
 ('oden-bench-set','おでん屋のベンチ二脚セット','Oden Nook Two-Bench Set','Shops/S03/Personality/OdenBenches'),
 ('tea-furniture-set','茶亭のテーブルと格子椅子セット','Tea Pavilion Tables and Lattice Chairs','Shops/S05/Personality/TeaFurniture'),
 ('confectioner-stool-set','菓子店のペデスタルスツールセット','Confectioner Pedestal Stool Set','Shops/S08/Personality/ConfectionerSeats'),
 ('mixology-tools','シェーカーとジガーのバーツールセット','Cocktail Shaker Jigger and Tray Kit','Shops/S06/Personality/MixologyTools')]:
 add(slug,ja,en,pre,'furniture' if 'stool' in slug or 'bench' in slug or 'furniture' in slug else 'props','food_venues.py' if 'mixology' not in slug else 'nightlife_venues.py')
SAFE={'Food_Upholstery':'woven.png; woven_normal.png','Noren3':'woven.png; woven_normal.png; woven_arm.png','Night_WineUpholstery':'woven.png; woven_normal.png','Night_IndigoUpholstery':'woven.png; woven_normal.png','Night_Print':'nightlife_signs.png','Kawara':'tile_clay.png; tile_clay_normal.png; tile_clay_arm.png','PaperLight':'lantern.png'}
rows=[r for r in rows if r['id'] != 'yokocho-fairy-confection-sign']
manifest=[]
for row in rows:
 nodes=[n for n in J['nodes'] if n.get('name','').startswith(row['prefix'])]
 if row['id']=='yokocho-bottle-keep-wall':nodes=[n for n in nodes if not n['name'].endswith('__Bronze')]
 assert nodes,row
 positions=np.concatenate([arr(p['attributes']['POSITION']) for n in nodes for p in J['meshes'][n['mesh']]['primitives']]); mn=positions.min(0);mx=positions.max(0); center=(mn+mx)/2;center[1]=mn[1]
 # Keep world yaw, offset only. Authored accessors remain byte-for-byte identical.
 doc={'asset':{'version':'2.0','generator':'TreeTopYokocho original geometry subset; original authored PNGs retained, external scanned materials replaced with neutral PBR'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':row['id'],'translation':(-center).tolist(),'children':list(range(1,len(nodes)+1))}],'meshes':[],'materials':[],'accessors':[],'bufferViews':[],'buffers':[]}
 out=bytearray();am={};vm={};mm={};tri=0;uv=0;im={};tm={};sm={};preserved=[];replaced=[];stlfaces=[]
 def accessor(i):
  if i in am:return am[i]
  a=copy.deepcopy(J['accessors'][i]);vi=a['bufferView']
  if vi not in vm:
   v=copy.deepcopy(J['bufferViews'][vi]);start=v.get('byteOffset',0);data=blob[start:start+v['byteLength']];out.extend(b'\0'*((-len(out))%4));v['byteOffset']=len(out);v['buffer']=0;vm[vi]=len(doc['bufferViews']);doc['bufferViews'].append(v);out.extend(data)
  a['bufferView']=vm[vi];am[i]=len(doc['accessors']);doc['accessors'].append(a);return am[i]
 def texture(i,filename):
  key=(i,filename)
  if key in tm:return tm[key]
  tex=copy.deepcopy(J['textures'][i])
  if filename not in im:
   data=(SRC.parent.parent/'Assets/TreeTopYokocho/Textures'/filename).read_bytes();out.extend(b'\0'*((-len(out))%4));vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(out),'byteLength':len(data)});out.extend(data);im[filename]=len(doc.setdefault('images',[]));doc['images'].append({'name':filename,'mimeType':'image/png','bufferView':vi})
  tex['source']=im[filename]
  if 'sampler' in tex:
   si=tex['sampler']
   if si not in sm:sm[si]=len(doc.setdefault('samplers',[]));doc['samplers'].append(copy.deepcopy(J['samplers'][si]))
   tex['sampler']=sm[si]
  tm[key]=len(doc.setdefault('textures',[]));doc['textures'].append(tex);return tm[key]
 def material(mi):
  m=copy.deepcopy(J['materials'][mi]);name=m['name'];p=m['pbrMetallicRoughness']
  if 'baseColorTexture' in p and name not in SAFE:
   replaced.append(name);return pal(name)
  preserved.append(name)
  for ob in [m,p]:
   for k,v in ob.items():
    if k.endswith('Texture') and isinstance(v,dict):
     base=SAFE[name].split(';')[0];filename=base
     if k=='normalTexture':filename=base.replace('.png','_normal.png')
     if k in ('metallicRoughnessTexture','occlusionTexture'):filename=base.replace('.png','_arm.png')
     v['index']=texture(v['index'],filename)
  return m
 for node in nodes:
  assert set(node)<= {'name','mesh'},node
  mesh=copy.deepcopy(J['meshes'][node['mesh']]);
  for p in mesh['primitives']:
   assert p.get('mode',4)==4
   tri+=J['accessors'][p['indices']]['count']//3
   stlfaces.append(arr(p['attributes']['POSITION'])[arr(p['indices']).ravel()].reshape(-1,3,3)-center)
   uv+=int('TEXCOORD_0' in p['attributes'])
   p['attributes']={k:accessor(v) for k,v in p['attributes'].items()};p['indices']=accessor(p['indices']);mi=p['material']
   if mi not in mm:mm[mi]=len(doc['materials']);doc['materials'].append(material(mi))
   p['material']=mm[mi]
  doc['nodes'].append({'name':node['name'],'mesh':len(doc['meshes'])});doc['meshes'].append(mesh)
 out.extend(b'\0'*((-len(out))%4));doc['buffers']=[{'byteLength':len(out)}];raw=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();raw+=b' '*((-len(raw))%4);glb=struct.pack('<III',0x46546c67,2,28+len(raw)+len(out))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(out),0x004e4942)+out
 folder=OUT/row['id'];folder.mkdir(exist_ok=True);(folder/'model.glb').write_bytes(glb)
 faces=np.concatenate(stlfaces).astype('<f4');norm=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]);length=np.linalg.norm(norm,axis=1);norm/=np.maximum(length[:,None],1e-20);dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);records=np.zeros(len(faces),dtype=dt);records['n']=norm;records['v']=faces;(folder/'model.stl').write_bytes(b'TreeTopYokocho - meters Y up - solid geometry only'.ljust(80,b' ')+struct.pack('<I',len(faces))+records.tobytes())
 row.update(triangles=tri,dimensions=(mx-mn).round(6).tolist(),unit='m',upAxis='Y',sourceNodes=[n['name'] for n in nodes],sourceTranslation=(-center).tolist(),file=str(folder/'model.glb'),thumbnail=str(folder/'preview.png'),preservedMaterials=preserved,replacedMaterials=replaced,embeddedImageCount=len(im),originalTextureSources={n:SAFE[n] for n in preserved if n in SAFE},stlFile=str(folder/'model.stl'),meshCount=len(nodes),uvMeshCount=uv,sourceSha256=hashlib.sha256(b).hexdigest(),sha256=hashlib.sha256(glb).hexdigest(),bytes=len(glb),uvNotes='Source TEXCOORD_0 buffers preserved byte-for-byte. Authored tiling/atlas coordinates may overlap and extend beyond 0–1; no new unwrap, UV2 or lightmap UVs. Original authored vertex colors preserved; allowlisted procedural/printed source PNGs embedded byte-for-byte (higher-fidelity replacements for the source GLB JPEG/resized encoding). Sampler definitions remain unchanged. External scanned materials replaced with textureless solid-color neutral PBR. STL contains geometry only and has no UVs, textures, or materials.',description=f'樹上横丁のオリジナル形状から切り出した{row["title"]}。原寸・底面中央原点。外部スキャン材質のみ単色PBRに置換し、該当するオリジナル布・印刷・瓦・紙テクスチャは保持。'+row['note'],descriptionEn=f'{row["titleEn"]} extracted from original TreeTopYokocho geometry at authored scale, centered horizontally with the base at Y=0. External scanned materials are replaced with solid-color neutral PBR; applicable original cloth, printed, tile and paper source PNGs are embedded unchanged. '+row['note'])
 manifest.append(row); print(row['id'],tri,row['dimensions'],len(glb),flush=True)
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
