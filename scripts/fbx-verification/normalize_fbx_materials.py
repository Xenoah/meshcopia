"""Source-aware, original-preserving FBX material derivatives.

FBX cannot carry full glTF PBR. This creates compatible image links, bakes linear
color factors, expands mirror tiles, and retains source data in conversion notes.
Only the imported temporary scene and new derived texture files are modified.
"""
from pathlib import Path
import hashlib, json, math, re, struct, zlib
import bpy
import numpy as np


def sha(b):
    return hashlib.sha256(b).hexdigest()


def png16(path, linear_pixels, color=True, bits=16):
    """Write deterministic RGBA8/16 PNG, with Blender-style bottom-up input."""
    data = np.clip(linear_pixels, 0, 1).copy()
    if color:
        rgb = data[..., :3]
        data[..., :3] = np.where(rgb <= .0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - .055)
    raw = np.rint(data[::-1] * (65535 if bits == 16 else 255)).astype('>u2' if bits == 16 else 'u1')
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)
    body = b''.join(b'\0' + row.tobytes() for row in raw)
    h, w = raw.shape[:2]
    encoded = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, bits, 6, 0, 0, 0))
    if color:
        encoded += chunk(b'sRGB', b'\0')
    encoded += chunk(b'IDAT', zlib.compress(body, 9)) + chunk(b'IEND', b'')
    if path.exists():
        assert path.read_bytes() == encoded, 'Existing derived texture differs; never overwrite it.'
    else:
        path.write_bytes(encoded)


