"""High-level audio environment built on top of scene and simulation APIs."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Mapping, Optional, Sequence

from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..effects.direct_effect import DirectEffect
from ..processor.audio_mixer import AudioMixer
from ..scene.geometry_scene import GeometryScene, MaterialRegistry
from ..simulation.direct_simulator import DirectSimulator
from ..spatial.spatialization import SpatializationParams
from ..spatial.vector3 import Vector3
from ..bindings.ctypes_bindings import (
    DIRECT_EFFECT_APPLY_AIR_ABSORPTION,
    DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION,
    DIRECT_EFFECT_APPLY_OCCLUSION,
    DIRECT_EFFECT_APPLY_TRANSMISSION,
    SCENE_OCCLUSION_RAYCAST,
)


@dataclass
class SourceConfig:
    """Per-source configuration used by AudioEnvironment."""

    position: Vector3
    ahead: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, -1.0))
    up: Vector3 = field(default_factory=lambda: Vector3(0.0, 1.0, 0.0))
    min_distance: float = 1.0
    direct_flags: int = (
        DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION
        | DIRECT_EFFECT_APPLY_AIR_ABSORPTION
        | DIRECT_EFFECT_APPLY_OCCLUSION
        | DIRECT_EFFECT_APPLY_TRANSMISSION
    )
    occlusion_type: int = SCENE_OCCLUSION_RAYCAST
    occlusion_radius: float = 1.0
    num_occlusion_samples: int = 16
    num_transmission_rays: int = 8
    input_channels: int = 1


class AudioEnvironment:
    """High-level object that manages scene, simulation, and playback helpers."""

    def __init__(
        self,
        scene: Optional[GeometryScene] = None,
        max_sources: int = 16,
        geometry_enabled: bool = True,
        material_registry: Optional[MaterialRegistry] = None,
    ):
        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")

        self.scene = scene or GeometryScene(material_registry=material_registry)
        self.mixer = AudioMixer(max_sources=max_sources)
        self.simulator = DirectSimulator(self.scene, max_sources=max_sources)
        self.geometry_enabled = geometry_enabled
        self.listener_position = Vector3(0.0, 0.0, 0.0)
        self.listener_ahead = Vector3(0.0, 0.0, -1.0)
        self.listener_up = Vector3(0.0, 1.0, 0.0)
        self._sources: Dict[int, SourceConfig] = {}
        self._effects: Dict[int, DirectEffect] = {}
        self._last_direct_params = {}

    def _ensure_source_exists(self, source_id: int) -> SourceConfig:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise InvalidParameterError(f"Source not found: {source_id}") from exc

    def __del__(self):
        self._cleanup()

    def _cleanup(self):
        for effect in list(self._effects.values()):
            effect._cleanup()
        self._effects.clear()
        self._sources.clear()
        if hasattr(self, "simulator") and self.simulator:
            self.simulator._cleanup()
        if hasattr(self, "mixer") and self.mixer:
            self.mixer._cleanup()
        if hasattr(self, "scene") and self.scene:
            self.scene._cleanup()

    def set_geometry_enabled(self, enabled: bool) -> None:
        """Enable or disable geometry-driven direct simulation."""
        self.geometry_enabled = enabled

    def set_listener(
        self,
        position: Vector3,
        ahead: Vector3 = Vector3(0.0, 0.0, -1.0),
        up: Vector3 = Vector3(0.0, 1.0, 0.0),
    ) -> None:
        """Update the listener transform."""
        self.listener_position = position
        self.listener_ahead = ahead
        self.listener_up = up
        self.simulator.set_listener(position, ahead=ahead, up=up)

    def add_source(self, source_id: int, config: SourceConfig) -> None:
        """Add a source to the environment."""
        if source_id in self._sources:
            raise InvalidParameterError(f"Source already exists: {source_id}")
        self.mixer.add_source(source_id, input_channels=config.input_channels)
        self.simulator.add_source(source_id)
        self._effects[source_id] = DirectEffect()
        self._sources[source_id] = replace(config)

    def remove_source(self, source_id: int) -> None:
        """Remove a source from the environment."""
        self._ensure_source_exists(source_id)
        self.mixer.remove_source(source_id)
        self.simulator.remove_source(source_id)
        self._effects[source_id]._cleanup()
        del self._effects[source_id]
        del self._sources[source_id]
        self._last_direct_params.pop(source_id, None)

    def update_source(self, source_id: int, **changes) -> None:
        """Update fields on an existing source config."""
        config = self._ensure_source_exists(source_id)
        for key, value in changes.items():
            if not hasattr(config, key):
                raise InvalidParameterError(f"Unknown source config field: {key}")
            setattr(config, key, value)

    def update_sources(
        self,
        updates: Mapping[int, SourceConfig | Mapping[str, object]],
    ) -> None:
        """Update multiple registered sources in one call."""
        for source_id, update in updates.items():
            if isinstance(update, SourceConfig):
                self._ensure_source_exists(source_id)
                self._sources[source_id] = replace(update)
                continue

            if not isinstance(update, Mapping):
                raise InvalidParameterError(
                    "Each source update must be a SourceConfig or mapping of field changes"
                )
            self.update_source(source_id, **dict(update))

    def add_static_mesh(
        self,
        vertices: Sequence[Vector3 | Sequence[float]],
        triangles: Sequence[Sequence[int]],
        material_indices: Sequence[int],
        materials: Sequence[object],
    ):
        """Add a static mesh through the environment-owned geometry scene."""
        return self.scene.add_static_mesh(vertices, triangles, material_indices, materials)

    def add_box(
        self,
        min_corner: Vector3 | Sequence[float],
        max_corner: Vector3 | Sequence[float],
        material,
    ):
        """Add a closed box mesh through the environment-owned geometry scene."""
        return self.scene.add_box(min_corner, max_corner, material)

    def add_room(
        self,
        width: float,
        height: float,
        depth: float,
        wall_material,
        floor_material=None,
        ceiling_material=None,
        center: Vector3 | Sequence[float] = Vector3(0.0, 0.0, 0.0),
    ):
        """Add a room shell through the environment-owned geometry scene."""
        return self.scene.add_room(
            width,
            height,
            depth,
            wall_material,
            floor_material=floor_material,
            ceiling_material=ceiling_material,
            center=center,
        )

    def add_wall_with_doorway(
        self,
        axis: str,
        offset: float,
        min_extent: float,
        max_extent: float,
        height: float,
        material,
        doorway_center: float = 0.0,
        doorway_half_width: float = 1.0,
        doorway_height: float = 2.5,
    ):
        """Add a doorway wall through the environment-owned geometry scene."""
        return self.scene.add_wall_with_doorway(
            axis,
            offset,
            min_extent,
            max_extent,
            height,
            material,
            doorway_center=doorway_center,
            doorway_half_width=doorway_half_width,
            doorway_height=doorway_height,
        )

    def commit_geometry(self) -> None:
        """Commit any pending geometry changes for subsequent direct simulation."""
        self.scene.commit()

    def get_last_direct_params(self, source_id: int):
        """Retrieve the latest direct simulation params for a source."""
        return self._last_direct_params.get(source_id)

    def process(self, sources_data: Dict[int, object]) -> object:
        """Run direct simulation, apply direct effects, and mix all sources."""
        if not self._sources:
            raise AudioProcessingError("No sources registered in environment")
        if set(sources_data.keys()) != set(self._sources.keys()):
            raise InvalidParameterError("sources_data keys must match registered sources")

        self.simulator.set_listener(
            self.listener_position,
            ahead=self.listener_ahead,
            up=self.listener_up,
        )

        processed_sources = {}
        spatial_params = {}

        for source_id, config in self._sources.items():
            if self.geometry_enabled:
                self.simulator.set_source(
                    source_id,
                    config.position,
                    ahead=config.ahead,
                    up=config.up,
                    min_distance=config.min_distance,
                    direct_flags=config.direct_flags,
                    occlusion_type=config.occlusion_type,
                    occlusion_radius=config.occlusion_radius,
                    num_occlusion_samples=config.num_occlusion_samples,
                    num_transmission_rays=config.num_transmission_rays,
                )

            params = SpatializationParams()
            params.listener_pos = self.listener_position
            params.listener_forward = self.listener_ahead
            params.listener_up = self.listener_up
            params.sound_pos = config.position
            params.min_distance = config.min_distance
            params.max_distance = 1000.0
            params.rolloff = 1.0
            params.directional_attenuation = 1.0
            spatial_params[source_id] = params

            processed_sources[source_id] = sources_data[source_id]

        if self.geometry_enabled:
            self.simulator.run_direct()
            for source_id in self._sources:
                sim_params = self.simulator.get_direct_params(source_id)
                self._effects[source_id].set_simulation_params(sim_params)
                processed_sources[source_id] = self._effects[source_id].process(processed_sources[source_id])
                self._last_direct_params[source_id] = sim_params
        else:
            self._last_direct_params.clear()

        return self.mixer.process(processed_sources, spatial_params)
