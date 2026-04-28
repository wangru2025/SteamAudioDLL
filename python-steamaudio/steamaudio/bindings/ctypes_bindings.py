"""Low-level ctypes bindings to Steam Audio C library."""

import ctypes
from ctypes import c_int, c_float, c_char_p, POINTER, Structure
from . import loader

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


class TriangleIndices(Structure):
    """Triangle index triplet for static meshes."""
    _fields_ = [
        ("indices", c_int * 3),
    ]


class AcousticMaterial(Structure):
    """Acoustic material structure matching the C API."""
    _fields_ = [
        ("absorption_low", c_float),
        ("absorption_mid", c_float),
        ("absorption_high", c_float),
        ("scattering", c_float),
        ("transmission_low", c_float),
        ("transmission_mid", c_float),
        ("transmission_high", c_float),
    ]


class CoordinateSpace(Structure):
    """Position and orientation in world space."""
    _fields_ = [
        ("origin", Vector3),
        ("ahead", Vector3),
        ("up", Vector3),
    ]


class DirectSimulationParams(Structure):
    """Direct-path simulation results from Steam Audio."""
    _fields_ = [
        ("flags", c_int),
        ("transmission_type", c_int),
        ("distance_attenuation", c_float),
        ("air_absorption", c_float * 3),
        ("directivity", c_float),
        ("occlusion", c_float),
        ("transmission", c_float * 3),
    ]


class DirectListenerParams(Structure):
    """Listener parameters for direct simulation."""
    _fields_ = [
        ("listener", CoordinateSpace),
    ]


class DirectSourceParams(Structure):
    """Source parameters for direct simulation."""
    _fields_ = [
        ("source", CoordinateSpace),
        ("min_distance", c_float),
        ("direct_flags", c_int),
        ("occlusion_type", c_int),
        ("occlusion_radius", c_float),
        ("num_occlusion_samples", c_int),
        ("num_transmission_rays", c_int),
    ]


# ============================================================================
# Opaque Handle Types
# ============================================================================

AudioProcessorHandle = ctypes.c_void_p
AudioMixerHandle = ctypes.c_void_p
GeometrySceneHandle = ctypes.c_void_p
StaticMeshHandle = ctypes.c_void_p
DirectSimulatorHandle = ctypes.c_void_p
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

SCENE_OCCLUSION_RAYCAST = 0
SCENE_OCCLUSION_VOLUMETRIC = 1


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
        POINTER(c_int),
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

    # ===== Geometry Scene =====
    lib.geometry_scene_create.argtypes = []
    lib.geometry_scene_create.restype = GeometrySceneHandle

    lib.geometry_scene_destroy.argtypes = [GeometrySceneHandle]
    lib.geometry_scene_destroy.restype = None

    lib.geometry_scene_commit.argtypes = [GeometrySceneHandle]
    lib.geometry_scene_commit.restype = c_int
    lib.geometry_scene_commit.errcheck = _check_error

    lib.geometry_scene_add_static_mesh.argtypes = [
        GeometrySceneHandle,
        POINTER(Vector3),
        c_int,
        POINTER(TriangleIndices),
        c_int,
        POINTER(c_int),
        c_int,
        POINTER(AcousticMaterial),
    ]
    lib.geometry_scene_add_static_mesh.restype = StaticMeshHandle

    lib.geometry_static_mesh_destroy.argtypes = [StaticMeshHandle]
    lib.geometry_static_mesh_destroy.restype = None

    lib.geometry_static_mesh_set_material.argtypes = [
        GeometrySceneHandle,
        StaticMeshHandle,
        c_int,
        POINTER(AcousticMaterial),
    ]
    lib.geometry_static_mesh_set_material.restype = c_int
    lib.geometry_static_mesh_set_material.errcheck = _check_error

    # ===== Direct Simulation =====
    lib.direct_simulator_create.argtypes = [GeometrySceneHandle, c_int]
    lib.direct_simulator_create.restype = DirectSimulatorHandle

    lib.direct_simulator_destroy.argtypes = [DirectSimulatorHandle]
    lib.direct_simulator_destroy.restype = None

    lib.direct_simulator_add_source.argtypes = [DirectSimulatorHandle, c_int]
    lib.direct_simulator_add_source.restype = c_int
    lib.direct_simulator_add_source.errcheck = _check_error

    lib.direct_simulator_remove_source.argtypes = [DirectSimulatorHandle, c_int]
    lib.direct_simulator_remove_source.restype = c_int
    lib.direct_simulator_remove_source.errcheck = _check_error

    lib.direct_simulator_set_listener.argtypes = [
        DirectSimulatorHandle,
        POINTER(DirectListenerParams),
    ]
    lib.direct_simulator_set_listener.restype = c_int
    lib.direct_simulator_set_listener.errcheck = _check_error

    lib.direct_simulator_set_source.argtypes = [
        DirectSimulatorHandle,
        c_int,
        POINTER(DirectSourceParams),
    ]
    lib.direct_simulator_set_source.restype = c_int
    lib.direct_simulator_set_source.errcheck = _check_error

    lib.direct_simulator_run_direct.argtypes = [DirectSimulatorHandle]
    lib.direct_simulator_run_direct.restype = c_int
    lib.direct_simulator_run_direct.errcheck = _check_error

    lib.direct_simulator_get_direct_params.argtypes = [
        DirectSimulatorHandle,
        c_int,
        POINTER(DirectSimulationParams),
    ]
    lib.direct_simulator_get_direct_params.restype = c_int
    lib.direct_simulator_get_direct_params.errcheck = _check_error
    
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

    lib.direct_effect_set_simulation_params.argtypes = [
        DirectEffectHandle,
        POINTER(DirectSimulationParams),
    ]
    lib.direct_effect_set_simulation_params.restype = c_int
    lib.direct_effect_set_simulation_params.errcheck = _check_error
    
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
    lib = loader.get_library()
    msg = lib.steam_audio_get_error_message()
    if msg:
        return msg.decode('utf-8')
    return "Unknown error"
