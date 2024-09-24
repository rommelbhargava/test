import json
import os

def load_gltf(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def validate_index(reference, total_count, ref_type):
    if reference >= total_count:
        raise ValueError(f"Invalid {ref_type} index: {reference} (total: {total_count})")

def combine_gltf_files(gltf_file_1, gltf_file_2):
    # Load the two glTF files
    gltf_1 = load_gltf(gltf_file_1)
    gltf_2 = load_gltf(gltf_file_2)

    # Initialize the combined glTF structure
    combined_gltf = {
        "asset": gltf_1.get("asset", {"version": "2.0"}),  # asset information from first glTF
        "scenes": [],
        "nodes": [],
        "meshes": [],
        "materials": [],
        "accessors": [],
        "bufferViews": [],
        "buffers": [],
        "textures": [],
        "samplers": [],
        "images": [],
        "animations": [],
        "skins": [],
        "cameras": [],
        "extensionsUsed": [],
        "extensionsRequired": [],
    }

    # Helper function to offset indices
    def offset_list(data, offset):
        if isinstance(data, list):
            return [item + offset for item in data]
        return data + offset if isinstance(data, int) else data

    # Helper function to merge two lists
    def merge_list(key, offset):
        combined_gltf[key].extend(gltf_2.get(key, []))
        if offset:
            for element in combined_gltf[key][-len(gltf_2.get(key, [])):]:
                if key == "nodes" and "mesh" in element:
                    element["mesh"] += mesh_offset
                if "camera" in element:
                    element["camera"] += camera_offset
                if "skin" in element:
                    element["skin"] += skin_offset
                if "children" in element:
                    element["children"] = offset_list(element["children"], node_offset)

    # Offsets
    node_offset = len(gltf_1.get("nodes", []))
    mesh_offset = len(gltf_1.get("meshes", []))
    material_offset = len(gltf_1.get("materials", []))
    accessor_offset = len(gltf_1.get("accessors", []))
    bufferView_offset = len(gltf_1.get("bufferViews", []))
    buffer_offset = len(gltf_1.get("buffers", []))
    texture_offset = len(gltf_1.get("textures", []))
    sampler_offset = len(gltf_1.get("samplers", []))
    image_offset = len(gltf_1.get("images", []))
    animation_offset = len(gltf_1.get("animations", []))
    skin_offset = len(gltf_1.get("skins", []))
    camera_offset = len(gltf_1.get("cameras", []))

    # Merge scenes
    for scene in gltf_1.get("scenes", []):
        combined_gltf["scenes"].append(scene)
    for scene in gltf_2.get("scenes", []):
        if "nodes" in scene:
            scene["nodes"] = offset_list(scene["nodes"], node_offset)
        combined_gltf["scenes"].append(scene)

    # Merge nodes, meshes, and all other glTF components, adjusting indices
    merge_list("nodes", node_offset)
    merge_list("meshes", mesh_offset)
    merge_list("materials", material_offset)
    merge_list("accessors", accessor_offset)
    merge_list("bufferViews", bufferView_offset)
    merge_list("buffers", buffer_offset)
    merge_list("textures", texture_offset)
    merge_list("samplers", sampler_offset)
    merge_list("images", image_offset)
    merge_list("animations", animation_offset)
    merge_list("skins", skin_offset)
    merge_list("cameras", camera_offset)

    # Merge extensions if used
    for ext in gltf_1.get("extensionsUsed", []):
        combined_gltf["extensionsUsed"].append(ext)
    for ext in gltf_2.get("extensionsUsed", []):
        if ext not in combined_gltf["extensionsUsed"]:
            combined_gltf["extensionsUsed"].append(ext)

    for ext in gltf_1.get("extensionsRequired", []):
        combined_gltf["extensionsRequired"].append(ext)
    for ext in gltf_2.get("extensionsRequired", []):
        if ext not in combined_gltf["extensionsRequired"]:
            combined_gltf["extensionsRequired"].append(ext)

    # Save combined glTF JSON
    with open('combined_model.gltf', 'w') as f:
        json.dump(combined_gltf, f, indent=2)

    # Handle binary buffers
    buffer_data = []
    for buffer in gltf_1.get("buffers", []):
        buffer_data.append(buffer['uri'])
    for buffer in gltf_2.get("buffers", []):
        buffer_data.append(buffer['uri'])

    with open('combined_model.bin', 'wb') as f_out:
        for buffer_file in buffer_data:
            with open(buffer_file, 'rb') as f_in:
                f_out.write(f_in.read())

# List of glTF files to combine
gltf_file_1 = 'model1.gltf'
gltf_file_2 = 'model2.gltf'

combine_gltf_files(gltf_file_1, gltf_file_2)