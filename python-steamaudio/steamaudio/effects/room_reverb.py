"""Room reverb effect."""

import numpy as np
from typing import Optional, Dict, Union
from ..core.context import Context
from ..core.exceptions import AudioProcessingError, InvalidParameterError
from ..bindings.loader import get_library
from ..bindings.ctypes_bindings import RoomReverbHandle
import ctypes


class RoomReverb:
    """
    Parametric room reverb effect.
    
    Simulates acoustic reflections and reverberation in a room
    using parametric modeling based on room dimensions and materials.
    
    Example:
        >>> with Context():
        ...     reverb = RoomReverb()
        ...     reverb.set_preset(RoomReverb.PRESET_MEDIUM_ROOM)
        ...     audio = np.random.randn(44100).astype(np.float32)
        ...     output = reverb.process(audio)
    """
    
    # Room presets
    PRESET_SMALL_ROOM = 0
    PRESET_MEDIUM_ROOM = 1
    PRESET_LARGE_ROOM = 2
    PRESET_SMALL_HALL = 3
    PRESET_LARGE_HALL = 4
    PRESET_CATHEDRAL = 5
    PRESET_OUTDOOR = 6
    
    _PRESET_NAMES = {
        0: "Small Room",
        1: "Medium Room",
        2: "Large Room",
        3: "Small Hall",
        4: "Large Hall",
        5: "Cathedral",
        6: "Outdoor",
    }
    
    def __init__(self):
        """
        Initialize room reverb effect.
        
        Raises:
            AudioProcessingError: If reverb creation fails
        """
        if not Context.is_initialized():
            raise AudioProcessingError("Steam Audio context is not initialized")
        
        self._handle: Optional[RoomReverbHandle] = None
        
        try:
            lib = get_library()
            self._handle = lib.room_reverb_create()
            if not self._handle:
                raise AudioProcessingError("Failed to create room reverb")
        except Exception as e:
            raise AudioProcessingError(f"Failed to create room reverb: {e}")
    
    def __del__(self):
        """Cleanup on deletion."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up resources."""
        if self._handle:
            try:
                lib = get_library()
                lib.room_reverb_destroy(self._handle)
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
    
    def set_preset(self, preset: int) -> None:
        """
        Set reverb from a preset.
        
        Args:
            preset: Preset constant (PRESET_*)
        
        Raises:
            InvalidParameterError: If preset is invalid
            AudioProcessingError: If setting preset fails
        """
        if not self._handle:
            raise AudioProcessingError("Reverb has been destroyed")
        
        if preset not in self._PRESET_NAMES:
            raise InvalidParameterError(f"Invalid preset: {preset}")
        
        try:
            lib = get_library()
            lib.room_reverb_set_preset(self._handle, preset)
        except Exception as e:
            raise AudioProcessingError(f"Failed to set reverb preset: {e}")
    
    def set_params(
        self,
        room_width: float,
        room_height: float,
        room_depth: float,
        wall_absorption: float,
        reverb_time: float,
    ) -> None:
        """
        Set custom reverb parameters.
        
        Args:
            room_width: Room width in meters (> 0.1)
            room_height: Room height in meters (> 0.1)
            room_depth: Room depth in meters (> 0.1)
            wall_absorption: Wall absorption coefficient (0.0-1.0)
            reverb_time: Reverb decay time in seconds (0.1-10.0)
        
        Raises:
            InvalidParameterError: If parameters are invalid
            AudioProcessingError: If setting parameters fails
        """
        if not self._handle:
            raise AudioProcessingError("Reverb has been destroyed")
        
        # Validate parameters
        if room_width <= 0.1:
            raise InvalidParameterError(f"room_width must be > 0.1, got {room_width}")
        if room_height <= 0.1:
            raise InvalidParameterError(f"room_height must be > 0.1, got {room_height}")
        if room_depth <= 0.1:
            raise InvalidParameterError(f"room_depth must be > 0.1, got {room_depth}")
        if not (0.0 <= wall_absorption <= 1.0):
            raise InvalidParameterError(
                f"wall_absorption must be 0.0-1.0, got {wall_absorption}"
            )
        if not (0.1 <= reverb_time <= 10.0):
            raise InvalidParameterError(
                f"reverb_time must be 0.1-10.0, got {reverb_time}"
            )
        
        try:
            lib = get_library()
            lib.room_reverb_set_params(
                self._handle,
                room_width,
                room_height,
                room_depth,
                wall_absorption,
                reverb_time,
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to set reverb parameters: {e}")
    
    def get_params(self) -> Dict[str, float]:
        """
        Get current reverb parameters.
        
        Returns:
            Dictionary with keys: room_width, room_height, room_depth,
            wall_absorption, reverb_time
        
        Raises:
            AudioProcessingError: If getting parameters fails
        """
        if not self._handle:
            raise AudioProcessingError("Reverb has been destroyed")
        
        try:
            lib = get_library()
            
            room_width = ctypes.c_float()
            room_height = ctypes.c_float()
            room_depth = ctypes.c_float()
            wall_absorption = ctypes.c_float()
            reverb_time = ctypes.c_float()
            
            lib.room_reverb_get_params(
                self._handle,
                ctypes.byref(room_width),
                ctypes.byref(room_height),
                ctypes.byref(room_depth),
                ctypes.byref(wall_absorption),
                ctypes.byref(reverb_time),
            )
            
            return {
                'room_width': room_width.value,
                'room_height': room_height.value,
                'room_depth': room_depth.value,
                'wall_absorption': wall_absorption.value,
                'reverb_time': reverb_time.value,
            }
        except Exception as e:
            raise AudioProcessingError(f"Failed to get reverb parameters: {e}")
    
    def process(
        self,
        audio_data: Union[np.ndarray, list],
    ) -> np.ndarray:
        """
        Process audio through reverb effect.
        
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
            raise AudioProcessingError("Reverb has been destroyed")
        
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
            lib = get_library()
            
            # Create ctypes pointers
            input_ptr = audio.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            output_ptr = output.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            output_frames = ctypes.c_int(0)
            
            # Call C function
            lib.room_reverb_process(
                self._handle,
                input_ptr,
                frames,
                output_ptr,
                ctypes.byref(output_frames),
            )
            
            return output[:output_frames.value]
        
        except Exception as e:
            raise AudioProcessingError(f"Reverb processing failed: {e}")
