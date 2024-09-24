import json

def load_gltf(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def offset_indices(data, offset_map):
    if isinstance(data, list):
        return [offset_indices(item, offset_map) for item in data]
    elif isinstance(data, int):
        for key, offset in offset_map.items():
            if key == 'nodes' and 'mesh' in offset_map and data >= offset_map['mesh']:
                return data + offset
            elif key == 'skins' and 'joints' in offset_map and data >= offset_map['joints']:
                return data + offset
            elif data >= offset:
                return data + offset
        return data
    elif isinstance(data, dict):
        for k, v in data.items():
            data[k] = offset_indices(v, offset_map)
    return data

def merge_gltf(gltf1, gltf2):
    combined_gltf = {
        "asset": gltf1.get("asset", {"version": "2.0"}),  
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

    # Calculate offsets for each section
    offsets = {
        "scenes": len(gltf1.get("scenes", [])),
        "nodes": len(gltf1.get("nodes", [])),
        "meshes": len(gltf1.get("meshes", [])),
        "materials": len(gltf1.get("materials", [])),
        "accessors": len(gltf1.get("accessors", [])),
        "bufferViews": len(gltf1.get("bufferViews", [])),
        "buffers": len(gltf1.get("buffers", [])),
        "textures": len(gltf1.get("textures", [])),
        "samplers": len(gltf1.get("samplers", [])),
        "images": len(gltf1.get("images", [])),
        "animations": len(gltf1.get("animations", [])),
        "skins": len(gltf1.get("skins", [])),
        "cameras": len(gltf1.get("cameras", [])),
    }

    # Function to merge two lists with offset correction
    def merge_and_offset(key, offset_key):
        offset = offsets[offset_key]
        for item in gltf2.get(key, []):
            item = offset_indices(item, offsets)
            combined_gltf[key].append(item)

    # Merge scenes
    for scene in gltf1.get("scenes", []):
        combined_gltf["scenes"].append(scene)
    for scene in gltf2.get("scenes", []):
        if "nodes" in scene:
            scene["nodes"] = [node + offsets['nodes'] for node in scene["nodes"]]
        combined_gltf["scenes"].append(scene)

    # Merge nodes
    merge_and_offset("nodes", "nodes")

    # Merge meshes
    merge_and_offset("meshes", "meshes")

    # Merge materials
    merge_and_offset("materials", "materials")

    # Merge accessors
    merge_and_offset("accessors", "accessors")

    # Merge bufferViews
    merge_and_offset("bufferViews", "bufferViews")

    # Merge buffers
    merge_and_offset("buffers", "buffers")

    # Merge textures
    merge_and_offset("textures", "textures")

    # Merge samplers
    merge_and_offset("samplers", "samplers")

    # Merge images
    merge_and_offset("images", "images")

    # Merge animations
    merge_and_offset("animations", "animations")

    # Merge skins
    merge_and_offset("skins", "skins")

    # Merge cameras
    merge_and_offset("cameras", "cameras")

    # Merge extensions
    for ext in gltf1.get("extensionsUsed", []):
        combined_gltf["extensionsUsed"].append(ext)
    for ext in gltf2.get("extensionsUsed", []):
        if ext not in combined_gltf["extensionsUsed"]:
            combined_gltf["extensionsUsed"].append(ext)

    for ext in gltf1.get("extensionsRequired", []):
        combined_gltf["extensionsRequired"].append(ext)
    for ext in gltf2.get("extensionsRequired", []):
        if ext not in combined_gltf["extensionsRequired"]:
            combined_gltf["extensionsRequired"].append(ext)

    return combined_gltf

def save_gltf(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def combine_gltf_files(gltf_file_1, gltf_file_2, output_file):
    gltf1 = load_gltf(gltf_file_1)
    gltf2 = load_gltf(gltf_file_2)

    combined_gltf = merge_gltf(gltf1, gltf2)

    save_gltf(output_file, combined_gltf)

# Example usage:
combine_gltf_files('model1.gltf', 'model2.gltf', 'combined_model.gltf')