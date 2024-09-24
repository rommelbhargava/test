import json
import os

def load_gltf(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def validate_index(reference, total_count, ref_type):
    if reference >= total_count:
        raise ValueError(f"Invalid {ref_type} index: {reference} (total: {total_count})")

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

        # Validate input data
        node_count = len(gltf.get('nodes', []))
        mesh_count = len(gltf.get('meshes', []))
        material_count = len(gltf.get('materials', []))
        accessor_count = len(gltf.get('accessors', []))
        texture_count = len(gltf.get('textures', []))
        bufferView_count = len(gltf.get('bufferViews', []))

        # Combine scenes
        for scene in gltf.get('scenes', []):
            combined_gltf['scenes'].append(scene)

        # Combine nodes
        for node in gltf.get('nodes', []):
            if 'mesh' in node:
                validate_index(node['mesh'], mesh_count, "mesh")
                node['mesh'] += mesh_offset  # Adjust mesh index
            combined_gltf['nodes'].append(node)

        # Combine meshes and update material indices
        for mesh in gltf.get('meshes', []):
            for primitive in mesh['primitives']:
                if 'material' in primitive:
                    validate_index(primitive['material'], material_count, "material")
                    primitive['material'] += material_offset  # Adjust material index
                validate_index(primitive['indices'], accessor_count, "accessor")
                primitive['indices'] += accessor_offset  # Adjust accessor index for indices
                primitive['attributes'] = {
                    k: v + accessor_offset for k, v in primitive['attributes'].items()
                }
            combined_gltf['meshes'].append(mesh)

        # Combine materials
        for material in gltf.get('materials', []):
            if 'pbrMetallicRoughness' in material:
                if 'baseColorTexture' in material['pbrMetallicRoughness']:
                    validate_index(material['pbrMetallicRoughness']['baseColorTexture']['index'], texture_count, "texture")
                    material['pbrMetallicRoughness']['baseColorTexture']['index'] += texture_offset
            combined_gltf['materials'].append(material)

        # Combine accessors
        for accessor in gltf.get('accessors', []):
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
            validate_index(texture['sampler'], len(gltf.get('samplers', [])), "sampler")
            validate_index(texture['source'], len(gltf.get('images', [])), "image")
            texture['sampler'] += sampler_offset
            texture['source'] += image_offset
            combined_gltf['textures'].append(texture)

        for sampler in gltf.get('samplers', []):
            combined_gltf['samplers'].append(sampler)

        for image in gltf.get('images', []):
            combined_gltf['images'].append(image)

        # Combine animations
        for animation in gltf.get('animations', []):
            for channel in animation['channels']:
                # Validate node index
                validate_index(channel['target']['node'], node_count, "node")
                channel['target']['node'] += node_offset

            for sampler in animation['samplers']:
                # Validate input/output accessors
                validate_index(sampler['input'], accessor_count, "accessor")
                validate_index(sampler['output'], accessor_count, "accessor")
                sampler['input'] += accessor_offset
                sampler['output'] += accessor_offset

            combined_gltf['animations'].append(animation)

        # Update offsets for the next glTF file
        node_offset += len(gltf['nodes'])
        mesh_offset += len(gltf['meshes'])
        material_offset += len(gltf['materials'])
        accessor_offset += len(gltf['accessors'])
        bufferView_offset += len(gltf['bufferViews'])
        buffer_offset += len(gltf['buffers'])
        animation_offset += len(gltf['animations'])
        texture_offset += len(gltf['textures'])
        sampler_offset += len(gltf['samplers'])
        image_offset += len(gltf['images'])

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