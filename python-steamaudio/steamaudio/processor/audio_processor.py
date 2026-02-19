"""Single-source audio processor."""

import numpy as np
from typing import Optional, Union
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..spatial.spatialization import SpatializationParams
from ..bindings.loader import get_library
from ..bindings.ctypes_bindings import (
    AudioProcessorHandle,
    SpatializationParams as CSpatializationParams,
    Vector3 as CVector3,
)
import ctypes


class AudioProcessor:
    """
    Single-source audio processor with spatialization.
    
    Processes audio from a single source with 3D spatialization,
    including HRTF binaural rendering and distance attenuation.
    
    Example:
        >>> with Context():
        ...     processor = AudioProcessor(input_channels=1)
        ...     params = SpatializationParams()
        ...     audio = np.random.randn(44100).astype(np.float32)
        ...     output = processor.process(audio, params)
    """
    
    def __init__(self, input_channels: int = 1):
        """
        Initialize audio processor.
        
        Args:
            input_channels: Number of input channels (1 or 2, default: 1)
        
        Raises:
            InvalidParameterError: If input_channels is invalid
            AudioProcessingError: If processor creation fails
        """
        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")
        
        if input_channels not in (1, 2):
            raise InvalidParameterError(
                f"input_channels must be 1 or 2, got {input_channels}"
            )
        
        self.input_channels = input_channels
        self._handle: Optional[AudioProcessorHandle] = None
        
        try:
            lib = get_library()
            self._handle = lib.audio_processor_create(input_channels, 2)
            if not self._handle:
                raise AudioProcessingError("Failed to create audio processor")
        except Exception as e:
            raise AudioProcessingError(f"Failed to create audio processor: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources."""
        if self._handle:
            try:
                lib = get_library()
                lib.audio_processor_destroy(self._handle)
            except Exception:
                pass
            finally:
                self._handle = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._cleanup()
    
    def process(
        self,
        audio_data: Union[np.ndarray, list],
        params: SpatializationParams,
    ) -> np.ndarray:
        """
        Process audio with spatialization.
        
        Args:
            audio_data: Input audio as numpy array or list
                - Shape: (frames,) for mono or (frames, channels) for multi-channel
                - dtype: float32
            params: Spatialization parameters
        
        Returns:
            Processed stereo audio (frames, 2) as float32
        
        Raises:
            InvalidParameterError: If parameters are invalid
            AudioProcessingError: If processing fails
        """
        if not self._handle:
            raise AudioProcessingError("Processor has been destroyed")
        
        # Convert input to numpy array
        audio = np.asarray(audio_data, dtype=np.float32)
        
        # Validate input shape
        if audio.ndim == 1:
            if self.input_channels != 1:
                raise InvalidParameterError(
                    f"Expected {self.input_channels} channels, got 1D array"
                )
            frames = len(audio)
        elif audio.ndim == 2:
            frames, channels = audio.shape
            if channels != self.input_channels:
                raise InvalidParameterError(
                    f"Expected {self.input_channels} channels, got {channels}"
                )
        else:
            raise InvalidParameterError(
                f"Expected 1D or 2D array, got {audio.ndim}D"
            )
        
        if frames <= 0:
            raise InvalidParameterError(f"Invalid frame count: {frames}")
        
        # Flatten to 1D if needed
        if audio.ndim == 2:
            audio = audio.flatten()
        
        # Prepare output buffer
        output = np.zeros(frames * 2, dtype=np.float32)
        
        # Convert parameters to C structure
        c_params = self._params_to_c(params)
        
        try:
            lib = get_library()
            
            # Create ctypes pointers
            input_ptr = audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            output_ptr = output.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            output_frames = ctypes.c_int(0)
            
            # Call C function
            lib.audio_processor_process(
                self._handle,
                input_ptr,
                frames,
                output_ptr,
                ctypes.byref(output_frames),
                ctypes.byref(c_params),
            )
            
            # Reshape output to (frames, 2)
            return output[:output_frames.value * 2].reshape(-1, 2)
        
        except Exception as e:
            raise AudioProcessingError(f"Audio processing failed: {e}")
    
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
