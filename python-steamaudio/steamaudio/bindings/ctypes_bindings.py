"""Low-level ctypes bindings to Steam Audio C library."""

import ctypes
from ctypes import c_int, c_float, c_char_p, POINTER, Structure

# ============================================================================
# C Structures
# ============================================================================


class Vector3(Structure):
    """3D vector structure matching C API."""
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
        ("z", c_float),
    ]


class AudioFormat(Structure):
    """Audio format structure."""
    _fields_ = [
        ("sample_rate", c_int),
        ("frame_size", c_int),
        ("channels", c_int),
    ]


class SpatializationParams(Structure):
    """Spatialization parameters structure."""
    _fields_ = [
        ("listener_pos", Vector3),
        ("listener_forward", Vector3),
        ("listener_up", Vector3),
        ("sound_pos", Vector3),
        ("min_distance", c_float),
        ("max_distance", c_float),
        ("rolloff", c_float),
        ("directional_attenuation", c_float),
    ]


# ============================================================================
# Opaque Handle Types
# ============================================================================

AudioProcessorHandle = ctypes.c_void_p
AudioMixerHandle = ctypes.c_void_p
RoomReverbHandle = ctypes.c_void_p
DirectEffectHandle = ctypes.c_void_p

# ============================================================================
# Error Codes
# ============================================================================

STEAM_AUDIO_OK = 0
STEAM_AUDIO_ERROR_INIT_FAILED = 1
STEAM_AUDIO_ERROR_INVALID_PARAM = 2
STEAM_AUDIO_ERROR_OUT_OF_MEMORY = 3
STEAM_AUDIO_ERROR_NOT_INITIALIZED = 4
STEAM_AUDIO_ERROR_PROCESSING_FAILED = 5

# ============================================================================
# Room Presets
# ============================================================================

ROOM_PRESET_SMALL_ROOM = 0
ROOM_PRESET_MEDIUM_ROOM = 1
ROOM_PRESET_LARGE_ROOM = 2
ROOM_PRESET_SMALL_HALL = 3
ROOM_PRESET_LARGE_HALL = 4
ROOM_PRESET_CATHEDRAL = 5
ROOM_PRESET_OUTDOOR = 6

# ============================================================================
# Direct Effect Flags
# ============================================================================

DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION = 1 << 0
DIRECT_EFFECT_APPLY_AIR_ABSORPTION = 1 << 1
DIRECT_EFFECT_APPLY_DIRECTIVITY = 1 << 2
DIRECT_EFFECT_APPLY_OCCLUSION = 1 << 3
DIRECT_EFFECT_APPLY_TRANSMISSION = 1 << 4


def _check_error(result, func, args):
    """Check C function return value and raise exception if error."""
    if result != STEAM_AUDIO_OK:
        from ..core.exceptions import AudioProcessingError
        error_msg = get_error_message()
        raise AudioProcessingError(f"Steam Audio error: {error_msg}")
    return result


