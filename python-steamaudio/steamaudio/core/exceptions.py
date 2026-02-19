"""Custom exceptions for Steam Audio library."""


class SteamAudioError(Exception):
    """Base exception for all Steam Audio errors."""
    pass


class InitializationError(SteamAudioError):
    """Raised when Steam Audio initialization fails."""
    pass


class AudioProcessingError(SteamAudioError):
    """Raised when audio processing fails."""
    pass


class InvalidParameterError(SteamAudioError):
    """Raised when invalid parameters are provided."""
    pass


class ResourceError(SteamAudioError):
    """Raised when resource allocation or management fails."""
    pass
