"""Group original static Meshcopia city repetitions without changing surface geometry.
Original GLBs remain untouched. Requires numpy from the existing asset toolchain.
Preserves per-corner vertices/UVs/normals and original PBR material records; no weld,
remesh, decimation, texture bake, new model ID, or performance/FPS assertion.
"""
from pathlib import Path
from collections import OrderedDict
import argparse,copy,hashlib,json,math,shutil,struct
import numpy as np

TYPES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
DTYPES={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}

def read_glb(path):
 raw=Path(path).read_bytes();assert raw[:4]==b'glTF' and struct.unpack_from('<I',raw,4)[0]==2
 size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
 assert not doc.get('animations') and not doc.get('skins') and not doc.get('images') and not doc.get('textures')
 return doc,binary

def accessor(doc,binary,index):
 a=doc['accessors'][index];assert not a.get('sparse')
 v=doc['bufferViews'][a['bufferView']];dtype=np.dtype(DTYPES[a['componentType']]);n=TYPES[a['type']]
 start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',n*dtype.itemsize)
 return np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=start,strides=(stride,dtype.itemsize)).copy()

def matrix(node):
 if 'matrix' in node:return np.array(node['matrix'],dtype=np.float64).reshape((4,4),order='F')
 x,y,z,w=node.get('rotation',[0,0,0,1]);q=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 m=np.eye(4);m[:3,:3]=q@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m

def primitives(doc,binary):
 result=[]
 def visit(index,parent):
  node=doc['nodes'][index];world=parent@matrix(node)
  if 'mesh' in node:
   for p in doc['meshes'][node['mesh']]['primitives']:
    assert p.get('mode',4)==4 and not p.get('targets')
    assert set(p['attributes'])=={'POSITION','NORMAL','TEXCOORD_0'},'Unexpected attribute set; refuse rather than discard.'
    attrs={key:accessor(doc,binary,value) for key,value in p['attributes'].items()}
    attrs['POSITION']=attrs['POSITION'].astype(np.float64)@world[:3,:3].T+world[:3,3]
    normal=attrs['NORMAL'].astype(np.float64)@np.linalg.inv(world[:3,:3]);normal/=np.linalg.norm(normal,axis=1)[:,None];attrs['NORMAL']=normal
    indices=accessor(doc,binary,p['indices']).reshape(-1) if 'indices' in p else np.arange(len(attrs['POSITION']),dtype=np.uint32)
    assert np.linalg.det(world[:3,:3])>0,'Negative determinant requires an explicit winding review.'
    result.append({'name':node.get('name',f'Component {index}'),'material':p['material'],'attrs':attrs,'indices':indices,'sourceNode':index})
  for child in node.get('children',[]):visit(child,world)
 for index in doc['scenes'][doc.get('scene',0)]['nodes']:visit(index,np.eye(4))
 return result

def group_name(slug,name,attrs):
 def starts(*prefixes):return name.startswith(prefixes)
 if slug=='city-solar-module-rack':
  if starts('Fine cell busbar'):return 'Module conductor array / static'
  if starts('Individual silicon cell'):return 'Module silicon cell array / static'
  if starts('Module perimeter'):return 'Module aluminum perimeter'
 if slug=='city-scaffold-bay':
  if starts('Hollow scaffold standard'):return 'Four scaffold standards'
  if starts('Standard connection collar'):return 'Standard collar assembly'
  if starts('Longitudinal ledger','End transverse ledger'):return 'Fixed horizontal scaffold frame'
  if starts('Screw jack thread'):return 'Screw-jack thread assembly'
  if starts('Collar securing bolt'):return 'Standard collar fasteners'
  if starts('Deck end reinforcement band'):return 'Deck reinforcement bands'
  if starts('Deck plank fastener'):return 'Deck plank fasteners'
  if starts('Access ladder stile','Ladder rung'):return 'Integrated access ladder'
  if starts('Brace terminal pin'):return 'Diagonal brace connection pins'
 if slug=='city-inspection-cover':
  if starts('Removable inspection lid','Lid concentric ridge','Center medallion ridge','Unbranded central medallion','Raised diamond tread','Lift recess cast shoulder','Underside stiffener'):return 'Removable inspection lid assembly'
 if slug=='city-hvac-condenser':
  if starts('Heat exchanger vertical fin'):return 'Rear heat exchanger fin array'
  if starts('Concentric fan safety guard','Guard radial spoke','Guard central cap'):return 'Front fan safety guard assembly'
  if starts('Fan motor','Swept axial fan blade'):return 'Static fan and motor assembly'
  if starts('Cabinet screw'):return 'Cabinet fastener assembly'
  if starts('Side electrical cooling slot'):return 'Electrical enclosure vent slots'
 if slug=='city-roller-shutter':
  if starts('Interlocking convex shutter slat'):return 'Closed interlocking shutter curtain'
  if starts('Track closed side web','Track retaining flange'):return ('Left' if attrs['POSITION'][:,0].mean()<0 else 'Right')+' shutter guide channel'
  if starts('Guide track fixing'):return 'Shutter guide anchors'
  if starts('Pull handle standoff','Recessed shutter pull'):return 'Shutter pull handle pair'
  if starts('Headbox front cover','Headbox upper cover','Headbox rear return'):return 'Folded shutter headbox cover'
 if slug=='city-ventilation-outlet':
  if starts('Louver blade'):return 'Sloping louver blade array'
  if starts('Louver rolled drip lip'):return 'Louver drip lip array'
  if starts('Rear insect screen'):return 'Rear insect screen grid'
  if starts('Flange screw'):return 'Vent mounting fasteners'
 if slug=='city-cable-tray-elbow':
  if starts('Continuous curved deck rail','Radial deck bridge'):return 'Perforated cable-tray deck'
  if starts('Side web','Folded upper stiffening lip','Perforated side web post','Joining end web'):return 'Curved cable-tray side walls'
  if starts('End splice bolt'):return 'Cable-tray splice fasteners'
 return name

