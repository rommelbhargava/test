#include <tiny_gltf.h>
#include <iostream>
#include <filesystem>  // C++17 required for std::filesystem
#include <string>

// Namespace alias for convenience
namespace fs = std::filesystem;

void CombineGLTFModels(tinygltf::Model& modelA, const tinygltf::Model& modelB) {
    // Offset for indices in modelB to merge into modelA
    size_t nodeOffset = modelA.nodes.size();
    size_t meshOffset = modelA.meshes.size();
    size_t bufferOffset = modelA.buffers.size();
    size_t materialOffset = modelA.materials.size();
    size_t cameraOffset = modelA.cameras.size();
    size_t animationOffset = modelA.animations.size();
    size_t lightOffset = modelA.lights.size();
    size_t textureOffset = modelA.textures.size();
    size_t imageOffset = modelA.images.size();
    size_t samplerOffset = modelA.samplers.size();
    size_t skinOffset = modelA.skins.size();
    size_t bufferViewOffset = modelA.bufferViews.size();
    size_t accessorOffset = modelA.accessors.size();

    // 1. Merge nodes (update node references to use the correct mesh/material indices)
    for (const auto& node : modelB.nodes) {
        tinygltf::Node newNode = node;
        if (newNode.mesh >= 0) newNode.mesh += meshOffset; // Adjust mesh index
        if (newNode.camera >= 0) newNode.camera += cameraOffset; // Adjust camera index
        if (newNode.skin >= 0) newNode.skin += skinOffset;  // Adjust skin index
        modelA.nodes.push_back(newNode);
    }

    // 2. Merge meshes
    for (const auto& mesh : modelB.meshes) {
        modelA.meshes.push_back(mesh);
    }

    // 3. Merge materials
    for (const auto& material : modelB.materials) {
        tinygltf::Material newMaterial = material;
        // Adjust texture indices in materials
        for (auto& val : newMaterial.values) {
            if (val.second.json_double_value["index"] >= 0) {
                val.second.json_double_value["index"] += textureOffset;
            }
        }
        for (auto& val : newMaterial.additionalValues) {
            if (val.second.json_double_value["index"] >= 0) {
                val.second.json_double_value["index"] += textureOffset;
            }
        }
        modelA.materials.push_back(newMaterial);
    }

    // 4. Merge buffers and bufferViews
    for (const auto& buffer : modelB.buffers) {
        modelA.buffers.push_back(buffer);
    }

    for (const auto& bufferView : modelB.bufferViews) {
        tinygltf::BufferView newBufferView = bufferView;
        newBufferView.buffer += bufferOffset; // Adjust buffer index
        modelA.bufferViews.push_back(newBufferView);
    }

    // 5. Merge accessors
    for (const auto& accessor : modelB.accessors) {
        modelA.accessors.push_back(accessor);
    }

    // 6. Merge scenes into a single scene (assumes modelA has one scene)
    if (!modelA.scenes.empty()) {
        tinygltf::Scene& sceneA = modelA.scenes[0];  // Use first scene from modelA
        for (const auto& sceneB : modelB.scenes) {
            for (const auto& nodeIndex : sceneB.nodes) {
                sceneA.nodes.push_back(nodeIndex + nodeOffset);  // Adjust node indices
            }
        }
    } else {
        // If modelA has no scene, just copy scenes (should not happen in normal cases)
        for (const auto& sceneB : modelB.scenes) {
            tinygltf::Scene newScene = sceneB;
            for (auto& node : newScene.nodes) {
                node += nodeOffset;  // Adjust node indices
            }
            modelA.scenes.push_back(newScene);
        }
    }

    // 7. Merge cameras
    for (const auto& camera : modelB.cameras) {
        modelA.cameras.push_back(camera);
    }

    // 8. Merge animations
    for (const auto& animation : modelB.animations) {
        tinygltf::Animation newAnimation = animation;
        // Adjust node indices in animation channels
        for (auto& channel : newAnimation.channels) {
            channel.target_node += nodeOffset;
        }
        modelA.animations.push_back(newAnimation);
    }

    // 9. Merge lights (requires extension handling)
    if (modelB.lights.size() > 0) {
        if (modelA.lights.empty()) {
            modelA.extensionsUsed.push_back("KHR_lights_punctual");
        }
        for (const auto& light : modelB.lights) {
            modelA.lights.push_back(light);
        }

        // Adjust node references for lights
        for (auto& node : modelA.nodes) {
            if (node.extensions.find("KHR_lights_punctual") != node.extensions.end()) {
                node.extensions["KHR_lights_punctual"]["light"] = node.extensions["KHR_lights_punctual"]["light"].Get<int>() + lightOffset;
            }
        }
    }

    // 10. Merge textures
    for (const auto& texture : modelB.textures) {
        tinygltf::Texture newTexture = texture;
        newTexture.sampler += samplerOffset;
        newTexture.source += imageOffset;
        modelA.textures.push_back(newTexture);
    }

    // 11. Merge images
    for (const auto& image : modelB.images) {
        modelA.images.push_back(image);
    }

    // 12. Merge samplers
    for (const auto& sampler : modelB.samplers) {
        modelA.samplers.push_back(sampler);
    }

    // 13. Merge skins
    for (const auto& skin : modelB.skins) {
        tinygltf::Skin newSkin = skin;
        for (auto& joint : newSkin.joints) {
            joint += nodeOffset;  // Adjust node indices in skin joints
        }
        modelA.skins.push_back(newSkin);
    }
}

void LoadAndCombineGLTFs(const std::string& directoryPath, tinygltf::Model& combinedModel) {
    tinygltf::TinyGLTF loader;
    std::string err, warn;

    // Create a single combined scene
    tinygltf::Scene combinedScene;
    combinedModel.scenes.push_back(combinedScene);  // Start with one scene

    // Iterate through the directory to find all .gltf files
    for (const auto& entry : fs::directory_iterator(directoryPath)) {
        if (entry.path().extension() == ".gltf") {
            std::cout << "Loading: " << entry.path().string() << std::endl;
            
            tinygltf::Model tempModel;
            bool success = loader.LoadASCIIFromFile(&tempModel, &err, &warn, entry.path().string());

            if (!warn.empty()) {
                std::cerr << "Warning: " << warn << std::endl;
            }
            if (!err.empty()) {
                std::cerr << "Error: " << err << std::endl;
            }

            if (success) {
                CombineGLTFModels(combinedModel, tempModel);
            } else {
                std::cerr << "Failed to load " << entry.path() << std::endl;
            }
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0]​⬤