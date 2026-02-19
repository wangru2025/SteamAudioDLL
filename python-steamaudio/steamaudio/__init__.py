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
from .effects.room_reverb import RoomReverb
from .effects.direct_effect import DirectEffect

__version__ = "1.0.0"
__author__ = "Steam Audio Contributors"

__all__ = [
    "Context",
    "Vector3",
    "SpatializationParams",
    "AudioProcessor",
    "AudioMixer",
    "RoomReverb",
    "DirectEffect",
    "SteamAudioError",
    "AudioProcessingError",
    "InitializationError",
    "InvalidParameterError",
    "ResourceError",
]
