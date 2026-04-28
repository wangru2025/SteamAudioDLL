"""Geometry-driven reflections effect."""

from __future__ import annotations

import ctypes
from typing import Optional, Union

import numpy as np

from ..bindings import loader
from ..bindings.ctypes_bindings import (
    DirectListenerParams as CDirectListenerParams,
    ReflectionEffectHandle,
    Vector3 as CVector3,
    CoordinateSpace as CCoordinateSpace,
)
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..spatial.vector3 import Vector3


class ReflectionEffect:
    """Applies Steam Audio reflection simulation results to a mono source."""

    def __init__(self, max_order: int = 1, max_duration: float = 1.5):
        self._handle: Optional[ReflectionEffectHandle] = None
        self.max_order = max_order
        self.max_duration = max_duration

        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")

        lib = loader.get_library()
        self._handle = lib.reflection_effect_create(max_order, max_duration)
        if not self._handle:
            raise AudioProcessingError("Failed to create reflection effect")

    def __del__(self):
        self._cleanup()

    def _cleanup(self):
        if getattr(self, "_handle", None):
            try:
                loader.get_library().reflection_effect_destroy(self._handle)
            except Exception:
                pass
            finally:
                self._handle = None

    def set_listener(
        self,
        position: Vector3,
        ahead: Vector3 = Vector3(0.0, 0.0, -1.0),
        up: Vector3 = Vector3(0.0, 1.0, 0.0),
    ) -> None:
        if not self._handle:
            raise AudioProcessingError("Reflection effect has been destroyed")

        params = CDirectListenerParams()
        params.listener = self._coord(position, ahead, up)
        loader.get_library().reflection_effect_set_listener(
            self._handle,
            ctypes.pointer(params),
        )

    def set_simulation_output(self, simulator, source_id: int) -> None:
        if not self._handle:
            raise AudioProcessingError("Reflection effect has been destroyed")
        if not getattr(simulator, "_handle", None):
            raise InvalidParameterError("Simulator has been destroyed")

        loader.get_library().reflection_effect_set_simulation_output(
            self._handle,
            simulator._handle,
            source_id,
        )

    def process(self, audio_data: Union[np.ndarray, list]) -> np.ndarray:
        if not self._handle:
            raise AudioProcessingError("Reflection effect has been destroyed")

        audio = np.asarray(audio_data, dtype=np.float32)
        if audio.ndim != 1:
            raise InvalidParameterError(f"Expected 1D mono array, got {audio.ndim}D")
        frames = len(audio)
        if frames <= 0:
            raise InvalidParameterError(f"Invalid frame count: {frames}")

        output = np.zeros(frames * 2, dtype=np.float32)
        output_frames = ctypes.c_int(0)
        loader.get_library().reflection_effect_process(
            self._handle,
            audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            frames,
            output.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            ctypes.pointer(output_frames),
        )
        return output[: output_frames.value * 2].reshape(-1, 2)

    @staticmethod
    def _coord(position: Vector3, ahead: Vector3, up: Vector3) -> CCoordinateSpace:
        coord = CCoordinateSpace()
        coord.origin = CVector3(position.x, position.y, position.z)
        coord.ahead = CVector3(ahead.x, ahead.y, ahead.z)
        coord.up = CVector3(up.x, up.y, up.z)
        return coord
