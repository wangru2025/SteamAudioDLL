"""Multi-source audio mixer."""

import numpy as np
from typing import Dict, Optional, Union
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..spatial.spatialization import SpatializationParams
from ..bindings.loader import get_library
from ..bindings.ctypes_bindings import (
    AudioMixerHandle,
    SpatializationParams as CSpatializationParams,
    Vector3 as CVector3,
)
import ctypes


class AudioMixer:
    """
    Multi-source audio mixer with spatialization.
    
    Mixes multiple audio sources with individual 3D spatialization,
    producing a single stereo output.
    
    Example:
        >>> with Context():
        ...     mixer = AudioMixer(max_sources=8)
        ...     mixer.add_source(0, input_channels=1)
        ...     mixer.add_source(1, input_channels=1)
        ...     
        ...     sources_data = {
        ...         0: audio_chunk_1,
        ...         1: audio_chunk_2,
        ...     }
        ...     params = {
        ...         0: SpatializationParams(...),
        ...         1: SpatializationParams(...),
        ...     }
        ...     
        ...     output = mixer.process(sources_data, params)
    """
    
    def __init__(self, max_sources: int = 32):
        """
        Initialize audio mixer.
        
        Args:
            max_sources: Maximum number of sources (1-256, default: 32)
        
        Raises:
            InvalidParameterError: If max_sources is invalid
            AudioProcessingError: If mixer creation fails
        """
        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")
        
        if not (1 <= max_sources <= 256):
            raise InvalidParameterError(
                f"max_sources must be 1-256, got {max_sources}"
            )
        
        self.max_sources = max_sources
        self._sources: Dict[int, int] = {}  # source_id -> input_channels
        self._handle: Optional[AudioMixerHandle] = None
        
        try:
            lib = get_library()
            self._handle = lib.audio_mixer_create(max_sources)
            if not self._handle:
                raise AudioProcessingError("Failed to create audio mixer")
        except Exception as e:
            raise AudioProcessingError(f"Failed to create audio mixer: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources."""
        if self._handle:
            try:
                lib = get_library()
                lib.audio_mixer_destroy(self._handle)
            except Exception:
                pass
            finally:
                self._handle = None
        self._sources.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup()
    
    def add_source(self, source_id: int, input_channels: int = 1) -> None:
        """
        Add a source to the mixer.
        
        Args:
            source_id: Unique source identifier
            input_channels: Number of input channels (1 or 2, default: 1)
        
        Raises:
            InvalidParameterError: If parameters are invalid
            AudioProcessingError: If adding source fails
        """
        if not self._handle:
            raise AudioProcessingError("Mixer has been destroyed")
        
        if source_id in self._sources:
            raise InvalidParameterError(f"Source {source_id} already exists")
        
        if input_channels not in (1, 2):
            raise InvalidParameterError(
                f"input_channels must be 1 or 2, got {input_channels}"
            )
        
        if len(self._sources) >= self.max_sources:
            raise AudioProcessingError(
                f"Mixer is full (max {self.max_sources} sources)"
            )
        
        try:
            lib = get_library()
            lib.audio_mixer_add_source(self._handle, source_id, input_channels)
            self._sources[source_id] = input_channels
        except Exception as e:
            raise AudioProcessingError(f"Failed to add source: {e}")
    
    def remove_source(self, source_id: int) -> None:
        """
        Remove a source from the mixer.
        
        Args:
            source_id: Source identifier
        
        Raises:
            InvalidParameterError: If source doesn't exist
            AudioProcessingError: If removal fails
        """
        if not self._handle:
            raise AudioProcessingError("Mixer has been destroyed")
        
        if source_id not in self._sources:
            raise InvalidParameterError(f"Source {source_id} not found")
        
        try:
            lib = get_library()
            lib.audio_mixer_remove_source(self._handle, source_id)
            del self._sources[source_id]
        except Exception as e:
            raise AudioProcessingError(f"Failed to remove source: {e}")
    
    def get_source_count(self) -> int:
        """Get number of active sources."""
        return len(self._sources)
    
    def process(
        self,
        sources_data: Dict[int, Union[np.ndarray, list]],
        params: Dict[int, SpatializationParams],
    ) -> np.ndarray:
        """
        Process multiple audio sources and mix them.
        
        Args:
            sources_data: {source_id: audio_data}
                - audio_data shape: (frames,) or (frames, channels)
                - dtype: float32
            params: {source_id: SpatializationParams}
        
        Returns:
            Mixed stereo audio (frames, 2) as float32
        
        Raises:
            InvalidParameterError: If parameters are invalid
            AudioProcessingError: If processing fails
        """
        if not self._handle:
            raise AudioProcessingError("Mixer has been destroyed")
        
        if not sources_data:
            raise InvalidParameterError("sources_data cannot be empty")
        
        if not params:
            raise InvalidParameterError("params cannot be empty")
        
        # Validate sources
        for source_id in sources_data:
            if source_id not in self._sources:
                raise InvalidParameterError(f"Source {source_id} not found in mixer")
        
        # Convert all audio data to numpy arrays
        audio_arrays = {}
        frame_counts = []
        max_frames = 0
        
        for source_id in sorted(sources_data.keys()):
            audio = np.asarray(sources_data[source_id], dtype=np.float32)
            
            # Validate shape
            if audio.ndim == 1:
                frames = len(audio)
            elif audio.ndim == 2:
                frames, channels = audio.shape
                if channels != self._sources[source_id]:
                    raise InvalidParameterError(
                        f"Source {source_id}: expected {self._sources[source_id]} "
                        f"channels, got {channels}"
                    )
                audio = audio.flatten()
            else:
                raise InvalidParameterError(
                    f"Source {source_id}: expected 1D or 2D array, got {audio.ndim}D"
                )
            
            if frames <= 0:
                raise InvalidParameterError(
                    f"Source {source_id}: invalid frame count {frames}"
                )
            
            audio_arrays[source_id] = audio
            frame_counts.append(frames)
            max_frames = max(max_frames, frames)
        
        # Prepare C arrays
        sorted_ids = sorted(sources_data.keys())
        num_sources = len(sorted_ids)
        
        # Create input pointers array
        input_ptrs = (ctypes.POINTER(ctypes.c_float) * num_sources)()
        for i, source_id in enumerate(sorted_ids):
            input_ptrs[i] = audio_arrays[source_id].ctypes.data_as(
                ctypes.POINTER(ctypes.c_float)
            )
        
        # Create frame counts array
        c_frame_counts = (ctypes.c_int * num_sources)(*frame_counts)
        
        # Create parameters array
        c_params_array = (CSpatializationParams * num_sources)()
        for i, source_id in enumerate(sorted_ids):
            c_params_array[i] = self._params_to_c(params[source_id])
        
        # Prepare output buffer
        output = np.zeros(max_frames * 2, dtype=np.float32)
        output_ptr = output.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        output_frames = ctypes.c_int(0)
        
        try:
            lib = get_library()
            lib.audio_mixer_process(
                self._handle,
                input_ptrs,
                c_frame_counts,
                num_sources,
                output_ptr,
                ctypes.byref(output_frames),
                c_params_array,
            )
            
            # Reshape output to (frames, 2)
            return output[:output_frames.value * 2].reshape(-1, 2)
        
        except Exception as e:
            raise AudioProcessingError(f"Mixer processing failed: {e}")
    
    @staticmethod
    def _params_to_c(params: SpatializationParams) -> CSpatializationParams:
        """Convert Python parameters to C structure."""
        c_params = CSpatializationParams()
        
        c_params.listener_pos = CVector3(
            params.listener_pos.x,
            params.listener_pos.y,
            params.listener_pos.z,
        )
        c_params.listener_forward = CVector3(
            params.listener_forward.x,
            params.listener_forward.y,
            params.listener_forward.z,
        )
        c_params.listener_up = CVector3(
            params.listener_up.x,
            params.listener_up.y,
            params.listener_up.z,
        )
        c_params.sound_pos = CVector3(
            params.sound_pos.x,
            params.sound_pos.y,
            params.sound_pos.z,
        )
        c_params.min_distance = params.min_distance
        c_params.max_distance = params.max_distance
        c_params.rolloff = params.rolloff
        c_params.directional_attenuation = params.directional_attenuation
        
        return c_params
