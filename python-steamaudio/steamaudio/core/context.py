"""Global Steam Audio context management."""

from typing import Optional
from ..bindings.loader import get_library
from ..core.exceptions import InitializationError


class Context:
    """
    Global Steam Audio context manager.
    
    Handles initialization and cleanup of the Steam Audio system.
    Should be used as a context manager (with statement).
    
    Example:
        >>> with Context(sample_rate=44100, frame_size=256):
        ...     processor = AudioProcessor()
        ...     # Use processor
    """
    
    _instance: Optional['Context'] = None
    _initialized = False
    
    def __init__(self, sample_rate: int = 44100, frame_size: int = 256):
        """
        Initialize Steam Audio context.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
            frame_size: Frame size in samples (default: 256)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if sample_rate <= 0:
            raise ValueError(f"sample_rate must be positive, got {sample_rate}")
        if frame_size <= 0:
            raise ValueError(f"frame_size must be positive, got {frame_size}")
        
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self._initialized = False
    
    def __enter__(self) -> 'Context':
        """Enter context manager - initialize Steam Audio."""
        if Context._initialized:
            raise InitializationError(
                "Steam Audio is already initialized. "
                "Only one Context can be active at a time."
            )
        
        try:
            lib = get_library()
            lib.steam_audio_init(self.sample_rate, self.frame_size)
            Context._initialized = True
            Context._instance = self
            self._initialized = True
            return self
        except Exception as e:
            raise InitializationError(f"Failed to initialize Steam Audio: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - shutdown Steam Audio."""
        if self._initialized:
            try:
                lib = get_library()
                lib.steam_audio_shutdown()
            except Exception as e:
                print(f"Warning: Error during Steam Audio shutdown: {e}")
            finally:
                self._initialized = False
                Context._initialized = False
                Context._instance = None
    
    @staticmethod
    def is_initialized() -> bool:
        """Check if Steam Audio is currently initialized."""
        return Context._initialized
    
    @staticmethod
    def get_instance() -> Optional['Context']:
        """Get the current Context instance."""
        return Context._instance
    
    @staticmethod
    def get_version() -> str:
        """
        Get Steam Audio library version.
        
        Returns:
            Version string
        """
        try:
            lib = get_library()
            version = lib.steam_audio_get_version()
            if version:
                return version.decode('utf-8')
            return "Unknown"
        except Exception:
            return "Unknown"
    
    @staticmethod
    def set_hrtf_enabled(enabled: bool) -> None:
        """
        Enable or disable HRTF (Head-Related Transfer Function).
        
        Args:
            enabled: True to enable HRTF, False to disable
        
        Raises:
            InitializationError: If Steam Audio is not initialized
        """
        if not Context._initialized:
            raise InitializationError("Steam Audio is not initialized")
        
        try:
            lib = get_library()
            lib.steam_audio_set_hrtf_enabled(1 if enabled else 0)
        except Exception as e:
            raise InitializationError(f"Failed to set HRTF: {e}")
    
    @staticmethod
    def get_hrtf_enabled() -> bool:
        """
        Check if HRTF is enabled.
        
        Returns:
            True if HRTF is enabled, False otherwise
        
        Raises:
            InitializationError: If Steam Audio is not initialized
        """
        if not Context._initialized:
            raise InitializationError("Steam Audio is not initialized")
        
        try:
            lib = get_library()
            return lib.steam_audio_get_hrtf_enabled() != 0
        except Exception as e:
            raise InitializationError(f"Failed to get HRTF status: {e}")
