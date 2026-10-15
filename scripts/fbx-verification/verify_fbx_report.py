"""Read-only adapter for frozen Meshcopia schema-v2 Blender reports. No export/import."""
from pathlib import Path, PurePosixPath
import hashlib, json, math, struct, re
PIPELINE = '89cdfcdcb1d84495c2fcecf34d944143a38137488dd62ef7b510a6b8576249ac'
RECIPES = ('convert_and_audit_fbx.py','normalize_fbx_materials.py','deterministic_fbx.py')
LIMITS = [
 'Blender-to-Blender evidence only; Unity and other consumers are not tested.',
 'FBX Phong is not lossless glTF metallic-roughness PBR; AO, IOR and physical transmission lack portable mappings.',
 'Roughness/shininess connections may require adjustment in other applications.',
 'Source single-sided culling is not retained; configure target-application culling as needed.',
 'Tangents/binormals are not exported; consumers recompute tangents from preserved normals and UVs.',
 'Per-corner numerical measurements are from the hash-bound converter report, not independently remeasured by this adapter.'
]
def need(ok, text):
 if not ok: raise ValueError(text)
def digest(data): return hashlib.sha256(data).hexdigest()
def filehash(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def finite(v):
 if isinstance(v,(int,float)) and not isinstance(v,bool):need(math.isfinite(v),'Nonfinite number')
 elif isinstance(v,list):
  for x in v:finite(x)
 elif isinstance(v,dict):
  for x in v.values():finite(x)
def relative(p):
 return isinstance(p,str) and p and not p.startswith('/') and '\\' not in p and ':' not in p and all(x not in ('','.','..') for x in p.split('/')) and not any(ord(x)<32 for x in p)
def safe_local(root,rel):
 need(relative(rel),'Unsafe relative local input');p=root/rel;need(p.resolve().is_relative_to(root.resolve()),'Input escapes root');return p
def unique(items,label):need(len(items)==len(set(items)),'Duplicate '+label)
def numeric(v,limit,label):need(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<limit,label+' exceeds threshold')
def maxdelta(a,b):
 if isinstance(a,list):need(isinstance(b,list) and len(a)==len(b),'Numeric shape mismatch');return max((maxdelta(x,y) for x,y in zip(a,b)),default=0)
 need(type(a) in (int,float) and type(b) in (int,float) and math.isfinite(a) and math.isfinite(b),'Invalid numeric data');return abs(a-b)
def fbx_container(data):
 """Bounded binary FBX 7400 parser. Skip array payloads, inspect structural nodes."""
 need(data[:23]==b'Kaydara FBX Binary  \x00\x1a\x00','Invalid FBX header');need(struct.unpack_from('<I',data,23)[0]==7400,'Unsupported FBX version')
 nodes=[]
 def node(pos,depth=0):
  need(depth<128 and pos+13<=len(data),'Invalid FBX nesting/header');end,count,nbytes,nlen=struct.unpack_from('<IIIB',data,pos)
  if end==0:need(data[pos:pos+13]==bytes(13),'Invalid FBX null record');return None,pos+13
  need(pos+13+nlen<=end<=len(data) and count<1000000,'Invalid FBX node extent');name=data[pos+13:pos+13+nlen].decode();cursor=pos+13+nlen;props_start=cursor;props=[]
  for _ in range(count):
   need(cursor<end,'Truncated FBX property');kind=chr(data[cursor]);cursor+=1
   if kind in 'YCIFDL':
    fmt={'Y':'h','C':'?','I':'i','F':'f','D':'d','L':'q'}[kind];size=struct.calcsize('<'+fmt);need(cursor+size<=end,'Truncated scalar');props.append(struct.unpack_from('<'+fmt,data,cursor)[0]);cursor+=size
   elif kind in 'SR':
    need(cursor+4<=end,'Truncated string length');size=struct.unpack_from('<I',data,cursor)[0];cursor+=4;need(cursor+size<=end,'Truncated string');props.append(data[cursor:cursor+size]);cursor+=size
   elif kind in 'fdlibc':
    need(cursor+12<=end,'Truncated array');length,encoding,size=struct.unpack_from('<III',data,cursor);cursor+=12;need(encoding in (0,1) and cursor+size<=end,'Invalid array');props.append(None);cursor+=size
   else:raise ValueError('Unknown FBX property type')
  need(cursor-props_start==nbytes,'FBX property extent mismatch');children=[]
  while cursor<end:
   child,cursor=node(cursor,depth+1)
   if child is not None:children.append(child)
   else:break
  need(cursor==end,'FBX child extent mismatch');obj=(name,props,children);nodes.append(obj);return obj,end
 pos=27
 while True:
  n,pos=node(pos)
  if n is None:break
 embedded=[];axes={};texture_refs=[]
 for name,props,children in nodes:
  if name=='Video':
   c={n:p for n,p,_ in children};raw=c.get('Content',[b''])[0];filename=c.get('RelativeFilename',[b''])[0].decode();need(relative(filename) and filename.startswith('textures/') and len(raw)>0,'Unsafe/missing embedded image');embedded.append({'relativeFilename':filename,'embeddedBytes':len(raw),'sha256':digest(raw)})
  if name=='Texture':
   c={n:p for n,p,_ in children}
   for key in ('FileName','Filename','RelativeFilename'):
    if key in c:
     ref=c[key][0].decode();need(relative(ref) and ref.startswith('textures/'),'Unsafe FBX texture dependency');texture_refs.append(ref)
  if name=='GlobalSettings':
   for n,p,ch in children:
    if n=='Properties70':
     for nn,pp,_ in ch:
      if nn=='P' and pp and isinstance(pp[0],bytes):
       key=pp[0].decode()
       if key in ('UpAxis','UpAxisSign','FrontAxis','FrontAxisSign','CoordAxis','CoordAxisSign','UnitScaleFactor'):axes[key]=pp[-1]
 need(not any(n in ('LayerElementTangent','LayerElementBinormal') for n,_,_ in nodes),'Tangent/binormal arrays unexpectedly exported')
 unique([e['relativeFilename'] for e in embedded],'embedded filename');need(set(texture_refs)==set(e['relativeFilename'] for e in embedded),'FBX Texture/Video dependency closure differs')
 need(axes=={'UpAxis':1,'UpAxisSign':1,'FrontAxis':2,'FrontAxisSign':1,'CoordAxis':0,'CoordAxisSign':1,'UnitScaleFactor':100.0},'FBX axis/unit mismatch')
 need(b'/workspace/' not in data and b'/tmp/' not in data,'Workspace path embedded in FBX')
 return {'fbxVersion':7400,'globalSettings':axes,'embeddedImages':embedded,'tangentExported':False,'binormalExported':False}
def validate_measurements(r):
 finite(r);need(r['schemaVersion']==2,'Unsupported report schema');b,a,o=r['before'],r['after'],r['originalGlbImportedScene'];g=r['geometry']
 for scene in (b,a,o):
  unique([x['name'] for x in scene['objects']],'object name')
  for obj in scene['objects']:
   for key in ('vertices','triangles','uvLayers','materialSlots','colorLayers'):need(type(obj[key]) is int and obj[key]>=0,'Invalid object count')
   need(bool(re.fullmatch('[0-9a-f]{64}',obj['triangleVertexIndexSha256'])) and all(re.fullmatch('[0-9a-f]{64}',h) for h in obj['uvLayerHashes'].values()),'Invalid object hash')
  need(scene['meshObjectCount']==len(scene['objects']) and scene['meshObjectCount']>0,'Object count mismatch')
  for total,field in [('triangleCount','triangles'),('vertexCount','vertices')]:need(scene[total]==sum(x[field] for x in scene['objects']) and scene[total]>0,'Geometry count mismatch')
  for key in ('nonFinitePositions','nonFiniteNormals','nonFiniteUvs','zeroLengthNormals','uvMissingCorners'):need(scene[key]==0,'Invalid geometry '+key)
  need(maxdelta(scene['dimensionsBlenderZUpMeters'],[scene['boundsBlenderZUpMeters'][1][i]-scene['boundsBlenderZUpMeters'][0][i] for i in range(3)])<1e-12,'Dimension/bounds inconsistency')
 for key in ('meshObjectCount','triangleCount','vertexCount'):need(b[key]==a[key]==o[key],'Changed geometry count')
 need([x['name'] for x in b['objects']]==[x['name'] for x in a['objects']]==[x['name'] for x in o['objects']],'Changed object names')
 for bo,ao,oo in zip(b['objects'],a['objects'],o['objects']):
  need(bo['materialSlots']==ao['materialSlots'],'Roundtrip material slots changed')
  for key in ('vertices','triangles','triangleVertexIndexSha256','colorLayers'):need(bo[key]==ao[key]==oo[key],'Changed object '+key)
  for obj in (bo,ao,oo):need(obj['uvLayers']==len(obj['uvLayerHashes']),'UV count mismatch')
  need(bo['uvLayerHashes']==ao['uvLayerHashes'],'Roundtrip UV hashes differ')
  need(set(oo['uvLayerHashes'].values())<=set(ao['uvLayerHashes'].values()),'Original UV lost')
 need(o['geometryQuantizedMicrometerSha256']==b['geometryQuantizedMicrometerSha256'],'Normalization changed source geometry hash')
 tolerance=max(5e-5,max(b['dimensionsBlenderZUpMeters'])*5e-6);need(g['positionToleranceMeters']==tolerance,'Declared tolerance changed')
 bounds=maxdelta(b['boundsBlenderZUpMeters'],a['boundsBlenderZUpMeters']);need(abs(bounds-g['maxBoundsDeltaMeters'])<1e-12,'Bounds measurement mismatch');numeric(bounds,tolerance,'bounds')
 for key,threshold in [('maxCorrespondingCornerPositionDeltaMeters',tolerance),('maxCorrespondingCornerUvDelta',2e-5),('maxCorrespondingCornerColorDelta',2e-5),('maxCorrespondingCornerNormalAngleDegrees',.1)]:numeric(g[key],threshold,key)
 # No raw corner vectors/assignment arrays are persisted. Retain this attested
 # measurement boundary explicitly; never substitute aggregate passed flags.
 need(g['materialAssignmentsEqual'] is True and g['sourceGeometryUnchangedByNormalization'] is True,'Converter correspondence attestation absent')
 color=r['vertexColorFileVerification'];need(color['sourceUniqueColors']==color['fbxUniqueColors'],'Raw color count changed');numeric(color['maxRawEncodedColorDelta'],2e-6,'raw color');need(color['linearBlenderReimportMaxDelta']==g['maxCorrespondingCornerColorDelta'],'Color measurement mismatch')
 need(set(b['materials'])==set(a['materials'])==set(r['materialComparison']),'Material inventory changed')
 for name,bm in b['materials'].items():
  am=a['materials'][name];need(set(bm['values'])==set(am['values']),'Material parameter inventory mismatch');delta=max(maxdelta(v,am['values'][k]) for k,v in bm['values'].items());numeric(delta,2e-5,'material value')
  need(set(i['pixelSha256'] for i in bm['images'])==set(i['pixelSha256'] for i in am['images']),'Image pixel hash mismatch')
  bc,ac=bm['textureConnections'],am['textureConnections'];extra=set(ac)-set(bc)
  need(not extra or extra=={'alpha'} and ac['alpha']['alphaRange']==[1.0,1.0] and bm['values']['alpha']==1,'Unexpected texture link')
  need(all(k in ac and v==ac[k] for k,v in bc.items()),'Texture connection mismatch')
  c=r['materialComparison'][name];need(c['valuesBefore']==bm['values'] and c['valuesAfter']==am['values'] and abs(c['materialValuesMaxDelta']-delta)<1e-12,'Material measurement mismatch')
 return {'positionToleranceMeters':tolerance,'maxBoundsDeltaMeters':bounds,**{k:g[k] for k in ('maxCorrespondingCornerPositionDeltaMeters','maxCorrespondingCornerUvDelta','maxCorrespondingCornerColorDelta','maxCorrespondingCornerNormalAngleDegrees')},'triangleCount':a['triangleCount'],'vertexCount':a['vertexCount'],'meshObjectCount':a['meshObjectCount']}
def report_shape(r):
 schema=json.loads((Path(__file__).resolve().parents[2]/'docs/fbx-verification/schema/fbx-report-input-schema.json').read_text())
 need(isinstance(r,dict) and set(r)==set(schema['required']),'Unknown/missing report field')
 types={'boolean':bool,'object':dict,'array':list,'integer':int,'string':str}
 for k,rule in schema['properties'].items():
  if 'const' in rule:need(r[k]==rule['const'],'Report version mismatch')
  else:need(type(r[k]) is types[rule['type']],'Wrong report field type '+k)
 finite(r)
def verify_report(report_bytes,row,source_bytes,fbx_bytes,recipe_hashes,runtime,addon_hashes,clean_root):
 need(digest(report_bytes)==row['qaSha256'],'Report hash mismatch');r=json.loads(report_bytes);report_shape(r);need(r['id']==row['id'],'Report identity mismatch')
 need(digest(source_bytes)==row['sourceGlbSha256']==r['sourceGlbSha256'],'Source hash mismatch');need(len(fbx_bytes)==row['fbxBytes']==r['fbxBytes'] and digest(fbx_bytes)==row['fbxSha256']==r['fbxSha256'],'FBX bytes/hash mismatch')
 need(r['recipeSha256']==recipe_hashes and digest(canonical(recipe_hashes).encode())==PIPELINE,'Recipe/pipeline mismatch');need(r['runtime']==runtime and r['blenderVersion']==runtime['blender'],'Runtime mismatch');need(r['deterministicExport']['addonSourceSha256']==addon_hashes,'Exporter addon hash mismatch');need(r['deterministicExport']['pythonHashSeed']=='0' and r['deterministicExport']['fixedHeaderTime']=='1970-01-01T10:00:00','Deterministic settings mismatch')
 need(r['exportSettings']['use_tspace'] is False and r['exportSettings']['embed_textures'] is True and r['exportSettings']['axis_up']=='Y' and r['exportSettings']['axis_forward']=='-Z' and r['exportSettings']['colors_type']=='LINEAR','Export settings mismatch')
 measures=validate_measurements(r);actual=fbx_container(fbx_bytes)
 for key in actual:need(r['container'][key]==actual[key],'Container measurement mismatch '+key)
 refs=r['deterministicExport']['embeddedTextureReferences'];embedded={x['relativeFilename']:x for x in actual['embeddedImages']};unique([x['relativePath'] for x in refs],'embedded reference');need(set(x['relativePath'] for x in refs)==set(embedded),'Embedded reference closure mismatch')
 for x in refs:need(x['packedSha256']==embedded[x['relativePath']]['sha256'] and x['packedBytes']==embedded[x['relativePath']]['embeddedBytes'],'Embedded byte/hash mismatch')
 imported=set();extracted_available=True
 for mat in r['after']['materials'].values():
  for image in mat['images']:
   p=Path(image['filepath']);need(p.is_absolute() and p.resolve().is_relative_to(clean_root.resolve()),'Image escapes clean reimport');rel=p.resolve().relative_to(clean_root.resolve()).as_posix();need(rel in embedded,'Imported image is not embedded');need(image['resolvedInsideCleanReimport'] is True,'Missing clean image evidence');
   if p.exists():need(p.is_file() and p.stat().st_size==embedded[rel]['embeddedBytes'] and filehash(p)==embedded[rel]['sha256'],'Clean image bytes mismatch')
   else:extracted_available=False
   imported.add(rel)
 need(imported==set(embedded),'Unused/unresolved embedded image closure')
 need(len(r['limits'])>=4 and any('tangent' in x.lower() for x in r['limits']) and any('culling' in x.lower() for x in r['limits']) and any('Unity' in x for x in r['limits']),'Missing limitations')
 # Whitelist projection: never copy absolute source/image paths or mixed-cohort
 # manifest limitations. Per-model path-bearing data remains in private audit.
 return {'id':row['id'],'sourceGlbSha256':r['sourceGlbSha256'],'fbx':{'filename':row['id']+'.fbx','bytes':len(fbx_bytes),'sha256':r['fbxSha256']},'originalReportSha256':row['qaSha256'],'sourceRelativePath':'content/assets/'+row['id']+'/source/'+row['id']+'.glb','pipelineSha256':PIPELINE,'runtime':runtime,'recipeSha256':recipe_hashes,'addonSourceSha256':addon_hashes,'measurements':measures,'embeddedImages':actual['embeddedImages'],'tangentExported':False,'cleanImportEvidence':{'reportAttestedClosure':True,'embeddedBytesIndependentlyChecked':True,'extractedCopiesAvailable':extracted_available},'limitations':LIMITS.copy()}
def validate_public_schema(value,schema):
 if 'const' in schema:need(value==schema['const'],'Public schema constant mismatch')
 kind=schema.get('type')
 if kind=='object':
  need(type(value) is dict and set(value)==set(schema['required']),'Public schema object fields mismatch')
  for k,v in value.items():validate_public_schema(v,schema['properties'][k])
 elif kind=='array':
  need(type(value) is list,'Public schema array type')
  for v in value:validate_public_schema(v,schema['items'])
 elif kind=='string':need(type(value) is str and len(value)>=schema.get('minLength',0),'Public schema string')
 elif kind=='boolean':need(type(value) is bool,'Public schema boolean')
 elif kind in ('number','integer'):
  need(type(value) in ((int,) if kind=='integer' else (int,float)) and math.isfinite(value) and value>=schema.get('minimum',-math.inf),'Public schema numeric')
def public_cohort(records,public_allowlist):
 allowed=set(public_allowlist);unique([r['id'] for r in records],'public record');need(all(r['id'] in allowed for r in records),'Private/unapproved model cannot enter public cohort')
 expected={'id','sourceGlbSha256','sourceRelativePath','fbx','originalReportSha256','pipelineSha256','runtime','recipeSha256','addonSourceSha256','measurements','embeddedImages','tangentExported','cleanImportEvidence','limitations'}
 for r in records:
  need(set(r)==expected,'Unknown/missing public QA field');need(r['limitations']==LIMITS,'Unreviewed cohort limitations');need(relative(r['sourceRelativePath']) and r['sourceRelativePath'].startswith('content/assets/'+r['id']+'/source/'),'Invalid public source provenance')
  encoded=json.dumps(r);need(not any(p in encoded for p in ('/workspace/','/tmp/','/home/','/Users/','file://','\\\\')),'Local path in public projection')
 cohort={'schemaVersion':1,'scope':'Selected verified public models only; no claim of full FBX coverage','records':records}
 schema=json.loads((Path(__file__).resolve().parents[2]/'docs/fbx-verification/schema/fbx-public-qa-schema.json').read_text());validate_public_schema(cohort,schema)
 return cohort
