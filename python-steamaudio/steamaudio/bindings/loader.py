"""DLL loader for Steam Audio library."""

import ctypes
import platform
import os
from pathlib import Path
from ..core.exceptions import InitializationError
from .ctypes_bindings import setup_library_functions

_library = None
_library_lock = None


def _get_library_name():
    """Get the platform-specific library name."""
    system = platform.system()
    
    if system == "Windows":
        return "SteamAudioDLL.dll"
    elif system == "Darwin":
        return "libSteamAudioDLL.dylib"
    elif system == "Linux":
        return "libSteamAudioDLL.so"
    else:
        raise InitializationError(f"Unsupported platform: {system}")


def _find_library():
    """Find the Steam Audio library in common locations."""
    lib_name = _get_library_name()
    candidate_names = [lib_name]
    if platform.system() == "Windows":
        candidate_names.append("libSteamAudioDLL.dll")
    
    # Search paths - prioritize package directory
    search_paths = [
        # First, check package directory (for installed package)
        Path(__file__).parent / "dll",
        # Then check relative to package root
        Path(__file__).parent.parent / "bindings" / "dll",
        # Then check current working directory
        Path.cwd(),
        Path.cwd() / "lib",
        Path.cwd() / "libs",
        Path.cwd() / "build" / "bin",
        Path.cwd() / "build" / "bin" / "Release",
        Path.cwd() / "build" / "Release",
        # Finally check system paths
        Path(__file__).parent.parent / "lib",
        Path(__file__).parent.parent / "build" / "bin",
        Path(__file__).parent.parent / "build" / "bin" / "Release",
    ]
    
    # Add system library paths
    if platform.system() == "Windows":
        search_paths.extend([
            Path(os.environ.get("PROGRAMFILES", "")) / "Steam Audio",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Steam Audio",
        ])
    
    for path in search_paths:
        for candidate in candidate_names:
            lib_path = path / candidate
            if lib_path.exists():
                return str(lib_path)
    
    # Try loading from system path
    for candidate in candidate_names:
        try:
            ctypes.CDLL(candidate)
            return candidate
        except OSError:
            pass
    
    raise InitializationError(
        f"Could not find Steam Audio library '{lib_name}'. "
        f"Please ensure it is installed and in the library search path."
    )


def load_library():
    """Load the Steam Audio library and setup function signatures."""
    global _library
    
    if _library is not None:
        return _library
    
    try:
        lib_path = _find_library()
        _library = ctypes.CDLL(lib_path)
        setup_library_functions(_library)
        return _library
    except OSError as e:
        raise InitializationError(f"Failed to load Steam Audio library: {e}")


def get_library():
    """Get the loaded Steam Audio library."""
    global _library
    
    if _library is None:
        load_library()
    
    return _library


def unload_library():
    """Unload the Steam Audio library."""
    global _library
    _library = None
