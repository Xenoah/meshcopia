"""Group generated static GLBs with translation and leaf rotations without changing normals, UVs or materials.
No simplification, imported libraries, remote resources or Blender re-export. CC BY 4.0.
"""
import argparse,copy,hashlib,json,struct
from pathlib import Path

WIDTH={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
TYPES={5121:('B',1),5123:('H',2),5125:('I',4),5126:('f',4)}

def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]

def classify(profile,name,t):
 if profile=='bicycle':
  if name.startswith('Front wheel '):return None if 'inflated commuter tire' in name else 'Front wheel metal assembly'
  if name.startswith('Rear wheel '):return None if 'inflated commuter tire' in name else 'Rear wheel metal assembly'
  if name.startswith(('Chain roller','Individual chain link plate')):return 'Linked drive chain'
  if name.startswith('Chainring tooth'):return 'Chainring teeth'
  if name.startswith('Chainring spider'):return 'Chainring spider'
  if name.startswith(('Seat tube','Down tube','Top tube','Head tube','Bottom bracket shell','Chain stay','Seat stay')):return 'Diamond frame assembly'
  if name.startswith(('Swept front fork','Fork crown')):return 'Front fork assembly'
  if name.startswith('Axle dropout'):return 'Front fork dropout hardware' if t[0]>0 else 'Rear frame dropout hardware'
  if name.startswith('Front metal mudguard support stay'):return 'Front fender stays'
  if name.startswith('Rear metal mudguard support stay'):return 'Rear fender stays'
  if name.startswith(('Rear rack perimeter','Rack cross slat')):return 'Rear rack platform'
  if name.startswith(('Rear rack leg','Rear rack forward brace')):return 'Rear rack support stays'
  if name.startswith('Front rim brake'):return 'Front rim brake assembly'
  if name.startswith('Rear rim brake'):return 'Rear rim brake assembly'
  if name.startswith(('Pedal side rail','Pedal end rail','Pedal traction rib','Pedal amber reflector')):return 'Left pedal assembly' if t[2]<0 else 'Right pedal assembly'
  if name.startswith('Saddle support rail'):return 'Saddle rail assembly'
 elif profile=='trolley':
  if name.startswith('Basket ' ) and not name.startswith('Basket support'):return 'Tapered open wire basket'
  if name.startswith(('Nesting gate','Rear gate upper')):return 'Rear nesting gate wire'
  if name.startswith('Rear gate hinge'):return 'Rear nesting gate hinges'
  if name.startswith(('Lower tray','Tray support')):return 'Lower open wire tray'
  if name.startswith(('Lower chassis','Basket support','Front basket support')):return 'Tubular trolley support chassis'
  if name.startswith('Handle support'):return 'Trolley handle supports'
  if name.startswith('Handle end plug'):return 'Handle end plugs'
  if name.startswith('Shopping trolley caster'):
   return ('Front' if t[0]>0 else 'Rear')+(' left' if t[2]<0 else ' right')+' caster assembly'
 elif profile=='vending':
  if name.startswith(('Stocked can body','Original color sleeve','Can rolled rim','Can pull tab')):return 'Stocked beverage cans'
  if name.startswith(('Stock shelf','Shelf stop bar')):return 'Display shelving'
  if name.startswith(('Shelf price rail','Blank shelf ticket')):return 'Shelf information rails'
  if name.startswith('Selection keypad key'):return 'Selection keypad buttons'
  if name.startswith('Display status line'):return 'Display status marks'
  if name.startswith('Internal stock lighting'):return 'Internal display lighting'
  if name.startswith('Compressor vent'):return 'Compressor front vent'
  if name.startswith('Rear cooling louver'):return 'Rear cooling louvers'
  if name.startswith('Rear access screw'):return 'Rear panel fasteners'
  if name.startswith('Folded cabinet side'):return 'Cabinet side panels'
  if name.startswith('Display return side'):return 'Display interior returns'
  if name.startswith('Front door hinge'):return 'Display door hinges'
  if name.startswith('Display door frame'):return 'Display door frame'
  if name.startswith('Display door seal'):return 'Display door seal'
  if name.startswith('Ground anchor foot'):return 'Vending base feet'
  if name.startswith('Anchor bolt'):return 'Vending foot anchors'
 return None