def setup_library_functions(lib):
    """Setup function signatures for the loaded library."""
    
    # ===== Core Initialization =====
    lib.steam_audio_init.argtypes = [c_int, c_int]
    lib.steam_audio_init.restype = c_int
    lib.steam_audio_init.errcheck = _check_error
    
    lib.steam_audio_shutdown.argtypes = []
    lib.steam_audio_shutdown.restype = None
    
    lib.steam_audio_is_initialized.argtypes = []
    lib.steam_audio_is_initialized.restype = c_int
    
    # ===== Audio Processor =====
    lib.audio_processor_create.argtypes = [c_int, c_int]
    lib.audio_processor_create.restype = AudioProcessorHandle
    
    lib.audio_processor_destroy.argtypes = [AudioProcessorHandle]
    lib.audio_processor_destroy.restype = None
    
    lib.audio_processor_process.argtypes = [
        AudioProcessorHandle,
        POINTER(c_float),
        c_int,
        POINTER(c_float),
        POINTER(c_int),
        POINTER(SpatializationParams),
    ]
    lib.audio_processor_process.restype = c_int
    lib.audio_processor_process.errcheck = _check_error
    
    # ===== HRTF Control =====
    lib.steam_audio_set_hrtf_enabled.argtypes = [c_int]
    lib.steam_audio_set_hrtf_enabled.restype = c_int
    lib.steam_audio_set_hrtf_enabled.errcheck = _check_error
    
    lib.steam_audio_get_hrtf_enabled.argtypes = []
    lib.steam_audio_get_hrtf_enabled.restype = c_int
    
    # ===== Audio Mixer =====
    lib.audio_mixer_create.argtypes = [c_int]
    lib.audio_mixer_create.restype = AudioMixerHandle
    
    lib.audio_mixer_destroy.argtypes = [AudioMixerHandle]
    lib.audio_mixer_destroy.restype = None
    
    lib.audio_mixer_add_source.argtypes = [AudioMixerHandle, c_int, c_int]
    lib.audio_mixer_add_source.restype = c_int
    lib.audio_mixer_add_source.errcheck = _check_error
    
    lib.audio_mixer_remove_source.argtypes = [AudioMixerHandle, c_int]
    lib.audio_mixer_remove_source.restype = c_int
    lib.audio_mixer_remove_source.errcheck = _check_error
    
    lib.audio_mixer_process.argtypes = [
        AudioMixerHandle,
        POINTER(POINTER(c_float)),
        POINTER(c_int),
        c_int,
        POINTER(c_float),
        POINTER(c_int),
        POINTER(SpatializationParams),
    ]
    lib.audio_mixer_process.restype = c_int
    lib.audio_mixer_process.errcheck = _check_error
    
    lib.audio_mixer_get_source_count.argtypes = [AudioMixerHandle]
    lib.audio_mixer_get_source_count.restype = c_int
    
    lib.audio_mixer_get_max_sources.argtypes = [AudioMixerHandle]
    lib.audio_mixer_get_max_sources.restype = c_int
    
    # ===== Room Reverb =====
    lib.room_reverb_create.argtypes = []
    lib.room_reverb_create.restype = RoomReverbHandle
    
    lib.room_reverb_destroy.argtypes = [RoomReverbHandle]
    lib.room_reverb_destroy.restype = None
    
    lib.room_reverb_set_preset.argtypes = [RoomReverbHandle, c_int]
    lib.room_reverb_set_preset.restype = c_int
    lib.room_reverb_set_preset.errcheck = _check_error
    
    lib.room_reverb_set_params.argtypes = [
        RoomReverbHandle,
        c_float,
        c_float,
        c_float,
        c_float,
        c_float,
    ]
    lib.room_reverb_set_params.restype = c_int
    lib.room_reverb_set_params.errcheck = _check_error
    
    lib.room_reverb_get_params.argtypes = [
        RoomReverbHandle,
        POINTER(c_float),
        POINTER(c_float),
        POINTER(c_float),
        POINTER(c_float),
        POINTER(c_float),
    ]
    lib.room_reverb_get_params.restype = c_int
    lib.room_reverb_get_params.errcheck = _check_error
    
    lib.room_reverb_process.argtypes = [
        RoomReverbHandle,
        POINTER(c_float),
        c_int,
        POINTER(c_float),
        POINTER(c_int),
    ]
    lib.room_reverb_process.restype = c_int
    lib.room_reverb_process.errcheck = _check_error
    
    # ===== Direct Effect =====
    lib.direct_effect_create.argtypes = []
    lib.direct_effect_create.restype = DirectEffectHandle
    
    lib.direct_effect_destroy.argtypes = [DirectEffectHandle]
    lib.direct_effect_destroy.restype = None
    
    lib.direct_effect_set_params.argtypes = [
        DirectEffectHandle,
        c_float,
        c_float,
        c_float,
        c_float,
        c_float,
        c_int,
    ]
    lib.direct_effect_set_params.restype = c_int
    lib.direct_effect_set_params.errcheck = _check_error
    
    lib.direct_effect_process.argtypes = [
        DirectEffectHandle,
        POINTER(c_float),
        c_int,
        POINTER(c_float),
        POINTER(c_int),
    ]
    lib.direct_effect_process.restype = c_int
    lib.direct_effect_process.errcheck = _check_error
    
    # ===== Utility =====
    lib.steam_audio_get_error_message.argtypes = []
    lib.steam_audio_get_error_message.restype = c_char_p
    
    lib.steam_audio_get_version.argtypes = []
    lib.steam_audio_get_version.restype = c_char_p


def get_error_message():
    """Get the last error message from Steam Audio."""
    from .loader import get_library
    lib = get_library()
    msg = lib.steam_audio_get_error_message()
    if msg:
        return msg.decode('utf-8')
    return "Unknown error"
