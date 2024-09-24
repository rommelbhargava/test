import json

def load_gltf(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_gltf(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def offset_indices(obj, offset_map):
    """Recursively offset indices based on the offset map."""
    if isinstance(obj, list):
        return [offset_indices(item, offset_map) for item in obj]
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in offset_map:
                obj[k] = v + offset_map[k]
            else:
                obj[k] = offset_indices(v, offset_map)
    elif isinstance(obj, int):
        return obj
    return obj

def merge_gltf(gltf1, gltf2):
    # Calculate offsets
    offsets = {
        "accessors": len(gltf1.get("accessors", [])),
        "animations": len(gltf1.get("animations", [])),
        "buffers": len(gltf1.get("buffers", [])),
        "bufferViews": len(gltf1.get("bufferViews", [])),
        "cameras": len(gltf1.get("cameras", [])),
        "images": len(gltf1.get("images", [])),
        "materials": len(gltf1.get("materials", [])),
        "meshes": len(gltf1.get("meshes", [])),
        "nodes": len(gltf1.get("nodes", [])),
        "samplers": len(gltf1.get("samplers", [])),
        "scenes": len(gltf1.get("scenes", [])),
        "skins": len(gltf1.get("skins", [])),
        "textures": len(gltf1.get("textures", [])),
    }

    combined_gltf = gltf1.copy()

    # Update nodes and their references
    for key in ['nodes', 'meshes', 'materials', 'accessors', 'bufferViews', 'buffers', 'textures', 'samplers', 'images', 'animations', 'skins', 'cameras', 'scenes']:
        if key in gltf2:
            for item in gltf2[key]:
                offset_item = offset_indices(item.copy(), offsets)
                combined_gltf[key].append(offset_item)

    # Update extensions if present
    for ext_key in ["extensionsUsed", "extensionsRequired"]:
        if ext_key in gltf2:
            if ext_key not in combined_gltf:
                combined_gltf[ext_key] = []
            for ext in gltf2[ext_key]:
                if ext not in combined_gltf[ext_key]:
                    combined_gltf[ext_key].append(ext)

    return combined_gltf

def combine_gltf_files(gltf_file_1, gltf_file_2, output_file):
    gltf1 = load_gltf(gltf_file_1)
    gltf2 = load_gltf(gltf_file_2)

    combined_gltf = merge_gltf(gltf1, gltf2)

    save_gltf(output_file, combined_gltf)

# Example usage:
combine_gltf_files('model1.gltf', 'model2.gltf', 'combined_model.gltf')