def pack_glb(original,pieces,slug,path):
 groups=OrderedDict()
 for p in pieces:
  group=group_name(slug,p['name'],p['attrs']);groups.setdefault(group,OrderedDict()).setdefault(p['material'],[]).append(p)
 buffers=[];views=[];accessors=[];meshes=[];nodes=[];offset=0;proof=[]
 def add(array,typ,component=5126,bounds=False):
  nonlocal offset
  array=np.asarray(array,dtype=DTYPES[component]);pad=(-offset)%4
  if pad:buffers.append(b'\0'*pad);offset+=pad
  data=array.tobytes();views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data)});buffers.append(data);offset+=len(data)
  a={'bufferView':len(views)-1,'componentType':component,'count':len(array),'type':typ}
  if bounds:a.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
  accessors.append(a);return len(accessors)-1
 for group,mats in groups.items():
  prims=[]
  for material,parts in mats.items():
   attrs={k:np.concatenate([p['attrs'][k] for p in parts]).astype(np.float32) for k in ['POSITION','NORMAL','TEXCOORD_0']}
   ix=[];base=0
   for p in parts:ix.append(p['indices'].astype(np.uint32)+base);base+=len(p['attrs']['POSITION'])
   indices=np.concatenate(ix);component=5123 if base<65536 else 5125
   fields={k:add(a,'VEC2' if k=='TEXCOORD_0' else 'VEC3',bounds=k=='POSITION') for k,a in attrs.items()}
   prims.append({'attributes':fields,'indices':add(indices,'SCALAR',component),'material':material,'mode':4})
   proof.append({'candidateNode':group,'material':material,'sourceNodes':[p['name'] for p in parts],'sourcePrimitiveCount':len(parts),'triangles':len(indices)//3})
  meshes.append({'name':group,'primitives':prims});nodes.append({'name':group,'mesh':len(meshes)-1})
 doc={'asset':copy.deepcopy(original['asset']),'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,'materials':copy.deepcopy(original['materials']),'buffers':[{'byteLength':offset}],'bufferViews':views,'accessors':accessors}
 doc['asset']['generator']=doc['asset'].get('generator','Meshcopia')+'; geometry-preserving static assembly grouping 1.0'
 for key in ['extensionsUsed','extensionsRequired']:
  if key in original:doc[key]=copy.deepcopy(original[key])
 j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary=b''.join(buffers);binary+=b'\0'*((-len(binary))%4)
 Path(path).write_bytes(struct.pack('<III',0x46546C67,2,28+len(j)+len(binary))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(binary),b'BIN\0')+binary)
 return doc,proof

def verify_equivalence(original,pieces,candidate,binary,proof):
 # Comparison follows explicit source-to-group mapping, not visual similarity or a
 # topology-only hash. Each triangle corner retains its material, normal and UV.
 assert candidate['materials']==original['materials'],'Material semantics changed'
 source_by_name={p['name']:p for p in pieces};actual=primitives(candidate,binary)
 assert len(actual)==len(proof)
 max_errors={'positionMetres':0.0,'normalComponent':0.0,'uvComponent':0.0};tris=0
 for got,mapping in zip(actual,proof):
  parts=[source_by_name[name] for name in mapping['sourceNodes']]
  assert got['material']==mapping['material']
  for key,metric in [('POSITION','positionMetres'),('NORMAL','normalComponent'),('TEXCOORD_0','uvComponent')]:
   want=np.concatenate([p['attrs'][key][p['indices']] for p in parts])
   have=got['attrs'][key][got['indices']];assert want.shape==have.shape
   error=float(np.max(np.abs(want-have)));max_errors[metric]=max(max_errors[metric],error)
   assert error<1e-6,(key,error)
  tris+=len(got['indices'])//3
 assert tris==sum(len(p['indices'])//3 for p in pieces)
 return {'triangles':tris,'materialsExactlyPreserved':True,'allSourceTrianglesRetained':True,'perTriangleCornerMaxError':max_errors,'tolerance':1e-6,'method':'Mapped original source primitive triangles compared with every candidate triangle corner in world Y-up space; material records exact; no deduplication or topology changes.'}

def write_stl(pieces,path):
 records=[]
 for p in pieces:
  tris=p['attrs']['POSITION'][p['indices']].reshape((-1,3,3)).astype(np.float32)
  norm=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-30)[:,None]
  for vertices,normal in zip(tris,norm):records.append(struct.pack('<12fH',*normal,*vertices.flatten(),0))
 Path(path).write_bytes(b'Meshcopia static grouped visual prop; CC BY 4.0; meters Y-up'.ljust(80,b'\0')+struct.pack('<I',len(records))+b''.join(records))

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 a=json.loads((args.input/'asset.json').read_text());slug=a['id'];folder=args.output/slug
 if slug not in {'city-solar-module-rack','city-scaffold-bay','city-inspection-cover','city-hvac-condenser','city-roller-shutter','city-ventilation-outlet','city-cable-tray-elbow'}:ap.error('No reviewed static grouping recipe for '+slug)
 if folder.exists():ap.error('Refusing to overwrite existing candidate: '+str(folder))
 raw=args.input/'source'/a['preview']
 if hashlib.sha256(raw.read_bytes()).hexdigest()!=a['provenance']['sourceSha256']:ap.error('Source GLB hash does not match its asset metadata')
 original,binary=read_glb(raw);pieces=primitives(original,binary)
 if len({p['name'] for p in pieces})!=len(pieces):ap.error('Source has repeated node names or multi-primitive nodes; explicit mapping review required')
 source=folder/'source';source.mkdir(parents=True)
 target=source/a['preview'];doc,mapping=pack_glb(original,pieces,slug,target);candidate,cb=read_glb(target)
 comparison=verify_equivalence(original,pieces,candidate,cb,mapping)
 newpieces=primitives(candidate,cb);write_stl(newpieces,source/(slug+'.stl'))
 a['provenance'].setdefault('baseGeneratorUrl',a['provenance'].get('generatorUrl',''))
 a['provenance']['postprocessGeneratorUrl']='https://github.com/Xenoah/meshcopia/blob/main/scripts/city/group_static_assemblies.py'
 a['provenance']['alternateFormat']='Binary STL written directly from the exact grouped GLB world-space triangle geometry by group_static_assemblies.py; meters, Y-up; no materials, UVs or manufacturing validation.'
 a['status']='draft';a['provenance']['sourceSha256']=hashlib.sha256(target.read_bytes()).hexdigest();a['provenance']['stlSha256']=hashlib.sha256((source/(slug+'.stl')).read_bytes()).hexdigest()
 a['provenance']['changes']='Static repeated mesh parts grouped by original material within named major assemblies; no decimation, remeshing, UV change or material change. Candidate equivalence audited against frozen original GLB '+hashlib.sha256(raw.read_bytes()).hexdigest()+'.'
 a['usages'][0]['sourcePaths'].append('scripts/city/group_static_assemblies.py')
 bounds=np.concatenate([p['attrs']['POSITION'] for p in newpieces]);a['dimensions']=np.round(bounds.max(axis=0)-bounds.min(axis=0),6).tolist()
 a['uv']+=' Repeated static parts are grouped into named assemblies; triangle-corner UVs and material records retained from original.'
 (folder/'asset.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
 qa=args.output/'_qa';qa.mkdir(exist_ok=True)
 report={'id':slug,'originalGlbSha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'candidateGlbSha256':a['provenance']['sourceSha256'],'originalMeshNodes':len(original['nodes']),'candidateMeshNodes':len(doc['nodes']),'originalPrimitiveInstances':len(pieces),'candidatePrimitiveInstances':len(newpieces),'materials':len(doc['materials']),'originalBytes':raw.stat().st_size,'candidateBytes':target.stat().st_size,'equivalence':comparison,'mapping':mapping,'notes':'Primitive instance counts are not measured renderer draw calls or FPS. Unchanged original kept separately; this is not a new model.'}
 (qa/(slug+'-grouping.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='mapping'},indent=2))

if __name__=='__main__':main()
