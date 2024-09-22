
#include <iostream>
#include <fstream>
#include <filesystem>
#include <nlohmann/json.hpp>

namespace fs = std::filesystem;
using json = nlohmann::json;

// Function to read a .gltf file and return its JSON content
json readGltfFile(const std::string& filePath) {
    std::ifstream file(filePath);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open the file: " + filePath);
    }
    
    json gltfJson;
    file >> gltfJson;
    file.close();
    return gltfJson;
}

// Function to process all .gltf and .glb files in a directory
json processGltfFiles(const std::string& directoryPath) {
    json combinedJson = json::array();
    
    // Iterate over each file in the directory
    for (const auto& entry : fs::directory_iterator(directoryPath)) {
        if (entry.is_regular_file()) {
            std::string filePath = entry.path().string();
            
            // Check for .gltf files
            if (entry.path().extension() == ".gltf") {
                try {
                    json gltfData = readGltfFile(filePath);
                    combinedJson.push_back({{"file", filePath}, {"content", gltfData}});
                } catch (const std::exception& ex) {
                    std::cerr << "Error reading file " << filePath << ": " << ex.what() << std::endl;
                }
            }
            
            // Optionally handle .glb files here (would require GLB to JSON conversion)
            // Placeholder for glb processing logic
            else if (entry.path().extension() == ".glb") {
                std::cerr << "Warning: .glb file handling is not implemented: " << filePath << std::endl;
                // Add logic to parse .glb file if needed
            }
        }
    }
    
    return combinedJson;
}

int main() {
    std::string directoryPath;
    std::cout << "Enter directory path: ";
    std::cin >> directoryPath;

    try {
        json allGltfFiles = processGltfFiles(directoryPath);
        
        // Output the combined JSON object
        std::cout << "Combined JSON content from all files: \n" << allGltfFiles.dump(4) << std::endl;
        
        // Save the combined JSON into a file
        std::ofstream outFile("combined_gltf.json");
        outFile << allGltfFiles.dump(4);
        outFile.close();
        
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << std::endl;
        return 1;
    }

    return 0;
}