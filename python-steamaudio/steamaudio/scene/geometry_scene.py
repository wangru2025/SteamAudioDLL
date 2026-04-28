"""Geometry scene, material registry, and helper APIs."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Sequence

from ..bindings import loader
from ..bindings.ctypes_bindings import (
    AcousticMaterial as CAcousticMaterial,
    GeometrySceneHandle,
    StaticMeshHandle,
    TriangleIndices as CTriangleIndices,
    Vector3 as CVector3,
)
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..spatial.vector3 import Vector3


@dataclass
class Material:
    """Acoustic material properties used by Steam Audio geometry."""

    absorption_low: float
    absorption_mid: float
    absorption_high: float
    scattering: float
    transmission_low: float
    transmission_mid: float
    transmission_high: float

    PRESETS = {
        "generic": (0.10, 0.20, 0.30, 0.05, 0.10, 0.05, 0.03),
        "brick": (0.03, 0.04, 0.07, 0.05, 0.015, 0.015, 0.015),
        "concrete": (0.05, 0.07, 0.08, 0.05, 0.015, 0.002, 0.001),
        "ceramic": (0.01, 0.02, 0.02, 0.05, 0.060, 0.044, 0.011),
        "gravel": (0.60, 0.70, 0.80, 0.05, 0.031, 0.012, 0.008),
        "carpet": (0.24, 0.69, 0.73, 0.05, 0.020, 0.005, 0.003),
        "glass": (0.06, 0.03, 0.02, 0.05, 0.060, 0.044, 0.011),
        "plaster": (0.12, 0.06, 0.04, 0.05, 0.056, 0.056, 0.004),
        "wood": (0.11, 0.07, 0.06, 0.05, 0.070, 0.014, 0.005),
        "metal": (0.20, 0.07, 0.06, 0.05, 0.200, 0.025, 0.010),
        "rock": (0.13, 0.20, 0.24, 0.05, 0.015, 0.002, 0.001),
    }

    @classmethod
    def preset(cls, name: str) -> "Material":
        """Create a material from one of the built-in presets."""
        return MaterialRegistry.defaults().get(name)

    def to_c(self) -> CAcousticMaterial:
        """Convert to the low-level C structure."""
        return CAcousticMaterial(
            self.absorption_low,
            self.absorption_mid,
            self.absorption_high,
            self.scattering,
            self.transmission_low,
            self.transmission_mid,
            self.transmission_high,
        )


class MaterialRegistry:
    """Named material registry for reusable scene materials."""

    _default_instance: Optional["MaterialRegistry"] = None

    def __init__(self, initial: Optional[Dict[str, Material]] = None):
        self._materials: Dict[str, Material] = dict(initial or {})

    @classmethod
    def defaults(cls) -> "MaterialRegistry":
        """Return the shared registry containing the built-in presets."""
        if cls._default_instance is None:
            cls._default_instance = cls(
                {
                    name: Material(*values)
                    for name, values in Material.PRESETS.items()
                }
            )
        return cls._default_instance

    def list(self) -> List[str]:
        """List registered material names."""
        return sorted(self._materials.keys())

    def register(self, name: str, material: Material, replace_existing: bool = True) -> None:
        """Register a named material."""
        if not name:
            raise InvalidParameterError("Material name cannot be empty")
        if (not replace_existing) and (name in self._materials):
            raise InvalidParameterError(f"Material already exists: {name}")
        self._materials[name] = replace(material)

    def get(self, name: str) -> Material:
        """Retrieve a named material."""
        try:
            return replace(self._materials[name])
        except KeyError as exc:
            raise InvalidParameterError(f"Unknown material preset: {name}") from exc

    def resolve(self, material: str | Material) -> Material:
        """Resolve either a material name or a concrete material object."""
        if isinstance(material, Material):
            return replace(material)
        return self.get(material)


class StaticMesh:
    """Static mesh owned by a geometry scene."""

    def __init__(self, scene: "GeometryScene", handle: StaticMeshHandle):
        self._scene = scene
        self._handle: Optional[StaticMeshHandle] = handle

    def __del__(self):
        self._cleanup()

    def _cleanup(self):
        if getattr(self, "_handle", None):
            try:
                loader.get_library().geometry_static_mesh_destroy(self._handle)
            except Exception:
                pass
            finally:
                self._handle = None

    def set_material(self, material_index: int, material: Material) -> None:
        """Replace one of the mesh's materials."""
        if not self._handle:
            raise AudioProcessingError("Static mesh has been destroyed")
        loader.get_library().geometry_static_mesh_set_material(
            self._scene._handle,
            self._handle,
            material_index,
            ctypes.pointer(material.to_c()),
        )


