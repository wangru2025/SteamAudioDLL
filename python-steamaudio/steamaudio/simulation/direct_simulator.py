"""Direct-path simulation backed by Steam Audio."""

from __future__ import annotations

import ctypes
from typing import Dict, Optional

from ..bindings import loader
from ..bindings.ctypes_bindings import (
    CoordinateSpace as CCoordinateSpace,
    DirectListenerParams as CDirectListenerParams,
    DirectSimulationParams as CDirectSimulationParams,
    DirectSimulatorHandle,
    DirectSourceParams as CDirectSourceParams,
    SCENE_OCCLUSION_RAYCAST,
    Vector3 as CVector3,
)
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..spatial.vector3 import Vector3


class DirectSimulator:
    """Steam Audio direct-path simulator using scene geometry."""

    def __init__(self, scene, max_sources: int = 16):
        self._handle: Optional[DirectSimulatorHandle] = None
        self._scene = scene
        self._sources: Dict[int, bool] = {}

        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")
        if not getattr(scene, "_handle", None):
            raise InvalidParameterError("Scene has been destroyed")

        lib = loader.get_library()
        self._handle = lib.direct_simulator_create(scene._handle, max_sources)
        if not self._handle:
            raise AudioProcessingError("Failed to create direct simulator")

    def __del__(self):
        self._cleanup()

    def _cleanup(self):
        if getattr(self, "_handle", None):
            try:
                loader.get_library().direct_simulator_destroy(self._handle)
            except Exception:
                pass
            finally:
                self._handle = None
        self._sources.clear()

    def add_source(self, source_id: int) -> None:
        if not self._handle:
            raise AudioProcessingError("Direct simulator has been destroyed")
        loader.get_library().direct_simulator_add_source(self._handle, source_id)
        self._sources[source_id] = True

    def remove_source(self, source_id: int) -> None:
        if not self._handle:
            raise AudioProcessingError("Direct simulator has been destroyed")
        loader.get_library().direct_simulator_remove_source(self._handle, source_id)
        self._sources.pop(source_id, None)

    def set_listener(
        self,
        position: Vector3,
        ahead: Vector3 = Vector3(0.0, 0.0, -1.0),
        up: Vector3 = Vector3(0.0, 1.0, 0.0),
    ) -> None:
        if not self._handle:
            raise AudioProcessingError("Direct simulator has been destroyed")

        params = CDirectListenerParams()
        params.listener = self._coord(position, ahead, up)
        loader.get_library().direct_simulator_set_listener(self._handle, ctypes.pointer(params))

    def set_source(
        self,
        source_id: int,
        position: Vector3,
        ahead: Vector3 = Vector3(0.0, 0.0, -1.0),
        up: Vector3 = Vector3(0.0, 1.0, 0.0),
        min_distance: float = 1.0,
        direct_flags: int = 0,
        occlusion_type: int = SCENE_OCCLUSION_RAYCAST,
        occlusion_radius: float = 1.0,
        num_occlusion_samples: int = 16,
        num_transmission_rays: int = 8,
    ) -> None:
        if not self._handle:
            raise AudioProcessingError("Direct simulator has been destroyed")
        if source_id not in self._sources:
            raise InvalidParameterError(f"Source {source_id} not found in simulator")

        params = CDirectSourceParams()
        params.source = self._coord(position, ahead, up)
        params.min_distance = min_distance
        params.direct_flags = direct_flags
        params.occlusion_type = occlusion_type
        params.occlusion_radius = occlusion_radius
        params.num_occlusion_samples = num_occlusion_samples
        params.num_transmission_rays = num_transmission_rays
        loader.get_library().direct_simulator_set_source(
            self._handle,
            source_id,
            ctypes.pointer(params),
        )

    def run_direct(self) -> None:
        if not self._handle:
            raise AudioProcessingError("Direct simulator has been destroyed")
        loader.get_library().direct_simulator_run_direct(self._handle)

    def get_direct_params(self, source_id: int) -> CDirectSimulationParams:
        if not self._handle:
            raise AudioProcessingError("Direct simulator has been destroyed")
        if source_id not in self._sources:
            raise InvalidParameterError(f"Source {source_id} not found in simulator")

        params = CDirectSimulationParams()
        loader.get_library().direct_simulator_get_direct_params(
            self._handle,
            source_id,
            ctypes.pointer(params),
        )
        return params

    @staticmethod
    def _coord(position: Vector3, ahead: Vector3, up: Vector3) -> CCoordinateSpace:
        coord = CCoordinateSpace()
        coord.origin = CVector3(position.x, position.y, position.z)
        coord.ahead = CVector3(ahead.x, ahead.y, ahead.z)
        coord.up = CVector3(up.x, up.y, up.z)
        return coord