def normalize(source, out):
    raw = Path(source).read_bytes()
    jslen = struct.unpack_from('<I', raw, 12)[0]
    gltf = json.loads(raw[20:20 + jslen])
    binary = raw[28 + jslen:]
    textures = Path(out) / 'textures'; textures.mkdir(parents=True, exist_ok=True)
    notes = {'derivedTextures': [], 'materialChanges': [], 'vertexColors': [], 'derivedUvs': [],
             'limitations': ['FBX Phong is not lossless glTF PBR; AO, IOR and physical transmission have no portable FBX mapping.',
                             'Roughness texture uses the Blender FBX shininess convention and may need reconnection in other applications.']}
    def accessor(index):
        a = gltf['accessors'][index]; v = gltf['bufferViews'][a['bufferView']]
        dtype = {5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        width = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        dt = np.dtype(dtype); off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        arr = np.ndarray((a['count'],width), dtype=dt, buffer=binary, offset=off,
                         strides=(v.get('byteStride',dt.itemsize*width),dt.itemsize)).copy()
        if a.get('normalized'):
            arr = arr.astype(np.float64) / np.iinfo(dt).max
        return arr
    # Restore exact source float colors, instead of glTF importer's BYTE_COLOR quantization.
    color_objects = []
    for node in gltf.get('nodes', []):
        if 'mesh' not in node:
            continue
        prims = gltf['meshes'][node['mesh']]['primitives']
        if not any('COLOR_0' in p['attributes'] for p in prims):
            continue
        assert len(prims) == 1, 'Explicit multi-primitive color reconstruction is required.'
        prim = prims[0]; name = node.get('name', '')
        obj = bpy.data.objects.get(name)
        if obj is None:
            found = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.name == name[:63]]
            assert len(found) == 1, ('Cannot unambiguously match color mesh', name)
            obj = found[0]
        source_pos = accessor(prim['attributes']['POSITION'])
        blender_pos = source_pos[:, [0,2,1]].copy(); blender_pos[:,1] *= -1
        actual = np.array([v.co[:] for v in obj.data.vertices])
        assert actual.shape == blender_pos.shape and np.max(np.abs(actual - blender_pos)) < 2e-5, ('Vertex order mismatch', name)
        col = accessor(prim['attributes']['COLOR_0']).astype(np.float64)
        if col.shape[1] == 3:
            col = np.column_stack([col,np.ones(len(col))])
        old_names = [x.name for x in obj.data.color_attributes]
        for attr in list(obj.data.color_attributes):
            obj.data.color_attributes.remove(attr)
        attr = obj.data.color_attributes.new(name='COLOR_0', type='FLOAT_COLOR', domain='POINT')
        attr.data.foreach_set('color', col.astype(np.float32).reshape(-1))
        obj.data.color_attributes.active_color = attr
        color_objects.append((obj, col, prim['material']))
        notes['vertexColors'].append({'object': obj.name, 'sourceAccessor': prim['attributes']['COLOR_0'],
                                     'sourceComponentType': gltf['accessors'][prim['attributes']['COLOR_0']]['componentType'],
                                     'restoredFloatColor': True, 'vertices':len(col),
                                     'nonwhiteVertices':int(np.any(abs(col[:,:3]-1)>1e-7,axis=1).sum())})
    loaded, derived = {}, {}
    def source_image(index, color):
        key = (index, color)
        if key not in loaded:
            image = gltf['images'][index]; view = gltf['bufferViews'][image['bufferView']]
            encoded = binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
            ext = '.jpg' if image.get('mimeType') == 'image/jpeg' else '.png'
            path = textures / ('original_' + sha(encoded)[:20] + ext)
            if not path.exists(): path.write_bytes(encoded)
            img = bpy.data.images.load(str(path), check_existing=False)
            img.name = 'FBX_source_' + str(index) + ('_color' if color else '_data')
            img.colorspace_settings.name = 'sRGB' if color else 'Non-Color'; img.pack()
            loaded[key] = img
        return loaded[key]
    def prepare(info, factor=(1,1,1,1), color=True, channel=None, role='color'):
        tex = gltf['textures'][info['index']]; img = source_image(tex['source'], color)
        sampler = gltf.get('samplers', [])[tex['sampler']] if 'sampler' in tex else {}
        ws,wt = sampler.get('wrapS',10497),sampler.get('wrapT',10497)
        assert ws == wt, 'Mixed wrap modes need explicit adaptation.'
        assert 'extensions' not in info or not info['extensions'].get('KHR_texture_transform'), 'Explicit texture transform adaptation required.'
        mirror = ws == 33648
        factor = tuple(factor)
        key = (tex['source'],factor,color,channel,ws,wt,role)
        if key not in derived:
            if mirror or factor != (1,1,1,1) or channel is not None:
                pixels = np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(pixels)
                pixels = pixels.reshape(img.size[1],img.size[0],4)
                if color:
                    # Blender Image.pixels for loaded byte PNGs exposes their
                    # encoded samples, even when the shader's color space is
                    # sRGB. Decode explicitly before multiplying linear factors.
                    rgb=pixels[...,:3]
                    pixels[...,:3]=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
                if channel is not None:
                    single = pixels[...,channel:channel+1]
                    pixels = np.concatenate([np.repeat(single,3,axis=2),np.ones_like(single)],axis=2)
                pixels = pixels * np.array(factor)
                if mirror:
                    strip = np.concatenate([pixels,pixels[:,::-1]],axis=1)
                    pixels = np.concatenate([strip,strip[::-1]],axis=0)
                keyhash = sha(repr(key).encode())[:16]
                path = textures / ('derived_' + role + '_' + keyhash + '.png')
                bits = 8 if mirror and factor == (1,1,1,1) and channel is None else 16
                png16(path,pixels,color=color,bits=bits)
                result = bpy.data.images.load(str(path),check_existing=False)
                result.name = path.stem; result.colorspace_settings.name='sRGB' if color else 'Non-Color';result.pack()
                notes['derivedTextures'].append({'file':str(path.relative_to(out)), 'sha256':sha(path.read_bytes()),
                     'sourceImage':tex['source'],'factorLinear':list(factor),'sourceChannel':channel,
                     'mirrorAtlas2x2':mirror,'uvScale':[.5,.5] if mirror else [1,1],
                     'size':list(result.size),'encoding':f'RGBA{bits} PNG; sRGB color / linear data'})
            else:
                result=img
            derived[key]=(result, 'REPEAT' if ws in (10497,33648) else 'EXTEND', .5 if mirror else 1)
        return derived[key]
    def image_link(mat, info, socket, factor=(1,1,1,1), color=True, channel=None, role='color', normal_scale=None):
        image, extension, scale = prepare(info,factor,color,channel,role)
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        node=nodes.new('ShaderNodeTexImage');node.image=image;node.extension=extension
        if scale != 1:
            tc=nodes.new('ShaderNodeTexCoord'); mp=nodes.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(scale,scale,1)
            links.new(tc.outputs['UV'],mp.inputs['Vector']);links.new(mp.outputs['Vector'],node.inputs['Vector'])
        if normal_scale is not None:
            nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=normal_scale
            links.new(node.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],socket)
        else:
            links.new(node.outputs['Color'],socket)
        return node
    materials=[]
    for i, desc in enumerate(gltf.get('materials', [])):
        name=desc.get('name',f'Material_{i}');mat=bpy.data.materials.get(name)
        if mat is None:
            used = any(p.get('material') == i for mesh in gltf.get('meshes',[]) for p in mesh['primitives'])
            assert not used, ('Cannot match used source material',name)
            materials.append(None)
            notes['materialChanges'].append({'name':name,'sourceMaterialIndex':i,'changes':['Unused glTF material definition omitted; no mesh references it.']})
            continue
        materials.append(mat);mat.use_nodes=True;mat.node_tree.nodes.clear()
        bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');output=mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
        pbr=desc.get('pbrMetallicRoughness',{});factor=pbr.get('baseColorFactor',[1,1,1,1])
        bs.inputs['Base Color'].default_value=factor;bs.inputs['Metallic'].default_value=pbr.get('metallicFactor',1)
        bs.inputs['Roughness'].default_value=pbr.get('roughnessFactor',1)
        bs.inputs['Alpha'].default_value=factor[3] if desc.get('alphaMode','OPAQUE')!='OPAQUE' else 1
        mat.use_backface_culling=not desc.get('doubleSided',False)
        if 'baseColorTexture' in pbr:
            node=image_link(mat,pbr['baseColorTexture'],bs.inputs['Base Color'],factor=factor,role='basecolor')
            # The source tint is already baked into this image. Keep the FBX
            # DiffuseColor neutral so other consumers cannot apply it twice.
            bs.inputs['Base Color'].default_value=(1,1,1,1)
            if desc.get('alphaMode','OPAQUE')!='OPAQUE':mat.node_tree.links.new(node.outputs['Alpha'],bs.inputs['Alpha'])
        if 'metallicRoughnessTexture' in pbr:
            metallic=pbr.get('metallicFactor',1);roughness=pbr.get('roughnessFactor',1)
            image_link(mat,pbr['metallicRoughnessTexture'],bs.inputs['Roughness'],factor=(roughness,roughness,roughness,1),color=False,channel=1,role='roughness')
            if metallic:
                image_link(mat,pbr['metallicRoughnessTexture'],bs.inputs['Metallic'],factor=(metallic,metallic,metallic,1),color=False,channel=2,role='metallic')
        if 'normalTexture' in desc:
            image_link(mat,desc['normalTexture'],bs.inputs['Normal'],color=False,role='normal',normal_scale=desc['normalTexture'].get('scale',1))
        emission=desc.get('emissiveFactor',[0,0,0]);extensions=desc.get('extensions',{})
        strength=extensions.get('KHR_materials_emissive_strength',{}).get('emissiveStrength',1)
        bs.inputs['Emission Color'].default_value=(*emission,1);bs.inputs['Emission Strength'].default_value=strength if any(emission) else 0
        if 'emissiveTexture' in desc:
            image_link(mat,desc['emissiveTexture'],bs.inputs['Emission Color'],factor=(*emission,1),role='emission')
            bs.inputs['Emission Color'].default_value=(1,1,1,1)
        if 'KHR_materials_specular' in extensions:
            bs.inputs['Specular IOR Level'].default_value=.5*extensions['KHR_materials_specular'].get('specularFactor',1)
        transmission=extensions.get('KHR_materials_transmission',{}).get('transmissionFactor',0)
        changes=['Source glTF constants restored directly; redundant vertex-color/Mix nodes removed.']
        if transmission:
            bs.inputs['Alpha'].default_value=.12
            changes.append('Physical transmission/IOR replaced by explicit alpha=0.12 visual approximation; not equivalent refraction.')
        if 'occlusionTexture' in desc:changes.append('AO is not mapped to a portable FBX channel or baked into diffuse. The unchanged source GLB retains the original AO image.')
        notes['materialChanges'].append({'name':name,'sourceMaterialIndex':i,'changes':changes,'originalMaterial':desc})
    # Constant face colors become material variants. The tree gets a unique UV atlas.
    for obj,col,mi in color_objects:
        if np.all(abs(col[:,:3]-1)<1e-7):continue
        mesh=obj.data;mesh.calc_loop_triangles();tris=list(mesh.loop_triangles)
        triplets=np.array([col[list(t.vertices)] for t in tris])
        constant=np.max(np.ptp(triplets,axis=1)) < 1e-7
        base=materials[mi];desc=gltf['materials'][mi];factor=np.array(desc.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1]))
        if constant:
            assert 'baseColorTexture' not in desc.get('pbrMetallicRoughness',{}), 'Textured color splitting requires a derived tint image.'
            variant={}
            for tri,rgba in zip(tris,triplets[:,0]):
                key=tuple(rgba)
                if key not in variant:
                    mat=base.copy();mat.name=base.name+'_FBXcolor_'+sha(np.array(key).tobytes())[:8]
                    bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=tuple(rgba*factor)
                    mesh.materials.append(mat);variant[key]=len(mesh.materials)-1
                mesh.polygons[tri.polygon_index].material_index=variant[key]
            notes['materialChanges'].append({'object':obj.name,'constantFaceColorVariants':len(variant),'geometryChanged':False,'originalUv0Retained':True})
        else:
            assert Path(source).stem=='city-pruned-street-tree', 'Unreviewed varying-color asset requires explicit bake review.'
            n=len(tris);cell=8;grid=math.ceil(math.sqrt(n));height=math.ceil(n/grid);w=grid*cell;h=height*cell
            pixels=np.ones((h,w,4),dtype=np.float32)
            uv=np.empty((len(mesh.loops),2),dtype=np.float32)
            # A linear gradient stays linear under bilinear filtering away from
            # the cell padding. All faces receive unique atlas islands.
            yy,xx=np.mgrid[0:cell,0:cell];u=(xx+.5-1.5)/5;v=(yy+.5-1.5)/5
            for i,tri in enumerate(tris):
                x=(i%grid)*cell;y=(i//grid)*cell;c=triplets[i]*factor
                patch=c[0]+u[...,None]*(c[1]-c[0])+v[...,None]*(c[2]-c[0]);pixels[y:y+cell,x:x+cell]=np.clip(patch,0,1)
                uv[list(tri.loops)]=np.array([(x+1.5,y+1.5),(x+6.5,y+1.5),(x+1.5,y+6.5)])/(w,h)
            original=np.array([v.uv[:] for v in mesh.uv_layers.active.data],dtype=np.float32)
            for layer in list(mesh.uv_layers):mesh.uv_layers.remove(layer)
            baked=mesh.uv_layers.new(name='FBX_BakedColor_UV');baked.data.foreach_set('uv',uv.reshape(-1))
            preserved=mesh.uv_layers.new(name='Original_UV0');preserved.data.foreach_set('uv',original.reshape(-1))
            mesh.uv_layers.active_index=0;baked.active_render=True
            path=textures/'derived_leaf_vertex_colors.png';png16(path,pixels,color=True)
            image=bpy.data.images.load(str(path),check_existing=False);image.name='FBX_leaf_vertex_colors';image.pack()
            node=base.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;node.extension='EXTEND'
            bs=next(n for n in base.node_tree.nodes if n.type=='BSDF_PRINCIPLED');base.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
            notes['derivedTextures'].append({'file':str(path.relative_to(out)),'sha256':sha(path.read_bytes()),'role':'linear vertex-color gradient bake','size':[w,h],'bitDepth':16})
            notes['derivedUvs'].append({'object':obj.name,'triangles':n,'primaryUv':'FBX_BakedColor_UV','preservedSourceUv':'Original_UV0','originalUvSha256':sha(original.tobytes()),'geometryChanged':False,'colorAttributeRetained':True,'atlasCellPixels':cell})
    # Avoid exporting orphaned source images/materials; only scene users count.
    return notes