def group_glb(raw,profile):
 magic,version,total=struct.unpack_from('<III',raw)
 if magic!=0x46546c67 or version!=2 or total!=len(raw):raise ValueError('Invalid GLB header')
 jslen,jstype=struct.unpack_from('<I4s',raw,12)
 if jstype!=b'JSON':raise ValueError('Expected JSON')
 doc=json.loads(raw[20:20+jslen]);binlen,bintype=struct.unpack_from('<I4s',raw,20+jslen)
 if bintype!=b'BIN\0':raise ValueError('Expected binary buffer')
 binary=raw[28+jslen:28+jslen+binlen]
 if len(doc.get('buffers',[]))!=1 or doc['buffers'][0].get('uri'):raise ValueError('Expected one embedded buffer')
 if any(doc.get(k) for k in ['images','textures','skins','animations','cameras']):raise ValueError('Only solid-material static generated meshes are supported')
 def values(index):
  a=doc['accessors'][index]
  if a.get('sparse') or a.get('normalized'):raise ValueError('Unsupported normalized/sparse accessor')
  view=doc['bufferViews'][a['bufferView']];fmt,bytes_=TYPES[a['componentType']];width=WIDTH[a['type']]
  start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',width*bytes_)
  return [struct.unpack_from('<'+fmt*width,binary,start+i*stride) for i in range(a['count'])]
 groups={};before_nodes=0;before_primitives=0
 def visit(index,parent_t):
  nonlocal before_nodes,before_primitives
  node=doc['nodes'][index]
  rotation=node.get('rotation',[0,0,0,1])
  if any(abs(x-1)>1e-10 for x in node.get('scale',[1,1,1])):raise ValueError('Apply scales before grouping')
  rotated=rotation!=[0,0,0,1]
  if rotated and node.get('children'):raise ValueError('Only leaf rotations supported')
  if 'matrix' in node:
   m=node['matrix'];identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
   if any(abs(m[i]-identity[i])>1e-10 for i in range(16) if i not in [12,13,14]):raise ValueError('Only translation matrices are supported')
   local=m[12:15]
  else:local=node.get('translation',[0,0,0])
  t=[a+b for a,b in zip(parent_t,local)]
  if 'mesh' in node:
   before_nodes+=1;name=node.get('name','Mesh '+str(index));assembly=classify(profile,name,t)
   for pi,p in enumerate(doc['meshes'][node['mesh']]['primitives']):
    before_primitives+=1
    if p.get('mode',4)!=4 or p.get('targets'):raise ValueError('Only static triangles are supported')
    attrs=p['attributes'];signature=tuple(sorted((k,doc['accessors'][i]['componentType'],doc['accessors'][i]['type']) for k,i in attrs.items()))
    if any(kind!=5126 for _,kind,_ in signature):raise ValueError('Expected float attributes')
    material=p['material'];key=(assembly or name,material,signature,tuple(rotation)) if assembly else ('single',index,pi)
    if key not in groups:groups[key]={'name':(assembly+' - '+doc['materials'][material].get('name',str(material))) if assembly else name,'material':material,'attributes':{k:[] for k in attrs},'types':{k:doc['accessors'][i]['type'] for k,i in attrs.items()},'indices':[],'members':[],'rotation':rotation}
    # Retain identical source rotations on grouped nodes and move translation into local positions.
    local_t=t
    if rotated:
     x,y,z,w=rotation
     m=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
     a,b,c=m[0];d,e,f=m[1];h,i,j=m[2];det=a*(e*j-f*i)-b*(d*j-f*h)+c*(d*i-e*h)
     inv=[[e*j-f*i,c*i-b*j,b*f-c*e],[f*h-d*j,a*j-c*h,c*d-a*f],[d*i-e*h,b*h-a*i,a*e-b*d]]
     local_t=[sum(row[k]*t[k] for k in range(3))/det for row in inv]
    g=groups[key];offset=len(g['attributes']['POSITION']);count=None
    for attr,accessor in attrs.items():
     v=values(accessor)
     if attr=='POSITION':v=[tuple(f32(p[j]+local_t[j]) for j in range(3)) for p in v]
     # NORMAL, TEXCOORD_0 and any other float attributes are copied exactly.
     if count is None:count=len(v)
     elif count!=len(v):raise ValueError('Mismatched attribute count')
     g['attributes'][attr].extend(v)
    indices=[x[0] for x in values(p['indices'])] if 'indices' in p else list(range(count))
    if len(indices)%3:raise ValueError('Invalid triangle indices')
    g['indices'].extend(i+offset for i in indices);g['members'].append(name)
  for child in node.get('children',[]):visit(child,t)
 for root in doc['scenes'][doc.get('scene',0)]['nodes']:visit(root,[0,0,0])
 out={k:copy.deepcopy(doc[k]) for k in ['asset','materials','extensionsUsed','extensionsRequired','extensions'] if k in doc}
 out['asset']['generator']=out['asset'].get('generator','')+'; Meshcopia static assembly grouping 1.0'
 out.update(scene=0,scenes=[{'nodes':[]}],nodes=[],meshes=[],buffers=[],bufferViews=[],accessors=[]);blob=bytearray();triangles=0
 def accessor(data,type_,component,target):
  while len(blob)%4:blob.append(0)
  offset=len(blob);fmt,_=TYPES[component];flat=[x for row in data for x in row];packed=struct.pack('<'+fmt*len(flat),*flat);blob.extend(packed)
  vi=len(out['bufferViews']);out['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(packed),'target':target})
  a={'bufferView':vi,'componentType':component,'count':len(data),'type':type_}
  if target==34962 and type_=='VEC3':a.update(min=[min(row[i] for row in data) for i in range(3)],max=[max(row[i] for row in data) for i in range(3)])
  out['accessors'].append(a);return len(out['accessors'])-1
 for g in groups.values():
  attrs={k:accessor(v,g['types'][k],5126,34962) for k,v in g['attributes'].items()};indices=g['indices'];component=5123 if max(indices)<65536 else 5125
  ia=accessor([(i,) for i in indices],'SCALAR',component,34963);mi=len(out['meshes']);out['meshes'].append({'name':g['name'],'primitives':[{'attributes':attrs,'indices':ia,'material':g['material'],'mode':4}]})
  out['scenes'][0]['nodes'].append(len(out['nodes']));out['nodes'].append({'name':g['name'],'mesh':mi,**({'rotation':g['rotation']} if g['rotation']!=[0,0,0,1] else {})});triangles+=len(indices)//3
 while len(blob)%4:blob.append(0)
 out['buffers']=[{'byteLength':len(blob)}];j=json.dumps(out,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4)
 result=struct.pack('<III',0x46546c67,2,28+len(j)+len(blob))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(blob),b'BIN\0')+blob
 report={'profile':profile,'meshNodesBefore':before_nodes,'meshNodesAfter':len(out['nodes']),'primitiveInstancesBefore':before_primitives,'primitiveInstancesAfter':len(out['nodes']),'triangles':triangles,'materialsBefore':len(doc['materials']),'materialsAfter':len(out['materials']),'sourceSha256':hashlib.sha256(raw).hexdigest(),'groupedSha256':hashlib.sha256(result).hexdigest(),'positionOperation':'translation baked to float32; validate roundoff bound','normalUvMaterialOperation':'source float values/material JSON preserved; no normal recomputation','geometrySimplification':False,'groups':[{'name':g['name'],'members':len(g['members'])} for g in groups.values()]}
 return bytes(result),report


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--profile',choices=['bicycle','trolley','vending'],required=True);p.add_argument('--report',type=Path);a=p.parse_args()
 if a.output.exists():p.error('Refusing to overwrite output')
 data,report=group_glb(a.input.read_bytes(),a.profile);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(data)
 if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='groups'},indent=2))