class GeometryScene:
    """Steam Audio geometry scene."""

    def __init__(self, material_registry: Optional[MaterialRegistry] = None):
        self._handle: Optional[GeometrySceneHandle] = None
        self._meshes: List[StaticMesh] = []
        self.materials = material_registry or MaterialRegistry.defaults()

        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")

        lib = loader.get_library()
        self._handle = lib.geometry_scene_create()
        if not self._handle:
            raise AudioProcessingError("Failed to create geometry scene")

    def __del__(self):
        self._cleanup()

    def _cleanup(self):
        for mesh in getattr(self, "_meshes", []):
            mesh._cleanup()
        self._meshes = []

        if getattr(self, "_handle", None):
            try:
                loader.get_library().geometry_scene_destroy(self._handle)
            except Exception:
                pass
            finally:
                self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def commit(self) -> None:
        """Commit mesh/material changes to the scene."""
        if not self._handle:
            raise AudioProcessingError("Geometry scene has been destroyed")
        loader.get_library().geometry_scene_commit(self._handle)

    def add_static_mesh(
        self,
        vertices: Sequence[Vector3 | Sequence[float]],
        triangles: Sequence[Sequence[int]],
        material_indices: Sequence[int],
        materials: Sequence[Material | str],
    ) -> StaticMesh:
        """Add a static mesh to the scene."""
        if not self._handle:
            raise AudioProcessingError("Geometry scene has been destroyed")
        if len(triangles) != len(material_indices):
            raise InvalidParameterError("material_indices length must match triangles length")
        if not vertices or not triangles or not materials:
            raise InvalidParameterError("vertices, triangles, and materials cannot be empty")

        c_vertices = (CVector3 * len(vertices))()
        for i, vertex in enumerate(vertices):
            if isinstance(vertex, Vector3):
                c_vertices[i] = CVector3(vertex.x, vertex.y, vertex.z)
            else:
                x, y, z = vertex
                c_vertices[i] = CVector3(float(x), float(y), float(z))

        c_triangles = (CTriangleIndices * len(triangles))()
        for i, tri in enumerate(triangles):
            if len(tri) != 3:
                raise InvalidParameterError(f"Triangle {i} must contain 3 indices")
            c_triangles[i].indices[0] = int(tri[0])
            c_triangles[i].indices[1] = int(tri[1])
            c_triangles[i].indices[2] = int(tri[2])

        c_material_indices = (ctypes.c_int * len(material_indices))(*[int(x) for x in material_indices])
        resolved_materials = [self.materials.resolve(m) for m in materials]
        c_materials = (CAcousticMaterial * len(resolved_materials))(
            *[m.to_c() for m in resolved_materials]
        )

        handle = loader.get_library().geometry_scene_add_static_mesh(
            self._handle,
            c_vertices,
            len(vertices),
            c_triangles,
            len(triangles),
            c_material_indices,
            len(materials),
            c_materials,
        )
        if not handle:
            raise AudioProcessingError("Failed to add static mesh")

        mesh = StaticMesh(self, handle)
        self._meshes.append(mesh)
        return mesh

    def add_box(
        self,
        min_corner: Vector3 | Sequence[float],
        max_corner: Vector3 | Sequence[float],
        material: Material | str,
    ) -> StaticMesh:
        """Add a closed box mesh to the scene."""
        min_x, min_y, min_z = self._xyz(min_corner)
        max_x, max_y, max_z = self._xyz(max_corner)
        if min_x >= max_x or min_y >= max_y or min_z >= max_z:
            raise InvalidParameterError("min_corner must be strictly less than max_corner on all axes")

        vertices = [
            Vector3(min_x, min_y, min_z),
            Vector3(max_x, min_y, min_z),
            Vector3(max_x, max_y, min_z),
            Vector3(min_x, max_y, min_z),
            Vector3(min_x, min_y, max_z),
            Vector3(max_x, min_y, max_z),
            Vector3(max_x, max_y, max_z),
            Vector3(min_x, max_y, max_z),
        ]
        triangles = [
            (0, 1, 2), (0, 2, 3),
            (0, 1, 5), (0, 5, 4),
            (1, 5, 6), (1, 6, 2),
            (2, 6, 7), (2, 7, 3),
            (3, 7, 4), (3, 4, 0),
            (4, 5, 6), (4, 6, 7),
        ]
        material_indices = [0] * len(triangles)
        return self.add_static_mesh(vertices, triangles, material_indices, [material])

    def add_room(
        self,
        width: float,
        height: float,
        depth: float,
        wall_material: Material | str,
        floor_material: Optional[Material | str] = None,
        ceiling_material: Optional[Material | str] = None,
        center: Vector3 | Sequence[float] = Vector3(0.0, 0.0, 0.0),
    ) -> StaticMesh:
        """Add a six-sided room shell centered at the given point."""
        if width <= 0.0 or height <= 0.0 or depth <= 0.0:
            raise InvalidParameterError("Room dimensions must be positive")

        cx, cy, cz = self._xyz(center)
        half_w = width / 2.0
        half_d = depth / 2.0
        min_x = cx - half_w
        max_x = cx + half_w
        min_y = cy
        max_y = cy + height
        min_z = cz - half_d
        max_z = cz + half_d

        floor_material = floor_material or wall_material
        ceiling_material = ceiling_material or wall_material

        vertices: List[Vector3] = []
        triangles: List[tuple[int, int, int]] = []
        material_indices: List[int] = []

        def add_quad(v0: Vector3, v1: Vector3, v2: Vector3, v3: Vector3, material_index: int):
            base = len(vertices)
            vertices.extend([v0, v1, v2, v3])
            triangles.extend([(base + 0, base + 1, base + 2), (base + 0, base + 2, base + 3)])
            material_indices.extend([material_index, material_index])

        add_quad(
            Vector3(min_x, min_y, min_z),
            Vector3(max_x, min_y, min_z),
            Vector3(max_x, min_y, max_z),
            Vector3(min_x, min_y, max_z),
            0,
        )
        add_quad(
            Vector3(min_x, max_y, max_z),
            Vector3(max_x, max_y, max_z),
            Vector3(max_x, max_y, min_z),
            Vector3(min_x, max_y, min_z),
            1,
        )
        add_quad(
            Vector3(min_x, min_y, min_z),
            Vector3(min_x, max_y, min_z),
            Vector3(max_x, max_y, min_z),
            Vector3(max_x, min_y, min_z),
            2,
        )
        add_quad(
            Vector3(max_x, min_y, max_z),
            Vector3(max_x, max_y, max_z),
            Vector3(min_x, max_y, max_z),
            Vector3(min_x, min_y, max_z),
            2,
        )
        add_quad(
            Vector3(min_x, min_y, max_z),
            Vector3(min_x, max_y, max_z),
            Vector3(min_x, max_y, min_z),
            Vector3(min_x, min_y, min_z),
            2,
        )
        add_quad(
            Vector3(max_x, min_y, min_z),
            Vector3(max_x, max_y, min_z),
            Vector3(max_x, max_y, max_z),
            Vector3(max_x, min_y, max_z),
            2,
        )

        return self.add_static_mesh(
            vertices,
            triangles,
            material_indices,
            [floor_material, ceiling_material, wall_material],
        )

    def add_wall_with_doorway(
        self,
        axis: str,
        offset: float,
        min_extent: float,
        max_extent: float,
        height: float,
        material: Material | str,
        doorway_center: float = 0.0,
        doorway_half_width: float = 1.0,
        doorway_height: float = 2.5,
    ) -> StaticMesh:
        """Add a flat wall with a centered doorway cutout."""
        if axis not in {"x", "z"}:
            raise InvalidParameterError("axis must be 'x' or 'z'")
        if max_extent <= min_extent:
            raise InvalidParameterError("max_extent must be greater than min_extent")
        if height <= 0.0:
            raise InvalidParameterError("height must be positive")
        if doorway_half_width <= 0.0:
            raise InvalidParameterError("doorway_half_width must be positive")
        doorway_height = min(height, doorway_height)

        segments = [
            (min_extent, doorway_center - doorway_half_width, 0.0, height),
            (doorway_center + doorway_half_width, max_extent, 0.0, height),
            (doorway_center - doorway_half_width, doorway_center + doorway_half_width, doorway_height, height),
        ]

        vertices: List[Vector3] = []
        triangles: List[tuple[int, int, int]] = []
        material_indices: List[int] = []

        def add_quad(v0: Vector3, v1: Vector3, v2: Vector3, v3: Vector3):
            base = len(vertices)
            vertices.extend([v0, v1, v2, v3])
            triangles.extend([(base + 0, base + 1, base + 2), (base + 0, base + 2, base + 3)])
            material_indices.extend([0, 0])

        for start, end, min_y, max_y in segments:
            if start >= end or min_y >= max_y:
                continue
            if axis == "x":
                add_quad(
                    Vector3(offset, min_y, start),
                    Vector3(offset, max_y, start),
                    Vector3(offset, max_y, end),
                    Vector3(offset, min_y, end),
                )
            else:
                add_quad(
                    Vector3(start, min_y, offset),
                    Vector3(start, max_y, offset),
                    Vector3(end, max_y, offset),
                    Vector3(end, min_y, offset),
                )

        if not triangles:
            raise InvalidParameterError("Doorway consumes the full wall; no geometry remains")

        return self.add_static_mesh(vertices, triangles, material_indices, [material])

    @staticmethod
    def _xyz(value: Vector3 | Sequence[float]) -> tuple[float, float, float]:
        if isinstance(value, Vector3):
            return value.x, value.y, value.z
        x, y, z = value
        return float(x), float(y), float(z)
