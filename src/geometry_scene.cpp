#include "geometry_scene.h"
#include "phonon_wrapper.h"
#include <stdexcept>

GeometryScene::GeometryScene() {
    auto& phonon = PhononWrapper::instance();
    if (!phonon.is_initialized()) {
        throw std::runtime_error("Steam Audio not initialized");
    }

    IPLSceneSettings settings{};
    settings.type = IPL_SCENETYPE_DEFAULT;

    if (iplSceneCreate(phonon.get_context(), &settings, &scene_) != IPL_STATUS_SUCCESS) {
        throw std::runtime_error("Failed to create geometry scene");
    }
}

GeometryScene::~GeometryScene() {
    if (scene_) {
        iplSceneRelease(&scene_);
    }
}

void GeometryScene::commit() {
    if (!scene_) {
        throw std::runtime_error("Invalid geometry scene");
    }

    iplSceneCommit(scene_);
}

StaticMesh::StaticMesh(
    IPLScene scene,
    const std::vector<IPLVector3>& vertices,
    const std::vector<IPLTriangle>& triangles,
    const std::vector<IPLint32>& material_indices,
    const std::vector<IPLMaterial>& materials) {

    IPLStaticMeshSettings settings{};
    settings.numVertices = static_cast<IPLint32>(vertices.size());
    settings.numTriangles = static_cast<IPLint32>(triangles.size());
    settings.numMaterials = static_cast<IPLint32>(materials.size());
    settings.vertices = const_cast<IPLVector3*>(vertices.data());
    settings.triangles = const_cast<IPLTriangle*>(triangles.data());
    settings.materialIndices = const_cast<IPLint32*>(material_indices.data());
    settings.materials = const_cast<IPLMaterial*>(materials.data());

    if (iplStaticMeshCreate(scene, &settings, &mesh_) != IPL_STATUS_SUCCESS) {
        throw std::runtime_error("Failed to create static mesh");
    }

    iplStaticMeshAdd(mesh_, scene);
}

StaticMesh::~StaticMesh() {
    if (mesh_) {
        iplStaticMeshRelease(&mesh_);
    }
}

void StaticMesh::set_material(IPLScene scene, IPLint32 material_index, const IPLMaterial& material) {
    if (!mesh_) {
        throw std::runtime_error("Invalid static mesh");
    }

    IPLMaterial copy = material;
    iplStaticMeshSetMaterial(mesh_, scene, &copy, material_index);
}
