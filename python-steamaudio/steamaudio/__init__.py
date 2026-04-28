"""
Steam Audio Python Library

A high-level, Pythonic wrapper around the Steam Audio C library.
Provides 3D audio spatialization, mixing, and effects processing.

Example:
    >>> import steamaudio
    >>> with steamaudio.Context(sample_rate=44100, frame_size=256):
    ...     processor = steamaudio.AudioProcessor(input_channels=1)
    ...     params = steamaudio.SpatializationParams()
    ...     output = processor.process(audio_data, params)
"""

from .core.context import Context
from .core.exceptions import (
    SteamAudioError,
    AudioProcessingError,
    InitializationError,
    InvalidParameterError,
    ResourceError,
)
from .spatial.vector3 import Vector3
from .spatial.spatialization import SpatializationParams
from .processor.audio_processor import AudioProcessor
from .processor.audio_mixer import AudioMixer
from .scene.geometry_scene import GeometryScene, StaticMesh, Material, MaterialRegistry
from .environment.audio_environment import AudioEnvironment, SourceConfig
from .simulation.direct_simulator import DirectSimulator
from .effects.room_reverb import RoomReverb
from .effects.direct_effect import DirectEffect
from .bindings.ctypes_bindings import (
    DIRECT_EFFECT_APPLY_AIR_ABSORPTION,
    DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION,
    DIRECT_EFFECT_APPLY_DIRECTIVITY,
    DIRECT_EFFECT_APPLY_OCCLUSION,
    DIRECT_EFFECT_APPLY_TRANSMISSION,
    SCENE_OCCLUSION_RAYCAST,
    SCENE_OCCLUSION_VOLUMETRIC,
)

__version__ = "1.1.0"
__author__ = "Steam Audio Contributors"

__all__ = [
    "Context",
    "Vector3",
    "SpatializationParams",
    "AudioProcessor",
    "AudioMixer",
    "GeometryScene",
    "StaticMesh",
    "Material",
    "MaterialRegistry",
    "AudioEnvironment",
    "SourceConfig",
    "DirectSimulator",
    "RoomReverb",
    "DirectEffect",
    "DIRECT_EFFECT_APPLY_AIR_ABSORPTION",
    "DIRECT_EFFECT_APPLY_DISTANCE_ATTENUATION",
    "DIRECT_EFFECT_APPLY_DIRECTIVITY",
    "DIRECT_EFFECT_APPLY_OCCLUSION",
    "DIRECT_EFFECT_APPLY_TRANSMISSION",
    "SCENE_OCCLUSION_RAYCAST",
    "SCENE_OCCLUSION_VOLUMETRIC",
    "SteamAudioError",
    "AudioProcessingError",
    "InitializationError",
    "InvalidParameterError",
    "ResourceError",
]
