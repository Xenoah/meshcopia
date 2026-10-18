"""Prove the repairs preserve positions and change only the intended faces."""
from pathlib import Path
from collections import Counter
import json
import numpy as np
from audit_mesh import read_glb,glb_audit
ROOT=Path(__file__).resolve().parents[2]
def geometry(file):
    raw,doc,access=read_glb(file);triangles=[];positions=set()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            vertices=[tuple(float(v) for v in xyz) for xyz in access(primitive['attributes']['POSITION'])];positions.update(vertices)
            faces=access(primitive['indices']).reshape(-1,3) if 'indices' in primitive else np.arange(len(vertices)).reshape(-1,3)
            triangles.extend(tuple(vertices[int(i)] for i in f) for f in faces)
    # A cyclic rotation preserves orientation; reversing order does not.
    oriented=Counter(min(t,t[1:]+t[:1],t[2:]+t[:2]) for t in triangles)
    return positions,oriented,Counter(tuple(sorted(t)) for t in triangles)
results=[]
for identity,flipped,removed in [('garden-arch',192,4),('wayfinding-sign',1152,0)]:
    old=ROOT/f'content/assets/{identity}/source/{identity}.glb';new=ROOT/f'asset-revisions/repair-appliances-v1/{identity}/source/{identity}-1.0.2.glb'
    before,after=geometry(old),geometry(new)
    assert before[0]==after[0],f'{identity}: coordinates changed'
    assert sum((before[2]-after[2]).values())==removed and not (after[2]-before[2]),f'{identity}: unexpected added/removed triangle geometry'
    assert sum((before[1]-after[1]).values())==flipped+removed and sum((after[1]-before[1]).values())==flipped
    audit=glb_audit(new);assert not audit['doubleSidedMaterials']
    assert all(c['closedOriented'] and c['orientation']=='outward' for p in audit['parts'] for c in p['components'])
    results.append({'id':identity,'allVertexPositionsUnchanged':True,'flippedTriangles':flipped,'removedConcealedInterfaceTriangles':removed,'newTriangleGeometry':0,'closedOutward':True,'doubleSided':False})
out=ROOT/'test-results/asset-revisions/component-repair-proof.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
