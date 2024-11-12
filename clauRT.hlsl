pragma kernel CSMain

// Structures
struct Material {
    float3 baseColor;
    float metallic;
    float roughness;
    float3 emission;
    float ao;
};

struct Light {
    float3 position;
    float3 color;
    float intensity;
};

// Input resources
RWTexture2D<float4> ReflectionMap;
Texture2D<float4> DepthBuffer;
StructuredBuffer<Material> MaterialBuffer;
StructuredBuffer<Light> LightBuffer;

// Constants and parameters
float4x4 ViewMatrix;
float4x4 InvViewMatrix;
float4x4 ProjectionMatrix;
float4x4 InvProjectionMatrix;
float3 CameraPosition;
uint NumLights;
float2 ScreenDimensions;

// Constants for PBR calculations
static const float PI = 3.14159265359;
static const float Epsilon = 0.0001;

// Helper functions
float3 GetWorldPositionFromDepth(float2 uv, float depth) {
    float4 clipSpacePosition = float4(uv * 2.0 - 1.0, depth, 1.0);
    float4 viewSpacePosition = mul(InvProjectionMatrix, clipSpacePosition);
    viewSpacePosition /= viewSpacePosition.w;
    float4 worldSpacePosition = mul(InvViewMatrix, viewSpacePosition);
    return worldSpacePosition.xyz;
}

// Normal Distribution Function (GGX/Trowbridge-Reitz)
float DistributionGGX(float3 N, float3 H, float roughness) {
    float a = roughness * roughness;
    float a2 = a * a;
    float NdotH = max(dot(N, H), 0.0);
    float NdotH2 = NdotH * NdotH;

    float nom = a2;
    float denom = (NdotH2 * (a2 - 1.0) + 1.0);
    denom = PI * denom * denom;

    return nom / max(denom, Epsilon);
}

// Geometry Function (Smith's Schlick-GGX)
float GeometrySchlickGGX(float NdotV, float roughness) {
    float r = (roughness + 1.0);
    float k = (r * r) / 8.0;
    float nom = NdotV;
    float denom = NdotV * (1.0 - k) + k;
    return nom / max(denom, Epsilon);
}

float GeometrySmith(float3 N, float3 V, float3 L, float roughness) {
    float NdotV = max(dot(N, V), 0.0);
    float NdotL = max(dot(N, L), 0.0);
    float ggx2 = GeometrySchlickGGX(NdotV, roughness);
    float ggx1 = GeometrySchlickGGX(NdotL, roughness);
    return ggx1 * ggx2;
}

// Fresnel Equation (Schlick approximation)
float3 FresnelSchlick(float cosTheta, float3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

[numthreads(8, 8, 1)]
void CSMain(uint3 id : SV_DispatchThreadID) {
    // Check if within bounds
    if (id.x >= ScreenDimensions.x || id.y >= ScreenDimensions.y) {
        return;
    }

    // Get UV coordinates
    float2 uv = float2(id.xy) / ScreenDimensions;
    
    // Sample depth and get world position
    float depth = DepthBuffer[id.xy].r;
    float3 worldPos = GetWorldPositionFromDepth(uv, depth);
    
    // Get material properties from G-buffer or material buffer
    Material material = MaterialBuffer[0]; // Assuming index corresponds to current pixel
    
    // Calculate view direction
    float3 V = normalize(CameraPosition - worldPos);
    
    // Assumed normal from G-buffer (in practice, you would read this from a G-buffer)
    float3 N = normalize(float3(0, 1, 0)); // Replace with actual normal from G-buffer
    
    // Calculate reflection vector
    float3 R = reflect(-V, N);
    
    // Initialize reflection color
    float3 reflectionColor = float3(0, 0, 0);
    
    // Calculate base reflectivity (F0)
    float3 F0 = lerp(float3(0.04, 0.04, 0.04), material.baseColor, material.metallic);
    
    // Accumulate reflection from all lights
    for (uint i = 0; i < NumLights; i++) {
        Light light = LightBuffer[i];
        float3 L = normalize(light.position - worldPos);
        float3 H = normalize(V + L);
        
        float distance = length(light.position - worldPos);
        float attenuation = 1.0 / (distance * distance);
        float3 radiance = light.color * light.intensity * attenuation;
        
        // Cook-Torrance BRDF
        float NDF = DistributionGGX(N, H, material.roughness);
        float G = GeometrySmith(N, V, L, material.roughness);
        float3 F = FresnelSchlick(max(dot(H, V), 0.0), F0);
        
        float3 numerator = NDF * G * F;
        float denominator = 4.0 * max(dot(N, V), 0.0) * max(dot(N, L), 0.0);
        float3 specular = numerator / max(denominator, Epsilon);
        
        float NdotL = max(dot(N, L), 0.0);
        reflectionColor += (specular * radiance * NdotL);
    }