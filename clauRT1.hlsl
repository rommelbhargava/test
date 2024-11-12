// Single bounce reflection compute shader using RayQuery
#pragma kernel CSMain

// Resources
RaytracingAccelerationStructure SceneAS : register(t0);
RWTexture2D<float4> ReflectionMap : register(u0);
Texture2D<float4> DepthBuffer : register(t1);
Texture2D<float4> NormalBuffer : register(t2);
StructuredBuffer<Material> MaterialBuffer : register(t3);

// Constants
cbuffer GlobalConstants : register(b0)
{
    float4x4 ViewMatrix;
    float4x4 InvViewMatrix;
    float4x4 ProjectionMatrix;
    float4x4 InvProjectionMatrix;
    float3 CameraPosition;
    float2 ScreenDimensions;
    float MaxRayLength;
}

struct Material {
    float3 baseColor;
    float metallic;
    float roughness;
    float3 emission;
    float ao;
};

// Helper functions
float3 GetWorldPositionFromDepth(float2 uv, float depth) {
    float4 clipSpacePosition = float4(uv * 2.0 - 1.0, depth, 1.0);
    float4 viewSpacePosition = mul(InvProjectionMatrix, clipSpacePosition);
    viewSpacePosition /= viewSpacePosition.w;
    float4 worldSpacePosition = mul(InvViewMatrix, viewSpacePosition);
    return worldSpacePosition.xyz;
}

float3 FresnelSchlick(float cosTheta, float3 F0) {
    return F0 + (1.0 - F0) * pow(1.0 - cosTheta, 5.0);
}

[numthreads(8, 8, 1)]
void CSMain(uint3 id : SV_DispatchThreadID)
{
    // Check if within bounds
    if (id.x >= ScreenDimensions.x || id.y >= ScreenDimensions.y)
    {
        return;
    }

    // Get UV coordinates
    float2 uv = float2(id.xy) / ScreenDimensions;
    
    // Sample depth and normal
    float depth = DepthBuffer[id.xy].r;
    float3 normal = NormalBuffer[id.xy].xyz * 2.0 - 1.0; // Assuming packed normals
    
    // Get world position
    float3 worldPos = GetWorldPositionFromDepth(uv, depth);
    
    // Get material properties
    Material material = MaterialBuffer[0]; // Replace with actual material index
    
    // Calculate view direction
    float3 V = normalize(CameraPosition - worldPos);
    
    // Calculate reflection direction
    float3 reflectionDir = reflect(-V, normal);
    
    // Initialize RayQuery
    RayQuery<RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES> q;
    
    // Setup ray
    RayDesc ray;
    ray.Origin = worldPos;
    ray.Direction = reflectionDir;
    ray.TMin = 0.001; // Avoid self-intersection
    ray.TMax = MaxRayLength;
    
    // Initialize reflection color
    float3 reflectionColor = float3(0, 0, 0);
    
    // Initialize ray query
    q.TraceRayInline(
        SceneAS,
        RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES | RAY_FLAG_ACCEPT_FIRST_HIT | RAY_FLAG_FORCE_OPAQUE,
        0xFF,
        ray
    );
    
    // Process ray query
    while (q.Proceed())
    {
        // We only care about the closest hit
        if (q.CandidateType() == CANDIDATE_NON_OPAQUE_TRIANGLE)
        {
            // Skip non-opaque geometry
            continue;
        }
    }
    
    // Check if we hit anything
    if (q.CommittedStatus() == COMMITTED_TRIANGLE_HIT)
    {
        // Get hit information
        float3 hitPosition = ray.Origin + ray.Direction * q.CommittedRayT();
        float3 hitNormal = q.CommittedGeometryNormal();
        int primitiveIndex = q.CommittedPrimitiveIndex();
        int instanceIndex = q.CommittedInstanceIndex();
        
        // Get hit material (implement based on your material system)
        Material hitMaterial = MaterialBuffer[primitiveIndex]; // Replace with actual material lookup
        
        // Calculate basic lighting at hit point
        float3 hitToLight = normalize(float3(1, 1, 1)); // Replace with actual light direction
        float NdotL = max(dot(hitNormal, hitToLight), 0.0);
        
        // Calculate base reflectivity
        float3 F0 = lerp(float3(0.04, 0.04, 0.04), material.baseColor, material.metallic);
        
        // Calculate Fresnel term
        float3 F = FresnelSchlick(max(dot(normal, V), 0.0), F0);
        
        // Calculate final reflection color
        reflectionColor = hitMaterial.baseColor * NdotL * F;
        
        // Apply roughness fade
        float roughnessFade = 1.0 - material.roughness;
        reflectionColor *= roughnessFade;
    }
    else
    {
        // Ray missed - could sample environment map here
        reflectionColor = float3(0, 0, 0);
    }
    
    // Store final reflection color
    ReflectionMap[id.xy] = float4(reflectionColor, 1.0);
}