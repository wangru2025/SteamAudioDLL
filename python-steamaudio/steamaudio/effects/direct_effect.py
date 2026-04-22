"""Direct effect (occlusion and transmission)."""

import numpy as np
from typing import Optional, Union
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..bindings import loader
from ..bindings.ctypes_bindings import (
    DirectEffectHandle,
    DIRECT_EFFECT_APPLY_AIR_ABSORPTION,
    DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION,
    DIRECT_EFFECT_APPLY_OCCLUSION,
    DIRECT_EFFECT_APPLY_TRANSMISSION,
)
import ctypes


class DirectEffect:
    """
    Direct effect for occlusion and transmission.
    
    Simulates how sound is affected by obstacles and materials,
    including distance attenuation, occlusion, and frequency-dependent
    transmission through materials.
    
    Example:
        >>> with Context():
        ...     effect = DirectEffect()
        ...     effect.set_params(distance=5.0, occlusion=0.5)
        ...     audio = np.random.randn(44100).astype(np.float32)
        ...     output = effect.process(audio)
    """
    
    def __init__(self):
        """
        Initialize direct effect.
        
        Raises:
            AudioProcessingError: If effect creation fails
        """
        self._handle: Optional[DirectEffectHandle] = None

        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")

        try:
            lib = loader.get_library()
            self._handle = lib.direct_effect_create()
            if not self._handle:
                raise AudioProcessingError("Failed to create direct effect")
        except Exception as e:
            raise AudioProcessingError(f"Failed to create direct effect: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources."""
        if getattr(self, "_handle", None):
            try:
                lib = loader.get_library()
                lib.direct_effect_destroy(self._handle)
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
    
    def set_params(
        self,
        distance: float,
        occlusion: float = 0.0,
        transmission_low: float = 1.0,
        transmission_mid: float = 1.0,
        transmission_high: float = 1.0,
    ) -> None:
        """
        Set direct effect parameters.
        
        Args:
            distance: Distance from source to listener in meters (> 0.1)
            occlusion: Occlusion factor (0.0-1.0, default: 0.0)
                - 0.0: no occlusion
                - 1.0: fully occluded
            transmission_low: Transmission at low frequencies (0.0-1.0, default: 1.0)
            transmission_mid: Transmission at mid frequencies (0.0-1.0, default: 1.0)
            transmission_high: Transmission at high frequencies (0.0-1.0, default: 1.0)
        
        Raises:
            InvalidParameterError: If parameters are invalid
            AudioProcessingError: If setting parameters fails
        """
        if not self._handle:
            raise AudioProcessingError("Effect has been destroyed")
        
        # Validate parameters
        if distance <= 0.1:
            raise InvalidParameterError(f"distance must be > 0.1, got {distance}")
        if not (0.0 <= occlusion <= 1.0):
            raise InvalidParameterError(
                f"occlusion must be 0.0-1.0, got {occlusion}"
            )
        if not (0.0 <= transmission_low <= 1.0):
            raise InvalidParameterError(
                f"transmission_low must be 0.0-1.0, got {transmission_low}"
            )
        if not (0.0 <= transmission_mid <= 1.0):
            raise InvalidParameterError(
                f"transmission_mid must be 0.0-1.0, got {transmission_mid}"
            )
        if not (0.0 <= transmission_high <= 1.0):
            raise InvalidParameterError(
                f"transmission_high must be 0.0-1.0, got {transmission_high}"
            )
        
        try:
            lib = loader.get_library()
            lib.direct_effect_set_params(
                self._handle,
                distance,
                occlusion,
                transmission_low,
                transmission_mid,
                transmission_high,
                DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION
                | DIRECT_EFFECT_APPLY_AIR_ABSORPTION
                | DIRECT_EFFECT_APPLY_OCCLUSION
                | DIRECT_EFFECT_APPLY_TRANSMISSION,
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to set direct effect parameters: {e}")
    
    def process(
        self,
        audio_data: Union[np.ndarray, list],
    ) -> np.ndarray:
        """
        Process audio through direct effect.
        
        Args:
            audio_data: Input audio as numpy array or list
                - Shape: (frames,) for mono
                - dtype: float32
        
        Returns:
            Processed audio (frames,) as float32
        
        Raises:
            InvalidParameterError: If parameters are invalid
            AudioProcessingError: If processing fails
        """
        if not self._handle:
            raise AudioProcessingError("Effect has been destroyed")
        
        # Convert input to numpy array
        audio = np.asarray(audio_data, dtype=np.float32)
        
        # Validate input shape
        if audio.ndim != 1:
            raise InvalidParameterError(
                f"Expected 1D array, got {audio.ndim}D"
            )
        
        frames = len(audio)
        if frames <= 0:
            raise InvalidParameterError(f"Invalid frame count: {frames}")
        
        # Prepare output buffer
        output = np.zeros(frames, dtype=np.float32)
        
        try:
            lib = loader.get_library()
            
            # Create ctypes pointers
            input_ptr = audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            output_ptr = output.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            output_frames = ctypes.c_int(0)
            
            # Call C function
            lib.direct_effect_process(
                self._handle,
                input_ptr,
                frames,
                output_ptr,
                ctypes.pointer(output_frames),
            )
            
            return output[:output_frames.value]
        
        except Exception as e:
            raise AudioProcessingError(f"Direct effect processing failed: {e}")
