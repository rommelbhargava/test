import json
import os

def load_gltf(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def validate_index(reference, total_count, ref_type):
    if reference >= total_count:
        raise ValueError(f"Invalid {ref_type} index: {reference} (total: {total_count})")

def unique_name(existing_names, name):
    if name not in existing_names:
        return name
    i = 1
    new_name = f"{name}_{i}"
    while new_name in existing_names:
        i += 1
        new_name = f"{name}_{i}"
    return new_name

def combine_gltf_files(gltf_files):
    combined_gltf = {
        "asset": {
            "version": "2.0"
        },
        "scenes": [],
        "nodes": [],
        "meshes": [],
        "materials": [],
        "accessors": [],
        "bufferViews": [],
        "buffers": [],
        "animations": [],
        "samplers": [],
        "textures": [],
        "images": [],
    }

    buffer_data = []
    existing_names = set()
    
    # Track offsets for index shifts
    node_offset = 0
    mesh_offset = 0
    material_offset = 0
    accessor_offset = 0
    bufferView_offset = 0
    buffer_offset = 0
    animation_offset = 0
    texture_offset = 0
    sampler_offset = 0
    image_offset = 0

    for gltf_file in gltf_files:
        gltf = load_gltf(gltf_file)

        # Get the number of elements, defaulting to 0 if the section is missing
        node_count = len(gltf.get('nodes', []))
        mesh_count = len(gltf.get('meshes', []))
        material_count = len(gltf.get('materials', []))
        accessor_count = len(gltf.get('accessors', []))
        texture_count = len(gltf.get('textures', []))
        bufferView_count = len(gltf.get('bufferViews', []))
        image_count = len(gltf.get('images', []))

        # Combine scenes
        for scene in gltf.get('scenes', []):
            if 'name' in scene:
                scene['name'] = unique_name(existing_names, scene['name'])
            combined_gltf['scenes'].append(scene)

        # Combine nodes
        for node in gltf.get('nodes', []):
            if 'mesh' in node:
                validate_index(node['mesh'], mesh_count, "mesh")
                node['mesh'] += mesh_offset  # Adjust mesh index
            if 'name' in node:
                node['name'] = unique_name(existing_names, node['name'])
            combined_gltf['nodes'].append(node)

        # Combine meshes and update material indices
        for mesh in gltf.get('meshes', []):
            if 'name' in mesh:
                mesh['name'] = unique_name(existing_names, mesh['name'])
            for primitive in mesh['primitives']:
                if 'material' in primitive:
                    validate_index(primitive['material'], material_count, "material")
                    primitive['material'] += material_offset  # Adjust material index
                if 'indices' in primitive:
                    validate_index(primitive['indices'], accessor_count, "accessor")
                    primitive['indices'] += accessor_offset  # Adjust accessor index for indices
                if 'attributes' in primitive:
                    primitive['attributes'] = {
                        k: v + accessor_offset for k, v in primitive['attributes'].items()
                    }
            combined_gltf['meshes'].append(mesh)

        # Combine materials and handle all texture references
        for material in gltf.get('materials', []):
            if 'name' in material:
                material['name'] = unique_name(existing_names, material['name'])
            
            texture_paths = [
                ('pbrMetallicRoughness', 'baseColorTexture'),
                ('pbrMetallicRoughness', 'metallicRoughnessTexture'),
                ('normalTexture', None),
                ('occlusionTexture', None),
                ('emissiveTexture', None)
            ]
            
            for texture_path in texture_paths:
                base_key = texture_path[0]
                sub_key = texture_path[1]
                
                if base_key in material:
                    texture_info = material[base_key]
                    if sub_key:
                        texture_info = texture_info.get(sub_key, {})
                    
                    texture_index = texture_info.get('index')
                    if texture_index is not None:
                        validate_index(texture_index, texture_count, "texture")
                        texture_info['index'] += texture_offset
            
            combined_gltf['materials'].append(material)

        # Combine accessors
        for accessor in gltf.get('accessors', []):
            if 'bufferView' in accessor:
                validate_index(accessor['bufferView'], bufferView_count, "bufferView")
                accessor['bufferView'] += bufferView_offset  # Adjust bufferView index
            combined_gltf['accessors'].append(accessor)

        # Combine bufferViews
        for bufferView in gltf.get('bufferViews', []):
            bufferView['buffer'] += buffer_offset  # Adjust buffer index
            combined_gltf['bufferViews'].append(bufferView)

        # Combine buffers and collect binary data
        for buffer in gltf.get('buffers', []):
            buffer_data.append(buffer['uri'])
            combined_gltf['buffers'].append(buffer)

        # Combine textures, samplers, and images
        for texture in gltf.get('textures', []):
            if 'sampler' in texture:
                validate_index(texture['sampler'], len(gltf.get('samplers', [])), "sampler")
                texture['sampler'] += sampler_offset
            if 'source' in texture:
                validate_index(texture['source'], image_count, "image")
                texture['source'] += image_offset
            combined_gltf['textures'].append(texture)

        for sampler in gltf.get('samplers', []):
            combined_gltf['samplers'].append(sampler)

        for image in gltf.get('images', []):
            combined_gltf['images'].append(image)

        # Combine animations (only if "animations" key exists)
        for animation in gltf.get('animations', []):
            for channel in animation.get('channels', []):
                if 'target' in channel and 'node' in channel['target']:
                    validate_index(channel['target']['node'], node_count, "node")
                    channel['target']['node'] += node_offset

            for sampler in animation.get('samplers', []):
                if 'input' in sampler:
                    validate_index(sampler['input'], accessor_count, "accessor")
                    sampler['input'] += accessor_offset
                if 'output' in sampler:
                    validate_index(sampler['output'], accessor_count, "accessor")
                    sampler['output'] += accessor_offset

            combined_gltf['animations'].append(animation)

        # Update offsets for the next glTF file
        node_offset += len(gltf.get('nodes', []))
        mesh_offset += len(gltf.get('meshes', []))
        material_offset += len(gltf.get('materials', []))
        accessor_offset += len(gltf.get('accessors', []))
        bufferView_offset += len(gltf.get('bufferViews', []))
        buffer_offset += len(gltf.get('buffers', []))
        animation_offset += len(gltf.get('animations', []))
        texture_offset += len(gltf.get('textures', []))
        sampler_offset += len(gltf.get('samplers', []))
        image_offset += len(gltf.get('images', []))

    # Save combined glTF JSON
    with open('combined_model.gltf', 'w') as f:
        json.dump(combined_gltf, f, indent=2)

    # Concatenate binary buffers
    with open('combined_model.bin', 'wb') as f_out:
        for buffer_file in buffer_data:
            with open(buffer_file, 'rb') as f_in:
                f_out.write(f_in.read())

# List of glTF files to combine
gltf_files = ['model1.gltf', 'model2.gltf', 'model3.gltf']

combine_gltf_files(gltf_files)