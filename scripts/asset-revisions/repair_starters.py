"""Stage two component-specific winding repairs without changing published sources."""
from pathlib import Path
import hashlib, importlib.util, json, struct, tempfile
import numpy as np
from audit_mesh import glb_audit

ROOT=Path(__file__).resolve().parents[2]; STAGE=ROOT/'asset-revisions/repair-appliances-v1'
spec=importlib.util.spec_from_file_location('original_starters',ROOT/'scripts/create-starter-assets.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
captured={}
old.save_model=lambda slug,*args:captured.setdefault(slug,args[-1])
old.models()
changes={
 'garden-arch':{'primitive':2,'reason':'Reverse only the inward curved strip and remove the four concealed pillar-top triangles at the matching interfaces, making one continuous closed arch surface. Preserve all vertex coordinates and the walk-through opening.','beforeTriangles':216,'afterTriangles':212},
 'wayfinding-sign':{'primitive':2,'reason':'The vertical torus was reflected by swapping Y/Z without reversing triangle order. Reverse only this torus; retain every coordinate and the central opening.','beforeTriangles':1420,'afterTriangles':1420}}

for identity,change in changes.items():
    mesh=captured[identity]; vertices,faces,material=mesh.parts[change['primitive']]
    repaired=faces[:,[0,2,1]].copy()
    if identity=='garden-arch':
        # The curve ends exactly meet the pillar tops. Remove their internal
        # faces, then inspect the joined surface; adding caps creates coincident
        # non-manifold interfaces after positional welding on reimport.
        assert len(vertices)==100 and len(faces)==192
        for index in [0,1]:
            pv,pf,pm=mesh.parts[index];mesh.parts[index]=(pv,pf[[i for i in range(len(pf)) if i not in [6,7]]],pm)
    mesh.parts[change['primitive']]=(vertices.copy(),repaired,material)
    if identity=='garden-arch':
        vv=[];ff=[];offset=0
        for pv,pf,pm in mesh.parts:
            assert pm==material;vv.append(pv);ff.append(pf+offset);offset+=len(pv)
        mesh.parts=[(np.vstack(vv),np.vstack(ff),material)]
    destination=STAGE/identity;source=destination/'source';source.mkdir(parents=True,exist_ok=True)
    name=f'{identity}-1.0.2.glb'
    with tempfile.TemporaryDirectory(prefix='meshcopia-starter-repair-') as tmp:
        mesh.export(Path(tmp),identity);raw=(Path(tmp)/(identity+'.glb')).read_bytes()
    size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    for m in doc['materials']:m['doubleSided']=False
    doc['asset']['generator']='Meshcopia component-specific starter winding repair 1'
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    result=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
    (source/name).write_bytes(result)
    meta=json.loads((ROOT/f'content/assets/{identity}/asset.json').read_text());meta.update(version='1.0.2',updated='2026-10-18',preview=name,triangles=change['afterTriangles'])
    meta['description']+=' 面順序を部品単位で修正した1.0.2候補。片面材質で表示し、開口を保持。'
    meta['descriptionEn']+=' Version 1.0.2 candidate repairs component winding, uses single-sided materials and preserves the opening.'
    meta['provenance']['tool']='Meshcopia original starter generator with component-specific winding repair 1; Blender 4.3.2 FBX conversion'
    meta['provenance']['changes']=meta['provenance'].get('changes','none.')+' Version 1.0.2: '+change['reason']
    meta['usages'].append({'relationship':'original','project':'Meshcopia winding repair','sourceUrl':'https://github.com/Xenoah/meshcopia','sourcePaths':['scripts/asset-revisions/repair_starters.py'],'selectors':[identity],'context':'Component-specific correction of the original Meshcopia model; no third-party geometry.'})
    (destination/'asset.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    audit=glb_audit(source/name);components=[c for p in audit['parts'] for c in p['components']]
    assert sum(p['triangles'] for p in audit['parts'])==change['afterTriangles']
    assert not audit['doubleSidedMaterials']
    assert all(c['closedOriented'] and c['orientation']=='outward' for c in components),components
    audit['file']='source/'+name
    report={'id':identity,'version':'1.0.2','publicationState':'unpublished-candidate','sourceFile':name,'sourceSha256':hashlib.sha256(result).hexdigest(),'change':change,'audit':audit}
    (destination/'repair-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(identity,json.dumps({'triangles':meta['triangles'],'allComponentsClosedOutward':True,'doubleSided':False,'sourceBytes':len(result)}))
