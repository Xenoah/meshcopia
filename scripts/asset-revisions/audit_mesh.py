"""Read-only oriented triangle audit. Open surfaces are reported, never auto-flipped."""
from collections import defaultdict
from pathlib import Path
import hashlib, json, struct
import numpy as np

STARTERS = ['studio-chair','atelier-lamp','slat-bench','terracotta-planter','market-crate','garden-arch','field-terminal','wayfinding-sign']

def triangles_audit(vertices, faces, normals=None):
    v=np.asarray(vertices,dtype=np.float64); f=np.asarray(faces,dtype=np.int64)
    t=v[f]; crosses=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]); lengths=np.linalg.norm(crosses,axis=1)
    # Weld positional copies only for topology inspection, never modify the source.
    _,inverse=np.unique(np.round(v,7),axis=0,return_inverse=True); wf=inverse[f]
    edges=defaultdict(list); links=[set() for _ in f]
    for i,face in enumerate(wf):
        for a,b in zip(face,np.roll(face,-1)):
            edges[tuple(sorted((int(a),int(b))))].append((i,int(a)<int(b)))
    for refs in edges.values():
        for i,_ in refs:
            links[i].update(j for j,_ in refs if j!=i)
    components=[]; remaining=set(range(len(f)))
    while remaining:
        pending=[remaining.pop()]; selected=[]
        while pending:
            i=pending.pop();selected.append(i)
            for j in links[i]&remaining:remaining.remove(j);pending.append(j)
        local=set(selected); ee=[r for r in edges.values() if r[0][0] in local]
        tt=t[selected]; anchor=tt.reshape(-1,3).mean(axis=0); centered=tt-anchor
        volume=float(np.einsum('ij,ij->i',centered[:,0],np.cross(centered[:,1],centered[:,2])).sum()/6)
        boundary=sum(len(r)==1 for r in ee); nonmanifold=sum(len(r)>2 for r in ee)
        inconsistent=sum(len(r)==2 and r[0][1]==r[1][1] for r in ee)
        closed=boundary==0 and nonmanifold==0 and inconsistent==0
        components.append({'triangles':len(selected),'boundaryEdges':boundary,'nonManifoldEdges':nonmanifold,
            'inconsistentWindingEdges':inconsistent,'closedOriented':closed,'signedVolumeMeters3':volume,
            'orientation':('outward' if volume>1e-12 else 'inward' if volume< -1e-12 else 'zero-volume') if closed else 'open-or-nonmanifold-requires-analytic-review'})
    dots=[]
    if normals is not None:
        nn=np.asarray(normals,dtype=float)
        if nn.shape==v.shape:nn=nn[f]
        nn=nn.mean(axis=1); denom=lengths*np.linalg.norm(nn,axis=1); valid=denom>1e-20
        dots=(np.einsum('ij,ij->i',crosses[valid],nn[valid])/denom[valid]).tolist()
    return {'triangles':len(f),'nonFiniteCoordinates':int((~np.isfinite(v)).sum()),'degenerateFaces':int((lengths<1e-12).sum()),
        'minStoredNormalDotFaceNormal':min(dots) if dots else None,'components':components}

def read_glb(path):
    raw=Path(path).read_bytes();magic,version,total=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and total==len(raw)
    cursor=12; doc=None; binary=None
    while cursor<len(raw):
        length,kind=struct.unpack_from('<I4s',raw,cursor);data=raw[cursor+8:cursor+8+length];cursor+=8+length
        if kind==b'JSON':doc=json.loads(data)
        elif kind==b'BIN\0':binary=data
    assert doc is not None and binary is not None
    def accessor(i):
        a=doc['accessors'][i];bv=doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=bv.get('byteOffset',0)+a.get('byteOffset',0),strides=(bv.get('byteStride',dtype.itemsize*width),dtype.itemsize)).copy()
    return raw,doc,accessor

def glb_audit(path):
    raw,doc,accessor=read_glb(path);parts=[]
    for mi,mesh in enumerate(doc['meshes']):
        for pi,p in enumerate(mesh['primitives']):
            assert p.get('mode',4)==4
            vertices=accessor(p['attributes']['POSITION']);faces=accessor(p['indices']).reshape(-1,3) if 'indices' in p else np.arange(len(vertices)).reshape(-1,3)
            normals=accessor(p['attributes']['NORMAL']) if 'NORMAL' in p['attributes'] else None
            parts.append({'mesh':mi,'primitive':pi,'material':p.get('material'),**triangles_audit(vertices,faces,normals)})
    nodes=[]
    for i,node in enumerate(doc.get('nodes',[])):
        determinant=float(np.linalg.det(np.array(node['matrix']).reshape(4,4).T[:3,:3])) if 'matrix' in node else float(np.prod(node.get('scale',[1,1,1])))
        nodes.append({'node':i,'name':node.get('name'),'localDeterminant':determinant})
    return {'file':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'nodes':nodes,
        'doubleSidedMaterials':[m.get('name',i) for i,m in enumerate(doc.get('materials',[])) if m.get('doubleSided',False)],'parts':parts}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result={'scope':'read-only original GLB topology, stored normals and transforms; not a repair decision for open surfaces','assets':{}}
    for identity in STARTERS:
        metadata=json.loads((a.repo/'content/assets'/identity/'asset.json').read_text())
        report=glb_audit(a.repo/'content/assets'/identity/'source'/metadata['preview']);result['assets'][identity]=report
        components=[c for part in report['parts'] for c in part['components']]
        print(identity,json.dumps({'triangles':sum(x['triangles'] for x in report['parts']),'inwardClosedComponents':sum(c['orientation']=='inward' for c in components),'openComponents':sum(not c['closedOriented'] for c in components),'negativeTransforms':sum(n['localDeterminant']<0 for n in report['nodes'])}))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
