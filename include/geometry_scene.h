#pragma once

#include <phonon.h>
#include <vector>
#include "c_interface.h"

class GeometryScene {
public:
    GeometryScene();
    ~GeometryScene();

    IPLScene get() const { return scene_; }
    void commit();

private:
    IPLScene scene_ = nullptr;
};

class StaticMesh {
public:
    StaticMesh(
        IPLScene scene,
        const std::vector<IPLVector3>& vertices,
        const std::vector<IPLTriangle>& triangles,
        const std::vector<IPLint32>& material_indices,
        const std::vector<IPLMaterial>& materials
    );
    ~StaticMesh();

    void set_material(IPLScene scene, IPLint32 material_index, const IPLMaterial& material);

private:
    IPLStaticMesh mesh_ = nullptr;
};
