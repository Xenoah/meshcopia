"""Read-only Blender import geometry/normals/transforms/material/image inspection."""
from pathlib import Path
import argparse, json, math, sys
import bpy
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from audit_mesh import triangles_audit

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--save-production',type=Path);a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
if a.source.suffix=='.fbx':bpy.ops.import_scene.fbx(filepath=str(a.source.resolve()),colors_type='LINEAR')
else:bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()))
bpy.context.view_layer.update()
parts=[];coordinates=[]
for obj in sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name):
    mesh=obj.data;mesh.calc_loop_triangles()
    vertices=np.array([obj.matrix_world@v.co for v in mesh.vertices]);coordinates.extend(vertices.tolist())
    faces=np.array([t.vertices[:] for t in mesh.loop_triangles])
    normals=np.array([n.vector[:] for n in mesh.corner_normals])@np.array(obj.matrix_world.to_3x3().inverted().transposed()).T
    corner_normals=np.array([normals[list(t.loops)] for t in mesh.loop_triangles])
    parts.append({'name':obj.name,'worldDeterminant':obj.matrix_world.to_3x3().determinant(),'uvLayers':len(mesh.uv_layers),'materialSlots':len(obj.material_slots),**triangles_audit(vertices,faces,corner_normals)})
coords=np.array(coordinates);dimensions=coords.max(axis=0)-coords.min(axis=0)
images=[]
for im in bpy.data.images:
    if im.users and im.type=='IMAGE':images.append({'name':im.name,'size':list(im.size),'channels':im.channels,'hasPixels':len(im.pixels)>0,'packed':bool(im.packed_file)})
report={'source':str(a.source),'importer':bpy.app.version_string,'dimensionsMetersYUp':dimensions[[0,2,1]].tolist(),'triangles':sum(p['triangles'] for p in parts),'parts':parts,'images':images,'materials':[{'name':m.name,'backfaceCullingOnImport':m.use_backface_culling} for m in bpy.data.materials if m.users]}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
if a.save_production:
    a.save_production.parent.mkdir(parents=True,exist_ok=True)
    for image in bpy.data.images:
        if image.users and image.type=='IMAGE':image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(a.save_production.resolve()))
print('IMPORT_AUDIT',json.dumps({'triangles':report['triangles'],'dimensions':report['dimensionsMetersYUp'],'inward':sum(c['orientation']=='inward' for p in parts for c in p['components']),'open':sum(not c['closedOriented'] for p in parts for c in p['components']),'degenerate':sum(p['degenerateFaces'] for p in parts),'negativeTransforms':sum(p['worldDeterminant']<0 for p in parts)}))
